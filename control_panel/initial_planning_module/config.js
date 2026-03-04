// ============================================================
// CONFIG.JS — Initial Planning Module (converted: no ES module syntax)
// ============================================================

const TABS = [
  { id: "producing", label: "🏭 Producing POs" },
  { id: "pending",   label: "📋 Pending POs"   },
];

const PENDING_COL_HEADERS = [
  "Machine", "PO No.", "Item Name", "Mold",
  "PO Qty", "ETA", "Lead Time", "Priority",
];

const TONNAGE_THRESHOLDS = [
  { min: 130, color: "#ff6b35" },
  { min: 100, color: "#f7c59f" },
  { min: 50,  color: "#a8d8ea" },
  { min: 0,   color: "#d4edda" },
];

const DASHBOARD_TITLE = {
  subtitle: "INJECTION MOLDING",
  title:    "PRODUCTION PLANNING DASHBOARD",
};
