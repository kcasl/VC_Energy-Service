import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import LevelPill from "../components/LevelPill";
import { api, type Dash } from "../lib/load";
import { usePrefs } from "../lib/prefs";
import { formatNum } from "../lib/vitality";

export default function Dashboard() {
  const { t, theme } = usePrefs();
  const [focus, setFocus] = useState("서울 평균");
  const [data, setData] = useState<Dash | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    api
      .dashboard(focus)
      .then((d) => {
        if (live) setData(d);
      })
      .catch(() => {
        if (live) setError(t("offline"));
      });
    return () => {
      live = false;
    };
  }, [focus]);

  if (error) return <p>{error}</p>;
  if (!data) return <p>{t("loading")}</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("dashTitle")}</h1>
          <p>
            {data.windowLabel}
            <span className="tag gap">{t("gap")}</span> {(data.gaps ?? ["가스", "공실", "건축물대장"]).join(", ")}
          </p>
        </div>
      </div>
      <section className="contribute">
        <h2>{t("contribute")}</h2>
        <div className="grid three">
          <article className="card">
            <h3>{t("c1")}</h3>
            <p>{t("c1b")}</p>
          </article>
          <article className="card">
            <h3>{t("c2")}</h3>
            <p>{t("c2b")}</p>
          </article>
          <article className="card">
            <h3>{t("c3")}</h3>
            <p>{t("c3b")}</p>
          </article>
        </div>
      </section>
      <div className="grid kpis">
        <div className="card">
          <div className="kpi-label">{t("avg")}</div>
          <div className="kpi-value">{data.avgScore.toFixed(1)}</div>
          <div className="kpi-sub">{t("districts25")}</div>
        </div>
        <div className="card">
          <div className="kpi-label">{t("yoy")}</div>
          <div className="kpi-value">{data.energyTop.name}</div>
          <div className={data.energyTop.gwh >= 0 ? "kpi-sub up" : "kpi-sub down"}>
            {data.energyTop.gwh >= 0 ? "+" : ""}
            {formatNum(data.energyTop.gwh, 1)} GWh
          </div>
        </div>
        <div className="card">
          <div className="kpi-label">{t("drop")}</div>
          <div className="kpi-value">{data.stagnantName}</div>
          <div className="kpi-sub">{t("dropSub")}</div>
        </div>
        <div className="card">
          <div className="kpi-label">{t("moreClose")}</div>
          <div className="kpi-value">
            {data.closeOverOpen}
            {t("places")}
          </div>
          <div className="kpi-sub">{t("q2")}</div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <div className="page-head" style={{ marginBottom: 8 }}>
          <h2>{t("scorePower")}</h2>
          <label className="inline">
            {t("gu")}
            <select value={focus} onChange={(e) => setFocus(e.target.value)}>
              {data.names.map((name) => (
                <option key={name}>{name}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid two" style={{ marginTop: 0 }}>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.chart}>
              <CartesianGrid stroke={theme === "dark" ? "#2c4054" : "#d5e2ee"} />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#003068" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.chart}>
              <CartesianGrid stroke={theme === "dark" ? "#2c4054" : "#d5e2ee"} />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="kwh" fill="#0078c0" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="grid two">
        <div className="card">
          <h2>
            {t("openInd")} · {data.quarterLabel}
          </h2>
          <table className="table">
            <thead>
              <tr>
                <th>{t("ind")}</th>
                <th>{t("opened")}</th>
                <th>{t("closed")}</th>
                <th>{t("stores")}</th>
              </tr>
            </thead>
            <tbody>
              {data.industries.map((row) => (
                <tr key={row.name}>
                  <td>{row.name}</td>
                  <td>{formatNum(row.opened)}</td>
                  <td>{formatNum(row.closed)}</td>
                  <td>{formatNum(row.stores)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>{t("lowPower")}</h2>
          <table className="table">
            <thead>
              <tr>
                <th>{t("district")}</th>
                <th>{t("vitality")}</th>
                <th>{t("yoyJune")}</th>
                <th>{t("closeRate")}</th>
              </tr>
            </thead>
            <tbody>
              {data.lowEnergy.map((d) => (
                <tr key={d.name}>
                  <td>{d.name}</td>
                  <td>
                    <LevelPill level={d.level} />
                  </td>
                  <td className={d.gwh >= 0 ? "up" : "down"}>
                    {d.gwh >= 0 ? "+" : ""}
                    {formatNum(d.gwh, 1)} GWh
                  </td>
                  <td>{d.closeRate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
