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

from backend import geoquery

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
NATIONAL = read_json(PROCESSED / "national_power.json")
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
        "gaps": ["가스", "공실", "건축물대장"],
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


def _signed(text: str, value: float) -> str:
    if value > 0:
        return f"+{text}"
    return text


def _won(value: float, sign: bool) -> str:
    if abs(value) >= 100_000_000:
        body = f"{value / 100_000_000:,.1f}억"
    else:
        body = f"{round(value):,}원"
    return _signed(body, value) if sign and value > 0 else body


def _count(value: float, sign: bool) -> str:
    body = f"{round(value):,}"
    return _signed(body, value) if sign and value > 0 else body


def _rank(rows: list[dict]) -> list[dict]:
    values = [row["value"] for row in rows]
    ordered = sorted(rows, key=lambda row: (-row["value"], row["name"], row["sido"]))
    for row in ordered:
        row["rank"] = 1 + sum(1 for value in values if value > row["value"])
    return ordered


@app.get("/api/rising")
def rising(scope: str = "seoul", metric: str = "score", mode: str = "level", sido: str = ""):
    metrics = {"score", "sales", "flpop", "stores", "power"}
    if scope not in {"seoul", "national"} or metric not in metrics:
        raise HTTPException(status_code=400, detail="범위와 항목을 확인하세요")
    if scope != "seoul":
        mode = "level"
    if mode not in {"level", "change"}:
        raise HTTPException(status_code=400, detail="범위와 항목을 확인하세요")
    rows: list[dict] = []
    if scope == "seoul":
        basis = {
            ("score", "level"): "서울 25개 구, 2026-06 활력 V",
            ("sales", "level"): "서울 25개 구, 2026-06에 넣은 분기 매출",
            ("flpop", "level"): "서울 25개 구, 2026-06에 넣은 분기 유동",
            ("stores", "level"): "서울 25개 구, 최신 분기 점포 수",
            ("power", "level"): "서울 25개 구, 2026-06 일반용",
            ("score", "change"): "서울 25개 구, 2026-06 V − 2025-07 V",
            ("sales", "change"): "서울 25개 구, 2026-06 매출 − 2025-07 매출",
            ("flpop", "change"): "서울 25개 구, 2026-06 유동 − 2025-07 유동",
            ("stores", "change"): "서울 25개 구, 최신 분기 개업률 − 폐업률",
            ("power", "change"): "서울 25개 구, 2026-06 일반용 − 2025-06 일반용",
        }[(metric, mode)]
        for district in DISTRICTS["districts"]:
            latest = district["latest"]
            first = district["series"][0]
            if mode == "level":
                raw = {
                    "score": latest["score"],
                    "sales": latest["salesKrw"],
                    "flpop": latest["flpop"],
                    "stores": district["stores"],
                    "power": latest["commercialKwhGwh"],
                }[metric]
                kind = "계산" if metric == "score" else "실측"
            else:
                raw = {
                    "score": district["delta"],
                    "sales": latest["salesKrw"] - first["salesKrw"],
                    "flpop": latest["flpop"] - first["flpop"],
                    "stores": round(district["openRate"] - district["closeRate"], 2),
                    "power": gwh(district["yoyKwh"]),
                }[metric]
                kind = "계산"
            if metric == "score":
                text = f"{raw:.1f}"
            elif metric == "sales":
                text = _won(raw, mode == "change")
            elif metric == "power":
                text = _signed(f"{raw:.1f} GWh", raw) if mode == "change" else f"{raw:.2f} GWh"
            elif metric == "stores" and mode == "change":
                text = _signed(f"{raw:.2f}%p", raw) if raw > 0 else f"{raw:.2f}%p"
            else:
                text = _count(raw, mode == "change")
            rows.append(
                {
                    "sido": "서울특별시",
                    "name": district["name"],
                    "value": raw,
                    "text": text,
                    "kind": kind,
                }
            )
    else:
        basis = {
            "score": "전국 시군구, 2026-06 활력. 서울 밖 매출·유동, 추론",
            "sales": "전국 시군구, 2026-06 매출. 서울 실측, 그 밖 추론",
            "flpop": "전국 시군구, 2026-06 유동. 서울 실측, 그 밖 추론",
            "stores": "전국 시군구, 2026-09-30 상가 수",
            "power": "전국 시군구, 2026-06 일반용",
        }[metric]
        for area in NATIONAL["areas"]:
            if sido and area["sido"] != sido:
                continue
            raw = {
                "score": area["score"],
                "sales": area["salesMonth"],
                "flpop": area["flpop"],
                "stores": area["stores"],
                "power": area["gwh"],
            }[metric]
            if metric == "score":
                text = f"{raw:.1f}"
                kind = "계산" if area["salesKind"] == "실측" else "추론"
            elif metric == "sales":
                text = _won(raw, False)
                kind = area["salesKind"]
            elif metric == "flpop":
                text = _count(raw, False)
                kind = area["flpopKind"]
            elif metric == "stores":
                text = _count(raw, False)
                kind = "실측"
            else:
                text = f"{raw:.2f} GWh"
                kind = "실측"
            rows.append(
                {
                    "sido": area["sido"],
                    "name": area["name"],
                    "value": raw,
                    "text": text,
                    "kind": kind,
                }
            )
    ranked = _rank(rows)
    total = len(ranked)
    shown = ranked if scope == "seoul" else ranked[:20]
    sidos = sorted({area["sido"] for area in NATIONAL["areas"]})
    return {
        "scope": scope,
        "metric": metric,
        "mode": mode,
        "basis": basis,
        "total": total,
        "sidos": sidos,
        "rows": [{key: row[key] for key in ("rank", "sido", "name", "text", "kind")} for row in shown],
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
                "titleEn": item.get("titleEn") or "",
                "ownerEn": item.get("ownerEn") or "",
                "purposeEn": item.get("purposeEn") or "",
                "grainEn": item.get("grainEn") or "",
                "cadenceEn": item.get("cadenceEn") or "",
                "statusEn": item.get("statusEn") or "",
                "notesEn": item.get("notesEn") or "",
                "usedInEn": item.get("usedInEn") or [],
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


def pct_value(values: list[float], value: float, higher: bool) -> int:
    beaten = sum(1 for item in values if (item < value if higher else item > value))
    return round(100 * beaten / max(len(values) - 1, 1))


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
    query: str
    industryId: str


@app.post("/api/simulate")
def simulate(body: SimBody):
    if not geoquery.READY:
        raise HTTPException(status_code=503, detail="전국 점포 자료를 아직 읽지 못했습니다")
    industry = next((i for i in INDUSTRIES["industries"] if i["id"] == body.industryId), None)
    query = body.query.strip()
    if not industry or len(query) < 2:
        raise HTTPException(status_code=400, detail="위치와 업종을 입력하세요")
    found = geoquery.geocode(query)
    area = geoquery.locate(found["lng"], found["lat"]) if found else None
    lat = found["lat"] if found else None
    lng = found["lng"] if found else None
    label = found["label"] if found else query
    if area is None:
        named = geoquery.match_name(query)
        if named is not None:
            area = named
            lat = named["lat"]
            lng = named["lng"]
            label = f"{named['sido']} {named['name']}"
    if area is None or lat is None or lng is None:
        raise HTTPException(status_code=400, detail="위치를 찾지 못했습니다. 시 이름과 동, 역을 같이 적어 보세요")
    shop = geoquery.area_row(area["sido"], area["name"])
    industry_stores = int(shop["byIndustry"][industry["id"]]) if shop else 0
    all_stores = int(shop["allStores"]) if shop else 0
    nearby = geoquery.count_near(industry["id"], lat, lng)
    universe = geoquery.POLYS
    near_values = [geoquery.NEAR[(row["sido"], row["name"], industry["id"])] for row in universe]
    store_values = []
    kwh_values = []
    vital_values = []
    net_values = []
    for row in universe:
        other = geoquery.area_row(row["sido"], row["name"])
        store_values.append(int(other["byIndustry"][industry["id"]]) if other else 0)
        shops = int(other["allStores"]) if other else 0
        if shops:
            kwh_values.append(row["gwh"] * 1_000_000 / shops)
        power = geoquery.POWER.get((row["sido"], row["name"]), {})
        vital_values.append(float(power.get("score") or 0))
        net_values.append(float(power.get("net") or 0))
    avg_kwh = area["gwh"] * 1_000_000 / all_stores if all_stores else None

    def opening_score(near: float, stores: int, kwh: float | None, vital: float, net: float):
        items = [
            ("수요", 35, pct_value(vital_values, vital, True), "활력지수가 높을수록 수요가 있는 상권"),
            ("업종 기반", 20, pct_value(store_values, stores, True), "이 업종이 그 시군구에 이미 있을수록 높음"),
            ("개폐 여유", 20, pct_value(net_values, net, True), "개업이 폐업보다 많을수록 높음"),
            ("주변 여유", 15, 100 - pct_value(near_values, near, True), "1km 같은 업종이 적을수록 높음"),
        ]
        if kwh is not None:
            items.append(("전력 활동", 10, pct_value(kwh_values, kwh, True), "상가당 일반용 전력이 클수록 높음"))
        weight = sum(item[1] for item in items)
        total = sum(item[1] * item[2] for item in items) / weight
        return total, items, weight

    part_scores = [
        pct_value(near_values, nearby, True),
        pct_value(store_values, industry_stores, True),
    ]
    if avg_kwh is not None:
        part_scores.append(pct_value(kwh_values, avg_kwh, True))
    compete = round(sum(part_scores) / len(part_scores))

    def composite(near: float, stores: int, kwh: float | None) -> float:
        scores = [pct_value(near_values, near, True), pct_value(store_values, stores, True)]
        if kwh is not None:
            scores.append(pct_value(kwh_values, kwh, True))
        return sum(scores) / len(scores)

    mine = composite(nearby, industry_stores, avg_kwh)
    mine_power = geoquery.POWER.get((area["sido"], area["name"]), {})
    mine_open, open_items, open_weight = opening_score(
        nearby,
        industry_stores,
        avg_kwh,
        float(mine_power.get("score") or 0),
        float(mine_power.get("net") or 0),
    )
    ahead = 0
    open_ahead = 0
    for row, near, stores in zip(universe, near_values, store_values):
        other = geoquery.area_row(row["sido"], row["name"])
        shops = int(other["allStores"]) if other else 0
        other_kwh = row["gwh"] * 1_000_000 / shops if shops else None
        if composite(near, stores, other_kwh) > mine:
            ahead += 1
        other_power = geoquery.POWER.get((row["sido"], row["name"]), {})
        other_open, _, _ = opening_score(
            near,
            stores,
            other_kwh,
            float(other_power.get("score") or 0),
            float(other_power.get("net") or 0),
        )
        if other_open > mine_open:
            open_ahead += 1
    rank = ahead + 1
    open_score = round(mine_open)
    open_rank = open_ahead + 1
    open_parts = [
        {
            "name": name,
            "weight": weight,
            "percentile": score,
            "points": round(weight * score / open_weight, 1),
            "text": text,
        }
        for name, weight, score, text in open_items
    ]
    parts = [
        {
            "name": "주변 점포",
            "kind": "실측",
            "score": part_scores[0],
            "text": f"1km 안 {comma(nearby)}곳",
            "source": "소상공인시장진흥공단 2026-09-30 상가업소. 각 시군구 중심 1km와 비교",
        },
        {
            "name": "시군구 점포",
            "kind": "실측",
            "score": part_scores[1],
            "text": f"{area['name']} {comma(industry_stores)}곳",
            "source": "같은 파일의 시군구 업종 점포 수. 한전이 구로 나누지 않은 시는 시 합계",
        },
    ]
    if avg_kwh is not None:
        parts.append(
            {
                "name": "상가당 전력",
                "kind": "계산",
                "score": part_scores[2],
                "text": f"{comma(avg_kwh)} kWh",
                "source": f"한전 {POWER_MONTH} {area['name']} 일반용 ÷ 상가업소 {comma(all_stores)}곳",
            }
        )
    parent = next(
        (d for d in DISTRICTS["districts"] if area["sido"] == "서울특별시" and d["name"] == area["name"]),
        None,
    )
    rows = INDUSTRY_ROWS.get(industry["id"]) if parent else None
    here = next((row for row in rows if row["district"] == parent["name"]), None) if rows and parent else None
    inferred_kwh = None
    inferred_bill = None
    factor = None
    seoul_compete = None
    seoul_rank = None
    if parent and here:
        latest = parent["latest"]
        seoul_avg = latest["commercialKwh"] / parent["stores"]
        base_sales = DISTRICT_SALES_PER_STORE[parent["name"]]
        sales_ratio = here["salesPerStore"] / base_sales if base_sales else 1
        raw_kwh = seoul_avg * (sales_ratio ** 0.5)
        factor = round(sales_ratio ** 0.5, 2)
        inferred_kwh = round(raw_kwh)
        inferred_bill = bill(raw_kwh, 0)
        seoul_parts = [
            pct(rows, "salesPerStore", here["salesPerStore"], True),
            pct(rows, "netOpen", here["netOpen"], True),
            pct(rows, "flpopPerStore", here["flpopPerStore"], True),
            pct(rows, "score", here["score"], True),
            pct(rows, "salesCountPerStore", here["salesCountPerStore"], True),
        ]
        seoul_compete = round(sum(seoul_parts) / len(seoul_parts))
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
        seoul_rank = next(i for i, row in enumerate(ordered, start=1) if row["district"] == parent["name"])
        names = "·".join(industry["seoulNames"])
        parts.extend(
            [
                {
                    "name": "서울 매출",
                    "kind": "실측",
                    "score": seoul_parts[0],
                    "text": f"점포당 {comma(here['salesPerStore'])}원",
                    "source": f"서울시 추정매출 {QUARTER} {names}",
                },
                {
                    "name": "서울 유지",
                    "kind": "실측",
                    "score": seoul_parts[1],
                    "text": f"개업 {here['openRate']}% - 폐업 {here['closeRate']}%",
                    "source": f"서울시 점포 {QUARTER} {names}",
                },
            ]
        )
    facts = [
        {
            "label": "찾은 위치",
            "kind": "실측",
            "value": label,
            "how": f"{lat:.5f}, {lng:.5f} → {area['sido']} {area['name']}",
            "source": "주소는 OSM 지오코딩. 시군구는 지도 경계 안에 들어가는지로 정함",
        },
        {
            "label": "1km 업종 점포",
            "kind": "실측",
            "value": f"{comma(nearby)}곳",
            "how": "입력 좌표에서 1km",
            "source": "소상공인시장진흥공단 상가(상권)정보 2026-09-30",
        },
        {
            "label": "시군구 업종 점포",
            "kind": "실측",
            "value": f"{comma(industry_stores)}곳",
            "how": f"상가 전체 {comma(all_stores)}곳",
            "source": "같은 상가업소 파일. 구 이름이 바뀐 곳은 좌표가 들어간 옛 경계로 합침",
        },
        {
            "label": "일반용 전력",
            "kind": "실측",
            "value": f"{area['gwh']} GWh",
            "how": f"전국 {area['rankLevel']}분위",
            "source": f"한전 {POWER_MONTH} {area['sido']} {area['name']} 일반용",
        },
    ]
    if avg_kwh is not None:
        facts.append(
            {
                "label": "상가 평균 전력",
                "kind": "계산",
                "value": f"{comma(avg_kwh)} kWh",
                "how": f"{area['gwh']} GWh ÷ {comma(all_stores)}",
                "source": "이 업종만의 전력은 아니고, 시군구 일반용을 상가 수로 나눈 값",
            }
        )
        facts.append(
            {
                "label": "상가 평균 전기세",
                "kind": "계산",
                "value": f"{comma(bill(avg_kwh, 0))}원",
                "how": f"{comma(avg_kwh)} kWh × 일반용 단가",
                "source": "한전 2025 일반용 172.69원, 부가세 10%, 기금 3.7%",
            }
        )
    if inferred_kwh is not None and parent and here:
        unit = TARIFF["energyPerKwh"] * (1 + TARIFF["vat"] + TARIFF["fund"])
        facts.append(
            {
                "label": "이 업종 전력",
                "kind": "추론",
                "value": f"{comma(inferred_kwh)} kWh",
                "how": f"서울 구 평균 × {factor}",
                "source": "업종 전력이 없어 점포당 매출 비율의 제곱근을 곱함",
            }
        )
        facts.append(
            {
                "label": "이 업종 전기세",
                "kind": "추론",
                "value": f"{comma(inferred_bill)}원",
                "how": f"{comma(inferred_kwh)} × {unit:.2f}원",
                "source": "추론 전력 × 한전 2025 일반용 단가",
            }
        )
    vital_score = mine_power.get("score")
    vital_level = mine_power.get("level")
    sales_kind = mine_power.get("salesKind", "추론")
    if vital_score is not None:
        if sales_kind == "실측":
            how = "전국 229곳 표준화. 이 구의 전력·매출·유동·개폐업은 실측"
            source = "서울 추정매출·유동·점포와 한전 일반용. 기온은 2026-06 서울 23.8도"
        else:
            how = (
                f"추론 매출 {comma(mine_power.get('salesMonth', 0))}원, "
                f"추론 유동 {comma(mine_power.get('flpop', 0))}"
            )
            source = (
                "매출·유동은 서울 점포당 값 × 이 지역 상가 수 × 점포당 전력 비율의 제곱근. "
                "개폐업 자리는 일반용 전년 대비 증감으로 추론"
            )
        facts.append(
            {
                "label": "활력지수",
                "kind": "계산" if sales_kind == "실측" else "추론",
                "value": f"{vital_score}점",
                "how": how,
                "source": source,
            }
        )
    open_kind = "계산" if mine_power.get("salesKind") == "실측" and mine_power.get("netKind") == "실측" else "추론"
    facts.append(
        {
            "label": "개업종합",
            "kind": open_kind,
            "value": f"{open_score} / 100",
            "how": f"{len(universe)}개 시군구 중 {open_rank}위",
            "source": "수요 35, 업종 기반 20, 개폐 여유 20, 주변 여유 15, 전력 활동 10. 각 항목은 전국 백분위",
        }
    )
    facts.append(
        {
            "label": "경쟁력",
            "kind": "계산",
            "value": f"{compete} / 100",
            "how": f"{len(universe)}개 시군구 중 {rank}위",
            "source": "1km 점포, 시군구 점포, 상가당 전력 순위의 평균",
        }
    )
    gaps = [
        {"label": "골목 전력", "reason": f"1km 점포 수는 세지만, 전력은 {area['name']} 일반용 전체입니다."},
        {"label": "가스", "reason": "건물에너지 가스는 받지 못했습니다."},
        {"label": "공실", "reason": "전국 시군구 공실 통계가 없습니다."},
        {"label": "면적별 전력", "reason": "평수·연면적 자료가 없습니다."},
    ]
    if parent is None:
        gaps.insert(0, {"label": "이 업종 전력", "reason": "업종별 전력 계량 자료가 없어 상가 평균 전력만 계산합니다."})
    return {
        "query": query,
        "place": label,
        "sido": area["sido"],
        "area": area["name"],
        "lat": round(lat, 5),
        "lng": round(lng, 5),
        "radiusM": geoquery.RADIUS_M,
        "industryName": industry["name"],
        "nearby": nearby,
        "areaStores": industry_stores,
        "allStores": all_stores,
        "gwh": area["gwh"],
        "rankLevel": area["rankLevel"],
        "avgKwh": round(avg_kwh) if avg_kwh is not None else None,
        "avgBill": bill(avg_kwh, 0) if avg_kwh is not None else None,
        "inferredKwh": inferred_kwh,
        "inferredBill": inferred_bill,
        "factor": factor,
        "score": vital_score if vital_score is not None else (parent["latest"]["score"] if parent else None),
        "level": mine_power.get("vitalRank") or vital_level or (parent["latest"]["level"] if parent else None),
        "scoreKind": "계산" if sales_kind == "실측" else "추론",
        "seoul": parent is not None,
        "salesPerStore": here["salesPerStore"] if here else None,
        "openRate": here["openRate"] if here else None,
        "closeRate": here["closeRate"] if here else None,
        "opened": here["opened"] if here else None,
        "closed": here["closed"] if here else None,
        "openScore": open_score,
        "openRank": open_rank,
        "openOf": len(universe),
        "openKind": open_kind,
        "openParts": open_parts,
        "compete": compete,
        "competeRank": rank,
        "competeOf": len(universe),
        "seoulCompete": seoul_compete,
        "seoulRank": seoul_rank,
        "parts": parts,
        "facts": facts,
        "gaps": gaps,
        "note": "개업종합은 이 서비스에서만 쓰는 100점입니다. 위치는 입력한 주소를 좌표로 바꾼 뒤 1km를 셉니다. 서울 밖 매출·유동·개폐업은 추론입니다.",
    }


try:
    geoquery.load()
except FileNotFoundError:
    pass


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
