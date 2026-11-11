import { FormEvent, useEffect, useState } from "react";
import LevelPill from "../components/LevelPill";
import { api, type SimOptions, type SimResult } from "../lib/load";
import { usePrefs } from "../lib/prefs";
import { formatKrw, formatNum } from "../lib/vitality";

const TAG = { 실측: "real", 추론: "guess", 계산: "calc" } as const;

function Tag({ kind }: { kind: keyof typeof TAG }) {
  const { t } = usePrefs();
  const label = kind === "실측" ? t("tagReal") : kind === "추론" ? t("tagGuess") : t("tagCalc");
  return <span className={`tag ${TAG[kind]}`}>{label}</span>;
}

export default function SimulatorPage() {
  const { t, lang, industry } = usePrefs();
  const [options, setOptions] = useState<SimOptions | null>(null);
  const [query, setQuery] = useState("");
  const [industryId, setIndustryId] = useState("cafe");
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.simOptions().then(setOptions).catch(() => setError(t("offline")));
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = query.trim();
    if (text.length < 2) {
      setError(t("needPlace"));
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
        setError(err.message || t("calcFail"));
      });
  }

  if (!options && !error) return <p>{t("loading")}</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("simTitle")}</h1>
        </div>
      </div>
      <form className="form" onSubmit={onSubmit}>
        <label>
          {t("place")}
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("placePh")}
          />
        </label>
        <label>
          {t("industry")}
          <select value={industryId} onChange={(e) => setIndustryId(e.target.value)}>
            {options?.industries.map((item) => (
              <option key={item.id} value={item.id}>
                {industry(item.id, item.name)}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={busy}>
          {busy ? t("calculating") : t("calc")}
        </button>
      </form>
      {error && <p>{error}</p>}
      {result && (
        <>
          <div className="card compete-card">
            <div className="kpi-label">
              {t("openParts")} · {result.sido} {result.area} {result.industryName}
              <Tag kind={result.openKind} />
            </div>
            <div className="compete">
              <strong>{result.openScore}</strong>
              <span>
                {lang === "en"
                  ? `${t("of100")} · ${result.openRank} of ${result.openOf}`
                  : `${t("of100")} · ${result.openOf}${t("rankOf")} ${result.openRank}${t("rank")}`}
              </span>
            </div>
            <p className="src">{result.place}</p>
          </div>
          <div className="card" style={{ marginBottom: 14 }}>
            <h2>{t("openParts")}</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>항목</th>
                  <th>{t("weight")}</th>
                  <th>{t("pct")}</th>
                  <th>{t("points")}</th>
                  <th>{t("meaning")}</th>
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
            <h2>{t("competeParts")}</h2>
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
            <h2>{t("usedNumbers")}</h2>
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
