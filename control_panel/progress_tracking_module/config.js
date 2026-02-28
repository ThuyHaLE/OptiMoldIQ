// ============================================================
//  ⚙️  PO STATUS BOARD CONFIG
// ============================================================
export const STATUS_CFG = {
  MOLDED:  { label:"MOLDED",  color:"#10b981", bg:"rgba(16,185,129,0.12)",  dot:"#34d399", border:"#10b98138" },
  MOLDING: { label:"MOLDING", color:"#3b82f6", bg:"rgba(59,130,246,0.12)",  dot:"#60a5fa", border:"#3b82f638" },
  PAUSED:  { label:"PAUSED",  color:"#f59e0b", bg:"rgba(245,158,11,0.12)",  dot:"#fbbf24", border:"#f59e0b38" },
  PENDING: { label:"PENDING", color:"#6b7280", bg:"rgba(107,114,128,0.08)", dot:"#9ca3af", border:"#37414138" },
};

export const ETA_CFG = {
  ONTIME:  { label:"ON TIME", color:"#10b981" },
  LATE:    { label:"LATE",    color:"#ef4444" },
  PENDING: { label:"—",       color:"#4a5a7a" },
};

export const PO_COLS = [
  { key:"expand",             label:"",           w:28,  noSort:true },
  { key:"poNo",               label:"PO No.",      w:90  },
  { key:"itemCode",           label:"Item Code",   w:95  },
  { key:"itemType",           label:"Item Type",   w:130 },
  { key:"itemName",           label:"Item Name",   w:200 },
  { key:"moldList",           label:"Mold",        w:120 },
  { key:"proStatus",          label:"Status",      w:82  },
  { key:"progress",           label:"Progress",    w:110 },
  { key:"etaStatus",          label:"ETA",         w:62  },
  { key:"poETA",              label:"Due Date",    w:76  },
  { key:"startedDate",        label:"Start",       w:70  },
  { key:"actualFinishedDate", label:"Finish",      w:70  },
  { key:"itemQuantity",       label:"Qty",         w:72  },
  { key:"itemRemain",         label:"Remain",      w:72  },
];

export const GANTT_COLORS = [
  "#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4",
  "#ec4899","#84cc16","#f97316","#6366f1","#14b8a6","#e11d48",
  "#a855f7","#0ea5e9","#22c55e","#fbbf24","#7c3aed","#059669",
  "#dc2626","#2563eb","#d97706","#0891b2","#9333ea","#15803d",
  "#b91c1c",
];

export const COL_W = 28;