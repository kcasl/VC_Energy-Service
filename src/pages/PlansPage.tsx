import { useEffect, useState } from "react";
import { api, type Plans } from "../lib/load";
import { usePrefs, type TextKey } from "../lib/prefs";

const PLAN: Record<string, [TextKey, TextKey, TextKey]> = {
  단기: ["planShort", "priceShort", "textShort"],
  월정액: ["planMonth", "priceMonth", "textMonth"],
  지자체: ["planGov", "priceGov", "textGov"],
};

export default function PlansPage() {
  const { t } = usePrefs();
  const [data, setData] = useState<Plans | null>(null);

  useEffect(() => {
    api.plans().then(setData);
  }, []);

  if (!data) return <p>{t("loading")}</p>;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>{t("plansTitle")}</h1>
        </div>
      </div>
      <div className="grid plans">
        {data.items.map((item) => {
          const keys = PLAN[item.title];
          return (
            <div key={item.title} className={item.featured ? "card featured" : "card"}>
              <h2>{keys ? t(keys[0]) : item.title}</h2>
              <p className="kpi-value">{keys ? t(keys[1]) : item.price}</p>
              <p>{keys ? t(keys[2]) : item.text}</p>
            </div>
          );
        })}
      </div>
      <div className="banner">
        <div>
          <strong>{t("ad")}</strong>
          <div>{t("banner")}</div>
        </div>
      </div>
    </div>
  );
}
