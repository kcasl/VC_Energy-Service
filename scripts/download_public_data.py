"""Download public sources for the commercial vitality prototype.

KEPCO monthly workbooks are fetched by file id from the public sales board.
Seoul commercial sheets are the same CSV export the open-data page uses.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1] / "public" / "data" / "raw"
ROOT.mkdir(parents=True, exist_ok=True)

KEPCO_FILES = {
    "202512": "9A4z/Nmuaryk32tG2xJtTw==",
    "202608": "jxw6J3czSiqSSvf4+6iqkg==",
}
KEPCO_SEQ = "DIMtNyzfJ3kKEXQCksqfEQ=="

SEOUL_SHEETS = {
    "seoul_signgu_store.csv": "OA-22173",
    "seoul_signgu_sales.csv": "OA-22176",
    "seoul_signgu_flpop.csv": "OA-22179",
    "seoul_signgu_worker.csv": "OA-22185",
}


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0"
    return s


def download_kepco(s: requests.Session) -> None:
    s.get(
        "https://www.kepco.co.kr/home/customer/library/electricity-statistics/sales-volume/boardList.do",
        timeout=40,
    )
    for stamp, file_no in KEPCO_FILES.items():
        dest = ROOT / f"kepco_sigungu_{stamp}.xlsx"
        if dest.exists() and dest.stat().st_size > 100_000:
            print("kepco skip", dest.name, dest.stat().st_size)
            continue
        r = s.post(
            "https://www.kepco.co.kr/c2r/FileDownload.do",
            data={"fileNo": file_no, "fileSeq": KEPCO_SEQ},
            timeout=120,
        )
        r.raise_for_status()
        if not r.content.startswith(b"PK"):
            raise SystemExit(f"kepco {stamp} is not an xlsx ({r.headers.get('content-type')})")
        dest.write_bytes(r.content)
        print("kepco", dest.name, len(r.content))


def download_seoul(s: requests.Session) -> None:
    for name, inf_id in SEOUL_SHEETS.items():
        dest = ROOT / name
        if dest.exists() and dest.stat().st_size > 5_000:
            print("seoul skip", name, dest.stat().st_size)
            continue
        r = s.post(
            "https://datafile.seoul.go.kr/bigfile/iot/sheet/csv/download.do",
            data={
                "srvType": "S",
                "infId": inf_id,
                "serviceKind": "0",
                "pageNo": "1",
                "ssUserId": "SAMPLE_VIEW",
                "strWhere": "",
                "strOrderby": "",
                "filterCol": "필터선택",
                "txtFilter": "",
            },
            timeout=180,
        )
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        head = r.content[:200]
        if b"html" in head[:80].lower() or "text/html" in ctype:
            dest.with_suffix(".err.html").write_bytes(r.content[:4000])
            raise SystemExit(f"seoul {name} returned html, not csv")
        dest.write_bytes(r.content)
        print("seoul", name, len(r.content), ctype)


def download_weather(s: requests.Session) -> None:
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=37.5665&longitude=126.978"
        "&start_date=2024-01-01&end_date=2026-08-31"
        "&daily=temperature_2m_mean&timezone=Asia%2FSeoul"
    )
    r = s.get(url, timeout=60)
    r.raise_for_status()
    payload = r.json()
    dest = ROOT / "seoul_weather_2024_2026.json"
    dest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print("weather", dest.name, len(r.content))


def download_sbiz(s: requests.Session) -> None:
    dest = ROOT / "sbiz_stores_20260930.zip"
    if dest.exists() and dest.stat().st_size > 300_000_000:
        print("sbiz skip", dest.stat().st_size)
        return
    s.get("https://www.data.go.kr/data/15083033/fileData.do", timeout=40)
    meta = s.post(
        "https://www.data.go.kr/tcs/dss/selectFileDataDownload.do",
        data={
            "publicDataDetailPk": "uddi:86f46f63-829a-46c1-abdd-d8e66846b6da",
            "publicDataPk": "15083033",
            "atchFileId": "",
            "fileDetailSn": "1",
            "publicDataTyCode": "PR0051",
        },
        timeout=40,
    ).json()
    with s.get(
        "https://www.data.go.kr/cmm/cmm/fileDownload.do",
        params={"atchFileId": meta["atchFileId"], "fileDetailSn": meta["fileDetailSn"]},
        stream=True,
        timeout=180,
    ) as response:
        response.raise_for_status()
        with dest.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    print("sbiz", dest.name, dest.stat().st_size)


def main() -> None:
    s = session()
    download_kepco(s)
    download_seoul(s)
    download_weather(s)
    download_sbiz(s)


if __name__ == "__main__":
    main()
