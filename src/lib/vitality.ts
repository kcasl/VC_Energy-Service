import type { VitalityLevel } from "../types";

export const LEVELS: Record<VitalityLevel, { label: string; color: string }> = {
  1: { label: "한산", color: "#2f9e5f" },
  2: { label: "여유", color: "#7cbc3d" },
  3: { label: "보통", color: "#e3c34a" },
  4: { label: "활발", color: "#e07b2e" },
  5: { label: "과밀", color: "#d63a2f" },
};

export function formatKrw(n: number) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatNum(n: number, digits = 0) {
  return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: digits }).format(n);
}
