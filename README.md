# 상권 활력

PDF 4번 — 전력·가스 사용량으로 상권 활력 지수를 읽는 웹 프로토타입.

설계는 `docs/commercial-vitality.pddl`, `docs/vitality-mvp.pddl`. 설명은 `docs/PDDL.md`. 화면은 Vite + React, 계산과 자료는 FastAPI.

```bash
npm install
npm run data
npm run api
npm run dev
```

- 대시보드: 1년 활력, 에너지 증감, 개폐업, 침체·공실
- 지도: 자치구 5단계 히트맵, 골목 포인트, 검색
- 사용 데이터 목록: 우선순위 데이터 출처·샘플
- 창업 시뮬: 위치×업종×면적 → kWh·요금
- 구독·배너: 수익 가설 화면

원문 데이터는 `public/data/raw`, 융합 결과는 `public/data/processed`.

```bash
npm run data
```

`scripts/download_public_data.py`가 한전 월보 xlsx, 서울 자치구 상권 CSV, Open-Meteo 기온을 받고 `scripts/build_processed_data.py`가 활력지수를 만든다. 가스·공실·건축물대장은 인증이 필요해 지수에서 빠져 있다.
