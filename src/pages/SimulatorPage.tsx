import { FormEvent, useEffect, useState } from "react";
import LevelPill from "../components/LevelPill";
import { api, type SimOptions, type SimResult } from "../lib/load";
import { formatKrw, formatNum } from "../lib/vitality";

const TAG = { 실측: "real", 추론: "guess", 계산: "calc" } as const;

function Tag({ kind }: { kind: keyof typeof TAG }) {
  return <span className={`tag ${TAG[kind]}`}>{kind}</span>;
}

export default function SimulatorPage() {
  const [options, setOptions] = useState<SimOptions | null>(null);
  const [query, setQuery] = useState("");
  const [industryId, setIndustryId] = useState("cafe");
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.simOptions().then(setOptions).catch(() => setError("서버에 연결되지 않습니다."));
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = query.trim();
    if (text.length < 2) {
      setError("위치를 입력하세요.");
      return;
    }
    setBusy(true);
    setError("");
    api
      .simulate({ query: text, industryId })
      .then((data) => {
        setResult(data);
        setBusy(false);
      })
      .catch((err: Error) => {
        setBusy(false);
        setError(err.message || "계산에 실패했습니다.");
      });
  }

  if (!options && !error) return <p>불러오는 중…</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>창업 계산</h1>
          <p>
            주소를 직접 입력합니다. 개업종합은 이 서비스 전용 100점이고, 수요·업종 기반·개폐 여유·주변 여유·전력 활동을 전국 백분위로 더합니다.
          </p>
        </div>
      </div>
      <form className="form" onSubmit={onSubmit}>
        <label>
          위치
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="해운대 우동, 수원역, 제주시 연동"
          />
        </label>
        <label>
          업종
          <select value={industryId} onChange={(e) => setIndustryId(e.target.value)}>
            {options?.industries.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "계산 중" : "계산"}
        </button>
      </form>
      {error && <p>{error}</p>}
      {result && (
        <>
          <div className="card compete-card">
            <div className="kpi-label">
              개업종합 · {result.sido} {result.area} {result.industryName}
              <Tag kind={result.openKind} />
            </div>
            <div className="compete">
              <strong>{result.openScore}</strong>
              <span>100점 만점 · {result.openOf}개 시군구 중 {result.openRank}위</span>
            </div>
            <p className="src">
              {result.place}. {result.note}
              {result.seoulCompete != null && result.seoulRank != null
                ? ` 서울 25개 구 경쟁력은 ${result.seoulCompete}, ${result.seoulRank}위입니다.`
                : ""}
            </p>
          </div>
          <div className="card" style={{ marginBottom: 14 }}>
            <h2>개업종합 항목</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th>가중</th>
                  <th>전국 백분위</th>
                  <th>반영</th>
                  <th>의미</th>
                </tr>
              </thead>
              <tbody>
                {result.openParts.map((part) => (
                  <tr key={part.name}>
                    <td>{part.name}</td>
                    <td>{part.weight}</td>
                    <td>{part.percentile}</td>
                    <td>{part.points}</td>
                    <td className="src">{part.text}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid kpis">
            <div className="card">
              <div className="kpi-label">
                1km {result.industryName}
                <Tag kind="실측" />
              </div>
              <div className="kpi-value">{formatNum(result.nearby)}곳</div>
              <div className="kpi-sub">
                {result.area} 전체 {formatNum(result.areaStores)}곳
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">
                상가 평균 전기
                <Tag kind="계산" />
              </div>
              <div className="kpi-value">{result.avgKwh == null ? "—" : `${formatNum(result.avgKwh)} kWh`}</div>
              <div className="kpi-sub">
                {result.avgBill == null ? "점포 수 없음" : formatKrw(result.avgBill)} · 일반용 {result.gwh} GWh
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">
                {result.seoul ? "이 업종 전력" : "이 업종 전력"}
                {result.inferredKwh == null ? <span className="tag gap">데이터 부족</span> : <Tag kind="추론" />}
              </div>
              <div className="kpi-value">
                {result.inferredKwh == null ? "—" : `${formatNum(result.inferredKwh)} kWh`}
              </div>
              <div className="kpi-sub">
                {result.inferredBill == null ? "서울 매출이 있을 때만 추론" : formatKrw(result.inferredBill)}
              </div>
            </div>
            <div className="card">
              <div className="kpi-label">
                활력지수
                <Tag kind={result.scoreKind === "추론" ? "추론" : "계산"} />
              </div>
              <div className="kpi-value">
                {result.score == null || result.level == null ? (
                  "—"
                ) : (
                  <>
                    {result.score} <LevelPill level={result.level} />
                  </>
                )}
              </div>
              <div className="kpi-sub">
                {result.scoreKind === "추론"
                  ? `${result.area} · 매출·유동은 상가와 전력으로 추론`
                  : `${result.area} · 매출·유동 실측`}
              </div>
            </div>
          </div>
          <div className="card" style={{ marginTop: 14 }}>
            <h2>경쟁력 항목</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th></th>
                  <th>이 위치</th>
                  <th>순위 점수</th>
                  <th>자료</th>
                </tr>
              </thead>
              <tbody>
                {result.parts.map((part) => (
                  <tr key={part.name}>
                    <td>{part.name}</td>
                    <td>
                      <Tag kind={part.kind} />
                    </td>
                    <td>{part.text}</td>
                    <td>{part.score}</td>
                    <td className="src">{part.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card" style={{ marginTop: 14 }}>
            <h2>화면에 쓴 숫자</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th></th>
                  <th>값</th>
                  <th>계산</th>
                  <th>자료</th>
                </tr>
              </thead>
              <tbody>
                {result.facts.map((fact) => (
                  <tr key={fact.label}>
                    <td>{fact.label}</td>
                    <td>
                      <Tag kind={fact.kind} />
                    </td>
                    <td>{fact.value}</td>
                    <td>{fact.how}</td>
                    <td className="src">{fact.source}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {result.salesPerStore != null && (
              <p className="src">
                서울 점포당 매출 {formatNum(result.salesPerStore)}원. 개업률 {result.openRate}%, 폐업률 {result.closeRate}%.
              </p>
            )}
          </div>
          <div className="card" style={{ marginTop: 14 }}>
            <h2>
              데이터 부족 <span className="tag gap">데이터 부족</span>
            </h2>
            <table className="table">
              <tbody>
                {result.gaps.map((gap) => (
                  <tr key={gap.label}>
                    <td>{gap.label}</td>
                    <td className="src">{gap.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
