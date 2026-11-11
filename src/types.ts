export type VitalityLevel = 1 | 2 | 3 | 4 | 5;

export type MonthPoint = {
  month: string;
  meanTemp: number;
  commercialKwh: number;
  commercialKwhGwh: number;
  salesKrw: number;
  flpop: number;
  openRate: number;
  closeRate: number;
  score: number;
  level: VitalityLevel;
  rankLevel: VitalityLevel;
};

export type District = {
  code: string;
  signguCode: string;
  name: string;
  type: "도심" | "근교";
  lat: number;
  lng: number;
  stores: number;
  openRate: number;
  closeRate: number;
  yoyKwh: number;
  intensityKwhPerStore: number;
  rivalsByIndustry: Record<string, number>;
  latest: MonthPoint;
  delta: number;
  series: MonthPoint[];
};

export type DistrictFile = {
  generatedAt: string;
  window: { from: string; to: string };
  formula: string;
  omitted: string[];
  norms: {
    month: string;
    kwhMean: number;
    kwhStd: number;
    salesMean: number;
    salesStd: number;
    flpopMean: number;
    flpopStd: number;
  };
  districts: District[];
};

export type Spot = {
  id: string;
  name: string;
  district: string;
  type: "골목" | "도심" | "근교";
  lat: number;
  lng: number;
  industryBias: string;
  rivals: number;
  score: number;
  level: VitalityLevel;
  parentScore: number;
  commercialKwhGwh: number;
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
  browse: string;
  rowCount: number;
  notes?: string;
};

export type BrowseFile = {
  columns: { key: string; label: string }[];
  rows: Record<string, string | number>[];
};

export type Industry = {
  id: string;
  name: string;
  kwhPerPyeong: number;
  kwPerPyeong: number;
  note: string;
  seoulNames?: string[];
};

export type IndustryQuarter = {
  quarter: string;
  rows: {
    name: string;
    stores: number;
    opened: number;
    closed: number;
    salesKrw: number;
  }[];
};

export type Tariff = {
  name: string;
  source: string;
  basePerKw: number;
  energyPerKwh: number;
  climatePerKwh: number;
  fuelPerKwh: number;
  vat: number;
  fund: number;
};
