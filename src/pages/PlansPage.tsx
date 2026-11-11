import { useEffect, useState } from "react";
import { api, type Plans } from "../lib/load";

export default function PlansPage() {
  const [data, setData] = useState<Plans | null>(null);

  useEffect(() => {
    api.plans().then(setData);
  }, []);

  if (!data) return <p>불러오는 중…</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>요금제</h1>
          <p>한 번 보는 자료와 매달 보는 골목 자료. 아직 결제 기능은 없습니다.</p>
        </div>
      </div>
      <div className="grid plans">
        {data.items.map((item) => (
          <div key={item.title} className={item.featured ? "card featured" : "card"}>
            <h2>{item.title}</h2>
            <p className="kpi-value">{item.price}</p>
            <p>{item.text}</p>
          </div>
        ))}
      </div>
      <div className="banner">
        <div>
          <strong>광고</strong>
          <div>{data.banner}</div>
        </div>
      </div>
    </div>
  );
}
