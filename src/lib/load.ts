async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} ${res.status}`);
  return res.json() as Promise<T>;
}

export type Dash = {
  windowLabel: string;
  gaps: string[];
  names: string[];
  avgScore: number;
  energyTop: { name: string; gwh: number };
  stagnantName: string;
  closeOverOpen: number;
  chart: { month: string; score: number; kwh: number }[];
  focus: string;
  quarterLabel: string;
  industries: { name: string; opened: number; closed: number; stores: number }[];
  lowEnergy: { name: string; level: 1 | 2 | 3 | 4 | 5; gwh: number; closeRate: number }[];
};

export type MapDistrict = {
  name: string;
  code: string;
  type: string;
  lat: number;
  lng: number;
  score: number;
  level: 1 | 2 | 3 | 4 | 5;
  rankLevel: 1 | 2 | 3 | 4 | 5;
  gwh: number;
  openRate: number;
  closeRate: number;
};

export type MapSpot = {
  id: string;
  name: string;
  district: string;
  type: string;
  lat: number;
  lng: number;
  industryBias: string;
  rivals: number;
  score: number;
  level: 1 | 2 | 3 | 4 | 5;
  rankLevel: 1 | 2 | 3 | 4 | 5;
};

export type CatalogItem = {
  id: string;
  priority: number;
  title: string;
  owner: string;
  purpose: string;
  grain: string;
  cadence: string;
  status: string;
  usedIn: string[];
  url: string;
  localFiles: string[];
  rowCount: number;
  notes: string;
  hasRows: boolean;
};

export type CatalogRows = {
  columns: { key: string; label: string }[];
  rows: Record<string, string | number>[];
  total: number;
  all: number;
  page: number;
  pageCount: number;
  districts: string[];
};

export type SimOptions = {
  industries: { id: string; name: string }[];
};

export type SimFact = {
  label: string;
  kind: "실측" | "추론" | "계산";
  value: string;
  how: string;
  source: string;
};

export type SimResult = {
  query: string;
  place: string;
  sido: string;
  area: string;
  lat: number;
  lng: number;
  radiusM: number;
  industryName: string;
  nearby: number;
  areaStores: number;
  allStores: number;
  gwh: number;
  rankLevel: 1 | 2 | 3 | 4 | 5;
  avgKwh: number | null;
  avgBill: number | null;
  inferredKwh: number | null;
  inferredBill: number | null;
  factor: number | null;
  score: number | null;
  level: 1 | 2 | 3 | 4 | 5 | null;
  scoreKind: "계산" | "추론";
  seoul: boolean;
  salesPerStore: number | null;
  openRate: number | null;
  closeRate: number | null;
  opened: number | null;
  closed: number | null;
  openScore: number;
  openRank: number;
  openOf: number;
  openKind: "계산" | "추론";
  openParts: { name: string; weight: number; percentile: number; points: number; text: string }[];
  compete: number;
  competeRank: number;
  competeOf: number;
  seoulCompete: number | null;
  seoulRank: number | null;
  parts: { name: string; kind: "실측" | "추론" | "계산"; score: number; text: string; source: string }[];
  facts: SimFact[];
  gaps: { label: string; reason: string }[];
  note: string;
};

export type Plans = {
  items: { title: string; price: string; text: string; featured: boolean }[];
  banner: string;
};

export const api = {
  dashboard: (focus: string) =>
    getJson<Dash>(`/api/dashboard?focus=${encodeURIComponent(focus)}`),
  map: () => getJson<{ districts: MapDistrict[]; spots: MapSpot[] }>("/api/map"),
  geo: () => getJson<GeoJSON.GeoJsonObject>("/api/geo"),
  catalog: () => getJson<{ items: CatalogItem[] }>("/api/catalog"),
  rows: (id: string, q: string, district: string, page: number) => {
    const params = new URLSearchParams({ q, district, page: String(page), size: "12" });
    return getJson<CatalogRows>(`/api/catalog/${id}/rows?${params}`);
  },
  simOptions: () => getJson<SimOptions>("/api/sim/options"),
  simulate: (payload: { query: string; industryId: string }) =>
    fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (res) => {
      if (!res.ok) {
        const err = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(err?.detail || "계산에 실패했습니다.");
      }
      return res.json() as Promise<SimResult>;
    }),
  plans: () => getJson<Plans>("/api/plans"),
};
