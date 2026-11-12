import { FormEvent, useState } from "react";
import Tex from "../components/Tex";
import { usePrefs, type Lang } from "../lib/prefs";

const GATE = "cvi-admin";

type Copy = { ko: string; en: string };
type Block = Copy | { tex: string };
type Section = { title: Copy; blocks: Block[] };

const SECTIONS: Section[] = [
  {
    title: { ko: "공통 정의", en: "Shared definitions" },
    blocks: [
      {
        ko: "집합 X, 크기 n의 평균과 모표준편차. 표준편차 0만 분모 1. 1 미만 양수 표준편차는 유지. 표본표준편차(n−1) 미사용.",
        en: "For a set X of size n, the mean and the population standard deviation are below. The denominator is replaced by 1 only when the standard deviation is 0. A positive standard deviation below 1 is kept. The sample standard deviation with n−1 is not used.",
      },
      {
        tex: String.raw`\bar x=\frac1n\sum_{i\in X}x_i,\quad s(X)=\sqrt{\frac1n\sum_{i\in X}(x_i-\bar x)^2},\quad z_X(x_i)=\frac{x_i-\bar x}{s^*(X)},\quad s^*(X)=\begin{cases}1&s(X)=0\\ s(X)&s(X)>0\end{cases}`,
      },
      {
        ko: "중앙값 m. 오름차순에서 홀수면 가운데 값, 짝수면 가운데 두 값의 평균.",
        en: "The median m is the middle value of the ascending list when n is odd, and the mean of the two middle values when n is even.",
      },
      {
        tex: String.raw`m(x)=\begin{cases}x_{((n+1)/2)}&n\text{ odd}\\[4pt]\frac12\left(x_{(n/2)}+x_{(n/2+1)}\right)&n\text{ even}\end{cases}`,
      },
      {
        ko: "백분위 P⁺. 자기 자신 제외, 엄격히 작은 값의 비율. 동점 미포함. round는 Python 3 round. 딱 0.5는 짝수 쪽.",
        en: "The percentile P⁺ excludes the value itself and counts elements that are strictly smaller. Ties are not counted as beaten. round is Python 3 round: a tie at .5 goes to the even neighbor.",
      },
      {
        tex: String.raw`P^{+}(v;a)=\mathrm{round}\!\left(\frac{100\cdot|\{b\in v:b<a\}|}{\max(|v|-1,1)}\right)`,
      },
      {
        ko: "절대 등급 L과 오름차순 분위 q, 서로 다른 양. 분위 첨자 i는 0부터. 같은 값은 안정 정렬로 입력 순서 유지.",
        en: "The absolute level L and the ascending quintile q are different quantities. The quintile index i starts at 0. Equal values keep their input order because the sort is stable.",
      },
      {
        tex: String.raw`L(V)=\begin{cases}5&V\ge 78\\4&V\ge 66\\3&V\ge 54\\2&V\ge 42\\1&V<42\end{cases}\qquad q(i,n)=\min\!\left(5,\left\lfloor\frac{5i}{n}\right\rfloor+1\right)`,
      },
    ],
  },
  {
    title: { ko: "서울 월별 활력", en: "Seoul monthly vitality" },
    blocks: [
      {
        ko: "대시보드 시계열. 구간 2025-07–2026-06. 매월 z점수는 서울 25개 구 안에서 재계산. E는 일반용 kWh. S는 분기 당월 매출 합의 1/3, 분기 내 동일. F는 그 분기 구 전체 유동인구.",
        en: "This is the dashboard series. The window is 2025-07 through 2026-06. Each month the z-scores are recomputed inside the 25 Seoul districts only. E is commercial kWh. S is that quarter’s monthly sales total divided by 3, so it is constant inside a quarter. F is the district’s quarterly footfall.",
      },
      {
        tex: String.raw`q(y,m)=10y+\left\lfloor\frac{m-1}{3}\right\rfloor+1`,
      },
      {
        ko: "분기 코드 q, 매출·유동·점포를 월에 붙이는 키. 2026-06은 20262. F, 그 분기의 총 유동인구. 시간대 칸과 직장인구, V 밖.",
        en: "The quarter code q attaches sales, footfall, and shops to a month. June 2026 is 20262. F is that quarter’s total footfall. Time-of-day columns and the worker count stay outside V.",
      },
      {
        ko: "개업률·폐업률, 점포 수 합으로 다시 계산한 퍼센트포인트. 파일의 개업률 칸은 표에만 사용. 점포 수 0이면 분모 1. 식에 들어가는 o·c, 소수 둘째 자리 반올림 후. T, 일평균의 월평균을 소수 한 자리로 반올림한 값. 가스·공실, 식에서 제외.",
        en: "Opening and closing rates are percentage points recomputed from summed shop counts. The rate column in the file is shown only in the table. A zero shop count uses 1 as the divisor. The o and c that enter the score are those rates after rounding to two decimals. T is the monthly mean of the daily means, rounded to one decimal before it enters the score. Gas and vacancy are not terms.",
      },
      {
        tex: String.raw`o=\mathrm{round}_2\!\left(100\cdot\frac{N_{\mathrm{open}}}{N_{\mathrm{store}}}\right),\quad c=\mathrm{round}_2\!\left(100\cdot\frac{N_{\mathrm{close}}}{N_{\mathrm{store}}}\right),\quad T_m=\mathrm{round}_1\!\left(\frac{1}{|D_m|}\sum_{d\in D_m}T_d\right)`,
      },
      {
        tex: String.raw`V_{m,d}=\mathrm{round}_1\!\left(52+28\,z(E_{m,d})+18\,z(S_{m,d})+10\,z(F_{m,d})+6(o_{m,d}-c_{m,d})-0.15\,|T_m-18|\right)`,
      },
      {
        ko: "이 식의 z, 그 달 25개 구. E·S·F, 반올림 전 값. S, 분기 당월 매출 합/3. 화면에 저장하는 매출 원, 그 값의 정수 반올림. 서울 평균 점수는 25개 반올림 V의 산술평균을 다시 소수 한 자리. 월별 rankLevel, (V, 구 이름) 오름차순 뒤 rank//5+1. 같은 점수는 구 이름 순.",
        en: "Here z is taken over the 25 districts of that month, using E, S, and F before display rounding. S is the quarter’s monthly sales total divided by 3. The won figure stored for the screen is that value rounded to an integer. The Seoul average score rounds the arithmetic mean of the 25 already rounded scores to one decimal. The monthly rankLevel sorts by (V, district name) ascending and uses rank//5+1. Equal scores break by district name.",
      },
    ],
  },
  {
    title: { ko: "전국 추론", en: "National inference" },
    blocks: [
      {
        ko: "지도의 2026년 6월 점수. 전국 z점수는 시군구 전체에서 1회. 추론값이 평균·표준편차에 포함되어 서울 z점수도 변동. 대시보드 서울 월별 점수와 다른 숫자.",
        en: "These are the June 2026 map scores. The national z-scores are computed once over every municipality, so inferred values enter the mean and standard deviation and move Seoul’s z-scores as well. The numbers are not the dashboard’s Seoul monthly scores.",
      },
      {
        ko: "E, 2026년 6월 일반용 kWh. 전년 같은 달 있으면 y=(E_2026−E_2025)/E_2025. 서울 매출·유동·개업률−폐업률은 실측, 기온 23.8°C 고정. 23.8은 대시보드 월평균 기온과 별개 상수.",
        en: "E is June 2026 commercial kWh. When the previous June exists, y=(E_2026−E_2025)/E_2025. Seoul keeps measured sales, footfall, and opening rate minus closing rate, and fixes temperature at 23.8°C. That 23.8 is a constant, separate from the monthly mean used on the dashboard.",
      },
      {
        ko: "기준 집합 R, 상가 수 0 초과 서울 시군구. 중앙값 분모의 상가 수는 소상공인시장진흥공단 전국 상가 수. 분자 매출·유동·개폐업률은 서울 열린데이터. 전국 상가 파일, 매출 없음.",
        en: "The reference set R is the Seoul municipalities with a positive shop count. The shop count in the median’s denominator is the SEMAS national shop count. The sales, footfall, and open-close rates in the numerator are Seoul open data. The national shop file has no sales.",
      },
      {
        tex: String.raw`m_s=m\!\left(\frac{\mathrm{sales}}{N}\right)_R,\ m_f=m\!\left(\frac{\mathrm{footfall}}{N}\right)_R,\ m_e=m\!\left(\frac{E}{N}\right)_R,\ m_n=m(o-c)_R,\ m_y=m(\{y_i:y_i\ \mathrm{exists}\})`,
      },
      {
        ko: "서울 외 시군구 i의 추론. 상가 수 0이면 상가당 전력 m_e, φ=1. 매출·유동 추론값은 상가 수 곱으로 0. 전년 값 없으면 y 자리 m_y, 개폐 보정 0.",
        en: "For a municipality i outside Seoul the inferences are below. With zero shops, kWh per shop is set to m_e so φ=1, and the inferred sales and footfall are 0 because they are multiplied by the shop count. A missing year-on-year rate uses m_y, so the open-close adjustment is 0.",
      },
      {
        tex: String.raw`e_i=\begin{cases}E_i/N_i&N_i>0\\ m_e&N_i=0\end{cases},\qquad \phi_i=\sqrt{e_i/m_e}`,
      },
      {
        tex: String.raw`\widehat{\mathrm{sales}}_i=m_s\,N_i\,\phi_i,\qquad \widehat{\mathrm{footfall}}_i=m_f\,N_i\,\phi_i`,
      },
      {
        tex: String.raw`\widehat{\mathrm{net}}_i=\min\!\bigl(4,\max(-4,\ m_n+12(y_i^{\ast}-m_y))\bigr),\quad y_i^{\ast}=y_i\ \mathrm{if\ defined,\ else}\ m_y`,
      },
      {
        tex: String.raw`\widehat T_i=\mathrm{round}_1\!\bigl(26-0.55(\mathrm{lat}_i-33)\bigr)`,
      },
      {
        ko: "위도 lat, 경계 바깥 꼭짓점의 산술평균을 소수 넷째 자리로 반올림한 값. 닫힌 고리의 시작점 반복 시 두 번 집계. 면적가중 중심 아님. 기온 식의 위도, 이 반올림 값. 관측소 값이 아닌 위도 직선. net 단위 퍼센트포인트. 전년 증가율이 중앙값보다 0.10 높으면 개폐 항에 1.2, −4에서 4로 절단.",
        en: "Latitude is the arithmetic mean of the outer-ring vertices, then rounded to four decimals. A closed ring that repeats its first vertex counts that vertex twice. It is not an area-weighted centroid. The temperature line uses that rounded latitude. It is a function of latitude, not a station reading. net is in percentage points: a year-on-year rate 0.10 above the median adds 1.2, then the result is clipped to [−4, 4].",
      },
      {
        ko: "상가당 전력 중앙값이 0이면 m_e=1. 전년 6월이 없거나 0이면 y 없음, 개폐 보정 0. V 계산 뒤 저장값, 매출·유동은 정수, 개폐 차는 소수 둘째 자리. z와 V, 그 반올림 전 값.",
        en: "If the median kWh per shop is 0, m_e is 1. A missing or zero previous June leaves y undefined, so the open-close adjustment is 0. After V is computed, stored sales and footfall are integers and the stored net is two decimals. The z-scores and V use the values from before that rounding.",
      },
    ],
  },
  {
    title: { ko: "전국 점수와 지도 색", en: "National score and map color" },
    blocks: [
      {
        ko: "실측과 추론, 같은 자리. E·매출·유동 z점수는 전국 기준. 점수는 소수 한 자리 반올림.",
        en: "Measured and inferred inputs occupy the same places. The z-scores of E, sales, and footfall are then national. The score is rounded to one decimal.",
      },
      {
        tex: String.raw`V_i=\mathrm{round}_1\!\left(52+28\,z(E_i)+18\,z(\mathrm{sales}_i)+10\,z(\mathrm{footfall}_i)+6\,\mathrm{net}_i-0.15\,|T_i-18|\right)`,
      },
      {
        ko: "지도 활력 색, L(V)가 아닌 V 오름차순 q. 전력 색, 2026년 6월 kWh 오름차순 q, 속성명 rankLevel. 표시 GWh, E/10^6 소수 둘째 자리.",
        en: "The vitality color on the map is the ascending quintile q of V, not L(V). The power color is the ascending quintile of June 2026 kWh, stored as rankLevel. Displayed GWh is E/10^6 rounded to two decimals.",
      },
      {
        ko: "확대 배율 z<8, 시·도 단위. 활력은 소속 시군구 V 평균의 q. 전력은 반올림 GWh 합의 q. z≥8, 시군구 자신의 q.",
        en: "Below zoom 8 the color is provincial. Vitality uses q of the mean V of the member municipalities. Power uses q of the sum of rounded GWh. At zoom 8 and above each municipality uses its own q.",
      },
      {
        tex: String.raw`\alpha=\min\!\left(1,\max\!\left(0,\frac{z-11}{1.6}\right)\right),\quad \mathrm{fill}=0.18-0.13\alpha`,
      },
      {
        ko: "길가 점 불투명도 α. z<10.6, 점 미표시. 화면 안 상가, 경위도 칸. 칸 크기 z≥15는 0.0018°, z≥13은 0.0032°, 그 아래 0.0055°.",
        en: "Street-dot opacity is also α. Dots are not drawn below zoom 10.6. Shops in view are counted on a latitude-longitude grid: 0.0018° at zoom 15 and above, 0.0032° at zoom 13 and above, otherwise 0.0055°.",
      },
      {
        ko: "화면 안 상가 20,000곳 초과 시 stride=⌈n/20000⌉. 색은 현재 화면 칸 중 더 적은 칸의 비율. 전국 고정 분위 아님. 경계 굵기 1.15 고정.",
        en: "Above 20,000 shops in view, only every stride=⌈n/20000⌉-th shop is counted. Color is the share of cells in the current view with a strictly smaller count. It is not a fixed national quintile. Polygon stroke weight stays at 1.15.",
      },
      {
        tex: String.raw`c=\min\!\left(4,\left\lfloor\frac{5\,|\{u:\mathrm{count}(u)<\mathrm{count}(cell)\}|}{n_{\mathrm{cells}}}\right\rfloor\right),\quad r=1.5+\min\!\bigl(2,\max(0,z-12)\cdot 0.45\bigr)`,
      },
      {
        ko: "길가 점 색 첨자 c, 0부터 4. 범례 1–5와 같은 다섯 색. 캔버스 알파 0.45, 레이어 불투명도 α와 곱한 값 0.45α. 경계선 불투명도 0.45 고정. 좌표, 소수 여섯째 자리(도).",
        en: "The street-dot color index c runs from 0 to 4 and uses the same five colors as legend levels 1 through 5. Canvas alpha is 0.45, so the visible alpha is 0.45α together with the layer opacity. Polygon stroke opacity stays at 0.45. Coordinates are stored to six decimal degrees.",
      },
    ],
  },
  {
    title: { ko: "대시보드 지표", en: "Dashboard indicators" },
    blocks: [
      {
        ko: "전년차 ΔE, 2026년 6월 일반용 kWh에서 2025년 6월 일반용 kWh를 뺀 값. 전국 추론의 비율 y와 다른 양. 화면 GWh, ΔE/10^6의 소수 한 자리. 증가 1위, ΔE가 가장 큰 구. 낮은 전력 표, ΔE가 작은 8개 구. 그 표의 등급, 분위가 아닌 L(V).",
        en: "The year-on-year change ΔE subtracts June 2025 commercial kWh from June 2026 commercial kWh. It is a difference in kWh, separate from the ratio y used in national inference. The screen shows ΔE/10^6 rounded to one decimal. The top gainer is the district with the largest ΔE. The low-power table is the eight districts with the smallest ΔE, and the level on that table is L(V), the absolute level.",
      },
      {
        tex: String.raw`\Delta E_d=E_{d,2026\text{-}06}-E_{d,2025\text{-}06},\quad \mathrm{GWh}_{\Delta}=\mathrm{round}_1(\Delta E_d/10^6)`,
      },
      {
        tex: String.raw`\delta_d=\mathrm{round}_1(V_{2026\text{-}06,d}-V_{2025\text{-}07,d})`,
      },
      {
        ko: "점수 변화 δ, 2026-06 V에서 2025-07 V를 뺀 값의 소수 한 자리. 정체 구, δ<0 이고 폐업률>개업률인 구 중 δ가 가장 작은 구. 해당 구가 없으면 없음. 폐업 초과, 폐업률이 개업률보다 큰 구의 개수.",
        en: "The score change δ is the June 2026 score minus the July 2025 score, rounded to one decimal. The stagnant district is the one with the smallest δ among districts that have δ<0 and a closing rate above the opening rate. If none qualify, the label is 없음. The closing-exceeds count is the number of districts whose closing rate is above the opening rate.",
      },
      {
        ko: "서울 평균 차트 전력, 이미 소수 둘째 자리인 GWh 25개의 합을 정수로 반올림. 구 하나 차트, 저장된 소수 둘째 자리 GWh. 월 눈금, 연도 네 자리에서 앞의 20을 뺀 표기.",
        en: "On the Seoul-average chart the power bar rounds the sum of the 25 already two-decimal GWh figures to an integer. A single-district chart uses the stored two-decimal GWh. Month labels drop the leading 20 from the four-digit year.",
      },
      {
        tex: String.raw`K_m=\mathrm{round}\!\left(\sum_{d=1}^{25}\mathrm{round}_2(E_{m,d}/10^6)\right)`,
      },
      {
        ko: "업종 표, 최신 분기 서울 전체. 서비스 업종명마다 개업·폐업·점포 합. 정렬 키, 개업 수−폐업 수 내림차순. 같은 값은 업종명 순. 상위 8행.",
        en: "The industry table is Seoul-wide for the latest quarter. Each service-trade name sums openings, closings, and shops. The sort key is openings minus closings, descending. Equal keys keep trade-name order. The screen shows the first eight rows.",
      },
    ],
  },
  {
    title: { ko: "오르는 활력", en: "Rising vitality" },
    blocks: [
      {
        ko: "순위, 값이 더 큰 시군구 수 + 1. 같은 값은 같은 순위. 화면 정렬, 값 내림차순 다음 이름. 서울 구는 25행 전부. 전국은 같은 시·도 안에서 상위 20행.",
        en: "Rank is one plus the number of municipalities with a strictly larger value. Ties share a rank. The table sorts by value descending, then by name. Seoul shows all 25 districts. Nationwide shows the top 20 inside the selected province.",
      },
      {
        ko: "서울 현재값, 2026-06 V·분기 매출·분기 유동·최신 점포·2026-06 일반용. 서울 기간 변화, V는 2026-06−2025-07, 매출·유동도 같은 두 달, 전력은 2026-06−2025-06 일반용, 점포는 최신 분기 개업률−폐업률. 점포 수의 월별 시계열은 없음.",
        en: "Seoul current values are the June 2026 score, the quarter sales and footfall attached to that month, the latest shop count, and June 2026 commercial power. Seoul change uses June 2026 minus July 2025 for the score, sales, and footfall. Power change is June 2026 commercial kWh minus June 2025. The shop row is the latest opening rate minus the closing rate, because shop counts have no monthly series.",
      },
      {
        ko: "전국 현재값, 2026-06 전국 활력·매출·유동·2026-09-30 상가·2026-06 일반용. 서울 밖 매출·유동은 추론. 전국 기간 변화는 없음. 골목 상권, 행정동, 주거인구는 자료 밖.",
        en: "Nationwide current values use the June 2026 national score, sales, and footfall, the 30 September 2026 shop count, and June 2026 commercial power. Sales and footfall outside Seoul are inferred. There is no nationwide change mode. Alley commercial areas, administrative dong, and residential population are outside this table.",
      },
    ],
  },
  {
    title: { ko: "지도 경계", en: "Map boundaries" },
    blocks: [
      {
        ko: "한전이 시 합계만 주는 13곳, 구 경계를 하나의 다각형으로 합친 뒤 시 합계 kWh 하나. 경기 고양·성남·수원·안산·안양·용인, 경남 창원, 경북 포항, 전북 전주, 충남 천안, 충북 청주.",
        en: "Thirteen cities publish one KEPCO total. Their gu polygons are merged into one shape and painted with that single city total: Gyeonggi Goyang, Seongnam, Suwon, Ansan, Anyang, and Yongin; Gyeongnam Changwon; Gyeongbuk Pohang; Jeonbuk Jeonju; Chungnam Cheonan; Chungbuk Cheongju.",
      },
      {
        ko: "이름 대응, 인천 미추홀구 = 2018 경계의 남구, 대구 군위군 = 2018 경계의 경상북도 군위군. 시·도 이름, 강원도→강원특별자치도, 전라북도→전북특별자치도, 제주도→제주특별자치도. 6월 일반용 kWh가 0 이하인 행, 지도에서 제외. 서울 점수, 구 한글 이름으로 연결. 통계청 코드와 행정코드는 다름.",
        en: "Name pairs are Incheon Michuhol-gu with the 2018 boundary’s Nam-gu, and Daegu Gunwi-gun with the 2018 boundary’s Gyeongsangbuk-do Gunwi-gun. Province names map Gangwon-do to Gangwon State, Jeollabuk-do to Jeonbuk State, and Jeju-do to Jeju State. A June commercial kWh of 0 or below is left off the map. Seoul scores join on the Korean district name. The statistical code and the administrative code differ.",
      },
      {
        ko: "골목 검색 후보, 소속 구의 최신 V. 골목 전용 점수 없음. 검색, 이름 부분 일치 최대 8건.",
        en: "A searched alley candidate uses the latest V of its parent district. There is no separate alley score. Search keeps at most eight substring matches.",
      },
    ],
  },
  {
    title: { ko: "1km 거리", en: "The 1 km distance" },
    blocks: [
      {
        ko: "같은 업종 상가 거리, 등방위 근사. 위도는 질문 지점 위도. 1,000m 밖 후보, 0.01° 격자의 중심 칸과 이웃 한 칸, 3×3만 검사.",
        en: "Distance to a same-trade shop is an equirectangular approximation. Latitude in the cosine is the query latitude. Candidates are tested only in the 3×3 block of 0.01° cells around the query cell.",
      },
      {
        tex: String.raw`\Delta N=\Delta\mathrm{lat}\times 110540,\quad \Delta E=\Delta\mathrm{lng}\times 111320\cos(\mathrm{lat}),\quad \Delta N^{2}+\Delta E^{2}\le 1000^{2}`,
      },
      {
        ko: "창업 계산 1km 개수, 입력 좌표 기준. 전국 순위 비교값, 각 시군구 경계 꼭짓점 평균 좌표. 두 좌표, 불일치.",
        en: "The startup calculation counts shops within 1 km of the typed coordinate. The national ranking compares that count with counts taken at each municipality’s vertex-mean coordinate. Those two coordinates are not the same.",
      },
    ],
  },
  {
    title: { ko: "개업종합", en: "Opening score" },
    blocks: [
      {
        ko: "개업종합, 활력지수와 다른 100점. 업종 고정, 시군구 집합 U의 백분위. 비교 목록 n, 각 시군구 중심의 1km 같은 업종 수. 현재 주소 백분위, 입력 좌표 개수와 그 목록의 비교. s, 시군구 업종 상가 수. e, 일반용 kWh / 전체 상가 수. 전체 상가 0이면 e는 전력 백분위 목록에서 제외.",
        en: "The opening score is a 100-point score separate from vitality. Percentiles are taken over the municipality set U with the trade held fixed. Each n in the comparison list is the 1 km same-trade count at that municipality’s centroid. The typed address is scored by comparing its own coordinate’s count with that list. s is that trade’s shop count in the municipality, and e is commercial kWh divided by all shops. A municipality with zero shops is left out of the power percentile list.",
      },
      {
        tex: String.raw`p_V=P^{+}(V),\ p_s=P^{+}(s),\ p_{\mathrm{net}}=P^{+}(\mathrm{net}),\ p_n=100-P^{+}(n),\ p_e=P^{+}(e)`,
      },
      {
        ko: "가중 수요 35, 업종 기반 20, 개폐 여유 20, 주변 여유 15, 전력 활동 10. 주변 여유, 1km 같은 업종이 많을수록 낮음. e 없으면 전력 10 제외 후 남은 가중으로 재분배.",
        en: "The weights are demand 35, trade base 20, open-close room 20, local room 15, and power activity 10. Local room falls as the 1 km same-trade count rises. If e is missing, the power weight 10 is dropped and the remaining weights are renormalized.",
      },
      {
        tex: String.raw`O=\frac{\sum_k w_k p_k}{\sum_k w_k},\quad \mathrm{score}=\mathrm{round}(O),\quad \mathrm{points}_k=\mathrm{round}_1\!\left(\frac{w_k p_k}{\sum_j w_j}\right)`,
      },
      {
        ko: "순위, 1 + O가 더 큰 시군구 수. 동점, 같은 순위. 매출·개폐 둘 다 실측이면 표시 계산, 하나라도 추론이면 추론. 유동 실측 여부는 이 표시에 미사용.",
        en: "Rank is 1 plus the number of municipalities with a strictly larger O. Ties share a rank. The label is calculated when both sales and open-close are measured, and inferred when either is inferred. Whether footfall is measured is not part of that label.",
      },
    ],
  },
  {
    title: { ko: "경쟁력, 업종 전력, 전기요금", en: "Competitiveness, trade power, and the bill" },
    blocks: [
      {
        ko: "화면 경쟁력, 개업종합과 다른 평균. 1km 수, 시군구 업종 수, 상가 있을 때 상가당 전력 백분위의 산술평균 후 반올림. 순위, 반올림 전 평균이 더 큰 시군구 수 + 1.",
        en: "The competitiveness shown on the screen is a different average from the opening score. It is the rounded arithmetic mean of the percentiles for the 1 km count, the municipality trade count, and, when shops exist, kWh per shop. Rank is 1 plus the number of municipalities with a strictly larger unrounded mean.",
      },
      {
        tex: String.raw`C=\mathrm{round}\!\left(\frac{P^{+}(n)+P^{+}(s)+[P^{+}(e)]}{2\ \mathrm{or}\ 3}\right)`,
      },
      {
        ko: "업종 전력, 서울 25개 구만 추론. 서울 밖, 빈칸·데이터 부족. 구 평균 전력, 구 일반용 kWh / 서울 점포 합. ρ 분모 0이면 ρ=1.",
        en: "Trade power is inferred only when the municipality is one of the 25 Seoul districts. Elsewhere it is left empty and marked missing. District average power divides that district’s commercial kWh by the Seoul shop total. If the denominator of ρ is 0, ρ is 1.",
      },
      {
        tex: String.raw`\bar e_d=\frac{E_d}{N_d}`,
      },
      {
        ko: "업종 목록, 서울 서비스 업종 가운데 전국 상가 소분류와 이름이 맞는 행. 앞의 열 개는 기존 묶음. 카페=커피, 한식=한식음식점, 치킨·분식=치킨 또는 분식, 호프·주점=호프, 편의점, 미용=미용실, 학원=예술·외국어·일반교습·컴퓨터, 의류소매=일반의류, 헬스=스포츠클럽, 약국=의약품. 분식·네일·피부관리·세부 학원·유아의류·의류임대·스터디 카페는 이 묶음 안. 전자상거래·게스트하우스·중고차·미용재료·녹음실·가정용품임대·주류도매·재생용품·중고가구는 전국 소분류에 같은 행이 없어 목록 밖.",
        en: "The trade list is the Seoul service names that also exist as a national shop category. The first ten stay grouped: cafe matches 커피, Korean food matches 한식음식점, chicken and snacks match 치킨 or 분식, pubs match 호프, convenience stores match 편의점, beauty matches 미용실, academies match the four academy names, apparel matches 일반의류, gyms match 스포츠클럽, and pharmacies match 의약품. Snacks, nails, skin care, the separate academies, children’s apparel, apparel rental, and study cafes stay inside those groups. Online retail, guesthouses, used cars, beauty supplies, recording studios, household rental, liquor wholesale, recycled goods, and used furniture have no matching national category and stay off the list.",
      },
      {
        ko: "서울 업종 표의 분자, 그 묶음의 매출 합/점포 수를 정수로 반올림한 값. 분모의 구 평균, 매출과 점포가 둘 다 있는 업종만의 합, 반올림 전. 분모 0이면 ρ=1. 점포 수 0이면 개업률·폐업률·점포당 매출·점포당 건수·유동/점포 모두 0. 활력식의 분모 1과 다른 규칙.",
        en: "The numerator in the Seoul trade table is the grouped sales total divided by shop count, then rounded to an integer. The district average in the denominator sums only trades that have both sales and shops and stays unrounded. A zero denominator sets ρ to 1. Zero shops set the opening rate, closing rate, sales per shop, sales count per shop, and footfall per shop to 0. That zero is a different rule from the vitality formula’s divisor of 1.",
      },
      {
        tex: String.raw`s^{\circ}=\mathrm{round}\!\left(\frac{\mathrm{sales}_{d,k}}{N_{d,k}}\right),\quad \rho=\begin{cases}s^{\circ}/(\mathrm{sales}_{d,\cdot}/N_{d,\cdot})&N_{d,\cdot}>0\\ 1&N_{d,\cdot}=0\end{cases},\quad \mathrm{kWh}^{\mathrm{raw}}=\bar e_d\sqrt{\rho}`,
      },
      {
        ko: "화면 kWh, kWh^raw의 정수 반올림. 화면 배수, √ρ 소수 둘째 자리. 전기요금, 반올림 전 kWh^raw에 2025년 일반용 172.69원을 곱한 뒤 부가세 10%와 기금 3.7%. 계약전력·기후환경요금·연료비 0. 평당 원단위, 요금 식 밖.",
        en: "The kWh on screen is kWh^raw rounded to an integer. The factor on screen is √ρ rounded to two decimals. The bill multiplies the unrounded kWh^raw by the 2025 commercial price 172.69 won, then applies 10% VAT and the 3.7% fund. Contract demand, the climate charge, and the fuel charge are 0. The per-pyeong intensities are outside the bill.",
      },
      {
        tex: String.raw`\widehat{\mathrm{kWh}}=\mathrm{round}(\mathrm{kWh}^{\mathrm{raw}}),\quad B=\mathrm{round}\!\left(\mathrm{kWh}^{\mathrm{raw}}\times 172.69\times(1+0.10+0.037)\right)`,
      },
      {
        ko: "서울 다섯 항, 점포당 매출, 개업률−폐업률, 유동/점포, 활력, 점포당 매출 건수. 개업률·폐업률은 소수 둘째 자리, 건수는 소수 한 자리, 매출과 유동/점포는 정수로 반올림한 뒤 P⁺. 유동/점포만 추론. 평균 C₅, 다섯 백분위의 산술평균을 정수로 반올림. 순위, 다섯 백분위 합의 내림차순 위치. 동점, 구 목록 순서의 연속 순위. 이 평균, 전국 경쟁력 C와 별도.",
        en: "The five Seoul terms are sales per shop, opening rate minus closing rate, footfall per shop, vitality, and sales count per shop. Opening and closing rates are rounded to two decimals, the sales count to one decimal, and sales and footfall per shop to integers before P⁺. Dividing footfall by shop count is the inferred term. C₅ rounds the arithmetic mean of the five percentiles to an integer. Rank is the position after sorting that sum descending. Ties keep district-list order and take consecutive ranks. This average is separate from the national competitiveness C.",
      },
      {
        tex: String.raw`S=p_{\mathrm{sales}}+p_{\mathrm{net}}+p_{\mathrm{flpop}}+p_{V}+p_{\mathrm{count}},\quad C_5=\mathrm{round}(S/5)`,
      },
    ],
  },
  {
    title: { ko: "식 밖", en: "Outside the formulas" },
    blocks: [
      {
        ko: "활력 V에 없는 값. 건물에너지 전기·가스, 주택용·산업용·교육용 계약, 직장인구, 시간대 유동, 2026년 8월 용도별 전력, 평당 원단위. 가스·공실·건축물대장, 시계열 없음. 이 항목, 데이터 표에만 있거나 비어 있음.",
        en: "These values are absent from V: building-energy electricity and gas, residential, industrial, and education contracts, worker counts, time-of-day footfall, the August 2026 use-by-purpose power table, and the per-pyeong intensities. Gas, vacancy, and the building register have no series. Those items appear only in the data tables, or the table is empty.",
      },
    ],
  },
];

export default function AdminPage() {
  const { t, lang } = usePrefs();
  const [open, setOpen] = useState(() => sessionStorage.getItem(GATE) === "1");
  const [password, setPassword] = useState("");
  const [bad, setBad] = useState(false);

  function unlock(event: FormEvent) {
    event.preventDefault();
    if (password === "1111") {
      sessionStorage.setItem(GATE, "1");
      setOpen(true);
      setBad(false);
      return;
    }
    setBad(true);
  }

  function lock() {
    sessionStorage.removeItem(GATE);
    setPassword("");
    setOpen(false);
    setBad(false);
  }

  if (!open) {
    return (
      <div>
        <div className="page-head">
          <div>
            <h1>{t("adminTitle")}</h1>
          </div>
        </div>
        <form className="card admin-gate" onSubmit={unlock}>
          <label>
            {t("adminPass")}
            <input
              type="password"
              value={password}
              autoComplete="off"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button type="submit">{t("adminEnter")}</button>
          {bad && <p>{t("adminBad")}</p>}
        </form>
      </div>
    );
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("adminTitle")}</h1>
          <p>{t("adminLead")}</p>
        </div>
        <button type="button" className="admin-lock" onClick={lock}>
          {t("adminLock")}
        </button>
      </div>
      <div className="grid formula-list">
        <Formulae lang={lang} />
      </div>
    </div>
  );
}

function Formulae({ lang }: { lang: Lang }) {
  return (
    <>
      {SECTIONS.map((section) => (
        <section key={section.title.ko} className="card formula-card">
          <h2>{lang === "en" ? section.title.en : section.title.ko}</h2>
          {section.blocks.map((block, index) =>
            "tex" in block ? (
              <Tex key={index} expr={block.tex} display />
            ) : (
              <p key={index}>{lang === "en" ? block.en : block.ko}</p>
            ),
          )}
        </section>
      ))}
    </>
  );
}
