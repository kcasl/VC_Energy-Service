import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MapPage from "./pages/MapPage";
import CatalogPage from "./pages/CatalogPage";
import SimulatorPage from "./pages/SimulatorPage";
import PlansPage from "./pages/PlansPage";

const links = [
  { to: "/", label: "대시보드" },
  { to: "/map", label: "지도" },
  { to: "/data", label: "데이터" },
  { to: "/sim", label: "창업 계산" },
  { to: "/plans", label: "요금제" },
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="side">
        <div className="brand">
          <img src="/brand/mark.png" alt="상권 활력" />
        </div>
        <nav className="nav">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main">
        <img className="corner-logo" src="/brand/kentech.png" alt="KENTECH" />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/data" element={<CatalogPage />} />
          <Route path="/sim" element={<SimulatorPage />} />
          <Route path="/plans" element={<PlansPage />} />
        </Routes>
      </main>
    </div>
  );
}
