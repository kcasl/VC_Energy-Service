"""Paint every municipality from KEPCO June 2026 commercial kWh.

Seoul keeps the vitality score already built. Other regions have no
store, sales, or footfall tables, so those fields stay empty.
"""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "public" / "data" / "raw"
OUT = ROOT / "public" / "data" / "processed"

SIDO = {
    "11": "서울특별시",
    "21": "부산광역시",
    "22": "대구광역시",
    "23": "인천광역시",
    "24": "광주광역시",
    "25": "대전광역시",
    "26": "울산광역시",
    "29": "세종특별자치시",
    "31": "경기도",
    "32": "강원특별자치도",
    "33": "충청북도",
    "34": "충청남도",
    "35": "전북특별자치도",
    "36": "전라남도",
    "37": "경상북도",
    "38": "경상남도",
    "39": "제주특별자치도",
}
ALT = {"강원도": "강원특별자치도", "전라북도": "전북특별자치도", "제주도": "제주특별자치도"}
# KEPCO publishes these as one city. The 2018 boundary file splits them into gu.
PARTS = {
    ("경기도", "고양시"): ["고양시덕양구", "고양시일산동구", "고양시일산서구"],
    ("경기도", "성남시"): ["성남시분당구", "성남시수정구", "성남시중원구"],
    ("경기도", "수원시"): ["수원시권선구", "수원시영통구", "수원시장안구", "수원시팔달구"],
    ("경기도", "안산시"): ["안산시단원구", "안산시상록구"],
    ("경기도", "안양시"): ["안양시동안구", "안양시만안구"],
    ("경기도", "용인시"): ["용인시기흥구", "용인시수지구", "용인시처인구"],
    ("경상남도", "창원시"): ["창원시마산합포구", "창원시마산회원구", "창원시성산구", "창원시의창구", "창원시진해구"],
    ("경상북도", "포항시"): ["포항시남구", "포항시북구"],
    ("전북특별자치도", "전주시"): ["전주시덕진구", "전주시완산구"],
    ("충청남도", "천안시"): ["천안시동남구", "천안시서북구"],
    ("충청북도", "청주시"): ["청주시상당구", "청주시서원구", "청주시청원구", "청주시흥덕구"],
}
# Boundary file still uses the old name or the old province.
RENAME = {
    ("인천광역시", "미추홀구"): ("인천광역시", "남구"),
    ("대구광역시", "군위군"): ("경상북도", "군위군"),
}


def june_commercial() -> dict[tuple[str, str], int]:
    path = RAW / "kepco_sigungu_202608.xlsx"
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    header = None
    found: dict[tuple[str, str], int] = {}
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == "연도":
            header = list(row)
            continue
        if header is None or not row or row[0] != 2026:
            continue
        if str(row[3]).replace(" ", "") != "일반용":
            continue
        kwh = int(row[header.index("6월")] or 0)
        if kwh <= 0:
            continue
        sido = ALT.get(str(row[1]).strip(), str(row[1]).strip())
        found[(sido, str(row[2]).strip())] = kwh
    wb.close()
    return found


def rings(geom: dict) -> list:
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return list(geom["coordinates"])
    raise SystemExit(geom["type"])


def centroid(geom: dict) -> tuple[float, float]:
    points = []
    for poly in rings(geom):
        for lng, lat in poly[0]:
            points.append((lat, lng))
    lat = sum(p[0] for p in points) / len(points)
    lng = sum(p[1] for p in points) / len(points)
    return round(lat, 4), round(lng, 4)


def main() -> None:
    power = june_commercial()
    geo = json.loads((RAW / "skorea_municipalities.geojson").read_text(encoding="utf-8"))
    seoul = {
        row["name"]: row
        for row in json.loads((OUT / "districts.json").read_text(encoding="utf-8"))["districts"]
    }
    by_key = {}
    for feat in geo["features"]:
        code = str(feat["properties"]["code"])
        sido = SIDO[code[:2]]
        by_key[(sido, feat["properties"]["name"])] = feat

    used = set()
    areas = []
    for (sido, name), kwh in sorted(power.items()):
        key = RENAME.get((sido, name), (sido, name))
        parts = PARTS.get((sido, name))
        if parts:
            feats = [by_key[(sido, part)] for part in parts]
            geom = {"type": "MultiPolygon", "coordinates": []}
            for feat in feats:
                geom["coordinates"].extend(rings(feat["geometry"]))
            code = str(feats[0]["properties"]["code"])
        else:
            feat = by_key[key]
            geom = feat["geometry"]
            code = str(feat["properties"]["code"])
            feats = [feat]
        for feat in feats:
            used.add(id(feat))
        parent = seoul.get(name) if sido == "서울특별시" else None
        areas.append(
            {
                "id": code,
                "sido": sido,
                "name": name,
                "kwh": kwh,
                "geometry": geom,
                "seoulScore": parent["latest"]["score"] if parent else None,
                "seoulLevel": parent["latest"]["level"] if parent else None,
            }
        )

    leftover = [ft["properties"]["name"] for ft in geo["features"] if id(ft) not in used]
    if leftover:
        raise SystemExit(f"boundary left over: {leftover}")

    ranked = sorted(areas, key=lambda row: row["kwh"])
    count = len(ranked)
    for index, row in enumerate(ranked):
        row["rankLevel"] = min(5, index * 5 // count + 1)

    features = []
    slim = []
    for row in areas:
        lat, lng = centroid(row["geometry"])
        props = {
            "id": row["id"],
            "sido": row["sido"],
            "name": row["name"],
            "gwh": round(row["kwh"] / 1_000_000, 2),
            "rankLevel": row["rankLevel"],
            "seoulScore": row["seoulScore"],
            "seoulLevel": row["seoulLevel"],
            "lat": lat,
            "lng": lng,
        }
        features.append({"type": "Feature", "properties": props, "geometry": row["geometry"]})
        slim.append(props)

    (OUT / "national_map.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "national_power.json").write_text(
        json.dumps({"month": "2026-06", "areas": slim}, ensure_ascii=False),
        encoding="utf-8",
    )
    print("areas", len(slim), "gwh", min(a["gwh"] for a in slim), max(a["gwh"] for a in slim))


if __name__ == "__main__":
    main()
