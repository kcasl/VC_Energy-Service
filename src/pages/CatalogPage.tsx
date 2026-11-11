import { useEffect, useState } from "react";
import { api, type CatalogItem, type CatalogRows } from "../lib/load";
import { usePrefs } from "../lib/prefs";
import { formatNum } from "../lib/vitality";

function text(item: CatalogItem, key: "title" | "owner" | "purpose" | "grain" | "cadence" | "status" | "notes", lang: "ko" | "en") {
  if (lang === "en") {
    const en = item[`${key}En` as keyof CatalogItem];
    if (typeof en === "string" && en) return en;
  }
  return item[key] ?? "";
}

function cell(value: string | number) {
  if (typeof value !== "number") return value;
  return formatNum(value, Number.isInteger(value) ? 0 : 2);
}

export default function CatalogPage() {
  const { t, lang } = usePrefs();
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [id, setId] = useState("");
  const [q, setQ] = useState("");
  const [district, setDistrict] = useState("전체");
  const [page, setPage] = useState(0);
  const [table, setTable] = useState<CatalogRows | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .catalog()
      .then((d) => {
        setItems(d.items);
        setId(d.items.find((item) => item.hasRows)?.id ?? d.items[0]?.id ?? "");
      })
      .catch(() => setError(t("offline")));
  }, []);

  const current = items.find((item) => item.id === id);

  useEffect(() => {
    if (!current?.hasRows) {
      setTable(null);
      return;
    }
    let live = true;
    api
      .rows(current.id, q, district, page)
      .then((rows) => {
        if (live) setTable(rows);
      })
      .catch(() => {
        if (live) setError(t("tableMiss"));
      });
    return () => {
      live = false;
    };
  }, [current, q, district, page]);

  if (error) return <p>{error}</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("dataTitle")}</h1>
        </div>
      </div>
      <div className="grid catalog-grid">
        <div className="catalog-list">
          {items.map((item) => (
            <button
              key={item.id}
              className={item.id === id ? "on" : ""}
              onClick={() => {
                setId(item.id);
                setQ("");
                setDistrict("전체");
                setPage(0);
              }}
            >
              <span className="badge">P{item.priority}</span>
              {text(item, "title", lang)}
              <div className="status-line">{text(item, "status", lang)}</div>
            </button>
          ))}
        </div>
        {current && (
          <div className="card">
            <h2>{text(current, "title", lang)}</h2>
            <table className="table">
              <tbody>
                <tr>
                  <th>{t("provider")}</th>
                  <td>{text(current, "owner", lang)}</td>
                </tr>
                <tr>
                  <th>{t("why")}</th>
                  <td>{text(current, "purpose", lang)}</td>
                </tr>
                <tr>
                  <th>{t("unit")}</th>
                  <td>{text(current, "grain", lang)}</td>
                </tr>
                <tr>
                  <th>{t("cadence")}</th>
                  <td>{text(current, "cadence", lang)}</td>
                </tr>
                <tr>
                  <th>{t("status")}</th>
                  <td>{text(current, "status", lang)}</td>
                </tr>
                <tr>
                  <th>{t("rows")}</th>
                  <td>{formatNum(current.rowCount)}</td>
                </tr>
                <tr>
                  <th>{t("screen")}</th>
                  <td>{(lang === "en" && current.usedInEn?.length ? current.usedInEn : current.usedIn).join(" · ")}</td>
                </tr>
                <tr>
                  <th>{t("source")}</th>
                  <td>
                    <a href={current.url} target="_blank" rel="noreferrer">
                      {t("link")}
                    </a>
                  </td>
                </tr>
                <tr>
                  <th>{t("file")}</th>
                  <td>{current.localFiles.length ? current.localFiles.join(", ") : t("none")}</td>
                </tr>
              </tbody>
            </table>
            {text(current, "notes", lang) && <p>{text(current, "notes", lang)}</p>}
            {table && (
              <>
                <div className="toolbar">
                  <input
                    value={q}
                    onChange={(e) => {
                      setQ(e.target.value);
                      setPage(0);
                    }}
                    placeholder={t("search")}
                  />
                  {table.districts.length > 0 && (
                    <select
                      value={district}
                      onChange={(e) => {
                        setDistrict(e.target.value);
                        setPage(0);
                      }}
                    >
                      <option value="전체">{t("all")}</option>
                      {table.districts.map((name) => (
                        <option key={name}>{name}</option>
                      ))}
                    </select>
                  )}
                  <span>
                    {formatNum(table.total)} / {formatNum(table.all)} {t("rows")}
                  </span>
                </div>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        {table.columns.map((col) => (
                          <th key={col.key}>{col.label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {table.rows.map((row, index) => (
                        <tr key={index}>
                          {table.columns.map((col) => (
                            <td key={col.key}>{cell(row[col.key] ?? "")}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="pager">
                  <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                    {t("prev")}
                  </button>
                  <span>
                    {table.page + 1} / {table.pageCount}
                  </span>
                  <button disabled={page + 1 >= table.pageCount} onClick={() => setPage((p) => p + 1)}>
                    {t("next")}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
