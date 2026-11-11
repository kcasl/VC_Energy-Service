# VC03 PDDL — 전력·가스 기반 상권 활력 지수

PDF 4번 항목(전력 사용량을 통한 상권 활력 지수 측정 서비스)을 구현 가능한 계획으로 고정한다. 플래너 파일은 `docs/commercial-vitality.pddl`(도메인)과 `docs/vitality-mvp.pddl`(문제)이다. 이 문서는 그 계획의 데이터·화면 설명이다.

## 1. Domain

```pddl
(define (domain commercial-vitality)
  (:requirements :typing :fluents :action-costs)
  (:types
    actor region trade-area industry dataset layer product
  )
  (:predicates
    (needs-intel ?a - actor)
    (hard-to-survey ?r - region)
    (has-energy ?r - region)
    (has-commerce ?r - region)
    (mapped ?r - region)
    (indexed ?r - region)
    (searchable ?r - region)
    (sim-ready ?i - industry)
    (cataloged ?d - dataset)
    (subscribed ?a - actor)
  )
  (:functions
    (vitality ?r - region)
    (vacancy-risk ?r - region)
    (energy-kwh ?i - industry)
    (energy-cost ?i - industry)
  )
)
```

### 객체

| 타입 | 인스턴스 |
| --- | --- |
| actor | 지자체, 신규 점포 자영업자, 부동산업자 |
| region | 서울 25 자치구 |
| trade-area | 도심 / 근교 / 골목 샘플 상권 |
| industry | 카페, 한식, 편의점 등 10종 |
| dataset | PDF 우선순위 1–10 + 서울 열린데이터 + Open-Meteo + 경계 |
| layer | 활력 1–5단계 히트맵 |
| product | 웹 공개형, 단기 데이터, 월정액 골목분석, 배너광고 |

### 초기 문제

```pddl
(define (problem vitality-mvp)
  (:domain commercial-vitality)
  (:init
    (needs-intel 지자체) (needs-intel 자영업자) (needs-intel 부동산업자)
    (hard-to-survey 서울)
  )
  (:goal (and
    (cataloged 사용데이터목록)
    (mapped 서울)
    (indexed 서울)
    (searchable 서울)
    (sim-ready 카페)
  ))
)
```

## 2. 문제와 목표

기존 상권 분석은 점포 수·매출·유동 중심이라 영업 강도의 단기 변화를 늦게 본다. 공실 파악도 현장 조사가 필요하다.

목표는 **확보 가능한 에너지 주기**로 자치구·샘플 골목의 활력을 1–5단계로 지도에 올리고, 창업 시 연간 전력·요금을 계산하며, 사용한 데이터를 목록에서 출처·해상도·앱 사용처까지 열어 보는 것이다.

차별점: 점포 수가 아니라 **에너지 활동 추정**.

## 3. Actions (구현 순서)

1. `ingest-public-data` — 키 없이 받는 원문부터 받고, API 키 데이터는 샘플+메타로 목록화.
2. `fuse-district-index` — 전력·가스·매출·유동·개폐업·공실·기온을 자치구 점수로 융합.
3. `paint-heatmap` — 레벨 1 초록(여유) ~ 레벨 5 빨강(활력).
4. `expose-catalog` — 데이터별 목적, 주기, 로컬 파일, 화면 사용처.
5. `simulate-startup` — 지역+업종+면적 → kWh·요금·경쟁·활력 변화.
6. `package-revenue` — 월정액·단기판매·연관 배너 슬롯을 화면으로 보여 주기.

## 4. 활력지수

\[
V = 52 + 28z(전력) + 8z(가스) + 18z(매출) + 10z(유동) + 6(\text{개업}-\text{폐업}) - 8z(공실) - 0.15|\bar T-18|
\]

| 레벨 | 점수 | 색 | 의미 |
| --- | --- | --- | --- |
| 5 | ≥ 78 | 빨강 | 에너지·매출이 몰린 과밀 상권 |
| 4 | ≥ 66 | 주황 | 강한 영업 활동 |
| 3 | ≥ 54 | 노랑 | 보통 |
| 2 | ≥ 42 | 연두 | 여유 |
| 1 | < 42 | 초록 | 한산·침체 징후 |

프로토타입 해상도는 **자치구 + 대표 골목/도심 포인트**. 골목 전수 SHP는 월정액 단계에서 서울시 상권영역과 맞춘다.

## 5. 데이터 호환

네 변수(도시 / 세부주소 / 업종 / 개업시기)는 코드가 다르다.

- 공간: 자치구코드(통계청 5자리) ↔ 서울 상권코드(`TRDAR_CD`) ↔ 좌표.
- 업종: 한전 용도업종 ↔ 서울 생활밀접업종(`SVC_INDUTY_CD`) ↔ 시뮬 10종 매핑 테이블.
- 시간: 한전 월 ↔ 서울 분기(`STDR_YYQU_CD`) ↔ 기상 월. 분기는 월 평균으로 펼친다.

키 발급 후 원문을 같은 키로 바꿔 끼우면 지수 함수는 유지한다.

## 6. 화면 (웹, Vite + React)

| 화면 | 목표 대응 |
| --- | --- |
| 대시보드 | 1년 활력 변화, 에너지 증감, 개폐업, 침체 예상, 공실, 인근 비교 |
| 지도 | 검색 + 5단계 레이어 + 골목 포인트 |
| 사용 데이터 목록 | 우선순위 데이터 상세·샘플 행 |
| 창업 시뮬 | 역삼 골목 카페 같은 시나리오 |
| 구독 | 단기 데이터 / 월정액 / 배너 |

## 7. 이번 수급에서 고정한 것

활력 창은 2025-07 ~ 2026-06. 이 12개월은 한전 월 전력과 서울 분기가 같이 있다.

- 전력: 한전 시군구 일반용 kWh. 2025년 연간 파일과 2026년 8월 파일.
- 매출·개폐업·유동·직장인구: 서울 열린데이터 자치구 시트 CSV.
- 기온: Open-Meteo 일평균을 월평균으로.
- 가스, 공실, 건축물대장, 전국 상가 좌표: 인증 또는 권역 불일치로 지수 밖. 가스·공실 계수는 0.
- 지도 색은 두 가지. 공식 구간은 4절 점수표, 상대 5분위는 25개 구를 다섯 묶음으로 나눈 것. 절대 전력은 강남 쪽에 몰려 공식 구간만 쓰면 1단계가 많다.
- 골목 점은 지명 검색용이다. 색은 자치구 점수와 같다.

## 8. 수익 가설 (보여주기)

- 단기: 특정 분기·자치구 원장 다운로드.
- 월정액: 골목 단위 시계열·공실 경보.
- 배너: 에너지 설비, 상가 임대, 소상공인 금융처럼 서비스와 맞춘 슬롯.
