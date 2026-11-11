"""Data and calculations for the commercial vitality site.

The browser only asks for finished numbers. Scores, bills, rankings,
and table filters are computed here.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "public" / "data" / "processed"
GEO = ROOT / "public" / "data" / "raw" / "seoul_municipalities.geojson"

app = FastAPI(title="상권 활력")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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


def quarter_label(code: str) -> str:
    text = str(code)
    return f"{text[:4]}년 {text[-1]}분기"


def gwh(kwh: float) -> float:
    return round(kwh / 1_000_000, 1)


DISTRICTS = read_json(PROCESSED / "districts.json")
SPOTS = read_json(PROCESSED / "spots.json")
CATALOG = read_json(PROCESSED / "catalog.json")
INDUSTRIES = read_json(PROCESSED / "industries.json")
INDUSTRY_Q = read_json(PROCESSED / "industry_latest.json")
TARIFF = read_json(PROCESSED / "tariff.json")
BROWSE: dict[str, dict] = {}
for item in CATALOG["items"]:
    if item.get("browse"):
        BROWSE[item["id"]] = read_json(PROCESSED / item["browse"])


def bill(monthly_kwh: float, contract_kw: float) -> int:
    energy = monthly_kwh * (
        TARIFF["energyPerKwh"] + TARIFF["climatePerKwh"] + TARIFF["fuelPerKwh"]
    )
    base = contract_kw * TARIFF["basePerKw"]
    sub = energy + base
    return round(sub * (1 + TARIFF["vat"] + TARIFF["fund"]))


def chart_rows(focus: str) -> list[dict]:
    rows = DISTRICTS["districts"]
    if focus == "서울 평균" or not any(d["name"] == focus for d in rows):
        first = rows[0]["series"]
        out = []
        for i, point in enumerate(first):
            score = sum(d["series"][i]["score"] for d in rows) / len(rows)
            kwh = sum(d["series"][i]["commercialKwhGwh"] for d in rows)
            out.append({"month": point["month"][2:], "score": round(score, 1), "kwh": round(kwh)})
        return out
    district = next(d for d in rows if d["name"] == focus)
    return [
        {"month": p["month"][2:], "score": p["score"], "kwh": p["commercialKwhGwh"]}
        for p in district["series"]
    ]


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/dashboard")
def dashboard(focus: str = "서울 평균"):
    rows = DISTRICTS["districts"]
    by_energy = sorted(rows, key=lambda d: d["yoyKwh"], reverse=True)
    stagnant = sorted(
        [d for d in rows if d["delta"] < 0 and d["closeRate"] > d["openRate"]],
        key=lambda d: d["delta"],
    )
    top = by_energy[0]
    low = list(reversed(by_energy))[:8]
    return {
        "windowLabel": "2025.7–2026.6",
        "names": ["서울 평균", *[d["name"] for d in rows]],
        "avgScore": round(sum(d["latest"]["score"] for d in rows) / len(rows), 1),
        "energyTop": {"name": top["name"], "gwh": gwh(top["yoyKwh"])},
        "stagnantName": stagnant[0]["name"] if stagnant else "없음",
        "closeOverOpen": sum(1 for d in rows if d["closeRate"] > d["openRate"]),
        "chart": chart_rows(focus),
        "focus": focus if focus in {d["name"] for d in rows} or focus == "서울 평균" else "서울 평균",
        "quarterLabel": quarter_label(INDUSTRY_Q["quarter"]),
        "industries": [
            {
                "name": row["name"],
                "opened": row["opened"],
                "closed": row["closed"],
                "stores": row["stores"],
            }
            for row in INDUSTRY_Q["rows"][:8]
        ],
        "lowEnergy": [
            {
                "name": d["name"],
                "level": d["latest"]["level"],
                "gwh": gwh(d["yoyKwh"]),
                "closeRate": d["closeRate"],
            }
            for d in low
        ],
    }


@app.get("/api/map")
def map_data():
    by_name = {d["name"]: d for d in DISTRICTS["districts"]}
    districts = [
        {
            "name": d["name"],
            "code": d["code"],
            "type": d["type"],
            "lat": d["lat"],
            "lng": d["lng"],
            "score": d["latest"]["score"],
            "level": d["latest"]["level"],
            "rankLevel": d["latest"]["rankLevel"],
            "gwh": d["latest"]["commercialKwhGwh"],
            "openRate": d["openRate"],
            "closeRate": d["closeRate"],
        }
        for d in DISTRICTS["districts"]
    ]
    spots = []
    for s in SPOTS["spots"]:
        parent = by_name[s["district"]]
        spots.append(
            {
                "id": s["id"],
                "name": s["name"],
                "district": s["district"],
                "type": s["type"],
                "lat": s["lat"],
                "lng": s["lng"],
                "industryBias": s["industryBias"],
                "rivals": s["rivals"],
                "score": s["score"],
                "level": s["level"],
                "rankLevel": parent["latest"]["rankLevel"],
            }
        )
    return {"districts": districts, "spots": spots}


@app.get("/api/geo")
def geo():
    return read_json(GEO)


@app.get("/api/catalog")
def catalog():
    items = []
    for item in sorted(CATALOG["items"], key=lambda x: (x["priority"], x["title"])):
        items.append(
            {
                "id": item["id"],
                "priority": item["priority"],
                "title": item["title"],
                "owner": item["owner"],
                "purpose": item["purpose"],
                "grain": item["grain"],
                "cadence": item["cadence"],
                "status": item["status"],
                "usedIn": item["usedIn"],
                "url": item["url"],
                "localFiles": item["localFiles"],
                "rowCount": item["rowCount"],
                "notes": item.get("notes") or "",
                "hasRows": bool(item.get("browse")),
            }
        )
    return {"items": items}


@app.get("/api/catalog/{item_id}/rows")
def catalog_rows(
    item_id: str,
    q: str = "",
    district: str = "전체",
    page: int = Query(0, ge=0),
    size: int = Query(12, ge=1, le=50),
):
    table = BROWSE.get(item_id)
    if table is None:
        raise HTTPException(status_code=404, detail="표 없음")
    names = sorted({row["district"] for row in table["rows"] if "district" in row})
    needle = q.strip()
    matched = []
    for row in table["rows"]:
        if district != "전체" and row.get("district") != district:
            continue
        if needle and not any(needle in str(value) for value in row.values()):
            continue
        matched.append(row)
    start = page * size
    page_count = max(1, (len(matched) + size - 1) // size)
    return {
        "columns": table["columns"],
        "rows": matched[start : start + size],
        "total": len(matched),
        "all": len(table["rows"]),
        "page": page,
        "pageCount": page_count,
        "districts": names,
    }


STORE_ROWS = BROWSE["seoul-store"]["rows"]
SALES_ROWS = BROWSE["seoul-sales"]["rows"]
QUARTER = "20262"
POWER_MONTH = "2026-06"


def _cells(names: set[str], district: str) -> dict:
    stores = opened = closed = sales = tickets = 0
    for row in STORE_ROWS:
        if row["district"] == district and row["industry"] in names:
            stores += row["stores"]
            opened += row["opened"]
            closed += row["closed"]
    for row in SALES_ROWS:
        if row["district"] == district and row["industry"] in names:
            sales += row["salesKrw"]
            tickets += row["salesCount"]
    return {
        "stores": stores,
        "opened": opened,
        "closed": closed,
        "openRate": round(opened / stores * 100, 2) if stores else 0,
        "closeRate": round(closed / stores * 100, 2) if stores else 0,
        "salesKrw": sales,
        "salesCount": tickets,
        "salesPerStore": round(sales / stores) if stores else 0,
        "salesCountPerStore": round(tickets / stores, 1) if stores else 0,
    }


def _district_sales_per_store() -> dict[str, float]:
    sales: dict[tuple[str, str], int] = {}
    stores: dict[tuple[str, str], int] = {}
    for row in SALES_ROWS:
        key = (row["district"], row["industry"])
        sales[key] = sales.get(key, 0) + row["salesKrw"]
    for row in STORE_ROWS:
        key = (row["district"], row["industry"])
        stores[key] = stores.get(key, 0) + row["stores"]
    totals: dict[str, list[int]] = {}
    for (district, industry), amount in sales.items():
        count = stores.get((district, industry), 0)
        if not count:
            continue
        bucket = totals.setdefault(district, [0, 0])
        bucket[0] += amount
        bucket[1] += count
    return {name: amount / count for name, (amount, count) in totals.items() if count}


DISTRICT_SALES_PER_STORE = _district_sales_per_store()


INDUSTRY_ROWS: dict[str, list[dict]] = {}
for spec in INDUSTRIES["industries"]:
    matched = set(spec["seoulNames"])
    packed = []
    for district in DISTRICTS["districts"]:
        cell = _cells(matched, district["name"])
        latest = district["latest"]
        cell.update(
            {
                "district": district["name"],
                "flpop": latest["flpop"],
                "flpopPerStore": round(latest["flpop"] / cell["stores"]) if cell["stores"] else 0,
                "score": latest["score"],
                "netOpen": round(cell["openRate"] - cell["closeRate"], 2),
            }
        )
        packed.append(cell)
    INDUSTRY_ROWS[spec["id"]] = packed


def pct(rows: list[dict], key: str, value: float, higher: bool) -> int:
    beaten = sum(1 for row in rows if (row[key] < value if higher else row[key] > value))
    return round(100 * beaten / max(len(rows) - 1, 1))


def comma(n: float, digits: int = 0) -> str:
    if digits:
        return f"{n:,.{digits}f}"
    return f"{round(n):,}"


@app.get("/api/sim/options")
def sim_options():
    return {
        "spots": [
            {"id": s["id"], "name": s["name"], "type": s["type"], "district": s["district"]}
            for s in SPOTS["spots"]
        ],
        "industries": [{"id": i["id"], "name": i["name"]} for i in INDUSTRIES["industries"]],
    }


class SimBody(BaseModel):
    spotId: str
    industryId: str


@app.post("/api/simulate")
def simulate(body: SimBody):
    spot = next((s for s in SPOTS["spots"] if s["id"] == body.spotId), None)
    industry = next((i for i in INDUSTRIES["industries"] if i["id"] == body.industryId), None)
    parent = next((d for d in DISTRICTS["districts"] if spot and d["name"] == spot["district"]), None)
    rows = INDUSTRY_ROWS.get(body.industryId)
    if not spot or not industry or not parent or not rows:
        raise HTTPException(status_code=400, detail="위치나 업종을 다시 고르세요")
    here = next(row for row in rows if row["district"] == parent["name"])
    latest = parent["latest"]
    avg_kwh = latest["commercialKwh"] / parent["stores"]
    base_sales = DISTRICT_SALES_PER_STORE[parent["name"]]
    sales_ratio = here["salesPerStore"] / base_sales if base_sales else 1
    factor = sales_ratio ** 0.5
    inferred_kwh = avg_kwh * factor
    inferred_bill = bill(inferred_kwh, 0)
    unit = TARIFF["energyPerKwh"] * (1 + TARIFF["vat"] + TARIFF["fund"])
    names = "·".join(industry["seoulNames"])
    parts = [
        {
            "name": "매출",
            "kind": "실측",
            "score": pct(rows, "salesPerStore", here["salesPerStore"], True),
            "text": f"점포당 {comma(here['salesPerStore'])}원",
            "source": f"서울시 추정매출 {QUARTER} {names} 합 ÷ 점포 수",
        },
        {
            "name": "유지",
            "kind": "실측",
            "score": pct(rows, "netOpen", here["netOpen"], True),
            "text": f"개업 {here['openRate']}% - 폐업 {here['closeRate']}%",
            "source": f"서울시 점포 {QUARTER} {names} 개업·폐업 점포 ÷ 점포 수",
        },
        {
            "name": "손님",
            "kind": "추론",
            "score": pct(rows, "flpopPerStore", here["flpopPerStore"], True),
            "text": f"유동 {comma(here['flpop'])} ÷ 점포 {comma(here['stores'])}",
            "source": "유동인구는 구 전체라 이 업종 점포 수로 나눔. 추론",
        },
        {
            "name": "상권",
            "kind": "계산",
            "score": pct(rows, "score", here["score"], True),
            "text": f"활력 {here['score']}점",
            "source": "2026-06 일반용 전력·매출·유동·개폐업·기온으로 계산",
        },
        {
            "name": "건수",
            "kind": "실측",
            "score": pct(rows, "salesCountPerStore", here["salesCountPerStore"], True),
            "text": f"점포당 {comma(here['salesCountPerStore'], 1)}건",
            "source": f"서울시 추정매출 {QUARTER} 매출 건수 ÷ 점포 수",
        },
    ]
    compete = round(sum(part["score"] for part in parts) / len(parts))
    ordered = sorted(
        rows,
        key=lambda row: (
            pct(rows, "salesPerStore", row["salesPerStore"], True)
            + pct(rows, "netOpen", row["netOpen"], True)
            + pct(rows, "flpopPerStore", row["flpopPerStore"], True)
            + pct(rows, "score", row["score"], True)
            + pct(rows, "salesCountPerStore", row["salesCountPerStore"], True)
        ),
        reverse=True,
    )
    rank = next(i for i, row in enumerate(ordered, start=1) if row["district"] == parent["name"])
    facts = [
        {
            "label": "구 평균 전력",
            "kind": "실측",
            "value": f"{comma(avg_kwh)} kWh",
            "how": f"{comma(latest['commercialKwh'])} ÷ {comma(parent['stores'])}",
            "source": f"한전 {POWER_MONTH} {parent['name']} 일반용 ÷ 서울시 점포 합",
        },
        {
            "label": "이 업종 전력",
            "kind": "추론",
            "value": f"{comma(inferred_kwh)} kWh",
            "how": f"{comma(avg_kwh)} × √({comma(here['salesPerStore'])} ÷ {comma(base_sales)}) = × {factor:.2f}",
            "source": "업종 전력이 없어 구 평균에 점포당 매출 비율의 제곱근을 곱함",
        },
        {
            "label": "이 업종 전기세",
            "kind": "추론",
            "value": f"{comma(inferred_bill)}원",
            "how": f"{comma(inferred_kwh)} × {unit:.2f}원",
            "source": "추론 전력 × 한전 2025 일반용 172.69원, 부가세 10%, 기금 3.7%",
        },
        {
            "label": "활력지수",
            "kind": "계산",
            "value": f"{latest['score']}점",
            "how": f"전력 {latest['commercialKwhGwh']} GWh, 개업 {latest['openRate']}%, 폐업 {latest['closeRate']}%",
            "source": "구 전체 공식. 업종으로 나누지 않음",
        },
        {
            "label": "같은 업종",
            "kind": "실측",
            "value": f"{comma(here['stores'])}곳",
            "how": f"개업 {comma(here['opened'])}, 폐업 {comma(here['closed'])}",
            "source": f"서울시 점포 {QUARTER} {names}",
        },
        {
            "label": "점포당 매출",
            "kind": "실측",
            "value": f"{comma(here['salesPerStore'])}원",
            "how": f"{comma(here['salesKrw'])} ÷ {comma(here['stores'])}. 구 평균 {comma(base_sales)}원",
            "source": f"서울시 추정매출 {QUARTER}. 건수 {comma(here['salesCount'])}",
        },
        {
            "label": "경쟁력",
            "kind": "계산",
            "value": f"{compete} / 100",
            "how": "매출·유지·손님·상권·건수 순위를 평균",
            "source": f"같은 업종 25개 구 비교. 이 구는 {rank}위. 손님만 추론",
        },
    ]
    return {
        "spotName": spot["name"],
        "district": parent["name"],
        "industryName": industry["name"],
        "seoulNames": industry["seoulNames"],
        "avgKwh": round(avg_kwh),
        "inferredKwh": round(inferred_kwh),
        "inferredBill": inferred_bill,
        "factor": round(factor, 2),
        "score": latest["score"],
        "level": latest["level"],
        "stores": here["stores"],
        "opened": here["opened"],
        "closed": here["closed"],
        "openRate": here["openRate"],
        "closeRate": here["closeRate"],
        "salesPerStore": here["salesPerStore"],
        "compete": compete,
        "competeRank": rank,
        "parts": parts,
        "facts": facts,
        "note": "골목 주소의 전력·매출은 공개 자료에 없습니다. 숫자는 이 구 행입니다.",
    }


@app.get("/api/plans")
def plans():
    return {
        "items": [
            {
                "title": "단기",
                "price": "4만 9천 원",
                "text": "한 분기, 한 구 자료.",
                "featured": False,
            },
            {
                "title": "월정액",
                "price": "월 19만 원",
                "text": "골목 단위 시계열, 업종 계산, 옆 구 비교.",
                "featured": True,
            },
            {
                "title": "지자체",
                "price": "협의",
                "text": "25개 구를 통째로.",
                "featured": False,
            },
        ],
        "banner": "광고는 전기설비, 상가 임대, 소상공인 대출만.",
    }
