# Count national shops and keep coordinates for the startup trades.
"""Count national shops from the SEMAS September 2026 store file.

Coordinates are kept for the startup trades so a typed address can be
queried. Every other shop is counted toward the municipality total.
"""

from __future__ import annotations

import csv
import io
import json
import struct
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.geoquery import _bbox, _contains
from backend.industry_catalog import INDUSTRY_IDS, classify, public_rows
from build_national_map import ALT, PARTS

RAW = ROOT / "public" / "data" / "raw" / "sbiz_stores_20260930.zip"
OUT = ROOT / "public" / "data" / "processed"
PACK = struct.Struct("<bii")
CODE = {name: index for index, name in enumerate(INDUSTRY_IDS)}


def main() -> None:
    power = json.loads((OUT / "national_power.json").read_text(encoding="utf-8"))["areas"]
    kepco = {(row["sido"], row["name"]): row for row in power}
    parents: dict[tuple[str, str], tuple[str, str]] = {}
    for (sido, city), parts in PARTS.items():
        for part in parts:
            parents[(sido, part)] = (sido, city)
            spaced = part.replace(city, f"{city} ", 1) if part.startswith(city) else part
            parents[(sido, spaced.replace(" ", ""))] = (sido, city)
    parents[("인천광역시", "남구")] = ("인천광역시", "미추홀구")
    parents[("경상북도", "군위군")] = ("대구광역시", "군위군")

    def canon(sido: str, name: str) -> tuple[str, str, bool]:
        sido = ALT.get(sido.strip(), sido.strip())
        name = name.strip()
        compact = name.replace(" ", "")
        if (sido, name) in kepco:
            return sido, name, True
        if (sido, compact) in kepco:
            return sido, compact, True
        parent = parents.get((sido, compact)) or parents.get((sido, name))
        if parent and parent in kepco:
            return parent[0], parent[1], True
        for (ps, city), parts in PARTS.items():
            if ps != sido:
                continue
            for part in parts:
                tail = part[len(city) :]
                if compact == tail or name == tail:
                    return ps, city, True
        return sido, name, False

    areas: list[dict] = []
    index_of: dict[tuple[str, str], int] = {}
    unmatched: Counter[str] = Counter()
    small_names: Counter[str] = Counter()
    points = bytearray()
    matched = 0
    total = 0
    geo = json.loads((OUT / "national_map.geojson").read_text(encoding="utf-8"))
    polys = [
        {
            "sido": feat["properties"]["sido"],
            "name": feat["properties"]["name"],
            "bbox": _bbox(feat["geometry"]),
            "geometry": feat["geometry"],
        }
        for feat in geo["features"]
    ]
    placed: dict[tuple[str, str], tuple[str, str] | None] = {}

    def snap(sido: str, name: str, lng: float, lat: float) -> tuple[str, str] | None:
        key = (sido, name)
        if key in placed:
            return placed[key]
        found = None
        for poly in polys:
            minx, miny, maxx, maxy = poly["bbox"]
            if lng < minx or lng > maxx or lat < miny or lat > maxy:
                continue
            if _contains(poly["geometry"], lng, lat):
                found = (poly["sido"], poly["name"])
                break
        placed[key] = found
        return found

    with zipfile.ZipFile(RAW) as zf:
        files = [info for info in zf.infolist() if info.filename.lower().endswith(".csv")]
        for info in files:
            print("read", Path(info.filename).name, flush=True)
            with zf.open(info) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                header = next(reader)
                col = {name: i for i, name in enumerate(header)}
                i_sido = col["시도명"]
                i_name = col["시군구명"]
                i_small = col["상권업종소분류명"]
                i_mid = col["상권업종중분류명"]
                i_lng = col["경도"]
                i_lat = col["위도"]
                for row in reader:
                    if len(row) <= i_lat:
                        continue
                    total += 1
                    raw_sido = row[i_sido].strip()
                    raw_name = row[i_name].strip()
                    sido, name, ok = canon(raw_sido, raw_name)
                    if not ok:
                        try:
                            lng = float(row[i_lng])
                            lat = float(row[i_lat])
                        except ValueError:
                            lng = lat = 0.0
                        if 124 < lng < 132 and 33 < lat < 39.5:
                            hit = snap(raw_sido, raw_name, lng, lat)
                            if hit:
                                sido, name, ok = hit[0], hit[1], True
                    key = (sido, name)
                    slot = index_of.get(key)
                    if slot is None:
                        slot = len(areas)
                        index_of[key] = slot
                        areas.append(
                            {
                                "sido": sido,
                                "name": name,
                                "kepco": ok,
                                "allStores": 0,
                                "byIndustry": {ind: 0 for ind in INDUSTRY_IDS},
                            }
                        )
                        if not ok:
                            unmatched[f"{sido} {name}"] += 0
                    area = areas[slot]
                    area["allStores"] += 1
                    if not ok:
                        unmatched[f"{sido} {name}"] += 1
                    kind = classify(row[i_small], row[i_mid])
                    small_names[row[i_small].strip()] += 1
                    if not kind:
                        continue
                    try:
                        lng = float(row[i_lng])
                        lat = float(row[i_lat])
                    except ValueError:
                        continue
                    if not (124 < lng < 132 and 33 < lat < 39.5):
                        continue
                    area["byIndustry"][kind] += 1
                    points += PACK.pack(CODE[kind], int(round(lat * 1_000_000)), int(round(lng * 1_000_000)))
                    matched += 1

    blob = OUT / "national_stores.bin"
    blob.write_bytes(b"PTS1" + struct.pack("<I", matched) + points)
    summary = {
        "source": "소상공인시장진흥공단 상가(상권)정보 2026-09-30",
        "industries": INDUSTRY_IDS,
        "totalStores": total,
        "matchedStores": matched,
        "areas": areas,
    }
    (OUT / "national_stores.json").write_text(
        json.dumps(summary, ensure_ascii=False),
        encoding="utf-8",
    )
    rows = []
    for area in areas:
        if not area["kepco"]:
            continue
        for ind in INDUSTRY_IDS:
            count = area["byIndustry"][ind]
            if not count:
                continue
            rows.append(
                {
                    "district": f"{area['sido']} {area['name']}",
                    "industry": ind,
                    "stores": count,
                    "allStores": area["allStores"],
                }
            )
    (OUT / "browse" / "national_stores.json").write_text(
        json.dumps(
            {
                "columns": ["district", "industry", "stores", "allStores"],
                "rows": rows,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    catalog_path = OUT / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    item = {
        "id": "sbiz-stores",
        "priority": 1,
        "title": "전국 상가업소",
        "owner": "소상공인시장진흥공단",
        "purpose": "서울 밖 점포 수와, 입력한 주소 1km 안의 업종 점포",
        "grain": "업소 · 좌표 · 2026-09-30",
        "cadence": "분기",
        "status": f"전국 {total:,}곳 집계, 창업 업종 좌표 {matched:,}곳",
        "usedIn": ["창업 계산 위치 조회", "시군구 점포 수"],
        "url": "https://www.data.go.kr/data/15083033/fileData.do",
        "localFiles": ["raw/sbiz_stores_20260930.zip"],
        "browse": "browse/national_stores.json",
        "rowCount": len(rows),
        "notes": "매출·개폐업·유동은 이 파일에 없습니다. 그 셋은 서울 열린데이터만 씁니다.",
    }
    catalog["items"] = [row for row in catalog["items"] if row["id"] != "sbiz-stores"]
    catalog["items"].append(item)
    for row in catalog["items"]:
        if row["id"] == "kepco-contract":
            row["notes"] = "지도와 창업 계산은 2026-06 일반용을 전국 시군구에 씁니다. 목록 표는 서울 행입니다."
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    report = Path(__file__).with_name("_store_report.txt")
    lines = [
        f"total {total}",
        f"matched {matched}",
        f"areas {len(areas)} kepco {sum(1 for a in areas if a['kepco'])}",
        "unmatched",
    ]
    for name, count in unmatched.most_common(40):
        lines.append(f"  {count} {name}")
    lines.append("small names")
    for name, count in small_names.most_common(60):
        lines.append(f"  {count} {name}")
    report.write_text("\n".join(lines), encoding="utf-8")
    (OUT / "industries.json").write_text(
        json.dumps({"industries": public_rows()}, ensure_ascii=False),
        encoding="utf-8",
    )
    print("matched", matched, "areas", len(areas), "trades", len(INDUSTRY_IDS))


if __name__ == "__main__":
    main()
