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
import { formatNum } from "../lib/vitality";

export default function Dashboard() {
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
        if (live) setError("서버에 연결되지 않습니다.");
      });
    return () => {
      live = false;
    };
  }, [focus]);

  if (error) return <p>{error}</p>;
  if (!data) return <p>불러오는 중…</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>대시보드</h1>
          <p>
            {data.windowLabel}. 한전 일반용 전력, 서울시 점포·매출·유동.{" "}
            <span className="tag gap">데이터 부족</span> {data.gaps.join(", ")}.
          </p>
        </div>
      </div>
      <div className="grid kpis">
        <div className="card">
          <div className="kpi-label">평균 점수</div>
          <div className="kpi-value">{data.avgScore.toFixed(1)}</div>
          <div className="kpi-sub">25개 구</div>
        </div>
        <div className="card">
          <div className="kpi-label">전년 6월보다 전력</div>
          <div className="kpi-value">{data.energyTop.name}</div>
          <div className={data.energyTop.gwh >= 0 ? "kpi-sub up" : "kpi-sub down"}>
            {data.energyTop.gwh >= 0 ? "+" : ""}
            {formatNum(data.energyTop.gwh, 1)} GWh
          </div>
        </div>
        <div className="card">
          <div className="kpi-label">점수 하락 + 폐업</div>
          <div className="kpi-value">{data.stagnantName}</div>
          <div className="kpi-sub">폐업률이 개업률보다 높음</div>
        </div>
        <div className="card">
          <div className="kpi-label">폐업이 더 많은 구</div>
          <div className="kpi-value">{data.closeOverOpen}곳</div>
          <div className="kpi-sub">2026년 2분기</div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <div className="page-head" style={{ marginBottom: 8 }}>
          <h2>점수와 전력</h2>
          <label className="inline">
            구
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
              <CartesianGrid stroke="#d5e2ee" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#003068" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={data.chart}>
              <CartesianGrid stroke="#d5e2ee" />
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
          <h2>개업 많은 업종 · {data.quarterLabel}</h2>
          <table className="table">
            <thead>
              <tr>
                <th>업종</th>
                <th>개업</th>
                <th>폐업</th>
                <th>점포</th>
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
          <h2>전력 증가가 적은 구</h2>
          <table className="table">
            <thead>
              <tr>
                <th>자치구</th>
                <th>활력</th>
                <th>전년 6월</th>
                <th>폐업률</th>
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
