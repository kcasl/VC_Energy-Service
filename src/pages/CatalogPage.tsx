import { useEffect, useState } from "react";
import { api, type CatalogItem, type CatalogRows } from "../lib/load";
import { formatNum } from "../lib/vitality";

function cell(value: string | number) {
  if (typeof value !== "number") return value;
  return formatNum(value, Number.isInteger(value) ? 0 : 2);
}

export default function CatalogPage() {
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
      .catch(() => setError("서버에 연결되지 않습니다."));
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
        if (live) setError("표를 읽지 못했습니다.");
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
          <h1>사용 데이터</h1>
          <p>받은 자료와 행. 구와 검색으로 걸러 볼 수 있습니다.</p>
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
              {item.title}
              <div className="status-line">{item.status}</div>
            </button>
          ))}
        </div>
        {current && (
          <div className="card">
            <h2>{current.title}</h2>
            <table className="table">
              <tbody>
                <tr>
                  <th>제공</th>
                  <td>{current.owner}</td>
                </tr>
                <tr>
                  <th>쓰는 이유</th>
                  <td>{current.purpose}</td>
                </tr>
                <tr>
                  <th>단위</th>
                  <td>{current.grain}</td>
                </tr>
                <tr>
                  <th>주기</th>
                  <td>{current.cadence}</td>
                </tr>
                <tr>
                  <th>상태</th>
                  <td>{current.status}</td>
                </tr>
                <tr>
                  <th>행</th>
                  <td>{formatNum(current.rowCount)}</td>
                </tr>
                <tr>
                  <th>화면</th>
                  <td>{current.usedIn.join(" · ")}</td>
                </tr>
                <tr>
                  <th>원문</th>
                  <td>
                    <a href={current.url} target="_blank" rel="noreferrer">
                      링크
                    </a>
                  </td>
                </tr>
                <tr>
                  <th>파일</th>
                  <td>{current.localFiles.length ? current.localFiles.join(", ") : "없음"}</td>
                </tr>
              </tbody>
            </table>
            {current.notes && <p>{current.notes}</p>}
            {table && (
              <>
                <div className="toolbar">
                  <input
                    value={q}
                    onChange={(e) => {
                      setQ(e.target.value);
                      setPage(0);
                    }}
                    placeholder="업종, 월"
                  />
                  {table.districts.length > 0 && (
                    <select
                      value={district}
                      onChange={(e) => {
                        setDistrict(e.target.value);
                        setPage(0);
                      }}
                    >
                      <option>전체</option>
                      {table.districts.map((name) => (
                        <option key={name}>{name}</option>
                      ))}
                    </select>
                  )}
                  <span>
                    {formatNum(table.total)} / {formatNum(table.all)}행
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
                    이전
                  </button>
                  <span>
                    {table.page + 1} / {table.pageCount}
                  </span>
                  <button disabled={page + 1 >= table.pageCount} onClick={() => setPage((p) => p + 1)}>
                    다음
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
