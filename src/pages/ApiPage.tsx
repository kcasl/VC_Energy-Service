import { useState } from "react";
import { usePrefs } from "../lib/prefs";

type Endpoint = {
  id: string;
  method: "GET" | "POST";
  path: string;
  ko: string;
  en: string;
  example: string;
};

const ENDPOINTS: Endpoint[] = [
  {
    id: "health",
    method: "GET",
    path: "/api/health",
    ko: "서버 기동 확인",
    en: "Checks that the server is up.",
    example: "/api/health",
  },
  {
    id: "dashboard",
    method: "GET",
    path: "/api/dashboard",
    ko: "서울 25개 구 점수, 전력 증감, 업종 개폐업. focus는 구 이름 또는 서울 평균",
    en: "Seoul scores, power change, and trade openings. focus is a district name or 서울 평균.",
    example: `/api/dashboard?focus=${encodeURIComponent("서울 평균")}`,
  },
  {
    id: "map",
    method: "GET",
    path: "/api/map",
    ko: "구별 활력, 주요 상권 위치",
    en: "District vitality and major commercial spots.",
    example: "/api/map",
  },
  {
    id: "geo",
    method: "GET",
    path: "/api/geo",
    ko: "서울 자치구 경계 GeoJSON",
    en: "Seoul district boundary GeoJSON.",
    example: "/api/geo",
  },
  {
    id: "catalog",
    method: "GET",
    path: "/api/catalog",
    ko: "데이터 항목 목록",
    en: "The data catalog.",
    example: "/api/catalog",
  },
  {
    id: "rows",
    method: "GET",
    path: "/api/catalog/{id}/rows",
    ko: "항목 표. 질의 q, district, page, size. size 1–50",
    en: "Rows for one catalog id. Query: q, district, page, size. size is 1–50.",
    example: `/api/catalog/kepco-contract/rows?q=&district=${encodeURIComponent("전체")}&page=0&size=12`,
  },
  {
    id: "options",
    method: "GET",
    path: "/api/sim/options",
    ko: "창업 계산용 위치 id, 업종 id",
    en: "Place ids and trade ids for the startup calculation.",
    example: "/api/sim/options",
  },
  {
    id: "simulate",
    method: "POST",
    path: "/api/simulate",
    ko: "위치 id와 업종 id의 전기, 경쟁력. 업종 cafe, korean, chicken, pub, cvs, beauty, academy, retail, gym, pharmacy",
    en: "Power and competitiveness for a place id and a trade id. Trades: cafe, korean, chicken, pub, cvs, beauty, academy, retail, gym, pharmacy.",
    example: JSON.stringify({ spotId: "gangnam", industryId: "cafe" }, null, 2),
  },
  {
    id: "plans",
    method: "GET",
    path: "/api/plans",
    ko: "요금제",
    en: "The plans.",
    example: "/api/plans",
  },
];

export default function ApiPage() {
  const { t, lang } = usePrefs();
  const [copied, setCopied] = useState("");
  const origin = window.location.origin;

  function copy(id: string, text: string) {
    const mark = () => setCopied(id);
    const fallback = () => {
      const el = document.createElement("textarea");
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      el.remove();
      mark();
    };
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(mark).catch(fallback);
      return;
    }
    fallback();
  }

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("apiTitle")}</h1>
          <p>
            {t("apiLead")} <code>{origin}</code>
          </p>
        </div>
      </div>
      <div className="grid api-list">
        {ENDPOINTS.map((item) => {
          const share =
            item.method === "POST"
              ? `${item.method} ${origin}${item.path}\n${item.example}`
              : `${origin}${item.example}`;
          return (
            <article key={item.id} className="card api-card">
              <div className="api-top">
                <span className={`verb ${item.method === "GET" ? "get" : "post"}`}>{item.method}</span>
                <code className="api-path">{item.path}</code>
              </div>
              <p>{lang === "en" ? item.en : item.ko}</p>
              <pre className="api-example">{item.example}</pre>
              <div className="api-actions">
                <button type="button" onClick={() => copy(item.id, share)}>
                  {copied === item.id ? t("copied") : t("copy")}
                </button>
                {item.method === "GET" && (
                  <a href={item.example} target="_blank" rel="noreferrer">
                    {t("open")}
                  </a>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
