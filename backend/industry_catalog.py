"""Startup trades backed by both Seoul service names and SEMAS shop categories.

The first ten keep the existing grouping. Later rows are Seoul service
names whose national small-category names were not already in those ten.
A shop is counted once, under the first matching trade.
"""

from __future__ import annotations

INDUSTRIES: list[dict] = [
    {"id": "cafe", "name": "카페", "match": ["커피"], "seoulNames": ["커피-음료"], "kwhPerPyeong": 118, "kwPerPyeong": 0.38, "note": "머신·냉난방 비중을 가정한 원단위. 지역 가중만 실측 전력/점포."},
    {"id": "korean", "name": "한식", "match": ["한식음식점"], "seoulNames": ["한식음식점"], "kwhPerPyeong": 176, "kwPerPyeong": 0.52, "note": "취사 부하를 가정한 원단위."},
    {"id": "chicken", "name": "치킨·분식", "match": ["치킨", "분식"], "seoulNames": ["분식전문점", "치킨전문점"], "kwhPerPyeong": 154, "kwPerPyeong": 0.48, "note": "튀김 피크를 가정한 원단위."},
    {"id": "pub", "name": "호프·주점", "match": ["호프"], "seoulNames": ["호프-간이주점"], "kwhPerPyeong": 96, "kwPerPyeong": 0.32, "note": "야간 조명·냉방을 가정한 원단위."},
    {"id": "cvs", "name": "편의점", "match": ["편의점"], "seoulNames": ["편의점"], "kwhPerPyeong": 268, "kwPerPyeong": 0.62, "note": "24시간 냉장·조명을 가정한 원단위."},
    {"id": "beauty", "name": "미용", "match": ["미용실"], "seoulNames": ["미용실"], "kwhPerPyeong": 54, "kwPerPyeong": 0.22, "note": "드라이어·온수를 가정한 원단위."},
    {"id": "academy", "name": "학원", "match": ["학원"], "seoulNames": ["예술학원", "외국어학원", "일반교습학원", "컴퓨터학원"], "kwhPerPyeong": 62, "kwPerPyeong": 0.24, "note": "조명·공조를 가정한 원단위. 예술·외국어·일반·컴퓨터학원을 합칩니다."},
    {"id": "retail", "name": "의류소매", "match": ["일반의류"], "seoulNames": ["일반의류"], "kwhPerPyeong": 41, "kwPerPyeong": 0.18, "note": "조명·공조를 가정한 원단위."},
    {"id": "gym", "name": "헬스", "match": ["스포츠클럽"], "seoulNames": ["스포츠클럽"], "kwhPerPyeong": 102, "kwPerPyeong": 0.36, "note": "운동기기·공조를 가정한 원단위."},
    {"id": "pharmacy", "name": "약국", "match": ["의약품"], "seoulNames": ["의약품"], "kwhPerPyeong": 47, "kwPerPyeong": 0.2, "note": "서울 생활밀접업종명은 의약품. 냉장·조명을 가정한 원단위."},
    {"id": "realestate", "name": "부동산중개업", "seoulNames": ["부동산중개업"], "smallNames": ["부동산 중개/대리업"]},
    {"id": "cosmetics", "name": "화장품", "seoulNames": ["화장품"], "smallNames": ["화장품 소매업"]},
    {"id": "mart", "name": "슈퍼마켓", "seoulNames": ["슈퍼마켓"], "smallNames": ["슈퍼마켓"]},
    {"id": "clinic", "name": "일반의원", "seoulNames": ["일반의원"], "smallNames": ["내과/소아과 의원", "피부/비뇨기과 의원", "외과 의원", "이비인후과 의원", "신경/정신과 의원", "성형외과 의원", "산부인과 의원", "안과 의원", "기타 의원", "방사선 진단/병리 검사 의원"]},
    {"id": "lighting", "name": "조명용품", "seoulNames": ["조명용품"], "smallNames": ["전기용품/조명장치 소매업"]},
    {"id": "banchan", "name": "반찬가게", "seoulNames": ["반찬가게"], "smallNames": ["반찬/식료품 소매업"]},
    {"id": "computer", "name": "컴퓨터및주변장치판매", "seoulNames": ["컴퓨터및주변장치판매"], "smallNames": ["컴퓨터/소프트웨어 소매업"]},
    {"id": "fruit", "name": "청과상", "seoulNames": ["청과상"], "smallNames": ["채소/과일 소매업"]},
    {"id": "western", "name": "양식음식점", "seoulNames": ["양식음식점"], "smallNames": ["경양식", "파스타/스테이크", "패밀리레스토랑", "기타 서양식 음식점"]},
    {"id": "tax", "name": "세무사사무소", "seoulNames": ["세무사사무소"], "smallNames": ["세무사"]},
    {"id": "bakery", "name": "제과점", "seoulNames": ["제과점"], "smallNames": ["빵/도넛"]},
    {"id": "butcher", "name": "육류판매", "seoulNames": ["육류판매"], "smallNames": ["정육점"]},
    {"id": "photo", "name": "사진관", "seoulNames": ["사진관"], "smallNames": ["사진촬영업"]},
    {"id": "travel", "name": "여행사", "seoulNames": ["여행사"], "smallNames": ["여행사", "기타 여행 보조/예약 서비스업"]},
    {"id": "japanese", "name": "일식음식점", "seoulNames": ["일식음식점"], "smallNames": ["일식 회/초밥", "일식 카레/돈가스/덮밥", "일식 면 요리", "기타 일식 음식점"]},
    {"id": "fastfood", "name": "패스트푸드점", "seoulNames": ["패스트푸드점"], "smallNames": ["피자", "버거", "토스트/샌드위치/샐러드"]},
    {"id": "flower", "name": "화초", "seoulNames": ["화초"], "smallNames": ["꽃집"]},
    {"id": "chinese", "name": "중식음식점", "seoulNames": ["중식음식점"], "smallNames": ["중국집", "마라탕/훠궈"]},
    {"id": "phone", "name": "핸드폰", "seoulNames": ["핸드폰"], "smallNames": ["핸드폰 소매업"]},
    {"id": "laundry", "name": "세탁소", "seoulNames": ["세탁소"], "smallNames": ["세탁소", "셀프 빨래방"]},
    {"id": "jewelry", "name": "시계및귀금속", "seoulNames": ["시계및귀금속"], "smallNames": ["시계/귀금속 소매업"]},
    {"id": "cleaning", "name": "건축물청소", "seoulNames": ["건축물청소"], "smallNames": ["건축물 일반 청소업"]},
    {"id": "karaoke", "name": "노래방", "seoulNames": ["노래방"], "smallNames": ["노래방"]},
    {"id": "seafood", "name": "수산물판매", "seoulNames": ["수산물판매"], "smallNames": ["수산물 소매업", "건어물/젓갈 소매업"]},
    {"id": "dental", "name": "치과의원", "seoulNames": ["치과의원"], "smallNames": ["치과의원"]},
    {"id": "lawyer", "name": "변호사사무소", "seoulNames": ["변호사사무소"], "smallNames": ["변호사"]},
    {"id": "carfix", "name": "자동차수리", "seoulNames": ["자동차수리"], "smallNames": ["자동차 정비소"]},
    {"id": "stationery", "name": "문구", "seoulNames": ["문구"], "smallNames": ["문구/회화용품 소매업"]},
    {"id": "interior", "name": "인테리어", "seoulNames": ["인테리어"], "smallNames": ["인테리어 디자인업"]},
    {"id": "books", "name": "서적", "seoulNames": ["서적"], "smallNames": ["서점"]},
    {"id": "shoes", "name": "신발", "seoulNames": ["신발"], "smallNames": ["신발 소매업"]},
    {"id": "sportsgoods", "name": "운동/경기용품", "seoulNames": ["운동/경기용품"], "smallNames": ["운동용품 소매업"]},
    {"id": "oriental", "name": "한의원", "seoulNames": ["한의원"], "smallNames": ["한의원"]},
    {"id": "billiards", "name": "당구장", "seoulNames": ["당구장"], "smallNames": ["당구장"]},
    {"id": "meddevice", "name": "의료기기", "seoulNames": ["의료기기"], "smallNames": ["의료기기 소매업"]},
    {"id": "autoparts", "name": "자동차부품", "seoulNames": ["자동차부품"], "smallNames": ["자동차 부품 소매업", "타이어 소매업"]},
    {"id": "textile", "name": "섬유제품", "seoulNames": ["섬유제품"], "smallNames": ["실/섬유제품 소매업"]},
    {"id": "motel", "name": "여관", "seoulNames": ["여관"], "smallNames": ["여관/모텔"]},
    {"id": "furniture", "name": "가구", "seoulNames": ["가구"], "smallNames": ["가구 소매업"]},
    {"id": "fixapp", "name": "가전제품수리", "seoulNames": ["가전제품수리"], "smallNames": ["가전제품 수리업"]},
    {"id": "bag", "name": "가방", "seoulNames": ["가방"], "smallNames": ["가방 소매업"]},
    {"id": "rice", "name": "미곡판매", "seoulNames": ["미곡판매"], "smallNames": ["곡물/곡분 소매업"]},
    {"id": "glasses", "name": "안경", "seoulNames": ["안경"], "smallNames": ["안경렌즈 소매업"]},
    {"id": "pet", "name": "애완동물", "seoulNames": ["애완동물"], "smallNames": ["애완동물/애완용품 소매업"]},
    {"id": "judicial", "name": "법무사사무소", "seoulNames": ["법무사사무소"], "smallNames": ["법무사"]},
    {"id": "appliance", "name": "가전제품", "seoulNames": ["가전제품"], "smallNames": ["가전제품 소매업"]},
    {"id": "artgoods", "name": "예술품", "seoulNames": ["예술품"], "smallNames": ["예술품 소매업"]},
    {"id": "hardware", "name": "철물점", "seoulNames": ["철물점"], "smallNames": ["철물/공구 소매업"]},
    {"id": "otherlaw", "name": "기타법무서비스", "seoulNames": ["기타법무서비스"], "smallNames": ["행정사", "공인노무사", "기타 법무관련 서비스업"]},
    {"id": "translate", "name": "통번역서비스", "seoulNames": ["통번역서비스"], "smallNames": ["번역/통역 서비스업"]},
    {"id": "golf", "name": "골프연습장", "seoulNames": ["골프연습장"], "smallNames": ["골프 연습장"]},
    {"id": "carwash", "name": "자동차미용", "seoulNames": ["자동차미용"], "smallNames": ["자동차 세차장"]},
    {"id": "pcroom", "name": "PC방", "seoulNames": ["PC방"], "smallNames": ["PC방"]},
    {"id": "toys", "name": "완구", "seoulNames": ["완구"], "smallNames": ["장난감 소매업"]},
    {"id": "vet", "name": "동물병원", "seoulNames": ["동물병원"], "smallNames": ["동물병원"]},
    {"id": "lottery", "name": "복권방", "seoulNames": ["복권방"], "smallNames": ["복권 발행/판매업"]},
    {"id": "accountant", "name": "회계사사무소", "seoulNames": ["회계사사무소"], "smallNames": ["공인회계사"]},
    {"id": "gas", "name": "주유소", "seoulNames": ["주유소"], "smallNames": ["주유소"]},
    {"id": "patent", "name": "변리사사무소", "seoulNames": ["변리사사무소"], "smallNames": ["변리사"]},
    {"id": "moto", "name": "모터사이클및부품", "seoulNames": ["모터사이클및부품"], "smallNames": ["모터사이클 및 부품 소매업"]},
    {"id": "bicycle", "name": "자전거 및 기타운송장비", "seoulNames": ["자전거 및 기타운송장비"], "smallNames": ["자전거 소매업"]},
    {"id": "instrument", "name": "악기", "seoulNames": ["악기"], "smallNames": ["악기 소매업"]},
    {"id": "dvd", "name": "DVD방", "seoulNames": ["DVD방"], "smallNames": ["비디오방"]},
    {"id": "motofix", "name": "모터사이클수리", "seoulNames": ["모터사이클수리"], "smallNames": ["모터사이클 수리업"]},
    {"id": "phonerepair", "name": "통신기기수리", "seoulNames": ["통신기기수리"], "smallNames": ["핸드폰/통신장비 수리업"]},
    {"id": "hanbok", "name": "한복점", "seoulNames": ["한복점"], "smallNames": ["한복 소매업"]},
    {"id": "arcade", "name": "전자게임장", "seoulNames": ["전자게임장"], "smallNames": ["전자 게임장"]},
    {"id": "bowling", "name": "볼링장", "seoulNames": ["볼링장"], "smallNames": ["볼링장"]},
    {"id": "goshiwon", "name": "고시원", "seoulNames": ["고시원"], "smallNames": ["기숙사/고시원"]},
]

INDUSTRY_IDS = [row["id"] for row in INDUSTRIES]
SMALL_TO_ID = {
    small: row["id"]
    for row in INDUSTRIES
    if row.get("smallNames")
    for small in row["smallNames"]
}


def legacy(small: str, mid: str) -> str | None:
    text = f"{small}|{mid}".replace(" ", "")
    if "약국" in text or "의약품" in text:
        return "pharmacy"
    if "편의점" in text:
        return "cvs"
    if "카페" in text or "커피" in text:
        return "cafe"
    if "치킨" in text or "분식" in text:
        return "chicken"
    if "주점" in text or "호프" in text or "생맥주" in text:
        return "pub"
    if any(token in text for token in ("한식", "백반", "한정식", "찌개", "국수", "냉면", "돼지고기", "소고기", "곱창", "족발", "보쌈")):
        return "korean"
    if "미용" in text or "피부관리" in text or "네일" in text:
        return "beauty"
    if "학원" in text or "교습" in text:
        return "academy"
    if "헬스" in text or "체력단련" in text or "피트니스" in text:
        return "gym"
    if "의류" in text:
        return "retail"
    return None


def classify(small: str, mid: str) -> str | None:
    exact = SMALL_TO_ID.get(small)
    old = legacy(small, mid)
    if exact and old and exact != old:
        raise RuntimeError(f"trade overlap {small}: {exact} and {old}")
    return exact or old


def public_rows() -> list[dict]:
    rows = []
    for row in INDUSTRIES:
        item = {"id": row["id"], "name": row["name"], "seoulNames": list(row["seoulNames"])}
        if row.get("smallNames"):
            item["smallNames"] = list(row["smallNames"])
        else:
            item["kwhPerPyeong"] = row["kwhPerPyeong"]
            item["kwPerPyeong"] = row["kwPerPyeong"]
            item["note"] = row["note"]
            item["match"] = list(row["match"])
        rows.append(item)
    return rows
