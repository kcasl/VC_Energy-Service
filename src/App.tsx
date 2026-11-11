import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import MapPage from "./pages/MapPage";
import CatalogPage from "./pages/CatalogPage";
import SimulatorPage from "./pages/SimulatorPage";
import PlansPage from "./pages/PlansPage";
import ApiPage from "./pages/ApiPage";
import AdminPage from "./pages/AdminPage";
import { usePrefs, type TextKey } from "./lib/prefs";

const links: { to: string; key: TextKey }[] = [
  { to: "/", key: "navDash" },
  { to: "/map", key: "navMap" },
  { to: "/data", key: "navData" },
  { to: "/sim", key: "navSim" },
  { to: "/plans", key: "navPlans" },
  { to: "/endpoints", key: "navApi" },
  { to: "/admin", key: "navAdmin" },
];

export default function App() {
  const { t, lang, theme, setLang, setTheme } = usePrefs();
  return (
    <div className="app-shell">
      <aside className="side">
        <div className="brand">
          <img src="/brand/mark.png" alt={t("brand")} />
        </div>
        <nav className="nav">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {t(l.key)}
            </NavLink>
          ))}
        </nav>
        <div className="mode-switch">
          <button className={lang === "ko" ? "on" : ""} onClick={() => setLang("ko")}>
            KR
          </button>
          <button className={lang === "en" ? "on" : ""} onClick={() => setLang("en")}>
            EN
          </button>
          <button className={theme === "light" ? "on" : ""} onClick={() => setTheme("light")}>
            {t("light")}
          </button>
          <button className={theme === "dark" ? "on" : ""} onClick={() => setTheme("dark")}>
            {t("dark")}
          </button>
        </div>
      </aside>
      <main className="main">
        <img className="corner-logo" src="/brand/kentech.png" alt="KENTECH" />
        <div className="main-body">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/data" element={<CatalogPage />} />
            <Route path="/sim" element={<SimulatorPage />} />
            <Route path="/plans" element={<PlansPage />} />
            <Route path="/endpoints" element={<ApiPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
        <footer className="site-foot">
          <div>
            <strong>{t("brand")}</strong>
            <span>{t("school")}</span>
          </div>
          <div>
            {t("contact")} <a href="mailto:kkcasl@ieee.org">kkcasl@ieee.org</a>
          </div>
          <div>© 2026 KENTECH. All rights reserved.</div>
        </footer>
      </main>
    </div>
  );
}
