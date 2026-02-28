// ============================================================
// CONFIG.JS — Toàn bộ phần tĩnh: màu sắc, ngày tháng, helpers
// Chỉnh ở đây khi cần đổi theme hoặc period báo cáo
// ============================================================

// ── MÀUSẮC THEME (đổi ở đây để thay đổi toàn bộ giao diện) ──
export const C = {
  bg:         "#07090f",
  panel:      "#0d1117",
  border:     "#1c2333",
  borderHover:"#2d3f5e",
  accent:     "#3b82f6",
  green:      "#10b981",
  yellow:     "#f59e0b",
  orange:     "#f97316",
  red:        "#ef4444",
  dim:        "#4b5563",
  muted:      "#6b7280",
  text:       "#c9d1d9",
  textBright: "#e6edf3",
};

// ── MÀUSẮC THEO LOẠI MÁY ─────────────────────────────────────
export const TYPE_COLORS = {
  CNS50: { line: "#a78bfa", bg: "#1e1040", border: "#7c3aed" },
  EC50:  { line: "#34d399", bg: "#052e16", border: "#059669" },
  J100:  { line: "#60a5fa", bg: "#0c1a2e", border: "#2563eb" },
  MD100: { line: "#f97316", bg: "#1c0d00", border: "#c2410c" },
  MD130: { line: "#fbbf24", bg: "#1c1400", border: "#b45309" },
  MD50:  { line: "#f472b6", bg: "#1c0614", border: "#be185d" },
};

// ── MÀUSẮC THEO MACHINE CODE ──────────────────────────────────
export const MACHINE_COLORS = {
  "CNS50-000":  "#a78bfa", "CNS50-001":   "#c4b5fd",
  "EC50ST-000": "#34d399",
  "J100ADS-000":"#60a5fa", "J100ADS-001": "#93c5fd",
  "MD100S-000": "#f97316", "MD100S-001":  "#fb923c",
  "MD130S-000": "#fbbf24", "MD130S-001":  "#fcd34d",
  "MD50S-000":  "#f472b6", "MD50S-001":   "#f9a8d4",
};

// ── MÀUSẮC THEO THÁNG (dùng cho heatmap pairing) ─────────────
// Thêm entry khi có thêm tháng dữ liệu
export const MONTH_PALETTE = {
  "11": { dot: "#a78bfa", bg: "#7c3aed18", label: "NOV 2018" },
  "12": { dot: "#60a5fa", bg: "#2563eb18", label: "DEC 2018" },
  "01": { dot: "#34d399", bg: "#05966918", label: "JAN 2019" },
};

export function monthColor(dateStr) {
  if (!dateStr) return null;
  return MONTH_PALETTE[dateStr.slice(5, 7)]?.dot ?? null;
}
export function monthBg(dateStr) {
  if (!dateStr) return null;
  return MONTH_PALETTE[dateStr.slice(5, 7)]?.bg ?? null;
}

// ── COLOR HELPERS (logic thuần, không phụ thuộc data) ─────────
export function defectColor(rate) {
  if (rate === 0)   return C.green;
  if (rate < 2)     return "#34d399";
  if (rate < 5)     return C.yellow;
  if (rate < 15)    return C.orange;
  return C.red;
}
export function etaColor(s) {
  if (s === "ontime")          return C.green;
  if (s === "late")            return C.red;
  if (s === "expected_ontime") return C.yellow;
  return C.dim;
}
export function statusColor(s) {
  if (s === "finished")    return C.green;
  if (s === "in_progress") return C.accent;
  return C.dim;
}
export function ngColor(r) {
  if (r === 0)  return C.green;
  if (r < 2)    return "#34d399";
  if (r < 5)    return C.yellow;
  if (r < 10)   return C.orange;
  return C.red;
}