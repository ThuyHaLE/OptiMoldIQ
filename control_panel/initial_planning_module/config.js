// ============================================================
// ✏️  config.js — Cấu hình UI tĩnh
//    Chỉnh file này khi muốn: thêm tab, đổi tên cột,
//    thay đổi ngưỡng màu theo tonnage
// ============================================================

// 🗂️  Danh sách tab — thêm tab mới chỉ cần thêm object vào đây
export const TABS = [
  { id: "producing", label: "🏭 Producing POs" },
  { id: "pending",   label: "📋 Pending POs"   },
];

// 📋 Header cột bảng Pending — đổi tên / thêm cột tại đây
export const PENDING_COL_HEADERS = [
  "Machine", "PO No.", "Item Name", "Mold",
  "PO Qty", "ETA", "Lead Time", "Priority",
];

// 🎨 Ngưỡng màu badge theo tải trọng máy (tonnage)
//    Sắp xếp từ cao → thấp, phần tử cuối là fallback
export const TONNAGE_THRESHOLDS = [
  { min: 130, color: "#ff6b35" },
  { min: 100, color: "#f7c59f" },
  { min: 50,  color: "#a8d8ea" },
  { min: 0,   color: "#d4edda" },
];

// 🔤 Tiêu đề dashboard (header góc trái)
export const DASHBOARD_TITLE = {
  subtitle: "INJECTION MOLDING",
  title:    "PRODUCTION PLANNING DASHBOARD",
};