import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Rising, type RisingRow } from "../lib/load";
import { usePrefs } from "../lib/prefs";

const TAG = { 실측: "real", 추론: "guess", 계산: "calc" } as const;

const METRICS = [
  ["score", "riseScore"],
  ["sales", "riseSales"],
  ["flpop", "riseFlpop"],
  ["stores", "riseStores"],
  ["power", "risePower"],
] as const;

const BASIS_EN: Record<string, string> = {
  "seoul-score-level": "All 25 Seoul districts, June 2026 vitality.",
  "seoul-sales-level": "All 25 Seoul districts, quarterly sales attached to June 2026.",
  "seoul-flpop-level": "All 25 Seoul districts, quarterly footfall attached to June 2026.",
  "seoul-stores-level": "All 25 Seoul districts, latest-quarter shop count.",
  "seoul-power-level": "All 25 Seoul districts, June 2026 commercial power.",
  "seoul-score-change": "All 25 Seoul districts, June 2026 vitality minus July 2025.",
  "seoul-sales-change": "All 25 Seoul districts, June 2026 sales minus July 2025.",
  "seoul-flpop-change": "All 25 Seoul districts, June 2026 footfall minus July 2025.",
  "seoul-stores-change": "All 25 Seoul districts, latest opening rate minus closing rate.",
  "seoul-power-change": "All 25 Seoul districts, June 2026 commercial power minus June 2025.",
  "national-score-level": "Municipalities, June 2026 vitality. Sales and footfall outside Seoul are inferred.",
  "national-sales-level": "Municipalities, June 2026 sales. Only Seoul is measured.",
  "national-flpop-level": "Municipalities, June 2026 footfall. Only Seoul is measured.",
  "national-stores-level": "Municipalities, shop count on 30 September 2026.",
  "national-power-level": "Municipalities, June 2026 commercial power.",
};

function mapTo(row: RisingRow, metric: string) {
  const params = new URLSearchParams({
    sido: row.sido,
    name: row.name,
    color: metric === "power" ? "전력" : "활력",
  });
  return `/map?${params.toString()}`;
}

function Tag({ kind }: { kind: keyof typeof TAG }) {
  const { t } = usePrefs();
  const label = kind === "실측" ? t("tagReal") : kind === "추론" ? t("tagGuess") : t("tagCalc");
  return <span className={`tag ${TAG[kind]}`}>{label}</span>;
}

export default function RisingPage() {
  const { t, lang } = usePrefs();
  const [scope, setScope] = useState<"seoul" | "national">("seoul");
  const [metric, setMetric] = useState("score");
  const [mode, setMode] = useState<"level" | "change">("level");
  const [sido, setSido] = useState("");
  const [data, setData] = useState<Rising | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const nextMode = scope === "seoul" ? mode : "level";
    api
      .rising(scope, metric, nextMode, scope === "national" ? sido : "")
      .then((row) => {
        setData(row);
        setError("");
      })
      .catch(() => setError(t("offline")));
  }, [scope, metric, mode, sido, t]);

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>{t("riseTitle")}</h1>
          <p className="lead">{t("riseLead")}</p>
        </div>
      </div>
      <div className="filters" style={{ flexWrap: "wrap" }}>
        <button type="button" className={scope === "seoul" ? "on" : ""} onClick={() => setScope("seoul")}>
          {t("riseSeoul")}
        </button>
        <button type="button" className={scope === "national" ? "on" : ""} onClick={() => setScope("national")}>
          {t("riseNational")}
        </button>
      </div>
      <div className="filters" style={{ flexWrap: "wrap" }}>
        {METRICS.map(([id, key]) => (
          <button key={id} type="button" className={metric === id ? "on" : ""} onClick={() => setMetric(id)}>
            {t(key)}
          </button>
        ))}
      </div>
      {scope === "seoul" && (
        <div className="filters" style={{ flexWrap: "wrap" }}>
          <button type="button" className={mode === "level" ? "on" : ""} onClick={() => setMode("level")}>
            {t("riseLevel")}
          </button>
          <button type="button" className={mode === "change" ? "on" : ""} onClick={() => setMode("change")}>
            {t("riseChange")}
          </button>
        </div>
      )}
      {scope === "national" && (
        <div className="filters" style={{ flexWrap: "wrap" }}>
          <select value={sido} onChange={(event) => setSido(event.target.value)} aria-label={t("riseAll")}>
            <option value="">{t("riseAll")}</option>
            {(data?.sidos ?? []).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      )}
      {error && <p className="hint">{error}</p>}
      {data && (
        <div className="card" style={{ marginTop: 14 }}>
          <p className="hint">
            {lang === "ko" ? data.basis : BASIS_EN[`${data.scope}-${data.metric}-${data.mode}`]}
          </p>
          {data.scope === "national" && data.total > data.rows.length && (
            <p className="hint">
              {t("riseTop")} {data.rows.length} / {data.total}
            </p>
          )}
          <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                {data.scope === "national" ? (
                  <>
                    <th>{t("riseColSido")}</th>
                    <th>{t("riseColName")}</th>
                  </>
                ) : (
                  <th>{t("riseColGu")}</th>
                )}
                <th>{t("riseColValue")}</th>
                <th>{t("riseColKind")}</th>
                <th>{t("riseMap")}</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={`${row.sido}-${row.name}`}>
                  <td>{row.rank}</td>
                  {data.scope === "national" && <td>{row.sido}</td>}
                  <td>{row.name}</td>
                  <td>{row.text}</td>
                  <td>
                    <Tag kind={row.kind} />
                  </td>
                  <td>
                    <Link className="map-jump" to={mapTo(row, data.metric)}>
                      {t("riseMap")}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </section>
  );
}
