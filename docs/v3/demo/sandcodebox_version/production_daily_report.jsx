import { useState, useMemo } from "react";

// ============================================================
//  ✏️  CONFIG — chỉnh tại đây, không cần động vào code bên dưới
// ============================================================
const CONFIG = {
  MACHINE_COUNT: 11,
  TODAY:         "2019-01-31",
  GANTT_START:   "2019-01-01",
  GANTT_DAYS:    31,
  REPORT_TITLE:    "PRODUCTION DAILY REPORT",
  REPORT_SUBTITLE: "INJECTION MOLDING",
  REPORT_DATE:     "Thu Jan 31, 2019",
};

// ============================================================
//  📋  RAW JSON — paste API response here
//      hoặc thay bằng: const RAW_JSON = await response.json();
// ============================================================
const RAW_JSON = [
  {"machine": "NO.09", "po": "IM1901032", "goods": "CT-CAX-BASE-COVER",       "mold": "14100CBR-M-001", "output": "2019-01-15", "prog": 100.0, "start": "2019-01-02", "end": "2019-01-31", "qty": 545000, "cap": 27853.2,  "wdays": 20.0, "rem": 0      },
  {"machine": "NO.05", "po": "IM1901033", "goods": "CT-CAX-REEL",              "mold": "15000CBR-M-001", "output": "2019-01-15", "prog": 100.0, "start": "2019-01-02", "end": "2019-01-31", "qty": 530000, "cap": 28924.5,  "wdays": 20.0, "rem": 0      },
  {"machine": "NO.06", "po": "IM1901002", "goods": "AB-TP-LARGE-CAP-025-YW",  "mold": "20101IBE-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-31", "end": "2019-01-31", "qty": 1000,   "cap": 1144.0,   "wdays": 1.0,  "rem": 0      },
  {"machine": "NO.06", "po": "IM1901004", "goods": "AB-TP-LARGE-CAP-027-BG",  "mold": "20101IBE-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-31", "end": "2019-01-31", "qty": 1000,   "cap": 1000.0,   "wdays": 1.0,  "rem": 0      },
  {"machine": "NO.02", "po": "IM1901014", "goods": "AB-TP-SMALL-CAP-062-YW",  "mold": "20102IBE-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-31", "end": "2019-01-31", "qty": 5000,   "cap": 5008.0,   "wdays": 1.0,  "rem": 0      },
  {"machine": "NO.07", "po": "IM1901026", "goods": "CT-CAX-UPPER-CASE-PINK",  "mold": "10100CBR-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-30", "end": "2019-01-31", "qty": 20000,  "cap": 10900.0,  "wdays": 2.0,  "rem": 0      },
  {"machine": "NO.08", "po": "IM1901028", "goods": "CT-CAX-LOWER-CASE-PINK",  "mold": "10000CBR-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-25", "end": "2019-01-31", "qty": 50000,  "cap": 8781.67,  "wdays": 6.0,  "rem": 0      },
  {"machine": "NO.03", "po": "IM1901031", "goods": "CT-CAX-CARTRIDGE-BASE",   "mold": "14000CBR-M-001", "output": "2019-01-30", "prog": 100.0, "start": "2019-01-12", "end": "2019-01-31", "qty": 445000, "cap": 26748.71, "wdays": 17.0, "rem": 0      },
  {"machine": "NO.01", "po": "IM1901040", "goods": "CT-CA-BASE-NL(NO-PRINT)", "mold": "14000CBQ-M-001", "output": "2019-01-30", "prog": 76.75, "start": "2019-01-03", "end": null,         "qty": 500000, "cap": 20748.33, "wdays": 18.0, "rem": 116267 },
  {"machine": "NO.11", "po": "IM1901044", "goods": "CT-PXN-HEAD-COVER-4.2MM","mold": "PXNHC4-M-002",   "output": "2019-01-30", "prog": 100.0, "start": "2019-01-28", "end": "2019-01-31", "qty": 138000, "cap": 34634.25, "wdays": 4.0,  "rem": 0      },
  {"machine": "NO.10", "po": "IM1901060", "goods": "CT-PS-SPACER",            "mold": "PSSP-M-001",     "output": "2019-01-30", "prog": 100.0, "start": "2019-01-31", "end": "2019-01-31", "qty": 30000,  "cap": 30368.0,  "wdays": 1.0,  "rem": 0      }
];
// ============================================================

// Map RAW_JSON → internal RAW_DATA (fields giữ nguyên, chỉ đặt tên lại cho rõ)
const RAW_DATA = RAW_JSON;

// ============================================================
//  ⚙️  Derived — không cần chỉnh bên dưới này
// ============================================================
function parseConfigDate(s) {
  // supports both YYYY-MM-DD and MM-DD-YYYY
  const parts = s.split("-");
  if (parts[0].length === 4) return new Date(+parts[0], +parts[1] - 1, +parts[2]);
  return new Date(+parts[2], +parts[0] - 1, +parts[1]);
}

const ALL_MACHINES = Array.from({ length: CONFIG.MACHINE_COUNT }, (_, i) => {
  const num = String(i + 1).padStart(2, "0");
  return `NO.${num}`;
});

const DATA_MAP = {};
RAW_DATA.forEach((r) => { DATA_MAP[r.machine] = r; });

const FULL_DATA = ALL_MACHINES.map((m) => {
  if (DATA_MAP[m]) return { ...DATA_MAP[m], idle: false };
  return {
    machine: m, po: "—", goods: "— NO ACTIVE JOB —", mold: "—",
    output: "—", prog: null, start: "—", end: "—",
    qty: 0, cap: 0, wdays: 0, rem: 0, idle: true,
  };
});

function genDates(startDate, n) {
  const out = [];
  const dt = new Date(startDate);
  for (let i = 0; i < n; i++) { out.push(new Date(dt)); dt.setDate(dt.getDate() + 1); }
  return out;
}
const GANTT_DATES = genDates(parseConfigDate(CONFIG.GANTT_START), CONFIG.GANTT_DAYS);
const TODAY = parseConfigDate(CONFIG.TODAY);

const COLORS = [
  "#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#ec4899",
  "#84cc16","#f97316","#6366f1","#14b8a6","#e11d48","#a855f7","#0ea5e9",
  "#22c55e","#fbbf24","#7c3aed","#059669","#dc2626","#2563eb","#d97706",
  "#0891b2","#9333ea","#15803d","#b91c1c",
];

function progColor(p) {
  if (p === null) return "#2a3245";
  if (p >= 90) return "#10b981";
  if (p >= 60) return "#3b82f6";
  if (p >= 30) return "#f59e0b";
  return "#ef4444";
}
function fmt(n) { return n.toLocaleString(); }
function parseD(s) {
  if (!s || s === "—") return null;
  const parts = s.split("-");
  if (parts[0].length === 4) return new Date(+parts[0], +parts[1] - 1, +parts[2]);
  return new Date(+parts[2], +parts[0] - 1, +parts[1]);
}

const COL_W = 28;

export default function App() {
  const [filter, setFilter] = useState("all");
  const [machineFilter, setMachineFilter] = useState("");
  const [search, setSearch] = useState("");
  const [tab, setTab] = useState("table");
  const [selectedRow, setSelectedRow] = useState(null);
  const [showIdle, setShowIdle] = useState(true);

  const filtered = useMemo(() => {
    return FULL_DATA.filter((r) => {
      if (!showIdle && r.idle) return false;
      if (machineFilter && r.machine !== machineFilter) return false;
      if (search && !r.goods.toLowerCase().includes(search.toLowerCase()) &&
        !r.po.toLowerCase().includes(search.toLowerCase()) &&
        !r.machine.toLowerCase().includes(search.toLowerCase())) return false;
      if (filter === "complete")   return !r.idle && r.prog >= 95;
      if (filter === "inprogress") return !r.idle && r.prog > 0 && r.prog < 95;
      if (filter === "notstarted") return !r.idle && r.prog === 0;
      if (filter === "overdue")    return !r.idle && r.prog < 90 && r.wdays > 6;
      if (filter === "idle")       return r.idle;
      return true;
    });
  }, [filter, machineFilter, search, showIdle]);

  const activeData = FULL_DATA.filter((r) => !r.idle);
  const idleCount  = FULL_DATA.filter((r) => r.idle).length;

  const totals = useMemo(() => {
    const active = filtered.filter((r) => !r.idle);
    return {
      qty: active.reduce((a, r) => a + r.qty, 0),
      cap: active.reduce((a, r) => a + r.cap, 0),
      rem: active.reduce((a, r) => a + r.rem, 0),
      avgProg: active.length
        ? (active.reduce((a, r) => a + r.prog, 0) / active.length).toFixed(1)
        : 0,
    };
  }, [filtered]);

  const FILTER_BTNS = [
    { k: "all",        label: "All",        count: FULL_DATA.length },
    { k: "inprogress", label: "In Progress", count: activeData.filter((r) => r.prog > 0 && r.prog < 95).length },
    { k: "complete",   label: "≥95% Done",   count: activeData.filter((r) => r.prog >= 95).length },
    { k: "notstarted", label: "Not Started", count: activeData.filter((r) => r.prog === 0).length },
    { k: "overdue",    label: "Long Run",    count: activeData.filter((r) => r.prog < 90 && r.wdays > 6).length },
    { k: "idle",       label: "Idle",        count: idleCount },
  ];

  return (
    <div style={{
      fontFamily: "'IBM Plex Mono',monospace",
      background: "#0c1018", color: "#c9d1e0",
      height: "100vh", display: "flex", flexDirection: "column",
      overflow: "hidden", fontSize: 11,
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:5px;height:5px;}
        ::-webkit-scrollbar-track{background:#0c1018;}
        ::-webkit-scrollbar-thumb{background:#2a3245;border-radius:3px;}
        ::-webkit-scrollbar-thumb:hover{background:#3a4a65;}
        .row-hover:hover{background:rgba(30,37,53,0.8)!important;}
        .row-sel{background:rgba(59,130,246,0.15)!important;}
        .row-idle{opacity:0.45;}
        .row-idle:hover{opacity:0.7!important;}
      `}</style>

      {/* HEADER */}
      <div style={{ background: "#131929", borderBottom: "1px solid #1e2d45", padding: "8px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#e8edf5", letterSpacing: "0.1em" }}>{CONFIG.REPORT_TITLE}</div>
          <div style={{ fontSize: 9, color: "#4a5a7a", marginTop: 1 }}>{CONFIG.REPORT_SUBTITLE} — {CONFIG.REPORT_DATE} &nbsp;|&nbsp; {ALL_MACHINES.length} MACHINES TOTAL</div>
        </div>
        <div style={{ display: "flex", gap: 20 }}>
          {[
            ["LAST UPDATE",      CONFIG.REPORT_DATE,              "#3b82f6"],
            ["ACTIVE MACHINES",  `${activeData.length} / ${ALL_MACHINES.length}`, "#10b981"],
            ["IDLE MACHINES",    `${idleCount}`,                  "#4a5a7a"],
            ["AVG PROGRESS",     totals.avgProg + "%",            progColor(+totals.avgProg)],
          ].map(([l, v, c]) => (
            <div key={l} style={{ textAlign: "right" }}>
              <div style={{ fontSize: 8, color: "#4a5a7a", letterSpacing: "0.05em" }}>{l}</div>
              <div style={{ fontSize: 11, fontWeight: 600, color: c }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {/* TOOLBAR */}
      <div style={{ background: "#101520", borderBottom: "1px solid #1a2438", padding: "5px 14px", display: "flex", alignItems: "center", gap: 6, flexShrink: 0, flexWrap: "wrap" }}>
        {FILTER_BTNS.map((b) => (
          <button key={b.k} onClick={() => { setFilter(b.k); if (b.k === "idle") setShowIdle(true); }}
            style={{ padding: "3px 9px", border: "1px solid", borderRadius: 3, cursor: "pointer", fontSize: 10, background: filter === b.k ? (b.k === "idle" ? "#1a2438" : "#1d4ed8") : "transparent", borderColor: filter === b.k ? (b.k === "idle" ? "#4a5a7a" : "#3b82f6") : "#2a3245", color: filter === b.k ? (b.k === "idle" ? "#6a7a9a" : "#fff") : "#7a8aaa", fontFamily: "inherit", transition: "all .15s" }}>
            {b.label} <span style={{ opacity: 0.6 }}>({b.count})</span>
          </button>
        ))}
        <div style={{ width: 1, height: 16, background: "#1e2d45", margin: "0 2px" }} />
        <button onClick={() => setShowIdle(!showIdle)}
          style={{ padding: "3px 9px", border: "1px solid", borderRadius: 3, cursor: "pointer", fontSize: 10, background: showIdle ? "rgba(74,90,122,0.15)" : "transparent", borderColor: showIdle ? "#4a5a7a" : "#2a3245", color: showIdle ? "#6a7a9a" : "#4a5a7a", fontFamily: "inherit" }}>
          {showIdle ? "⊙ Showing Idle" : "⊘ Idle Hidden"}
        </button>
        <div style={{ width: 1, height: 16, background: "#1e2d45", margin: "0 2px" }} />
        <select value={machineFilter} onChange={(e) => setMachineFilter(e.target.value)}
          style={{ padding: "3px 6px", background: "#0c1018", border: "1px solid #2a3245", borderRadius: 3, color: "#c9d1e0", fontSize: 10, fontFamily: "inherit" }}>
          <option value="">All Machines</option>
          {ALL_MACHINES.map((m) => <option key={m} value={m}>{m}{DATA_MAP[m] ? "" : " (idle)"}</option>)}
        </select>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search goods / PO..."
          style={{ padding: "3px 8px", background: "#0c1018", border: "1px solid #2a3245", borderRadius: 3, color: "#c9d1e0", fontSize: 10, fontFamily: "inherit", width: 160 }} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
          {[["table","Table"],["gantt","Gantt"],["both","Both"]].map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} style={{ padding: "3px 9px", border: "1px solid", borderRadius: 3, cursor: "pointer", fontSize: 10, background: tab === k ? "#0f2d4a" : "transparent", borderColor: tab === k ? "#0ea5e9" : "#2a3245", color: tab === k ? "#0ea5e9" : "#7a8aaa", fontFamily: "inherit" }}>{l}</button>
          ))}
        </div>
      </div>

      {/* SUMMARY BAR */}
      <div style={{ background: "#0e1622", borderBottom: "1px solid #1a2438", padding: "4px 14px", display: "flex", gap: 24, flexShrink: 0 }}>
        {[
          ["Total Qty",       fmt(totals.qty), "#c9d1e0"],
          ["Total Capacity",  fmt(totals.cap), "#8b9ab5"],
          ["Total Remaining", fmt(totals.rem), totals.rem > 500000 ? "#ef4444" : "#f59e0b"],
        ].map(([l, v, c]) => (
          <div key={l} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 9, color: "#4a5a7a", letterSpacing: "0.04em" }}>{l}</span>
            <span style={{ fontSize: 11, fontWeight: 600, color: c }}>{v}</span>
          </div>
        ))}
        <div style={{ marginLeft: "auto", fontSize: 9, color: "#4a5a7a", alignSelf: "center" }}>
          {filtered.filter(r => !r.idle).length} active + {filtered.filter(r => r.idle).length} idle = {filtered.length} rows
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* TABLE PANEL */}
        {(tab === "table" || tab === "both") && (
          <div style={{ flex: tab === "both" ? "0 0 640px" : 1, overflow: "auto", borderRight: tab === "both" ? "2px solid #1a2438" : "none" }}>
            <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 10.5 }}>
              <thead>
                <tr style={{ background: "#101926", position: "sticky", top: 0, zIndex: 10 }}>
                  {[["Machine",52],["PO #",88],["Goods Name",190],["Mold",90],["Output",72],["Progress",100],["Start",70],["End",70],["Qty",65],["Cap/Day",65],["W.Days",50],["Remain",65]].map(([h, w]) => (
                    <th key={h} style={{ width: w, padding: "4px 5px", textAlign: "left", color: "#4a5a7a", fontWeight: 600, fontSize: 9, textTransform: "uppercase", letterSpacing: "0.05em", borderBottom: "2px solid #1a2d45", borderRight: "1px solid #1a2438", whiteSpace: "nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => {
                  const pc = progColor(row.prog);
                  const isSel = selectedRow === i;
                  return (
                    <tr key={row.machine + i} className={"row-hover" + (isSel ? " row-sel" : "") + (row.idle ? " row-idle" : "")} onClick={() => setSelectedRow(isSel ? null : i)}
                      style={{ borderBottom: "1px solid rgba(26,36,56,0.7)", cursor: row.idle ? "default" : "pointer", background: isSel ? "rgba(59,130,246,0.12)" : "transparent" }}>
                      <td style={{ padding: "3px 5px", fontWeight: 600, color: row.idle ? "#2a3a55" : "#3b82f6" }}>{row.machine}</td>
                      <td style={{ padding: "3px 5px", color: row.idle ? "#2a3a55" : "#4a5a7a", fontSize: 9.5 }}>{row.po}</td>
                      <td style={{ padding: "3px 5px", color: row.idle ? "#2a3a55" : "#e8edf5", maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontStyle: row.idle ? "italic" : "normal" }} title={row.goods}>{row.goods}</td>
                      <td style={{ padding: "3px 5px", color: "#6a7a9a", fontSize: 9 }}>{row.mold}</td>
                      <td style={{ padding: "3px 5px", color: "#5a6a8a", fontSize: 9 }}>{row.output}</td>
                      <td style={{ padding: "3px 5px" }}>
                        {row.idle ? (
                          <div style={{ fontSize: 8, color: "#2a3a55", letterSpacing: "0.08em", fontStyle: "italic", paddingLeft: 2 }}>IDLE</div>
                        ) : (
                          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                            <div style={{ flex: 1, height: 9, background: "#1a2438", borderRadius: 2, overflow: "hidden", border: "1px solid #2a3245" }}>
                              <div style={{ width: row.prog + "%", height: "100%", background: pc, borderRadius: 2 }} />
                            </div>
                            <span style={{ color: pc, fontSize: 9, width: 32, textAlign: "right" }}>{row.prog}%</span>
                          </div>
                        )}
                      </td>
                      <td style={{ padding: "3px 5px", color: "#7a8aaa", fontSize: 9 }}>{row.start}</td>
                      <td style={{ padding: "3px 5px", color: "#7a8aaa", fontSize: 9 }}>{row.end}</td>
                      <td style={{ padding: "3px 5px", textAlign: "right", fontWeight: 600, color: row.idle ? "#2a3a55" : "#c9d1e0" }}>{row.idle ? "—" : fmt(row.qty)}</td>
                      <td style={{ padding: "3px 5px", textAlign: "right", color: "#6a7a9a" }}>{row.idle ? "—" : fmt(row.cap)}</td>
                      <td style={{ padding: "3px 5px", textAlign: "center" }}>
                        {!row.idle && (
                          <span style={{ padding: "1px 5px", borderRadius: 2, fontSize: 9, fontWeight: 600, background: row.wdays >= 8 ? "rgba(239,68,68,0.15)" : row.wdays >= 5 ? "rgba(245,158,11,0.15)" : "rgba(16,185,129,0.12)", color: row.wdays >= 8 ? "#ef4444" : row.wdays >= 5 ? "#f59e0b" : "#10b981" }}>{row.wdays}</span>
                        )}
                      </td>
                      <td style={{ padding: "3px 5px", textAlign: "right", fontWeight: 600, color: row.idle ? "#2a3a55" : row.rem > 50000 ? "#ef4444" : row.rem > 10000 ? "#f59e0b" : "#10b981" }}>{row.idle ? "—" : fmt(row.rem)}</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr style={{ background: "#101926", position: "sticky", bottom: 0, borderTop: "2px solid #1a2d45" }}>
                  <td colSpan={8} style={{ padding: "4px 5px", color: "#4a5a7a", fontSize: 9, textAlign: "right", letterSpacing: "0.05em" }}>TOTALS (ACTIVE ONLY)</td>
                  <td style={{ padding: "4px 5px", textAlign: "right", fontWeight: 600, color: "#3b82f6" }}>{fmt(totals.qty)}</td>
                  <td style={{ padding: "4px 5px", textAlign: "right", color: "#6a7a9a" }}>{fmt(totals.cap)}</td>
                  <td />
                  <td style={{ padding: "4px 5px", textAlign: "right", fontWeight: 600, color: "#f59e0b" }}>{fmt(totals.rem)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        {/* GANTT PANEL */}
        {(tab === "gantt" || tab === "both") && (
          <div style={{ flex: 1, overflow: "auto" }}>
            <div style={{ minWidth: GANTT_DATES.length * COL_W + 100 }}>
              <table style={{ borderCollapse: "collapse", width: "100%" }}>
                <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                  <tr style={{ background: "#0c1018" }}>
                    {tab === "gantt" && <th style={{ width: 90, background: "#101926", borderRight: "2px solid #1a2d45", borderBottom: "1px solid #1a2438" }} />}
                    {(() => {
                      let cur = null, span = 0, cells = [];
                      GANTT_DATES.forEach((d, i) => {
                        const mon = new Date(d); mon.setDate(d.getDate() - ((d.getDay() + 6) % 7));
                        const key = `${mon.getMonth() + 1}/${mon.getDate()}`;
                        if (key !== cur) { if (cur) cells.push({ key: cur, span }); cur = key; span = 1; } else span++;
                        if (i === GANTT_DATES.length - 1) cells.push({ key: cur, span });
                      });
                      return cells.map((c) => (
                        <th key={c.key} colSpan={c.span} style={{ textAlign: "center", padding: "2px 0", fontSize: 9, fontWeight: 600, color: "#3b82f6", borderRight: "1px solid #1a2438", borderBottom: "1px solid #1a2438", background: "#0c1018", letterSpacing: "0.04em" }}>
                          Feb-{c.key.split("/")[1]}
                        </th>
                      ));
                    })()}
                  </tr>
                  <tr style={{ background: "#101926" }}>
                    {tab === "gantt" && <th style={{ width: 90, padding: "3px 6px", textAlign: "left", fontSize: 9, color: "#4a5a7a", fontWeight: 600, letterSpacing: "0.05em", borderRight: "2px solid #1a2d45", borderBottom: "2px solid #1a2d45" }}>MACHINE</th>}
                    {GANTT_DATES.map((d, i) => {
                      const isToday = d.toDateString() === TODAY.toDateString();
                      const isWE = d.getDay() === 0 || d.getDay() === 6;
                      const days = ["Su","Mo","Tu","We","Th","Fr","Sa"];
                      return (
                        <th key={i} style={{ width: COL_W, padding: "3px 0", textAlign: "center", fontSize: 8, color: isToday ? "#f59e0b" : isWE ? "#2a3a55" : "#5a6a8a", borderRight: "1px solid #1a2438", borderBottom: `2px solid ${isToday ? "#f59e0b" : "#1a2d45"}`, background: isToday ? "rgba(245,158,11,0.08)" : "transparent", whiteSpace: "nowrap" }}>
                          <div>{days[d.getDay()]}</div>
                          <div style={{ fontWeight: 600 }}>{d.getDate()}</div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((row, ri) => {
                    const start = parseD(row.start);
                    const end   = parseD(row.end);
                    return (
                      <tr key={row.machine + ri} className="row-hover" style={{ borderBottom: "1px solid rgba(26,36,56,0.5)", height: 28, opacity: row.idle ? 0.35 : 1 }}>
                        {tab === "gantt" && <td style={{ padding: "2px 5px", fontSize: 9.5, fontWeight: 600, color: row.idle ? "#2a3a55" : "#3b82f6", borderRight: "2px solid #1a2d45", whiteSpace: "nowrap" }}>{row.machine}</td>}
                        {GANTT_DATES.map((d, di) => {
                          const isToday = d.toDateString() === TODAY.toDateString();
                          const isWE    = d.getDay() === 0 || d.getDay() === 6;
                          const isStart = !row.idle && start && d.toDateString() === start.toDateString();
                          let barSpan = 0;
                          if (isStart && start && end) {
                            const diff = Math.round((end - start) / 864e5) + 1;
                            barSpan = Math.min(Math.max(1, diff), GANTT_DATES.length - di);
                          }
                          return (
                            <td key={di} style={{ position: "relative", width: COL_W, background: isToday ? "rgba(245,158,11,0.05)" : isWE ? "repeating-linear-gradient(45deg,rgba(26,36,56,0.3),rgba(26,36,56,0.3) 2px,transparent 2px,transparent 6px)" : row.idle ? "repeating-linear-gradient(135deg,rgba(20,28,44,0.4),rgba(20,28,44,0.4) 2px,transparent 2px,transparent 8px)" : "transparent", borderRight: `1px solid ${isToday ? "rgba(245,158,11,0.3)" : "rgba(26,36,56,0.5)"}`, overflow: "visible" }}>
                              {isStart && (
                                <div style={{ position: "absolute", top: 4, left: 2, width: barSpan * COL_W - 4, height: 18, borderRadius: 2, background: COLORS[ri % COLORS.length], opacity: 0.8, zIndex: 2, cursor: "pointer", overflow: "hidden" }}
                                  title={`${row.machine}: ${row.goods}\n${row.start} → ${row.end}\n${row.prog}%`}>
                                  <div style={{ position: "absolute", top: 0, left: 0, width: row.prog + "%", height: "100%", background: "rgba(255,255,255,0.18)", borderRadius: 2 }} />
                                  {barSpan >= 3 && (
                                    <div style={{ position: "absolute", top: "50%", left: 4, transform: "translateY(-50%)", fontSize: 8, color: "rgba(255,255,255,0.9)", whiteSpace: "nowrap", fontWeight: 600, letterSpacing: "0.03em" }}>{row.prog}%</div>
                                  )}
                                </div>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}