"""Fill a June 2026 vitality score for every municipality.

Seoul keeps measured sales, footfall, and open/close. Other regions
do not publish those tables, so those three inputs are inferred from
shop counts and commercial electricity and marked as such.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_national_map import ALT

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "public" / "data" / "raw"
OUT = ROOT / "public" / "data" / "processed"
SEOUL_JUNE = 23.8


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


def zscores(values: list[float]) -> list[float]:
    mean = sum(values) / len(values)
    var = sum((n - mean) ** 2 for n in values) / len(values)
    std = var**0.5 or 1.0
    return [(n - mean) / std for n in values]


def median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def commercial(path: Path, year: int) -> dict[tuple[str, str], int]:
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    header = None
    found: dict[tuple[str, str], int] = {}
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == "연도":
            header = list(row)
            continue
        if header is None or not row or row[0] != year:
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


def main() -> None:
    power = json.loads((OUT / "national_power.json").read_text(encoding="utf-8"))
    shops = {
        (row["sido"], row["name"]): row
        for row in json.loads((OUT / "national_stores.json").read_text(encoding="utf-8"))["areas"]
        if row.get("kepco")
    }
    seoul = {
        row["name"]: row
        for row in json.loads((OUT / "districts.json").read_text(encoding="utf-8"))["districts"]
    }
    kwh_2025 = commercial(RAW / "kepco_sigungu_202512.xlsx", 2025)
    kwh_2026 = commercial(RAW / "kepco_sigungu_202608.xlsx", 2026)

    rows = []
    for area in power["areas"]:
        key = (area["sido"], area["name"])
        shop = shops.get(key)
        stores = int(shop["allStores"]) if shop else 0
        kwh = kwh_2026.get(key, int(round(area["gwh"] * 1_000_000)))
        prev = kwh_2025.get(key)
        yoy = (kwh - prev) / prev if prev else None
        parent = seoul.get(area["name"]) if area["sido"] == "서울특별시" else None
        rows.append(
            {
                "area": area,
                "stores": stores,
                "kwh": kwh,
                "yoy": yoy,
                "seoul": parent,
            }
        )

    seoul_rows = [row for row in rows if row["seoul"] and row["stores"]]
    sales_per = [row["seoul"]["latest"]["salesKrw"] / row["stores"] for row in seoul_rows]
    flpop_per = [row["seoul"]["latest"]["flpop"] / row["stores"] for row in seoul_rows]
    kwh_per = [row["kwh"] / row["stores"] for row in seoul_rows]
    nets = [row["seoul"]["latest"]["openRate"] - row["seoul"]["latest"]["closeRate"] for row in seoul_rows]
    med_sales = median(sales_per)
    med_flpop = median(flpop_per)
    med_kwh = median(kwh_per) or 1.0
    med_net = median(nets)
    yoys = [row["yoy"] for row in rows if row["yoy"] is not None]
    med_yoy = median(yoys) if yoys else 0.0

    sales_values = []
    flpop_values = []
    for row in rows:
        parent = row["seoul"]
        if parent:
            row["sales"] = float(parent["latest"]["salesKrw"])
            row["flpop"] = float(parent["latest"]["flpop"])
            row["net"] = parent["latest"]["openRate"] - parent["latest"]["closeRate"]
            row["salesKind"] = "실측"
            row["flpopKind"] = "실측"
            row["netKind"] = "실측"
            row["temp"] = SEOUL_JUNE
            row["tempKind"] = "실측"
        else:
            per = row["kwh"] / row["stores"] if row["stores"] else med_kwh
            factor = (per / med_kwh) ** 0.5
            row["sales"] = med_sales * row["stores"] * factor
            row["flpop"] = med_flpop * row["stores"] * factor
            yoy = row["yoy"] if row["yoy"] is not None else med_yoy
            row["net"] = max(-4.0, min(4.0, med_net + 12 * (yoy - med_yoy)))
            row["salesKind"] = "추론"
            row["flpopKind"] = "추론"
            row["netKind"] = "추론"
            row["temp"] = round(26 - 0.55 * (row["area"]["lat"] - 33), 1)
            row["tempKind"] = "추론"
        sales_values.append(row["sales"])
        flpop_values.append(row["flpop"])

    zk = zscores([row["kwh"] for row in rows])
    zs = zscores(sales_values)
    zp = zscores(flpop_values)
    for index, row in enumerate(rows):
        score = (
            52
            + 28 * zk[index]
            + 18 * zs[index]
            + 10 * zp[index]
            + 6 * row["net"]
            - 0.15 * abs(row["temp"] - 18)
        )
        row["score"] = round(score, 1)
        row["level"] = level_of(row["score"])

    ordered = sorted(rows, key=lambda row: row["score"])
    count = len(ordered)
    for index, row in enumerate(ordered):
        row["vitalRank"] = min(5, index * 5 // count + 1)

    for row in rows:
        area = row["area"]
        area.update(
            {
                "score": row["score"],
                "level": row["level"],
                "vitalRank": row["vitalRank"],
                "salesMonth": round(row["sales"]),
                "flpop": round(row["flpop"]),
                "net": round(row["net"], 2),
                "temp": row["temp"],
                "salesKind": row["salesKind"],
                "flpopKind": row["flpopKind"],
                "netKind": row["netKind"],
                "tempKind": row["tempKind"],
                "stores": row["stores"],
            }
        )

    (OUT / "national_power.json").write_text(json.dumps(power, ensure_ascii=False), encoding="utf-8")
    geo_path = OUT / "national_map.geojson"
    geo = json.loads(geo_path.read_text(encoding="utf-8"))
    by_key = {(row["area"]["sido"], row["area"]["name"]): row for row in rows}
    for feat in geo["features"]:
        props = feat["properties"]
        row = by_key[(props["sido"], props["name"])]
        props.update(
            {
                "score": row["score"],
                "level": row["level"],
                "vitalRank": row["vitalRank"],
                "salesKind": row["salesKind"],
                "flpopKind": row["flpopKind"],
                "netKind": row["netKind"],
            }
        )
    geo_path.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"n {len(rows)} score {min(r['score'] for r in rows)} .. {max(r['score'] for r in rows)}",
        "levels " + " ".join(f"{lv}:{sum(1 for r in rows if r['level']==lv)}" for lv in range(1, 6)),
        f"med sales/store {med_sales:.0f} flpop/store {med_flpop:.0f} kwh/store {med_kwh:.0f} net {med_net:.2f} yoy {med_yoy:.3f}",
    ]
    for sido, name in [
        ("서울특별시", "강남구"),
        ("서울특별시", "도봉구"),
        ("경기도", "수원시"),
        ("부산광역시", "해운대구"),
        ("강원특별자치도", "철원군"),
        ("인천광역시", "동구"),
    ]:
        row = by_key[(sido, name)]
        lines.append(
            f"{sido} {name} score {row['score']} L{row['level']} q{row['vitalRank']} "
            f"sales {row['salesKind']} {round(row['sales'])} flpop {row['flpopKind']} {round(row['flpop'])} "
            f"net {row['netKind']} {row['net']:.2f}"
        )
    Path(__file__).with_name("_vital_out.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", len(rows))


if __name__ == "__main__":
    main()
