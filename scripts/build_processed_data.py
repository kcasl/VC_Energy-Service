# Build the Seoul monthly vitality index and the browse tables.
"""Fuse downloaded public files into the vitality index and browse tables.

Window is 2025-07 through 2026-06 so monthly electricity and quarterly
commerce exist for every month. Gas and vacancy stay out of the score
until a district-level file is on disk.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "public" / "data" / "raw"
OUT = ROOT / "public" / "data" / "processed"
BROWSE = OUT / "browse"
OUT.mkdir(parents=True, exist_ok=True)
BROWSE.mkdir(parents=True, exist_ok=True)

WINDOW = [f"2025-{m:02d}" for m in range(7, 13)] + [f"2026-{m:02d}" for m in range(1, 7)]

PLACES = {
    "종로구": ("도심", 37.5735, 126.979),
    "중구": ("도심", 37.5641, 126.9979),
    "용산구": ("도심", 37.5326, 126.990),
    "성동구": ("근교", 37.5506, 127.040),
    "광진구": ("근교", 37.5384, 127.082),
    "동대문구": ("근교", 37.5744, 127.040),
    "중랑구": ("근교", 37.6063, 127.093),
    "성북구": ("근교", 37.5894, 127.0167),
    "강북구": ("근교", 37.6396, 127.0255),
    "도봉구": ("근교", 37.6688, 127.0471),
    "노원구": ("근교", 37.6542, 127.0568),
    "은평구": ("근교", 37.6176, 126.9227),
    "서대문구": ("도심", 37.5791, 126.9368),
    "마포구": ("도심", 37.5638, 126.9084),
    "양천구": ("근교", 37.517, 126.8665),
    "강서구": ("근교", 37.5509, 126.8495),
    "구로구": ("근교", 37.4954, 126.8874),
    "금천구": ("근교", 37.4569, 126.8955),
    "영등포구": ("도심", 37.5264, 126.896),
    "동작구": ("근교", 37.5124, 126.9393),
    "관악구": ("근교", 37.4784, 126.9516),
    "서초구": ("도심", 37.4837, 127.0324),
    "강남구": ("도심", 37.5172, 127.0473),
    "송파구": ("도심", 37.5145, 127.106),
    "강동구": ("근교", 37.5301, 127.1238),
}

sys.path.insert(0, str(ROOT))
from backend.industry_catalog import public_rows

INDUSTRIES = public_rows()

SPOTS = [
    {"id": "yeoksam", "name": "역삼역 인근 골목", "district": "강남구", "type": "골목", "lat": 37.5007, "lng": 127.0366, "industryBias": "카페"},
    {"id": "gangnam", "name": "강남역 중심", "district": "강남구", "type": "도심", "lat": 37.4979, "lng": 127.0276, "industryBias": "한식"},
    {"id": "garosu", "name": "가로수길", "district": "강남구", "type": "골목", "lat": 37.521, "lng": 127.023, "industryBias": "의류소매"},
    {"id": "samsung", "name": "삼성·코엑스", "district": "강남구", "type": "도심", "lat": 37.511, "lng": 127.059, "industryBias": "카페"},
    {"id": "hongdae", "name": "홍대입구", "district": "마포구", "type": "도심", "lat": 37.5563, "lng": 126.9236, "industryBias": "호프·주점"},
    {"id": "yeonnam", "name": "연남동 골목", "district": "마포구", "type": "골목", "lat": 37.5623, "lng": 126.9254, "industryBias": "카페"},
    {"id": "mangwon", "name": "망원시장 일대", "district": "마포구", "type": "골목", "lat": 37.556, "lng": 126.91, "industryBias": "한식"},
    {"id": "hapjeong", "name": "합정·망원", "district": "마포구", "type": "골목", "lat": 37.5495, "lng": 126.9139, "industryBias": "카페"},
    {"id": "seongsu", "name": "성수 카페거리", "district": "성동구", "type": "골목", "lat": 37.5446, "lng": 127.0559, "industryBias": "카페"},
    {"id": "ittwon", "name": "이태원·한남", "district": "용산구", "type": "골목", "lat": 37.5345, "lng": 126.994, "industryBias": "호프·주점"},
    {"id": "myeongdong", "name": "명동", "district": "중구", "type": "도심", "lat": 37.5636, "lng": 126.983, "industryBias": "의류소매"},
    {"id": "euljiro", "name": "을지로 골목", "district": "중구", "type": "골목", "lat": 37.5662, "lng": 126.991, "industryBias": "호프·주점"},
    {"id": "jongno", "name": "종로·익선동", "district": "종로구", "type": "골목", "lat": 37.5744, "lng": 126.9899, "industryBias": "한식"},
    {"id": "yeouido", "name": "여의도", "district": "영등포구", "type": "도심", "lat": 37.5216, "lng": 126.9243, "industryBias": "카페"},
    {"id": "yeongdeungpo", "name": "영등포 타임스퀘어", "district": "영등포구", "type": "도심", "lat": 37.5172, "lng": 126.903, "industryBias": "편의점"},
    {"id": "jamsil", "name": "잠실", "district": "송파구", "type": "도심", "lat": 37.5133, "lng": 127.1028, "industryBias": "카페"},
    {"id": "munjeong", "name": "문정 법조타운", "district": "송파구", "type": "도심", "lat": 37.4874, "lng": 127.1225, "industryBias": "카페"},
    {"id": "konkuk", "name": "건대입구", "district": "광진구", "type": "도심", "lat": 37.5404, "lng": 127.0692, "industryBias": "호프·주점"},
    {"id": "sinchon", "name": "신촌", "district": "서대문구", "type": "도심", "lat": 37.5597, "lng": 126.942, "industryBias": "카페"},
    {"id": "sillim", "name": "신림", "district": "관악구", "type": "근교", "lat": 37.4842, "lng": 126.9296, "industryBias": "학원"},
    {"id": "nowon", "name": "노원역", "district": "노원구", "type": "근교", "lat": 37.6552, "lng": 127.0615, "industryBias": "편의점"},
    {"id": "suyu", "name": "수유", "district": "강북구", "type": "근교", "lat": 37.6377, "lng": 127.0247, "industryBias": "한식"},
    {"id": "gasan", "name": "가산디지털단지", "district": "금천구", "type": "도심", "lat": 37.4812, "lng": 126.8826, "industryBias": "카페"},
    {"id": "mokdong", "name": "목동", "district": "양천구", "type": "근교", "lat": 37.526, "lng": 126.875, "industryBias": "학원"},
    {"id": "gongdeok", "name": "공덕", "district": "마포구", "type": "도심", "lat": 37.5436, "lng": 126.951, "industryBias": "카페"},
    {"id": "apgujeong", "name": "압구정", "district": "강남구", "type": "도심", "lat": 37.5274, "lng": 127.0286, "industryBias": "의류소매"},
    {"id": "cheongdam", "name": "청담", "district": "강남구", "type": "골목", "lat": 37.5229, "lng": 127.0474, "industryBias": "미용"},
    {"id": "cheonho", "name": "천호", "district": "강동구", "type": "근교", "lat": 37.5386, "lng": 127.1235, "industryBias": "한식"},
    {"id": "wangsimni", "name": "왕십리", "district": "성동구", "type": "근교", "lat": 37.5614, "lng": 127.037, "industryBias": "편의점"},
    {"id": "seocho", "name": "강남대로 서초", "district": "서초구", "type": "도심", "lat": 37.491, "lng": 127.007, "industryBias": "카페"},
]


def level_of(score: float) -> int:
    if score >= 78:
        return 5
    if score >= 66:
        return 4
    if score >= 54:
        return 3
    if score >= 42:
        return 2
    return 1


def quarter_code(month: str) -> int:
    year, mon = map(int, month.split("-"))
    return year * 10 + ((mon - 1) // 3 + 1)


def zscores(values: dict[str, float]) -> tuple[dict[str, float], float, float]:
    nums = list(values.values())
    mean = sum(nums) / len(nums)
    var = sum((n - mean) ** 2 for n in nums) / len(nums)
    std = var**0.5 or 1.0
    return {k: (v - mean) / std for k, v in values.items()}, mean, std


def read_kepco() -> dict[tuple[str, str, str], int]:
    """(district, YYYY-MM, contract) -> kWh for Seoul."""
    found: dict[tuple[str, str, str], int] = {}
    for path in [RAW / "kepco_sigungu_202512.xlsx", RAW / "kepco_sigungu_202608.xlsx"]:
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb[wb.sheetnames[0]]
        header = None
        for row in ws.iter_rows(values_only=True):
            if row and row[0] == "연도":
                header = row
                continue
            if header is None or not row or row[0] is None:
                continue
            if str(row[1]).strip() != "서울특별시":
                continue
            year = int(row[0])
            district = str(row[2]).strip()
            contract = str(row[3]).replace(" ", "")
            for idx, cell in enumerate(header):
                if not isinstance(cell, str) or not cell.endswith("월"):
                    continue
                month_no = int(cell.replace("월", ""))
                value = row[idx]
                if value is None:
                    continue
                kwh = int(value)
                if kwh <= 0:
                    continue
                found[(district, f"{year}-{month_no:02d}", contract)] = kwh
        wb.close()
    return found


def read_industry_month() -> list[dict]:
    path = RAW / "kepco_sigungu_202608.xlsx"
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[1]]
    rows = []
    header = None
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == "연도":
            header = list(row)
            continue
        if header is None or not row or row[0] != 2026:
            continue
        if str(row[1]).strip() != "서울특별시":
            continue
        # August is column index of "8월"
        aug = header.index("8월")
        kwh = int(row[aug] or 0)
        if kwh <= 0:
            continue
        rows.append(
            {
                "district": str(row[2]).strip(),
                "industry": str(row[3]).replace(" ", ""),
                "month": "2026-08",
                "kwh": kwh,
            }
        )
    wb.close()
    return rows


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / name, encoding="cp949")


def monthly_weather() -> dict[str, float]:
    payload = json.loads((RAW / "seoul_weather_2024_2026.json").read_text(encoding="utf-8"))
    daily = payload["daily"]
    bucket: dict[str, list[float]] = defaultdict(list)
    for day, temp in zip(daily["time"], daily["temperature_2m_mean"]):
        if temp is None:
            continue
        bucket[day[:7]].append(float(temp))
    return {m: round(sum(v) / len(v), 1) for m, v in bucket.items()}


def dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    kepco = read_kepco()
    weather = monthly_weather()
    store = read_csv("seoul_signgu_store.csv")
    sales = read_csv("seoul_signgu_sales.csv")
    flpop = read_csv("seoul_signgu_flpop.csv")
    worker = read_csv("seoul_signgu_worker.csv")

    store_q = (
        store.groupby(["기준_년분기_코드", "자치구_코드", "자치구_코드_명"], as_index=False)
        .agg(stores=("전체_점포_수", "sum"), opened=("개업_점포_수", "sum"), closed=("폐업_점포_수", "sum"))
    )
    sales_q = sales.groupby(["기준_년분기_코드", "자치구_코드_명"], as_index=False).agg(
        sales=("당월_매출_금액", "sum")
    )
    store_lookup = {
        (int(r.기준_년분기_코드), r.자치구_코드_명): r for r in store_q.itertuples(index=False)
    }
    sales_lookup = {
        (int(r.기준_년분기_코드), r.자치구_코드_명): float(r.sales) for r in sales_q.itertuples(index=False)
    }
    flpop_lookup = {
        (int(r.기준_년분기_코드), r.자치구_코드_명): int(r.총_유동인구_수)
        for r in flpop.itertuples(index=False)
    }
    signgu_code = {r.자치구_코드_명: str(int(r.자치구_코드)).zfill(5) for r in store_q.itertuples(index=False)}

    geo = json.loads((RAW / "seoul_municipalities.geojson").read_text(encoding="utf-8"))
    geo_code = {ft["properties"]["name"]: str(ft["properties"]["code"]) for ft in geo["features"]}
    missing_names = [name for name in PLACES if name not in geo_code or name not in signgu_code]
    if missing_names:
        raise SystemExit(f"name mismatch {missing_names}")

    for month in WINDOW:
        if month not in weather:
            raise SystemExit(f"weather missing {month}")

    series_raw: dict[str, list[dict]] = {name: [] for name in PLACES}
    norms_out = None
    for month in WINDOW:
        q = quarter_code(month)
        kwh_map = {}
        sales_map = {}
        pop_map = {}
        for name in PLACES:
            kwh = kepco.get((name, month, "일반용"))
            if not kwh:
                raise SystemExit(f"kepco missing {name} {month}")
            if (q, name) not in store_lookup or (q, name) not in sales_lookup or (q, name) not in flpop_lookup:
                raise SystemExit(f"commerce missing {name} {q}")
            kwh_map[name] = kwh
            sales_map[name] = sales_lookup[(q, name)] / 3
            pop_map[name] = flpop_lookup[(q, name)]
        zk, kwh_mean, kwh_std = zscores(kwh_map)
        zs, sales_mean, sales_std = zscores(sales_map)
        zp, pop_mean, pop_std = zscores({k: float(v) for k, v in pop_map.items()})
        if month == WINDOW[-1]:
            norms_out = {
                "month": month,
                "kwhMean": kwh_mean,
                "kwhStd": kwh_std,
                "salesMean": sales_mean,
                "salesStd": sales_std,
                "flpopMean": pop_mean,
                "flpopStd": pop_std,
            }
        temp = weather[month]
        for name in PLACES:
            row = store_lookup[(q, name)]
            stores = float(row.stores) or 1
            open_rate = round(float(row.opened) / stores * 100, 2)
            close_rate = round(float(row.closed) / stores * 100, 2)
            score = (
                52
                + 28 * zk[name]
                + 18 * zs[name]
                + 10 * zp[name]
                + 6 * (open_rate - close_rate)
                - 0.15 * abs(temp - 18)
            )
            score = round(score, 1)
            series_raw[name].append(
                {
                    "month": month,
                    "meanTemp": temp,
                    "commercialKwh": kwh_map[name],
                    "commercialKwhGwh": round(kwh_map[name] / 1_000_000, 2),
                    "salesKrw": round(sales_map[name]),
                    "flpop": pop_map[name],
                    "openRate": open_rate,
                    "closeRate": close_rate,
                    "score": score,
                    "level": level_of(score),
                    "rankLevel": 3,
                }
            )

    for i in range(len(WINDOW)):
        ordered = sorted(PLACES, key=lambda name: (series_raw[name][i]["score"], name))
        for rank, name in enumerate(ordered):
            series_raw[name][i]["rankLevel"] = rank // 5 + 1

    latest_q = quarter_code(WINDOW[-1])
    latest_store = store[store["기준_년분기_코드"] == latest_q]
    rivals: dict[tuple[str, str], int] = {}
    for spec in INDUSTRIES:
        names = latest_store["서비스_업종_코드_명"].astype(str)
        if spec.get("match"):
            mask = False
            for token in spec["match"]:
                mask = mask | names.str.contains(token, na=False)
            matched = latest_store[mask]
        else:
            matched = latest_store[names.isin(spec["seoulNames"])]
        if matched.empty:
            raise SystemExit(f"industry match empty: {spec.get('match') or spec['seoulNames']}")
        spec["seoulNames"] = sorted(matched["서비스_업종_코드_명"].unique())
        for name, part in matched.groupby("자치구_코드_명"):
            rivals[(str(name), spec["name"])] = int(part["전체_점포_수"].sum())

    districts = []
    for name, (kind, lat, lng) in PLACES.items():
        series = series_raw[name]
        latest = series[-1]
        first = series[0]
        districts.append(
            {
                "code": geo_code[name],
                "signguCode": signgu_code[name],
                "name": name,
                "type": kind,
                "lat": lat,
                "lng": lng,
                "stores": int(store_lookup[(latest_q, name)].stores),
                "openRate": latest["openRate"],
                "closeRate": latest["closeRate"],
                "yoyKwh": kepco[(name, "2026-06", "일반용")] - kepco[(name, "2025-06", "일반용")],
                "intensityKwhPerStore": round(latest["commercialKwh"] / max(store_lookup[(latest_q, name)].stores, 1), 1),
                "rivalsByIndustry": {spec["name"]: rivals.get((name, spec["name"]), 0) for spec in INDUSTRIES},
                "latest": latest,
                "delta": round(latest["score"] - first["score"], 1),
                "series": series,
            }
        )

    spots = []
    by_name = {d["name"]: d for d in districts}
    for spot in SPOTS:
        parent = by_name[spot["district"]]
        spots.append(
            {
                **spot,
                "rivals": parent["rivalsByIndustry"].get(spot["industryBias"], 0),
                "score": parent["latest"]["score"],
                "level": parent["latest"]["level"],
                "parentScore": parent["latest"]["score"],
                "commercialKwhGwh": parent["latest"]["commercialKwhGwh"],
            }
        )

    # Citywide industry rollup for the latest quarter.
    sales_latest = sales[sales["기준_년분기_코드"] == latest_q]
    sales_by_ind = sales_latest.groupby("서비스_업종_코드_명")["당월_매출_금액"].sum()
    industry_rows = []
    grouped = latest_store.groupby("서비스_업종_코드_명", as_index=False).agg(
        stores=("전체_점포_수", "sum"),
        opened=("개업_점포_수", "sum"),
        closed=("폐업_점포_수", "sum"),
    )
    for row in grouped.itertuples(index=False):
        industry_rows.append(
            {
                "name": row.서비스_업종_코드_명,
                "stores": int(row.stores),
                "opened": int(row.opened),
                "closed": int(row.closed),
                "salesKrw": int(sales_by_ind.get(row.서비스_업종_코드_명, 0)),
            }
        )
    industry_rows.sort(key=lambda r: r["opened"] - r["closed"], reverse=True)

    kepco_rows = []
    for (district, month, contract), kwh in sorted(kepco.items()):
        if contract not in {"일반용", "주택용", "산업용", "교육용"}:
            continue
        if month < "2025-01" or month > "2026-08":
            continue
        kepco_rows.append({"district": district, "month": month, "contract": contract, "kwh": kwh})

    store_browse = latest_store[
        ["기준_년분기_코드", "자치구_코드_명", "서비스_업종_코드_명", "전체_점포_수", "개업_점포_수", "폐업_점포_수", "개업_율", "폐업_률"]
    ].copy()
    store_rows = [
        {
            "quarter": str(int(r.기준_년분기_코드)),
            "district": r.자치구_코드_명,
            "industry": r.서비스_업종_코드_명,
            "stores": int(r.전체_점포_수),
            "opened": int(r.개업_점포_수),
            "closed": int(r.폐업_점포_수),
            "openRate": round(float(r.개업_율), 2),
            "closeRate": round(float(r.폐업_률), 2),
        }
        for r in store_browse.itertuples(index=False)
    ]
    sales_rows = [
        {
            "quarter": str(int(r.기준_년분기_코드)),
            "district": r.자치구_코드_명,
            "industry": r.서비스_업종_코드_명,
            "salesKrw": int(r.당월_매출_금액),
            "salesCount": int(r.당월_매출_건수),
        }
        for r in sales_latest.itertuples(index=False)
    ]
    flpop_rows = [
        {
            "quarter": str(int(r.기준_년분기_코드)),
            "district": r.자치구_코드_명,
            "flpop": int(r.총_유동인구_수),
            "day": int(r.시간대_11_14_유동인구_수),
            "evening": int(r.시간대_17_21_유동인구_수),
            "night": int(r.시간대_21_24_유동인구_수),
        }
        for r in flpop.itertuples(index=False)
    ]
    worker_rows = [
        {
            "quarter": str(int(r.기준_년분기_코드)),
            "district": r.자치구_코드_명,
            "workers": int(r.총_직장_인구_수),
        }
        for r in worker.itertuples(index=False)
    ]

    def browse(columns: list[tuple[str, str]], rows: list[dict]) -> dict:
        return {"columns": [{"key": k, "label": label} for k, label in columns], "rows": rows}

    dump(
        BROWSE / "kepco.json",
        browse(
            [("district", "자치구"), ("month", "월"), ("contract", "계약종"), ("kwh", "사용량 kWh")],
            kepco_rows,
        ),
    )
    dump(
        BROWSE / "kepco_industry.json",
        browse(
            [("district", "자치구"), ("industry", "용도업종"), ("month", "월"), ("kwh", "사용량 kWh")],
            read_industry_month(),
        ),
    )
    dump(
        BROWSE / "store.json",
        browse(
            [
                ("quarter", "분기"),
                ("district", "자치구"),
                ("industry", "업종"),
                ("stores", "점포"),
                ("opened", "개업"),
                ("closed", "폐업"),
                ("openRate", "개업률"),
                ("closeRate", "폐업률"),
            ],
            store_rows,
        ),
    )
    dump(
        BROWSE / "sales.json",
        browse(
            [
                ("quarter", "분기"),
                ("district", "자치구"),
                ("industry", "업종"),
                ("salesKrw", "매출 원"),
                ("salesCount", "매출 건수"),
            ],
            sales_rows,
        ),
    )
    dump(
        BROWSE / "flpop.json",
        browse(
            [
                ("quarter", "분기"),
                ("district", "자치구"),
                ("flpop", "총 유동"),
                ("day", "11–14시"),
                ("evening", "17–21시"),
                ("night", "21–24시"),
            ],
            flpop_rows,
        ),
    )
    dump(
        BROWSE / "worker.json",
        browse(
            [("quarter", "분기"), ("district", "자치구"), ("workers", "직장인구")],
            worker_rows,
        ),
    )
    weather_rows = [{"month": m, "meanTemp": weather[m]} for m in sorted(weather) if "2025-01" <= m <= "2026-08"]
    dump(
        BROWSE / "weather.json",
        browse([("month", "월"), ("meanTemp", "평균기온 ℃")], weather_rows),
    )

    catalog = [
        {
            "id": "kepco-contract",
            "priority": 1,
            "title": "시군구별 계약종별 전력사용량",
            "owner": "한국전력공사",
            "purpose": "상업 활동의 에너지 소비. 활력지수의 전력 축은 일반용.",
            "grain": "시군구 · 월 · 계약종",
            "cadence": "월간",
            "status": "2025년 연간·2026년 1–8월 원문 다운로드",
            "usedIn": ["활력지수 전력 축", "대시보드 증감", "창업 지역 가중"],
            "url": "https://www.kepco.co.kr/home/customer/library/electricity-statistics/sales-volume/boardList.do",
            "localFiles": ["raw/kepco_sigungu_202512.xlsx", "raw/kepco_sigungu_202608.xlsx"],
            "browse": "browse/kepco.json",
            "rowCount": len(kepco_rows),
            "notes": "서울 25개 구, 일반·주택·산업·교육용. 9–12월 0은 미공표라 제외.",
        },
        {
            "id": "kepco-industry",
            "priority": 1,
            "title": "시군구별 용도업종별 전력사용량",
            "owner": "한국전력공사",
            "purpose": "업종 믹스가 전력에 어떻게 실리는지 확인",
            "grain": "시군구 · 월 · 한전 용도업종",
            "cadence": "월간",
            "status": "2026-08 서울 원문 적재",
            "usedIn": ["데이터 목록"],
            "url": "https://www.kepco.co.kr/home/customer/library/electricity-statistics/sales-volume/boardList.do",
            "localFiles": ["raw/kepco_sigungu_202608.xlsx"],
            "browse": "browse/kepco_industry.json",
            "rowCount": len(read_industry_month()),
            "notes": "한전 업종명과 서울 생활밀접업종 코드는 다릅니다. 지수는 일반용 합계를 쓰고, 업종 표는 목록에서만 엽니다.",
        },
        {
            "id": "molit-gas",
            "priority": 2,
            "title": "건물에너지 가스에너지",
            "owner": "국토교통부",
            "purpose": "건물 단위 에너지 활동 추정",
            "grain": "건물",
            "cadence": "수시",
            "status": "미연동 · 지수 가중 0",
            "usedIn": ["가스 축은 파일이 생기면 같은 z-score 자리에 넣는다"],
            "url": "https://www.data.go.kr/",
            "localFiles": [],
            "browse": "",
            "rowCount": 0,
            "notes": "인증이 필요해 받지 못했습니다. 점수는 가스 항 없이 계산합니다.",
        },
        {
            "id": "store-info",
            "priority": 3,
            "title": "전국 상가업소 정보",
            "owner": "소상공인시장진흥공단",
            "purpose": "점포 좌표",
            "grain": "점포",
            "cadence": "분기",
            "status": "미연동 · 로그인 파일",
            "usedIn": ["골목 전수 좌표는 월정액 단계"],
            "url": "https://www.data.go.kr/data/15083033/fileData.do",
            "localFiles": [],
            "browse": "",
            "rowCount": 0,
        },
        {
            "id": "seoul-store",
            "priority": 4,
            "title": "서울시 상권분석서비스(점포-자치구)",
            "owner": "서울신용보증재단 / 서울시",
            "purpose": "개업·폐업으로 성장과 쇠퇴를 측정",
            "grain": "자치구 · 업종 · 분기",
            "cadence": "분기",
            "status": f"원문 {len(store):,}행 · 목록은 {latest_q} 분기",
            "usedIn": ["개폐업", "경쟁 점포", "대시보드"],
            "url": "https://data.seoul.go.kr/dataList/OA-22173/S/1/datasetView.do",
            "localFiles": ["raw/seoul_signgu_store.csv"],
            "browse": "browse/store.json",
            "rowCount": len(store_rows),
            "notes": "전체는 2021-1분기부터 2026-2분기. 화면 표는 최신 분기 업종 행입니다.",
        },
        {
            "id": "seoul-sales",
            "priority": 5,
            "title": "서울시 상권분석서비스(추정매출-자치구)",
            "owner": "서울신용보증재단 / 서울시",
            "purpose": "활력지수의 경제활동 검증",
            "grain": "자치구 · 업종 · 분기",
            "cadence": "분기",
            "status": f"원문 {len(sales):,}행 · 목록은 {latest_q} 분기",
            "usedIn": ["매출 축", "업종 표"],
            "url": "https://data.seoul.go.kr/dataList/OA-22176/S/1/datasetView.do",
            "localFiles": ["raw/seoul_signgu_sales.csv"],
            "browse": "browse/sales.json",
            "rowCount": len(sales_rows),
            "notes": "분기 행의 당월_매출_금액을 3으로 나눠 월 지수에 넣습니다. 분기 안에서는 같은 값입니다.",
        },
        {
            "id": "seoul-flpop",
            "priority": 6,
            "title": "서울시 상권분석서비스(길단위인구-자치구)",
            "owner": "서울시 / KT",
            "purpose": "방문·체류 활동",
            "grain": "자치구 · 분기",
            "cadence": "분기",
            "status": f"원문 {len(flpop):,}행 전부 목록에 표시",
            "usedIn": ["유동 축"],
            "url": "https://data.seoul.go.kr/dataList/OA-22179/S/1/datasetView.do",
            "localFiles": ["raw/seoul_signgu_flpop.csv"],
            "browse": "browse/flpop.json",
            "rowCount": len(flpop_rows),
        },
        {
            "id": "seoul-worker",
            "priority": 6,
            "title": "서울시 상권분석서비스(직장인구-자치구)",
            "owner": "서울시 / SKT",
            "purpose": "직장 수요를 목록에서 확인. 지수 식에는 넣지 않음",
            "grain": "자치구 · 분기",
            "cadence": "분기",
            "status": f"원문 {len(worker):,}행",
            "usedIn": ["데이터 목록"],
            "url": "https://data.seoul.go.kr/dataList/OA-22185/S/1/datasetView.do",
            "localFiles": ["raw/seoul_signgu_worker.csv"],
            "browse": "browse/worker.json",
            "rowCount": len(worker_rows),
        },
        {
            "id": "building-ledger",
            "priority": 7,
            "title": "건축물대장",
            "owner": "국토교통부",
            "purpose": "면적 원단위를 건물 규모로 바꾸기 위한 자료",
            "grain": "건물",
            "cadence": "수시",
            "status": "미연동 · 인증 필요",
            "usedIn": ["시뮬레이터 면적 원단위는 가정"],
            "url": "https://www.data.go.kr/data/15044713/openapi.do",
            "localFiles": [],
            "browse": "",
            "rowCount": 0,
        },
        {
            "id": "tariff",
            "priority": 8,
            "title": "일반용 전력 판매단가",
            "owner": "한국전력공사",
            "purpose": "창업 시 예상 전기요금",
            "grain": "계약종 · 연",
            "cadence": "연간 공시",
            "status": "2025년 일반용 평균 판매단가 반영",
            "usedIn": ["시뮬레이터"],
            "url": "https://www.kepco.co.kr/home/esg/esgdata/entire/conts.do",
            "localFiles": ["processed/tariff.json"],
            "browse": "",
            "rowCount": 1,
            "notes": "172.69원/kWh에 부가세 10%와 전력산업기반기금 3.7%를 더합니다. 계절·시간대 선택요금은 아닙니다.",
        },
        {
            "id": "weather",
            "priority": 9,
            "title": "서울 기온 (Open-Meteo)",
            "owner": "Open-Meteo",
            "purpose": "계절에 따른 에너지 소비 보정",
            "grain": "일 → 월 평균",
            "cadence": "일",
            "status": "2024-01-01 ~ 2026-08-31 다운로드",
            "usedIn": ["활력지수 기온 항"],
            "url": "https://open-meteo.com/",
            "localFiles": ["raw/seoul_weather_2024_2026.json"],
            "browse": "browse/weather.json",
            "rowCount": len(weather_rows),
        },
        {
            "id": "vacancy",
            "priority": 10,
            "title": "상업용부동산 공실률",
            "owner": "한국부동산원 R-ONE",
            "purpose": "상권 침체와 공실 위험",
            "grain": "상권 권역 · 분기",
            "cadence": "분기",
            "status": "미연동 · 지수 가중 0",
            "usedIn": ["공실 항은 자치구 파일이 생기면 -8z로 넣는다"],
            "url": "https://www.reb.or.kr/r-one/portal/stat/easyStatPage/T249633134845544.do",
            "localFiles": [],
            "browse": "",
            "rowCount": 0,
            "notes": "공개 통계는 중대형·소규모 상가 권역 단위라 25개 구와 1:1로 붙이지 않았습니다.",
        },
        {
            "id": "geo",
            "priority": 0,
            "title": "서울 자치구 경계",
            "owner": "southkorea/seoul-maps",
            "purpose": "지도 폴리곤",
            "grain": "자치구",
            "cadence": "정적",
            "status": "GeoJSON 사용",
            "usedIn": ["지도"],
            "url": "https://github.com/southkorea/seoul-maps",
            "localFiles": ["raw/seoul_municipalities.geojson"],
            "browse": "",
            "rowCount": 25,
            "notes": "경계 코드는 통계청 5자리, 상권 파일 코드는 행정기관코드. 이름은 같고 코드는 다릅니다.",
        },
    ]

    tariff = {
        "name": "2025년 일반용 평균 판매단가",
        "source": "한국전력공사 2025년 일반용 판매단가 172.69원/kWh. 부가세 10%, 전력산업기반기금 3.7%를 더합니다.",
        "basePerKw": 0,
        "energyPerKwh": 172.69,
        "climatePerKwh": 0,
        "fuelPerKwh": 0,
        "vat": 0.1,
        "fund": 0.037,
    }

    dump(
        OUT / "districts.json",
        {
            "generatedAt": datetime.now().strftime("%Y-%m-%d"),
            "window": {"from": WINDOW[0], "to": WINDOW[-1]},
            "formula": "52 + 28z(일반용 kWh) + 18z(분기매출/3) + 10z(유동) + 6(개업률-폐업률) - 0.15|기온-18|. 가스·공실은 0.",
            "omitted": ["가스", "공실"],
            "norms": norms_out,
            "districts": districts,
        },
    )
    dump(OUT / "spots.json", {"spots": spots, "note": "점 위치는 대표 지명. 색과 점수는 그 자치구의 실측 활력과 같습니다."})
    dump(OUT / "industries.json", {"industries": INDUSTRIES})
    dump(OUT / "industry_latest.json", {"quarter": str(latest_q), "rows": industry_rows})
    dump(OUT / "tariff.json", tariff)
    dump(OUT / "catalog.json", {"items": catalog})
    dump(OUT / "seoul_weather_monthly.json", {"monthly": weather_rows})

    scores = [d["latest"]["score"] for d in districts]
    print(
        "districts",
        len(districts),
        "score",
        min(scores),
        max(scores),
        "spots",
        len(spots),
        "store rows",
        len(store),
        "browse store",
        len(store_rows),
    )


if __name__ == "__main__":
    main()
