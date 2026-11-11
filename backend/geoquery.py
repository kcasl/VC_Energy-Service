"""Resolve a typed place and count nearby shops.

Shop coordinates come from the SEMAS national file. The municipality
comes from the same boundaries the map paints.
"""

from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "public" / "data" / "processed"
PACK = struct.Struct("<bii")
CELL = 0.01
RADIUS_M = 1000

INDUSTRY_IDS: list[str] = []
AREAS: list[dict] = []
POWER: dict[tuple[str, str], dict] = {}
POLYS: list[dict] = []
GRID: dict[int, dict[tuple[int, int], list[tuple[int, int]]]] = {}
NEAR: dict[tuple[str, str, str], int] = {}
READY = False


def _bbox(geom: dict) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []

    def walk(node) -> None:
        if isinstance(node[0], (int, float)):
            xs.append(node[0])
            ys.append(node[1])
            return
        for child in node:
            walk(child)

    walk(geom["coordinates"])
    return min(xs), min(ys), max(xs), max(ys)


def _inside(lng: float, lat: float, ring: list) -> bool:
    hit = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def _contains(geom: dict, lng: float, lat: float) -> bool:
    if geom["type"] == "Polygon":
        return _inside(lng, lat, geom["coordinates"][0])
    return any(_inside(lng, lat, poly[0]) for poly in geom["coordinates"])


def load() -> None:
    global READY, INDUSTRY_IDS, AREAS, POWER, POLYS, GRID
    summary = json.loads((PROCESSED / "national_stores.json").read_text(encoding="utf-8"))
    power = json.loads((PROCESSED / "national_power.json").read_text(encoding="utf-8"))
    geo = json.loads((PROCESSED / "national_map.geojson").read_text(encoding="utf-8"))
    blob = (PROCESSED / "national_stores.bin").read_bytes()
    count = struct.unpack_from("<I", blob, 4)[0]
    INDUSTRY_IDS = summary["industries"]
    AREAS = summary["areas"]
    POWER = {(row["sido"], row["name"]): row for row in power["areas"]}
    POLYS = []
    for feat in geo["features"]:
        props = feat["properties"]
        POLYS.append(
            {
                "sido": props["sido"],
                "name": props["name"],
                "lat": props["lat"],
                "lng": props["lng"],
                "gwh": props["gwh"],
                "rankLevel": props["rankLevel"],
                "bbox": _bbox(feat["geometry"]),
                "geometry": feat["geometry"],
            }
        )
    GRID = {index: {} for index in range(len(INDUSTRY_IDS))}
    offset = 8
    for _ in range(count):
        code, lat_e6, lng_e6 = PACK.unpack_from(blob, offset)
        offset += PACK.size
        cell = (lat_e6 // 10_000, lng_e6 // 10_000)
        GRID[code].setdefault(cell, []).append((lat_e6, lng_e6))
    NEAR.clear()
    for poly in POLYS:
        for industry_id in INDUSTRY_IDS:
            NEAR[(poly["sido"], poly["name"], industry_id)] = count_near(
                industry_id, poly["lat"], poly["lng"]
            )
    READY = True


def count_near(industry_id: str, lat: float, lng: float, radius_m: int = RADIUS_M) -> int:
    code = INDUSTRY_IDS.index(industry_id)
    lat_e6 = int(round(lat * 1_000_000))
    lng_e6 = int(round(lng * 1_000_000))
    span = int(radius_m / 111_000 / CELL) + 1
    base_lat = lat_e6 // 10_000
    base_lng = lng_e6 // 10_000
    limit = radius_m * radius_m
    cos_lat = math.cos(math.radians(lat))
    found = 0
    cells = GRID[code]
    for dy in range(-span, span + 1):
        for dx in range(-span, span + 1):
            for plat, plng in cells.get((base_lat + dy, base_lng + dx), ()):
                north = (plat - lat_e6) * 0.11054
                east = (plng - lng_e6) * 0.11132 * cos_lat
                if north * north + east * east <= limit:
                    found += 1
    return found


def locate(lng: float, lat: float) -> dict | None:
    for poly in POLYS:
        minx, miny, maxx, maxy = poly["bbox"]
        if lng < minx or lng > maxx or lat < miny or lat > maxy:
            continue
        if _contains(poly["geometry"], lng, lat):
            return poly
    return None


def match_name(query: str) -> dict | None:
    hits = [poly for poly in POLYS if poly["name"] and poly["name"] in query]
    if not hits:
        compact = query.replace(" ", "")
        hits = [poly for poly in POLYS if poly["name"].replace(" ", "") in compact]
    if not hits:
        return None
    hits.sort(key=lambda poly: len(poly["name"]), reverse=True)
    best_len = len(hits[0]["name"])
    hits = [poly for poly in hits if len(poly["name"]) == best_len]
    if len(hits) == 1:
        return hits[0]
    narrowed = [poly for poly in hits if poly["sido"][:2] in query or poly["sido"] in query]
    if len(narrowed) == 1:
        return narrowed[0]
    return None


def geocode(query: str) -> dict | None:
    url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "limit": "1",
            "countrycodes": "kr",
            "accept-language": "ko",
        }
    )
    req = Request(url, headers={"User-Agent": "vc03-commercial-vitality/1.0 (local)"})
    try:
        with urlopen(req, timeout=12) as res:
            rows = json.loads(res.read().decode())
    except Exception:
        return None
    if not rows:
        return None
    row = rows[0]
    return {
        "lat": float(row["lat"]),
        "lng": float(row["lon"]),
        "label": row.get("display_name") or query,
    }


def area_row(sido: str, name: str) -> dict | None:
    for area in AREAS:
        if area["sido"] == sido and area["name"] == name and area.get("kepco"):
            return area
    return None
