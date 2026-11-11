"""Split each municipality into ~1.5km blocks from shop coordinates.

None of the KEPCO, MOLIT, or LH public files publish alley electricity.
The block color starts from the municipality vitality and moves with
how many shops sit in that block. That shift is labeled as inference.
"""

from __future__ import annotations

import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.geoquery import _bbox, _contains

OUT = ROOT / "public" / "data" / "processed"
PACK = struct.Struct("<bii")
CELL = 0.015
MIN_SHOPS = 4


def locate(polys: list[dict], lng: float, lat: float) -> dict | None:
    for poly in polys:
        minx, miny, maxx, maxy = poly["bbox"]
        if lng < minx or lng > maxx or lat < miny or lat > maxy:
            continue
        if _contains(poly["geometry"], lng, lat):
            return poly
    return None


def main() -> None:
    geo = json.loads((OUT / "national_map.geojson").read_text(encoding="utf-8"))
    power = {
        (row["sido"], row["name"]): row
        for row in json.loads((OUT / "national_power.json").read_text(encoding="utf-8"))["areas"]
    }
    polys = [
        {
            "sido": feat["properties"]["sido"],
            "name": feat["properties"]["name"],
            "bbox": _bbox(feat["geometry"]),
            "geometry": feat["geometry"],
        }
        for feat in geo["features"]
    ]
    blob = (OUT / "national_stores.bin").read_bytes()
    count = struct.unpack_from("<I", blob, 4)[0]
    cells: dict[tuple[int, int], int] = defaultdict(int)
    offset = 8
    for _ in range(count):
        _code, lat_e6, lng_e6 = PACK.unpack_from(blob, offset)
        offset += PACK.size
        cells[(lat_e6 // 15_000, lng_e6 // 15_000)] += 1

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    missed = 0
    for (ilat, ilng), shops in cells.items():
        if shops < MIN_SHOPS:
            continue
        south = ilat * CELL
        west = ilng * CELL
        lat = south + CELL / 2
        lng = west + CELL / 2
        parent = locate(polys, lng, lat)
        if parent is None:
            missed += 1
            continue
        grouped[(parent["sido"], parent["name"])].append(
            {"south": south, "west": west, "lat": round(lat, 5), "lng": round(lng, 5), "stores": shops}
        )

    features = []
    for key, blocks in grouped.items():
        parent = power.get(key)
        if parent is None:
            continue
        base = int(parent.get("vitalRank") or 3)
        ordered = sorted(blocks, key=lambda row: row["stores"])
        total = len(ordered)
        for index, block in enumerate(ordered):
            local = min(5, index * 5 // total + 1)
            rank = min(5, max(1, base + local - 3))
            south, west = block["south"], block["west"]
            north, east = round(south + CELL, 5), round(west + CELL, 5)
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "lat": block["lat"],
                        "lng": block["lng"],
                        "stores": block["stores"],
                        "vitalRank": rank,
                        "sido": key[0],
                        "name": key[1],
                        "score": parent.get("score"),
                        "kind": "추론",
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
                    },
                }
            )

    (OUT / "alley_grid.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )
    print("cells", len(features), "missed", missed)


if __name__ == "__main__":
    main()
