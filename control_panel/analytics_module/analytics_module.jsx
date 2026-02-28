import { useState, useMemo } from "react";
import {C, TYPE_COLORS, MACHINE_COLORS, MONTH_PALETTE,
  monthColor, monthBg, defectColor, etaColor, statusColor, ngColor} from "./config.js";
import { DATA as MOCK_DATA } from "./data.js";

const USE_MOCK = false;

let layout, machineMoldFirstRunPair, moldMachineFirstRunPair;
let DayLevelDataProcessor, MonthLevelDataProcessor, YearLevelDataProcessor;
let DATE_A, DATE_B, PERIOD_LABEL, LIVE_DATE;
let layoutMachines, allSlots, moldKeys, machineKeys, moldMachineMatrix, machineRunCounts, moldRunCounts, totalPairs;
let activeSlots, TOTAL_SLOTS;

// ============================================================
// SHARED MICRO-COMPONENTS
// ============================================================

function PillA({ active, onClick, children }) {
  return (
    <button onClick={onClick} className={`pill${active ? " active" : ""}`}>{children}</button>
  );
}

function PillB({ label, active, onClick, danger }) {
  return (
    <button onClick={onClick} style={{
      background: active ? (danger ? C.red + "33" : C.accent + "33") : "transparent",
      border: `1px solid ${active ? (danger ? C.red : C.accent) : C.border}`,
      borderRadius: 5, color: active ? (danger ? C.red : "#93c5fd") : C.muted,
      padding: "4px 12px", cursor: "pointer", fontSize: 11,
      fontFamily: "'Space Mono', monospace", letterSpacing: "0.04em", transition: "all .15s",
    }}>{label}</button>
  );
}

function KpiCardA({ label, value, color, sub }) {
  return (
    <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderLeft: `3px solid ${color}`, borderRadius: 8, padding: "14px 18px" }}>
      <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.15em", marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 34, color, lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 9, color: "#334155", marginTop: 3 }}>{sub}</div>
    </div>
  );
}

function KpiCardB({ label, value, color, sub }) {
  return (
    <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: "14px 16px", borderTop: `2px solid ${color}` }}>
      <div style={{ fontSize: 9, color: C.muted, letterSpacing: ".16em", marginBottom: 7 }}>{label}</div>
      <div style={{ fontSize: 26, fontFamily: "'Space Mono', monospace", color, lineHeight: 1, fontWeight: 700 }}>{value}</div>
      {sub && <div style={{ fontSize: 9, color: C.dim, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function DividerV() {
  return <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />;
}

function Arc({ pct, warn, size = 46, maxRate = 1 }) {
  const ep = Math.min(pct / maxRate, 1);
  const r = 17, cx = size / 2, cy = size / 2;
  const circ = Math.PI * 2 * r * 0.75;
  const filled = circ * ep;
  const color = warn ? C.red : ep >= 1 ? C.green : ep > 0.5 ? C.accent : C.yellow;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={C.border} strokeWidth="4"
        strokeDasharray={`${circ} 999`} strokeLinecap="round" transform={`rotate(135 ${cx} ${cy})`} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="4"
        strokeDasharray={`${filled} 999`} strokeLinecap="round" transform={`rotate(135 ${cx} ${cy})`}
        style={{ transition: "stroke-dasharray .5s ease" }} />
      <text x={cx} y={cy + 4} textAnchor="middle" fill={color} fontSize="9"
        fontWeight="700" fontFamily="'Space Mono',monospace">{Math.round(ep * 100)}%</text>
    </svg>
  );
}

function Badge({ label, color }) {
  return (
    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 4, background: color + "22",
      color, border: `1px solid ${color}44`, letterSpacing: ".08em", whiteSpace: "nowrap",
      fontFamily: "'Space Mono',monospace" }}>{label}</span>
  );
}

// ============================================================
// MACHINE LAYOUT CHANGE — Floor Layout & Cards
// ============================================================

function LayoutCards({ activeType, filter }) {
  const machines = layoutMachines.filter(m => {
    if (filter === "new")   return m.isNew;
    if (filter === "moved") return m.moved;
    if (filter === "fixed") return m.unchanged;
    return true;
  }).filter(m => !activeType || m.name === activeType);

  return machines.length === 0 ? (
    <div style={{ textAlign: "center", padding: 60, color: "#334155", fontSize: 11, letterSpacing: "0.1em" }}>NO MACHINES MATCH FILTER</div>
  ) : (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(276px, 1fr))", gap: 12 }}>
      {machines.map(m => {
        const c = TYPE_COLORS[m.name] || { line: "#64748b", bg: "#0c1a2e", border: "#334155" };
        const tag = m.isNew ? { label: "NEW", color: "#a78bfa" } : m.moved ? { label: "MOVED", color: "#fbbf24" } : { label: "FIXED", color: "#22c55e" };
        return (
          <div key={m.code} style={{ background: c.bg, border: `1px solid ${c.border}`, borderLeft: `3px solid ${c.line}`, borderRadius: 8, padding: "14px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
              <div>
                <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 20, color: c.line, letterSpacing: "0.1em" }}>{m.name}</div>
                <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>{m.code}</div>
              </div>
              <span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: tag.color + "22", color: tag.color, border: `1px solid ${tag.color}44`, letterSpacing: "0.1em" }}>{tag.label}</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 24px 1fr", alignItems: "center", gap: 4 }}>
              <div style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
                <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.1em", marginBottom: 3 }}>{DATE_A}</div>
                {m.posA ? <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 18, color: "#64748b" }}>{m.posA}</div>
                  : <div style={{ fontSize: 10, color: "#1e3a5f" }}>—</div>}
              </div>
              <div style={{ textAlign: "center" }}>
                {m.isNew ? <span style={{ color: "#a78bfa", fontSize: 14 }}>+</span>
                  : m.moved ? <span style={{ color: "#fbbf24", fontSize: 12 }}>→</span>
                  : <span style={{ color: "#1e3a5f", fontSize: 10 }}>＝</span>}
              </div>
              <div style={{ background: "#060f1c", border: `1px solid ${m.isNew ? "#7c3aed55" : m.moved ? "#b4530955" : "#1e3a5f"}`, borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
                <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.1em", marginBottom: 3 }}>{DATE_B}</div>
                <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 18, color: m.isNew ? "#a78bfa" : m.moved ? "#fbbf24" : "#22c55e" }}>{m.posB}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function LayoutFloor({ activeType }) {
  const getMachineAtSlot = (slot, key) =>
    layoutMachines.find(m => (key === "A" ? m.posA : m.posB) === slot);

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {[["A", DATE_A], ["B", DATE_B]].map(([key, date]) => (
          <div key={key} style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 10, padding: 14 }}>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em", marginBottom: 12 }}>
              FLOOR LAYOUT — <span style={{ color: "#60a5fa" }}>{date}</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
              {allSlots.map(slot => {
                const m = getMachineAtSlot(slot, key);
                const c = m ? (TYPE_COLORS[m.name] || { line: "#64748b", bg: "#0c1a2e", border: "#334155" }) : null;
                const glow   = activeType && m && m.name === activeType;
                const dimmed = activeType && m && m.name !== activeType;
                return (
                  <div key={slot} style={{
                    background: m ? c.bg : "#0a1120", border: `1px solid ${m ? (glow ? c.line : c.border) : "#0f1e2e"}`,
                    borderRadius: 6, padding: "8px 6px", textAlign: "center",
                    boxShadow: glow ? `0 0 12px ${c.line}55` : "none",
                    opacity: dimmed ? 0.25 : 1, transition: "all 0.2s", minHeight: 60,
                    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  }}>
                    <div style={{ fontSize: 8, color: "#1e3a5f", letterSpacing: "0.08em", marginBottom: 3 }}>{slot}</div>
                    {m ? (
                      <>
                        <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 13, color: c.line, letterSpacing: "0.08em", lineHeight: 1 }}>{m.name}</div>
                        <div style={{ fontSize: 7, color: "#334155", marginTop: 2 }}>{m.code.split("-")[1]}</div>
                      </>
                    ) : <div style={{ fontSize: 8, color: "#1e293b" }}>EMPTY</div>}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 14, background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }}>
        <div style={{ padding: "10px 14px", borderBottom: "1px solid #1e3a5f", fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>POSITION CHANGE SUMMARY</div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr>{["MACHINE TYPE","CODE",`SLOT — ${DATE_A}`,`SLOT — ${DATE_B}`,"CHANGE"].map(h => (
              <th key={h} style={{ padding: "7px 12px", textAlign: "left", fontSize: 8, color: "#475569", letterSpacing: "0.1em", fontWeight: 500, borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap" }}>{h}</th>
            ))}</tr>
          </thead>
          <tbody>
            {layoutMachines.map((m, i) => {
              const c   = TYPE_COLORS[m.name] || { line: "#64748b" };
              const tag = m.isNew ? { label: "NEW", color: "#a78bfa" } : m.moved ? { label: "MOVED", color: "#fbbf24" } : { label: "FIXED", color: "#22c55e" };
              const dimmed = activeType && m.name !== activeType;
              return (
                <tr key={i} style={{ borderBottom: "1px solid #0a1929", background: i % 2 === 0 ? "transparent" : "#060e1a", opacity: dimmed ? 0.3 : 1, transition: "opacity 0.2s" }}>
                  <td style={{ padding: "8px 12px" }}><span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 15, color: c.line }}>{m.name}</span></td>
                  <td style={{ padding: "8px 12px", fontSize: 10, color: "#64748b" }}>{m.code}</td>
                  <td style={{ padding: "8px 12px" }}>{m.posA ? <span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 15, color: "#475569" }}>{m.posA}</span> : <span style={{ fontSize: 9, color: "#1e3a5f" }}>NOT INSTALLED</span>}</td>
                  <td style={{ padding: "8px 12px" }}><span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 15, color: c.line }}>{m.posB}</span></td>
                  <td style={{ padding: "8px 12px" }}><span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: tag.color + "22", color: tag.color, border: `1px solid ${tag.color}44`, letterSpacing: "0.1em" }}>{tag.label}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================
// MACHINE-MOLD & MOLD-MACHINE FIRST RUN PAIR — Heatmaps & List
// ============================================================

function HeatmapMoldMachine({ hoverCell, setHoverCell }) {
  return (
    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "55vh" }}>
      <table style={{ borderCollapse: "collapse", fontSize: 9 }}>
        <thead>
          <tr>
            <th style={{ padding: "4px 10px", textAlign: "left", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, left: 0, zIndex: 3, borderBottom: "1px solid #1e3a5f", minWidth: 140 }}>MOLD</th>
            {machineKeys.map(m => (
              <th key={m} style={{ padding: "5px 3px", fontSize: 8, color: MACHINE_COLORS[m] || "#64748b", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f", whiteSpace: "nowrap", minWidth: 58, textAlign: "center" }}>{m}</th>
            ))}
            <th style={{ padding: "5px 8px", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f" }}>TOTAL</th>
          </tr>
        </thead>
        <tbody>
          {moldKeys.map((mold, mi) => {
            if (moldRunCounts[mi] === 0) return null;
            return (
              <tr key={mold} style={{ borderBottom: "1px solid #0a1929" }}>
                <td style={{ padding: "4px 10px", color: "#64748b", fontSize: 9, background: "#060f1c", position: "sticky", left: 0, zIndex: 1, whiteSpace: "nowrap", borderRight: "1px solid #1e3a5f" }}>{mold}</td>
                {machineKeys.map((machine, machi) => {
                  const date  = moldMachineMatrix[mi][machi];
                  const color = monthColor(date);
                  const isHov = hoverCell?.mold === mold && hoverCell?.machine === machine;
                  return (
                    <td key={machine}
                      onMouseEnter={() => setHoverCell({ mold, machine, date })}
                      onMouseLeave={() => setHoverCell(null)}
                      style={{ padding: "3px", textAlign: "center", background: isHov ? "#0f2040" : date ? monthBg(date) : "transparent", border: isHov ? `1px solid ${color}` : "1px solid transparent", minWidth: 56 }}>
                      {date ? (
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
                          <div style={{ width: 7, height: 7, borderRadius: "50%", background: color, margin: "0 auto" }} />
                          <span style={{ color, fontSize: 7.5, fontFamily: "'DM Mono',monospace" }}>{date.slice(5)}</span>
                        </div>
                      ) : <span style={{ color: "#1e293b", fontSize: 9 }}>·</span>}
                    </td>
                  );
                })}
                <td style={{ padding: "4px 8px", textAlign: "center", fontFamily: "'DM Mono',monospace", fontSize: 10 }}>
                  <span style={{ color: "#60a5fa" }}>{moldRunCounts[mi]}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function HeatmapMachMold({ hoverCell, setHoverCell }) {
  const activeMolds = moldKeys.filter((_, mi) => moldRunCounts[mi] > 0);
  return (
    <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "55vh" }}>
      <table style={{ borderCollapse: "collapse", fontSize: 9 }}>
        <thead>
          <tr>
            <th style={{ padding: "4px 10px", textAlign: "left", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, left: 0, zIndex: 3, borderBottom: "1px solid #1e3a5f", minWidth: 110 }}>MACHINE</th>
            {activeMolds.map(mold => (
              <th key={mold} style={{ padding: "5px 2px", fontSize: 7, color: "#475569", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f", whiteSpace: "nowrap", minWidth: 50, textAlign: "center", writingMode: "vertical-rl", height: 88, verticalAlign: "bottom" }}>{mold}</th>
            ))}
            <th style={{ padding: "5px 8px", fontSize: 8, color: "#334155", background: "#060f1c", position: "sticky", top: 0, zIndex: 2, borderBottom: "1px solid #1e3a5f" }}>TOTAL</th>
          </tr>
        </thead>
        <tbody>
          {machineKeys.map((machine, machi) => (
            <tr key={machine} style={{ borderBottom: "1px solid #0a1929" }}>
              <td style={{ padding: "5px 10px", color: MACHINE_COLORS[machine] || "#64748b", fontSize: 10, background: "#060f1c", position: "sticky", left: 0, zIndex: 1, fontFamily: "'DM Mono',monospace", whiteSpace: "nowrap", fontWeight: 500, borderRight: "1px solid #1e3a5f" }}>{machine}</td>
              {activeMolds.map(mold => {
                const mi    = moldKeys.indexOf(mold);
                const date  = moldMachineMatrix[mi][machi];
                const color = monthColor(date);
                const isHov = hoverCell?.mold === mold && hoverCell?.machine === machine;
                return (
                  <td key={mold}
                    onMouseEnter={() => setHoverCell({ mold, machine, date })}
                    onMouseLeave={() => setHoverCell(null)}
                    style={{ padding: "3px", textAlign: "center", background: isHov ? "#0f2040" : date ? monthBg(date) : "transparent", border: isHov ? `1px solid ${color}` : "1px solid transparent", minWidth: 48 }}>
                    {date ? (
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}>
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
                        <span style={{ color, fontSize: 7, fontFamily: "'DM Mono',monospace" }}>{date.slice(5)}</span>
                      </div>
                    ) : <span style={{ color: "#1e293b" }}>·</span>}
                  </td>
                );
              })}
              <td style={{ padding: "4px 8px", textAlign: "center", fontFamily: "'DM Mono',monospace", fontSize: 10 }}>
                <span style={{ color: machineRunCounts[machi] > 0 ? MACHINE_COLORS[machine] : "#1e293b", fontWeight: 500 }}>{machineRunCounts[machi]}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PairList({ monthFilter }) {
  const rows = useMemo(() => {
    const out = [];
    moldKeys.forEach((mold, mi) => {
      machineKeys.forEach((machine, machi) => {
        const date = moldMachineMatrix[mi][machi];
        if (!date) return;
        if (monthFilter !== "all" && date.slice(5, 7) !== monthFilter) return;
        out.push({ mold, machine, date });
      });
    });
    return out.sort((a, b) => a.date.localeCompare(b.date));
  }, [monthFilter]);

  return (
    <div style={{ overflowY: "auto", maxHeight: "55vh" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
        <thead>
          <tr>{["DATE","MOLD","MACHINE","MONTH"].map(h => (
            <th key={h} style={{ padding: "7px 12px", textAlign: "left", fontSize: 8, color: "#475569", letterSpacing: "0.12em", fontWeight: 500, borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap" }}>{h}</th>
          ))}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const color = monthColor(r.date);
            return (
              <tr key={i} style={{ borderBottom: "1px solid #0a1929", background: i % 2 === 0 ? "transparent" : "#060e1a" }}>
                <td style={{ padding: "7px 12px", color, fontFamily: "'DM Mono',monospace", fontWeight: 500 }}>{r.date}</td>
                <td style={{ padding: "7px 12px", color: "#64748b", fontSize: 10 }}>{r.mold}</td>
                <td style={{ padding: "7px 12px", color: MACHINE_COLORS[r.machine] || "#64748b", fontWeight: 500 }}>{r.machine}</td>
                <td style={{ padding: "7px 12px" }}>
                  <span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: color + "22", color, border: `1px solid ${color}44`, letterSpacing: "0.08em" }}>{r.date.slice(0, 7)}</span>
                </td>
              </tr>
            );
          })}
          {rows.length === 0 && (
            <tr><td colSpan={4} style={{ textAlign: "center", padding: 40, color: "#334155", letterSpacing: "0.1em" }}>NO DATA</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ============================================================
// APP1 — MACHINE LAYOUT CHANGE & MACHINE-MOLD PAIRING ANALYTICS
// ============================================================
function App1() {
  const [module,       setModule]       = useState("layout");
  const [layoutView,   setLayoutView]   = useState("cards");
  const [activeType,   setActiveType]   = useState(null);
  const [filterChange, setFilterChange] = useState("all");
  const [pairView,     setPairView]     = useState("heatmap_mm");
  const [hoverCell,    setHoverCell]    = useState(null);
  const [monthFilter,  setMonthFilter]  = useState("all");

  const layoutTypes = [...new Set(layoutMachines.map(m => m.name))];
  const layoutStats = {
    total: layoutMachines.length,
    newM:  layoutMachines.filter(m => m.isNew).length,
    moved: layoutMachines.filter(m => m.moved).length,
    fixed: layoutMachines.filter(m => m.unchanged).length,
  };

  // Count first-run pairs by month, use MONTH_PALETTE to avoid hardcoding "11","12","01"
  const countByMonth = (mo) =>
    moldMachineFirstRunPair.reduce(
      (s, r) => s + Object.values(r).filter(v => v && v !== "NaT" && v.slice(5, 7) === mo).length, 0
    );

  return (
    <div style={{ minHeight: "100vh", background: "#020b18", fontFamily: "'DM Mono','Courier New',monospace", color: "#e2e8f0" }}>
      {/* ── HEADER ── */}
      <div style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f", padding: "12px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 3, height: 36, background: "#2563eb", borderRadius: 2 }} />
          <div>
            <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 24, letterSpacing: "0.12em", color: "#60a5fa" }}>INJECTION MOLDING OPS</div>
            <div style={{ fontSize: 9, color: "#334155", letterSpacing: "0.2em" }}>FLOOR LAYOUT · MOLD–MACHINE PAIRING — {PERIOD_LABEL}</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button className={`mod-btn ${module === "layout" ? "active" : ""}`} onClick={() => setModule("layout")}>▣ LAYOUT</button>
          <button className={`mod-btn ${module === "pairing" ? "active" : ""}`} onClick={() => setModule("pairing")}>⊞ PAIRING</button>
          <DividerV />
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} className="blink" />
          <span style={{ fontSize: 9, color: "#334155", letterSpacing: "0.1em" }}>LIVE</span>
        </div>
      </div>

      <div style={{ padding: "18px 28px" }}>
        {/* ── LAYOUT MODULE ── */}
        {module === "layout" && (
          <div className="fade-up">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 16 }}>
              <KpiCardA label="TOTAL MACHINES"    value={layoutStats.total} color="#60a5fa" sub="in layout" />
              <KpiCardA label="NEWLY ADDED"       value={layoutStats.newM}  color="#a78bfa" sub={`as of ${DATE_B}`} />
              <KpiCardA label="POSITION CHANGED"  value={layoutStats.moved} color="#fbbf24" sub="slot reassigned" />
              <KpiCardA label="UNCHANGED"         value={layoutStats.fixed} color="#22c55e" sub="same slot" />
            </div>
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "10px 14px", marginBottom: 12, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
              <PillA active={layoutView === "cards"} onClick={() => setLayoutView("cards")}>CARD VIEW</PillA>
              <PillA active={layoutView === "floor"} onClick={() => setLayoutView("floor")}>FLOOR PLAN</PillA>
              <DividerV />
              {layoutTypes.map(t => {
                const c = TYPE_COLORS[t] || { line: "#64748b", border: "#334155" };
                const isActive = activeType === t;
                return (
                  <button key={t} onClick={() => setActiveType(isActive ? null : t)} className="type-btn"
                    style={{ borderColor: isActive ? c.line : c.border, color: isActive ? c.line : "#475569", background: isActive ? c.line + "22" : "transparent" }}>
                    {t}
                  </button>
                );
              })}
              {layoutView === "cards" && (
                <>
                  <DividerV />
                  {[["all","ALL"],["new","NEW"],["moved","MOVED"],["fixed","FIXED"]].map(([v,l]) => (
                    <PillA key={v} active={filterChange === v} onClick={() => setFilterChange(v)}>{l}</PillA>
                  ))}
                </>
              )}
            </div>
            <div style={{ display: "flex", gap: 16, marginBottom: 12, alignItems: "center" }}>
              {[["#a78bfa","+","New machine added"],["#fbbf24","→","Position reassigned"],["#22c55e","＝","Position unchanged"]].map(([c,s,l]) => (
                <div key={l} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 9, color: "#475569" }}>
                  <span style={{ color: c, fontSize: 13, fontWeight: 700 }}>{s}</span>{l}
                </div>
              ))}
            </div>
            {layoutView === "cards" && <LayoutCards activeType={activeType} filter={filterChange} />}
            {layoutView === "floor" && <LayoutFloor activeType={activeType} />}
          </div>
        )}

        {/* ── PAIRING MODULE ── */}
        {module === "pairing" && (
          <div className="fade-up">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 10, marginBottom: 16 }}>
              <KpiCardA label="TOTAL PAIRS"    value={totalPairs} color="#60a5fa" sub="mold-machine runs" />
              <KpiCardA label="MOLDS ACTIVE"   value={moldKeys.filter((_,i) => moldRunCounts[i] > 0).length} color="#34d399" sub={`of ${moldKeys.length} total`} />
              <KpiCardA label="MACHINES ACTIVE" value={machineKeys.filter((_,i) => machineRunCounts[i] > 0).length} color="#f472b6" sub={`of ${machineKeys.length} total`} />
              {/* Month KPIs — render từ MONTH_PALETTE để dễ mở rộng */}
              {Object.entries(MONTH_PALETTE).map(([mo, p]) => (
                <KpiCardA key={mo} label={p.label} value={countByMonth(mo)} color={p.dot} sub="first runs" />
              ))}
            </div>
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "10px 14px", marginBottom: 12, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
              <PillA active={pairView === "heatmap_mach"} onClick={() => setPairView("heatmap_mach")}>MACHINE × MOLD</PillA>
              <PillA active={pairView === "heatmap_mm"}   onClick={() => setPairView("heatmap_mm")}>MOLD × MACHINE</PillA>
              <PillA active={pairView === "list"}         onClick={() => setPairView("list")}>LIST VIEW</PillA>
              {pairView === "list" && (
                <>
                  <DividerV />
                  {[["all","ALL"], ...Object.entries(MONTH_PALETTE).map(([mo, p]) => [mo, p.label.slice(0,3)])].map(([v,l]) => (
                    <PillA key={v} active={monthFilter === v} onClick={() => setMonthFilter(v)}>{l}</PillA>
                  ))}
                </>
              )}
              <div style={{ marginLeft: "auto", display: "flex", gap: 12, alignItems: "center" }}>
                {Object.values(MONTH_PALETTE).map(p => (
                  <div key={p.label} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 9, color: "#475569" }}>
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: p.dot }} />{p.label}
                  </div>
                ))}
              </div>
            </div>
            {hoverCell?.date && (
              <div style={{ background: "#0c1a2e", border: `1px solid ${monthColor(hoverCell.date)}`, borderRadius: 6, padding: "7px 14px", marginBottom: 10, display: "flex", gap: 18, alignItems: "center", fontSize: 10 }} className="fade-up">
                <span style={{ color: "#475569" }}>MOLD</span>
                <span style={{ color: "#93c5fd", fontWeight: 500 }}>{hoverCell.mold}</span>
                <span style={{ color: "#1e3a5f" }}>×</span>
                <span style={{ color: "#475569" }}>MACHINE</span>
                <span style={{ color: MACHINE_COLORS[hoverCell.machine] || "#64748b", fontWeight: 500 }}>{hoverCell.machine}</span>
                <span style={{ color: "#475569" }}>FIRST RUN</span>
                <span style={{ color: monthColor(hoverCell.date), fontWeight: 700 }}>{hoverCell.date}</span>
              </div>
            )}
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }}>
              {pairView === "heatmap_mm"   && <HeatmapMoldMachine hoverCell={hoverCell} setHoverCell={setHoverCell} />}
              {pairView === "heatmap_mach" && <HeatmapMachMold    hoverCell={hoverCell} setHoverCell={setHoverCell} />}
              {pairView === "list"         && <PairList monthFilter={monthFilter} />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// DAY LEVEL
// ============================================================
function DayLevel() {
  const [tab,             setTab]             = useState("machine");
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [shiftFilter,     setShiftFilter]     = useState(0);

  const moldRows = DayLevelDataProcessor.moldBasedRecords;
  const itemRows = DayLevelDataProcessor.itemBasedRecords;
  const machines = [...new Set(moldRows.map(r => r.machineInfo))];

  const totalProd = moldRows.reduce((s, r) => s + r.itemTotalQuantity, 0);
  const totalGood = moldRows.reduce((s, r) => s + r.itemGoodQuantity,  0);
  const totalDef  = moldRows.reduce((s, r) => s + r.defectQuantity,    0);
  const overallRate = totalProd > 0 ? (totalDef / totalProd) * 100 : 0;

  function machineStats(machine) {
    const rows    = moldRows.filter(r => r.machineInfo === machine);
    const filtered = shiftFilter === 0 ? rows : rows.filter(r => r.workingShift === shiftFilter);
    const tot  = filtered.reduce((s, r) => s + r.itemTotalQuantity, 0);
    const good = filtered.reduce((s, r) => s + r.itemGoodQuantity,  0);
    const def  = filtered.reduce((s, r) => s + r.defectQuantity,    0);
    const rate = tot > 0 ? (def / tot) * 100 : 0;
    const isIdle = rows.every(r => r.changeType === "machine_idle");
    return { rows, filtered, tot, good, def, rate, isIdle };
  }

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 18 }}>
        <KpiCardB label="TOTAL PRODUCED" value={totalProd.toLocaleString()} color={C.accent}           sub="pcs" />
        <KpiCardB label="GOOD OUTPUT"    value={totalGood.toLocaleString()} color={C.green}            sub="pcs" />
        <KpiCardB label="DEFECTS"        value={totalDef.toLocaleString()}  color={C.orange}           sub="pcs" />
        <KpiCardB label="DEFECT RATE"    value={overallRate.toFixed(2) + "%"} color={defectColor(overallRate)} sub="overall" />
      </div>
      <div style={{ display: "flex", gap: 6, marginBottom: 14, flexWrap: "wrap" }}>
        <PillB label="MACHINE VIEW" active={tab === "machine"} onClick={() => { setTab("machine"); setSelectedMachine(null); }} />
        <PillB label="ITEM VIEW"    active={tab === "item"}    onClick={() => { setTab("item");    setSelectedMachine(null); }} />
        {tab === "machine" && <>
          <span style={{ width: 1, height: 22, background: C.border, alignSelf: "center" }} />
          {[0,1,2,3].map(s => (
            <PillB key={s} label={s === 0 ? "ALL SHIFTS" : `SHIFT ${s}`} active={shiftFilter === s} onClick={() => setShiftFilter(s)} />
          ))}
        </>}
      </div>

      {tab === "machine" && !selectedMachine && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
          {machines.map(m => {
            const { filtered, tot, good, def, rate, isIdle, rows } = machineStats(m);
            const colorBorder = isIdle ? C.border : rate > 15 ? C.red : rate > 5 ? C.orange : C.border;
            return (
              <div key={m} onClick={() => !isIdle && setSelectedMachine(m)}
                style={{ background: C.panel, border: `1px solid ${colorBorder}`, borderRadius: 8, padding: 16, cursor: isIdle ? "default" : "pointer", opacity: isIdle ? .5 : 1, position: "relative", transition: "border-color .2s" }}>
                {isIdle && <span style={{ position: "absolute", top: 10, right: 10, fontSize: 8, background: C.border, color: C.dim, padding: "2px 7px", borderRadius: 3 }}>IDLE</span>}
                {rows.some(r => r.changeType === "color_change") && <span style={{ position: "absolute", top: 10, right: 10, fontSize: 8, background: "#1e3a5f", color: "#93c5fd", padding: "2px 7px", borderRadius: 3 }}>CLR CHG</span>}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div>
                    <div style={{ fontFamily: "'Space Mono',monospace", fontSize: 15, color: "#93c5fd", fontWeight: 700 }}>{m.split(" ")[0]}</div>
                    <div style={{ fontSize: 9, color: C.muted }}>{m.replace(m.split(" ")[0] + " ", "")}</div>
                  </div>
                  <Arc pct={rate} maxRate={30} warn={rate > 20} size={48} />
                </div>
                <div style={{ fontSize: 9, color: C.dim, marginBottom: 10 }}>MOLD: <span style={{ color: C.muted }}>{rows[0]?.moldNo}</span></div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}>
                  {[["TOTAL",tot.toLocaleString(),C.accent],["GOOD",good.toLocaleString(),C.green],["DEFECT",def.toLocaleString(),def>0?C.orange:C.dim]].map(([l,v,c]) => (
                    <div key={l} style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 15, fontWeight: 700, color: c }}>{v}</div>
                      <div style={{ fontSize: 8, color: C.dim, letterSpacing: ".12em" }}>{l}</div>
                    </div>
                  ))}
                </div>
                <div style={{ height: 3, background: C.border, borderRadius: 2, marginTop: 12, overflow: "hidden" }}>
                  <div style={{ width: `${tot > 0 ? (good/tot)*100 : 0}%`, height: "100%", background: C.green, borderRadius: 2, transition: "width .6s" }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {tab === "machine" && selectedMachine && (() => {
        const { tot, good, def, rate } = machineStats(selectedMachine);
        const allRows = moldRows.filter(r => r.machineInfo === selectedMachine);
        return (
          <div>
            <button onClick={() => setSelectedMachine(null)} style={{ background: "transparent", border: `1px solid ${C.border}`, borderRadius: 5, color: C.muted, padding: "5px 12px", cursor: "pointer", fontSize: 11, fontFamily: "'Space Mono',monospace", marginBottom: 14 }}>← BACK</button>
            <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
              <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontFamily: "'Space Mono',monospace", fontSize: 18, color: "#93c5fd", fontWeight: 700 }}>{selectedMachine}</div>
                  <div style={{ fontSize: 9, color: C.muted }}>MOLD: {allRows[0]?.moldNo} · CAVITY: {allRows[0]?.moldCavity ?? "—"}</div>
                </div>
                <Arc pct={rate} maxRate={30} warn={rate > 20} size={52} />
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr style={{ background: "#09111d" }}>
                    {["SHIFT","SHOTS","CAVITY","TOTAL","GOOD","DEFECT","RATE","STATUS"].map(h => (
                      <th key={h} style={{ padding: "8px 14px", textAlign: h==="SHIFT"?"center":"right", fontSize: 8, color: C.dim, letterSpacing: ".14em", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {allRows.map((r, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}` }}>
                      <td style={{ padding: "10px 14px", textAlign: "center" }}>
                        <div style={{ display: "inline-flex", width: 24, height: 24, borderRadius: "50%", background: C.border, color: "#93c5fd", fontSize: 11, alignItems: "center", justifyContent: "center", fontWeight: 700 }}>{r.workingShift}</div>
                      </td>
                      {[r.moldShot, r.moldCavity??"—", r.itemTotalQuantity.toLocaleString(), r.itemGoodQuantity.toLocaleString()].map((v, j) => (
                        <td key={j} style={{ padding: "10px 14px", textAlign: "right", color: C.muted }}>{v}</td>
                      ))}
                      <td style={{ padding: "10px 14px", textAlign: "right", color: r.defectQuantity>0?C.orange:C.dim }}>{r.defectQuantity.toLocaleString()}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: defectColor(r.defectRate), fontWeight: 700 }}>{r.defectRate.toFixed(2)}%</td>
                      <td style={{ padding: "10px 14px", textAlign: "right" }}>
                        <Badge label={r.changeType==="machine_idle"?"IDLE":r.changeType==="color_change"?"CLR CHG":"RUNNING"}
                          color={r.changeType==="machine_idle"?C.dim:r.changeType==="color_change"?"#60a5fa":C.green} />
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ background: "#09111d", borderTop: `1px solid ${C.border}` }}>
                    <td colSpan={3} style={{ padding: "10px 14px", fontSize: 9, color: C.dim }}>TOTAL</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", color: C.accent, fontWeight: 700 }}>{tot.toLocaleString()}</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", color: C.green,  fontWeight: 700 }}>{good.toLocaleString()}</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", color: def>0?C.orange:C.dim, fontWeight: 700 }}>{def.toLocaleString()}</td>
                    <td style={{ padding: "10px 14px", textAlign: "right", color: defectColor(rate), fontWeight: 700 }}>{rate.toFixed(2)}%</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        );
      })()}

      {tab === "item" && (
        <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr style={{ background: "#09111d" }}>
                  {["ITEM CODE","DESCRIPTION","TOTAL","GOOD","DEFECT","DEFECT RATE","SHOTS","CAVITY","SHIFTS"].map(h => (
                    <th key={h} style={{ padding: "9px 14px", textAlign: h==="ITEM CODE"||h==="DESCRIPTION"?"left":"right", fontSize: 8, color: C.dim, letterSpacing: ".14em", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {itemRows.map((r, i) => {
                  const [code, ...rest] = r.itemInfo.split(" ");
                  const name = rest.join(" ").replace(/^\(|\)$/g, "");
                  return (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}`, background: i%2?`#09111d`:"transparent" }}>
                      <td style={{ padding: "9px 14px", color: "#93c5fd", fontWeight: 700 }}>{code}</td>
                      <td style={{ padding: "9px 14px", color: C.muted, fontSize: 10, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right", color: C.text }}>{r.itemTotalQuantity.toLocaleString()}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right", color: C.green }}>{r.itemGoodQuantity.toLocaleString()}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right", color: r.defectQuantity>0?C.orange:C.dim }}>{r.defectQuantity.toLocaleString()}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "flex-end" }}>
                          <div style={{ width: 56, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                            <div style={{ width: `${Math.min(r.defectRate/30*100,100)}%`, height: "100%", background: defectColor(r.defectRate), borderRadius: 2 }} />
                          </div>
                          <span style={{ color: defectColor(r.defectRate), fontWeight: 700, minWidth: 46 }}>{r.defectRate.toFixed(2)}%</span>
                        </div>
                      </td>
                      <td style={{ padding: "9px 14px", textAlign: "right", color: C.muted }}>{r.moldTotalShots.toLocaleString()}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right", color: C.muted }}>{r.avgCavity??"—"}</td>
                      <td style={{ padding: "9px 14px", textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 3, justifyContent: "flex-end" }}>
                          {[1,2,3].map(s => <div key={s} style={{ width: 9, height: 9, borderRadius: 2, background: r.totalShifts>=s?C.accent:C.border }} />)}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// MONTH LEVEL
// ============================================================
function MonthLevel() {
  const [statusF,  setStatusF]  = useState("all");
  const [etaF,     setEtaF]     = useState("all");
  const [search,   setSearch]   = useState("");
  const [sortK,    setSortK]    = useState("poNo");
  const [sortD,    setSortD]    = useState("asc");
  const [selected, setSelected] = useState(null);

  const allRecs = useMemo(() => [
    ...MonthLevelDataProcessor.finishedRecords.map(r  => ({ ...r, category: "finished",   completionProgress: 1.0 })),
    ...MonthLevelDataProcessor.unfinishedRecords.map(r => ({ ...r, category: "unfinished" })),
  ], []);

  const stats = useMemo(() => {
    const fin  = MonthLevelDataProcessor.finishedRecords.length;
    const inP  = MonthLevelDataProcessor.unfinishedRecords.filter(r => r.poStatus === "in_progress").length;
    const ns   = MonthLevelDataProcessor.unfinishedRecords.filter(r => r.poStatus === "not_started").length;
    const crit = MonthLevelDataProcessor.unfinishedRecords.filter(r => r.capacitySeverity === "critical").length;
    const od   = MonthLevelDataProcessor.unfinishedRecords.filter(r => r.is_overdue).length;
    const totalQty = allRecs.reduce((s, r) => s + (r.itemQuantity || 0), 0);
    return { fin, inP, ns, crit, od, totalQty };
  }, [allRecs]);

  const filtered = useMemo(() => {
    let d = allRecs;
    if (statusF !== "all") d = d.filter(r => r.poStatus === statusF);
    if (etaF    !== "all") d = d.filter(r => r.etaStatus === etaF);
    if (search) { const q = search.toLowerCase(); d = d.filter(r => r.poNo?.toLowerCase().includes(q) || r.itemName?.toLowerCase().includes(q) || r.itemCode?.toLowerCase().includes(q)); }
    return [...d].sort((a, b) => {
      let av = a[sortK] ?? "", bv = b[sortK] ?? "";
      if (typeof av === "string") av = av.toLowerCase();
      if (typeof bv === "string") bv = bv.toLowerCase();
      return sortD === "asc" ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
    });
  }, [allRecs, statusF, etaF, search, sortK, sortD]);

  const TS = ({ k, label }) => (
    <th onClick={() => { if (sortK === k) setSortD(d => d === "asc" ? "desc" : "asc"); else { setSortK(k); setSortD("asc"); } }}
      style={{ padding: "8px 12px", textAlign: "left", fontSize: 8, color: sortK === k ? "#93c5fd" : C.dim, letterSpacing: ".15em", borderBottom: `1px solid ${C.border}`, background: "#09111d", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap" }}>
      {label}{sortK === k ? (sortD === "asc" ? " ▲" : " ▼") : <span style={{ color: C.border }}> ⬦</span>}
    </th>
  );

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 10, marginBottom: 18 }}>
        <KpiCardB label="FINISHED"    value={stats.fin}  color={C.green}  sub="completed" />
        <KpiCardB label="IN PROGRESS" value={stats.inP}  color={C.accent} sub="active" />
        <KpiCardB label="NOT STARTED" value={stats.ns}   color={C.yellow} sub="pending" />
        <KpiCardB label="CRITICAL"    value={stats.crit} color={C.orange} sub="over capacity" />
        <KpiCardB label="OVERDUE"     value={stats.od}   color={C.red}    sub="past ETA" />
        <KpiCardB label="TOTAL QTY"   value={(stats.totalQty/1000).toFixed(0)+"K"} color="#a78bfa" sub="units" />
      </div>
      <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: "11px 14px", marginBottom: 14, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        <input placeholder="SEARCH PO / CODE / NAME..." value={search} onChange={e => setSearch(e.target.value)}
          style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 5, padding: "5px 12px", fontSize: 10, color: C.text, outline: "none", fontFamily: "'Space Mono',monospace", minWidth: 220 }} />
        <div style={{ width: 1, height: 20, background: C.border }} />
        {[["all","ALL"],["finished","FINISHED"],["in_progress","IN PROG"],["not_started","NOT STARTED"]].map(([v,l]) => (
          <PillB key={v} label={l} active={statusF === v} onClick={() => setStatusF(v)} />
        ))}
        <div style={{ width: 1, height: 20, background: C.border }} />
        {[["all","ALL ETA"],["ontime","ON TIME"],["late","LATE"],["expected_ontime","EXPECTED"]].map(([v,l]) => (
          <PillB key={v} label={l} active={etaF === v} onClick={() => setEtaF(v)} danger={v==="late"} />
        ))}
        <span style={{ marginLeft: "auto", fontSize: 9, color: C.dim }}>{filtered.length} RECORDS</span>
      </div>
      <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr>
                <TS k="poNo" label="PO NO" /><TS k="itemCode" label="CODE" /><TS k="itemName" label="ITEM NAME" />
                <TS k="poETA" label="ETA" /><TS k="poStatus" label="STATUS" /><TS k="etaStatus" label="ETA STATUS" />
                <TS k="itemQuantity" label="ORDER QTY" /><TS k="itemGoodQuantity" label="GOOD QTY" />
                <TS k="itemRemainQuantity" label="REMAIN" />
                <th style={{ padding: "8px 12px", fontSize: 8, color: C.dim, letterSpacing: ".15em", borderBottom: `1px solid ${C.border}`, background: "#09111d", textAlign: "center" }}>PROGRESS</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, i) => (
                <tr key={r.poNo+i} onClick={() => setSelected(selected?.poNo === r.poNo ? null : r)}
                  style={{ borderBottom: `1px solid ${C.border}`, background: i%2?"#09111d":"transparent", cursor: "pointer" }}>
                  <td style={{ padding: "9px 12px", fontWeight: 700, color: "#93c5fd", whiteSpace: "nowrap" }}>
                    {r.is_backlog && <span style={{ color: C.yellow, marginRight: 4 }}>★</span>}{r.poNo}
                  </td>
                  <td style={{ padding: "9px 12px", color: C.dim, fontSize: 10 }}>{r.itemCode}</td>
                  <td style={{ padding: "9px 12px", color: C.muted, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                  <td style={{ padding: "9px 12px", color: C.dim, fontSize: 10, whiteSpace: "nowrap" }}>{r.poETA}</td>
                  <td style={{ padding: "9px 12px" }}><Badge label={r.poStatus?.replace("_"," ").toUpperCase()} color={statusColor(r.poStatus)} /></td>
                  <td style={{ padding: "9px 12px" }}><Badge label={r.etaStatus==="expected_ontime"?"EXP ON-TIME":r.etaStatus?.toUpperCase()} color={etaColor(r.etaStatus)} /></td>
                  <td style={{ padding: "9px 12px", textAlign: "right", color: C.accent }}>{(r.itemQuantity||0).toLocaleString()}</td>
                  <td style={{ padding: "9px 12px", textAlign: "right", color: C.green }}>{r.itemGoodQuantity!=null?r.itemGoodQuantity.toLocaleString():"—"}</td>
                  <td style={{ padding: "9px 12px", textAlign: "right", color: (r.itemRemainQuantity||0)>0?C.yellow:C.dim }}>{(r.itemRemainQuantity||0).toLocaleString()}</td>
                  <td style={{ padding: "6px 12px", textAlign: "center" }}><Arc pct={r.completionProgress||0} warn={r.capacityWarning} size={42} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {selected && (
        <div style={{ marginTop: 14, background: C.panel, border: `1px solid ${selected.is_overdue?C.red+"55":C.border}`, borderRadius: 8, padding: "20px 22px", borderTop: `3px solid ${selected.is_overdue?C.red:selected.poStatus==="finished"?C.green:C.accent}` }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontFamily: "'Space Mono',monospace", fontSize: 20, color: "#93c5fd", fontWeight: 700 }}>{selected.poNo}</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 3 }}>{selected.itemName} <span style={{ color: C.dim }}>({selected.itemCode})</span></div>
            </div>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <Arc pct={selected.completionProgress||0} warn={selected.capacityWarning} size={56} />
              <button onClick={() => setSelected(null)} style={{ background: "transparent", border: `1px solid ${C.border}`, borderRadius: 5, color: C.muted, padding: "5px 12px", cursor: "pointer", fontSize: 11, fontFamily: "'Space Mono',monospace" }}>✕ CLOSE</button>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(148px,1fr))", gap: 8 }}>
            {[["PO RECEIVED",selected.poReceivedDate],["ETA DATE",selected.poETA],["FIRST RECORD",selected.firstRecord||"NOT STARTED"],["LAST RECORD",selected.lastRecord||"—"],["ORDER QTY",(selected.itemQuantity||0).toLocaleString()],["GOOD QTY",selected.itemGoodQuantity!=null?selected.itemGoodQuantity.toLocaleString():"—"],["NG QTY",selected.itemNGQuantity!=null?selected.itemNGQuantity.toLocaleString():"—"],["REMAIN QTY",(selected.itemRemainQuantity||0).toLocaleString()],["MOLD",selected.moldHist||"—"],["CAPACITY",selected.capacitySeverity?.toUpperCase()||"—"],["EST. LEAD TIME",selected.totalEstimatedLeadtime!=null?selected.totalEstimatedLeadtime.toFixed(2)+"d":"—"],["BACKLOG",selected.is_backlog?"YES ★":"NO"]].map(([l,v]) => (
              <div key={l} style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: "10px 12px" }}>
                <div style={{ fontSize: 8, color: C.dim, letterSpacing: ".14em", marginBottom: 4 }}>{l}</div>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.muted }}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// YEAR LEVEL
// ============================================================
function YearLevel() {
  const [view,     setView]     = useState("table");
  const [statusF,  setStatusF]  = useState("all");
  const [etaF,     setEtaF]     = useState("all");
  const [search,   setSearch]   = useState("");
  const [sortK,    setSortK]    = useState("poNo");
  const [sortD,    setSortD]    = useState("asc");
  const [selected, setSelected] = useState(null);

  const allRecs = useMemo(() => [
    ...YearLevelDataProcessor.finishedRecords.map(r  => ({ ...r, category: "finished",   completionProgress: 1.0 })),
    ...YearLevelDataProcessor.unfinishedRecords.map(r => ({ ...r, category: "unfinished" })),
  ], []);

  function calcNgRate(r) {
    const tot = (r.itemGoodQuantity || 0) + (r.itemNGQuantity || 0);
    if (!r.itemNGQuantity || tot === 0) return 0;
    return (r.itemNGQuantity / tot) * 100;
  }

  const stats = useMemo(() => {
    const fin  = YearLevelDataProcessor.finishedRecords.length;
    const inP  = YearLevelDataProcessor.unfinishedRecords.filter(r => r.poStatus === "in_progress").length;
    const ns   = YearLevelDataProcessor.unfinishedRecords.filter(r => r.poStatus === "not_started").length;
    const crit = YearLevelDataProcessor.unfinishedRecords.filter(r => r.capacitySeverity === "critical").length;
    const od   = YearLevelDataProcessor.unfinishedRecords.filter(r => r.is_overdue).length;
    const totalQty  = allRecs.reduce((s, r) => s + (r.itemQuantity || 0), 0);
    const totalNG   = YearLevelDataProcessor.finishedRecords.reduce((s, r) => s + (r.itemNGQuantity || 0), 0);
    const totalGood = YearLevelDataProcessor.finishedRecords.reduce((s, r) => s + (r.itemGoodQuantity || 0), 0);
    const avgNGRate = totalGood + totalNG > 0 ? (totalNG / (totalGood + totalNG)) * 100 : 0;
    return { fin, inP, ns, crit, od, totalQty, avgNGRate };
  }, [allRecs]);

  const filtered = useMemo(() => {
    let d = allRecs;
    if (statusF !== "all") d = d.filter(r => r.poStatus === statusF);
    if (etaF    !== "all") d = d.filter(r => r.etaStatus === etaF);
    if (search) { const q = search.toLowerCase(); d = d.filter(r => r.poNo?.toLowerCase().includes(q) || r.itemName?.toLowerCase().includes(q) || r.itemCode?.toLowerCase().includes(q)); }
    return [...d].sort((a, b) => {
      let av = a[sortK] ?? "", bv = b[sortK] ?? "";
      if (typeof av === "string") av = av.toLowerCase();
      if (typeof bv === "string") bv = bv.toLowerCase();
      return sortD === "asc" ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
    });
  }, [allRecs, statusF, etaF, search, sortK, sortD]);

  const ngChart = useMemo(() => {
    return [...YearLevelDataProcessor.finishedRecords]
      .filter(r => r.itemNGQuantity > 0)
      .map(r => ({ ...r, ngRate: calcNgRate(r) }))
      .sort((a, b) => b.ngRate - a.ngRate)
      .slice(0, 12);
  }, []);
  const maxNG = Math.max(...ngChart.map(d => d.itemNGQuantity));

  const TS = ({ k, label }) => (
    <th onClick={() => { if (sortK === k) setSortD(d => d === "asc" ? "desc" : "asc"); else { setSortK(k); setSortD("asc"); } }}
      style={{ padding: "8px 12px", textAlign: "left", fontSize: 8, color: sortK === k ? "#93c5fd" : C.dim, letterSpacing: ".15em", borderBottom: `1px solid ${C.border}`, background: "#09111d", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap" }}>
      {label}{sortK === k ? (sortD === "asc" ? " ▲" : " ▼") : <span style={{ color: C.border }}> ⬦</span>}
    </th>
  );

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 10, marginBottom: 18 }}>
        <KpiCardB label="FINISHED"    value={stats.fin}  color={C.green}  sub="completed" />
        <KpiCardB label="IN PROGRESS" value={stats.inP}  color={C.accent} sub="active" />
        <KpiCardB label="NOT STARTED" value={stats.ns}   color={C.yellow} sub="pending" />
        <KpiCardB label="CRITICAL"    value={stats.crit} color={C.orange} sub="over capacity" />
        <KpiCardB label="OVERDUE"     value={stats.od}   color={C.red}    sub="past ETA" />
        <KpiCardB label="TOTAL QTY"   value={(stats.totalQty/1000).toFixed(0)+"K"} color="#a78bfa" sub="units" />
        <KpiCardB label="AVG NG RATE" value={stats.avgNGRate.toFixed(1)+"%"} color={ngColor(stats.avgNGRate)} sub="finished POs" />
      </div>
      <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: "11px 14px", marginBottom: 14, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        <PillB label="TABLE"       active={view === "table"} onClick={() => setView("table")} />
        <PillB label="NG ANALYSIS" active={view === "ng"}    onClick={() => setView("ng")} />
        {view === "table" && <>
          <div style={{ width: 1, height: 20, background: C.border }} />
          <input placeholder="SEARCH PO / CODE / NAME..." value={search} onChange={e => setSearch(e.target.value)}
            style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 5, padding: "5px 12px", fontSize: 10, color: C.text, outline: "none", fontFamily: "'Space Mono',monospace", minWidth: 220 }} />
          <div style={{ width: 1, height: 20, background: C.border }} />
          {[["all","ALL"],["finished","FINISHED"],["in_progress","IN PROG"],["not_started","NOT STARTED"]].map(([v,l]) => (
            <PillB key={v} label={l} active={statusF === v} onClick={() => setStatusF(v)} />
          ))}
          <div style={{ width: 1, height: 20, background: C.border }} />
          {[["all","ALL ETA"],["ontime","ON TIME"],["late","LATE"],["expected_ontime","EXPECTED"]].map(([v,l]) => (
            <PillB key={v} label={l} active={etaF === v} onClick={() => setEtaF(v)} danger={v==="late"} />
          ))}
          <span style={{ marginLeft: "auto", fontSize: 9, color: C.dim }}>{filtered.length} ROWS</span>
        </>}
      </div>

      {view === "table" && (
        <>
          <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr>
                    <TS k="poNo" label="PO NO" /><TS k="itemCode" label="CODE" /><TS k="itemName" label="ITEM NAME" />
                    <TS k="poETA" label="ETA" /><TS k="poStatus" label="STATUS" /><TS k="etaStatus" label="ETA STATUS" />
                    <TS k="itemQuantity" label="ORDER QTY" /><TS k="itemGoodQuantity" label="GOOD QTY" />
                    <TS k="itemNGQuantity" label="NG QTY" />
                    <th style={{ padding: "8px 12px", fontSize: 8, color: C.dim, letterSpacing: ".15em", borderBottom: `1px solid ${C.border}`, background: "#09111d", textAlign: "center" }}>PROGRESS</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r, i) => {
                    const nr = calcNgRate(r);
                    return (
                      <tr key={r.poNo+i} onClick={() => setSelected(selected?.poNo === r.poNo ? null : r)}
                        style={{ borderBottom: `1px solid ${C.border}`, background: i%2?"#09111d":"transparent", cursor: "pointer" }}>
                        <td style={{ padding: "9px 12px", fontWeight: 700, color: "#93c5fd", whiteSpace: "nowrap" }}>
                          {r.is_backlog && <span style={{ color: C.yellow, marginRight: 4 }}>★</span>}{r.poNo}
                        </td>
                        <td style={{ padding: "9px 12px", color: C.dim, fontSize: 10 }}>{r.itemCode}</td>
                        <td style={{ padding: "9px 12px", color: C.muted, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                        <td style={{ padding: "9px 12px", color: C.dim, fontSize: 10, whiteSpace: "nowrap" }}>{r.poETA}</td>
                        <td style={{ padding: "9px 12px" }}><Badge label={r.poStatus?.replace("_"," ").toUpperCase()} color={statusColor(r.poStatus)} /></td>
                        <td style={{ padding: "9px 12px" }}><Badge label={r.etaStatus==="expected_ontime"?"EXP ON-TIME":r.etaStatus?.toUpperCase()} color={etaColor(r.etaStatus)} /></td>
                        <td style={{ padding: "9px 12px", textAlign: "right", color: C.accent }}>{(r.itemQuantity||0).toLocaleString()}</td>
                        <td style={{ padding: "9px 12px", textAlign: "right", color: C.green }}>{r.itemGoodQuantity!=null?r.itemGoodQuantity.toLocaleString():"—"}</td>
                        <td style={{ padding: "9px 12px", textAlign: "right", color: ngColor(nr) }}>{r.itemNGQuantity!=null?r.itemNGQuantity.toLocaleString():"—"}</td>
                        <td style={{ padding: "6px 12px", textAlign: "center" }}><Arc pct={r.completionProgress||0} warn={r.capacityWarning} size={40} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          {selected && (
            <div style={{ marginTop: 14, background: C.panel, border: `1px solid ${selected.is_overdue?C.red+"55":C.border}`, borderRadius: 8, padding: "20px 22px", borderTop: `3px solid ${selected.is_overdue?C.red:selected.poStatus==="finished"?C.green:C.accent}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                <div>
                  <div style={{ fontFamily: "'Space Mono',monospace", fontSize: 20, color: "#93c5fd", fontWeight: 700 }}>{selected.poNo}</div>
                  <div style={{ fontSize: 11, color: C.muted, marginTop: 3 }}>{selected.itemName} <span style={{ color: C.dim }}>({selected.itemCode})</span></div>
                </div>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                  <Arc pct={selected.completionProgress||0} warn={selected.capacityWarning} size={54} />
                  <button onClick={() => setSelected(null)} style={{ background: "transparent", border: `1px solid ${C.border}`, borderRadius: 5, color: C.muted, padding: "5px 12px", cursor: "pointer", fontSize: 11, fontFamily: "'Space Mono',monospace" }}>✕ CLOSE</button>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(145px,1fr))", gap: 8 }}>
                {[["PO RECEIVED",selected.poReceivedDate],["ETA DATE",selected.poETA],["FIRST RECORD",selected.firstRecord||"NOT STARTED"],["LAST RECORD",selected.lastRecord||"—"],["ORDER QTY",(selected.itemQuantity||0).toLocaleString()],["GOOD QTY",selected.itemGoodQuantity!=null?selected.itemGoodQuantity.toLocaleString():"—"],["NG QTY",selected.itemNGQuantity!=null?selected.itemNGQuantity.toLocaleString():"—"],["NG RATE",calcNgRate(selected).toFixed(2)+"%"],["REMAIN QTY",(selected.itemRemainQuantity||0).toLocaleString()],["MOLD",selected.moldHist||selected.moldList||"—"],["CAPACITY",selected.capacitySeverity?.toUpperCase()||"—"],["EST. LEAD TIME",selected.totalEstimatedLeadtime!=null?selected.totalEstimatedLeadtime.toFixed(2)+"d":"—"],["BACKLOG",selected.is_backlog?"YES ★":"NO"],["OVERDUE",selected.is_overdue?"YES ⚠":"NO"]].map(([l,v]) => (
                  <div key={l} style={{ background: C.bg, border: `1px solid ${C.border}`, borderRadius: 6, padding: "10px 12px" }}>
                    <div style={{ fontSize: 8, color: C.dim, letterSpacing: ".14em", marginBottom: 4 }}>{l}</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: C.muted }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {view === "ng" && (
        <div>
          <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, padding: "20px 22px", marginBottom: 14 }}>
            <div style={{ fontSize: 9, color: C.dim, letterSpacing: ".2em", marginBottom: 16 }}>TOP NG RATE — FINISHED POs</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {ngChart.map((d, i) => {
                const color = ngColor(d.ngRate);
                return (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "150px 1fr 90px 56px", gap: 12, alignItems: "center" }}>
                    <div style={{ fontSize: 9, color: C.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.poNo} <span style={{ color: C.dim, fontSize: 8 }}>{d.itemName.slice(0,18)}</span></div>
                    <div style={{ background: C.bg, borderRadius: 3, height: 8, overflow: "hidden" }}>
                      <div style={{ width: `${(d.itemNGQuantity/maxNG)*100}%`, height: "100%", background: color, borderRadius: 3, transition: "width .5s ease" }} />
                    </div>
                    <div style={{ textAlign: "right", fontSize: 10, color: C.muted }}>{d.itemNGQuantity.toLocaleString()} ng</div>
                    <div style={{ textAlign: "right", fontSize: 11, color, fontWeight: 700 }}>{d.ngRate.toFixed(1)}%</div>
                  </div>
                );
              })}
            </div>
          </div>
          <div style={{ background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr>
                    {["PO NO","ITEM NAME","ORDER QTY","GOOD QTY","NG QTY","NG RATE","MOLD","ETA STATUS"].map(h => (
                      <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontSize: 8, color: C.dim, letterSpacing: ".14em", borderBottom: `1px solid ${C.border}`, background: "#09111d", whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...YearLevelDataProcessor.finishedRecords].sort((a,b) => calcNgRate(b)-calcNgRate(a)).map((r,i) => {
                    const nr = calcNgRate(r);
                    return (
                      <tr key={i} style={{ borderBottom: `1px solid ${C.border}`, background: i%2?"#09111d":"transparent" }}>
                        <td style={{ padding: "8px 12px", color: "#93c5fd", fontWeight: 700, fontSize: 10 }}>{r.poNo}</td>
                        <td style={{ padding: "8px 12px", color: C.muted, fontSize: 10, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                        <td style={{ padding: "8px 12px", textAlign: "right", color: C.accent }}>{r.itemQuantity.toLocaleString()}</td>
                        <td style={{ padding: "8px 12px", textAlign: "right", color: C.green }}>{r.itemGoodQuantity.toLocaleString()}</td>
                        <td style={{ padding: "8px 12px", textAlign: "right", color: ngColor(nr) }}>{(r.itemNGQuantity||0).toLocaleString()}</td>
                        <td style={{ padding: "8px 12px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <div style={{ width: 52, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
                              <div style={{ width: `${Math.min(nr/30*100,100)}%`, height: "100%", background: ngColor(nr), borderRadius: 2 }} />
                            </div>
                            <span style={{ color: ngColor(nr), fontWeight: 700, minWidth: 42 }}>{nr.toFixed(2)}%</span>
                          </div>
                        </td>
                        <td style={{ padding: "8px 12px", color: C.dim, fontSize: 9 }}>{r.moldHist||"—"}</td>
                        <td style={{ padding: "8px 12px" }}><Badge label={r.etaStatus==="ontime"?"ON TIME":r.etaStatus?.toUpperCase()} color={etaColor(r.etaStatus)} /></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// APP2 — Production Intelligence
// ============================================================
function App2() {
  const [level, setLevel] = useState("day");
  const LEVELS = [
    { id: "day",   label: "DAY",   sub: "Machine & Item" },
    { id: "month", label: "MONTH", sub: "PO Tracking"    },
    { id: "year",  label: "YEAR",  sub: "PO + NG Analysis" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.text, fontFamily: "'Space Mono','Courier New',monospace" }}>
      <div style={{ background: "#060810", borderBottom: `1px solid ${C.border}`, padding: "0 28px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 54 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ display: "flex", gap: 3 }}>
              {[C.red, C.orange, C.green].map((c, i) => (
                <div key={i} style={{ width: 4, height: 24 + i * 6, background: c, borderRadius: 2, opacity: 0.85 }} />
              ))}
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: ".14em", color: C.textBright }}>PRODUCTION INTELLIGENCE</div>
              <div style={{ fontSize: 8, color: C.dim, letterSpacing: ".22em" }}>DAILY · MONTHLY · YEARLY ANALYSIS</div>
            </div>
          </div>
          <div style={{ display: "flex", background: C.panel, border: `1px solid ${C.border}`, borderRadius: 8, overflow: "hidden" }}>
            {LEVELS.map(l => (
              <button key={l.id} onClick={() => setLevel(l.id)} style={{
                background: level === l.id ? C.accent+"22" : "transparent",
                borderRight: `1px solid ${C.border}`, border: "none",
                borderLeft: "none", padding: "0 20px", cursor: "pointer",
                borderBottom: level === l.id ? `2px solid ${C.accent}` : "2px solid transparent",
                transition: "all .15s",
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: level===l.id?"#93c5fd":C.muted, letterSpacing: ".1em" }}>{l.label}</div>
                <div style={{ fontSize: 8, color: C.dim, letterSpacing: ".1em" }}>{l.sub}</div>
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: C.green, boxShadow: `0 0 8px ${C.green}` }} className="pulse" />
            <span style={{ fontSize: 9, color: C.dim, letterSpacing: ".12em" }}>LIVE · {LIVE_DATE}</span>
          </div>
        </div>
      </div>
      <div style={{ padding: "22px 28px" }} className="fade" key={level}>
        {level === "day"   && <DayLevel />}
        {level === "month" && <MonthLevel />}
        {level === "year"  && <YearLevel />}
      </div>
    </div>
  );
}

// ============================================================
// AnalyticsViz
// ============================================================
export default function AnalyticsViz({ data }) {
  const source = USE_MOCK ? MOCK_DATA : data;

  layout                  = source.MachineLayoutTracker.machineLayoutChange;
  machineMoldFirstRunPair = source.MoldMachinePairTracker.machineMoldFirstRunPair;
  moldMachineFirstRunPair = source.MoldMachinePairTracker.moldMachineFirstRunPair;
  DayLevelDataProcessor   = source.DayLevelDataProcessor;
  MonthLevelDataProcessor = source.MonthLevelDataProcessor;
  YearLevelDataProcessor  = source.YearLevelDataProcessor;

  // ============================================================
  // DERIVED DATA
  // ============================================================

  const fmt = (d) => new Date(d).toLocaleDateString("en-US", { month: "short", year: "numeric" }).toUpperCase();

  ([DATE_A, DATE_B] = Object.keys(layout[0]).filter(k => k !== "machineName" && k !== "machineCode"));
  PERIOD_LABEL = `${fmt(DATE_A)} — ${fmt(DATE_B)}`;
  LIVE_DATE = DATE_B;
  activeSlots = new Set(layout.map(r => r[DATE_B]).filter(Boolean));
  TOTAL_SLOTS = activeSlots.size;
  allSlots = Array.from({ length: TOTAL_SLOTS },(_, i) => `NO.${String(i + 1).padStart(2, "0")}`);
  layoutMachines = layout.map(m => ({
    name:      m.machineName,
    code:      m.machineCode,
    posA:      m[DATE_A],
    posB:      m[DATE_B],
    isNew:     m[DATE_A] === null,
    moved:     m[DATE_A] !== null && m[DATE_A] !== m[DATE_B],
    unchanged: m[DATE_A] !== null && m[DATE_A] === m[DATE_B],
  }));

  moldKeys    = Object.keys(machineMoldFirstRunPair[0]);
  machineKeys = Object.keys(moldMachineFirstRunPair[0]);
  moldMachineMatrix = moldMachineFirstRunPair.map(row => machineKeys.map(m => (row[m] !== "NaT" ? row[m] : null)));
  machineRunCounts = machineKeys.map((_, mi) => moldMachineMatrix.reduce((s, row) => s + (row[mi] !== null ? 1 : 0), 0));
  moldRunCounts = moldKeys.map((_, di) => machineMoldFirstRunPair.reduce(
    (s, row) => s + (row[moldKeys[di]] !== "NaT" ? 1 : 0), 0));
  totalPairs = moldMachineMatrix.reduce((s, row) => s + row.filter(v => v !== null).length, 0);

  const [activeApp, setActiveApp] = useState("layout");
  const apps = [
    { id: "layout",     label: "FLOOR OPS",   sub: "Layout · Pairing",    icon: "▣" },
    { id: "production", label: "PRODUCTION",  sub: "Day · Month · Year",  icon: "◈" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#020508", fontFamily: "monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&family=Space+Mono:wght@400;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        .pill { background: transparent; border: 1px solid #1e3a5f; border-radius: 4px; color: #64748b; padding: 5px 12px; cursor: pointer; font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.08em; transition: all 0.15s; }
        .pill.active { background: #1d4ed8; border-color: #2563eb; color: #fff; }
        .pill:hover:not(.active) { border-color: #334155; color: #94a3b8; }
        .mod-btn { background: transparent; border: 1px solid #1e3a5f; border-radius: 6px; color: #475569; padding: 8px 20px; cursor: pointer; font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.1em; transition: all 0.2s; }
        .mod-btn.active { background: #0c1a2e; border-color: #2563eb; color: #60a5fa; box-shadow: 0 0 12px #2563eb33; }
        .mod-btn:hover:not(.active) { border-color: #334155; color: #64748b; }
        .type-btn { background: transparent; border: 1px solid; border-radius: 4px; padding: 4px 12px; cursor: pointer; font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.08em; transition: all 0.15s; }
        tr:hover td { background: #06111e !important; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
        .fade-up { animation: fadeUp 0.25s ease forwards; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
        .fade { animation: fadeIn 0.3s ease forwards; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0.3} }
        .blink { animation: blink 1.6s ease-in-out infinite; }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.35} }
        .pulse { animation: pulse 2s ease-in-out infinite; }
        input::placeholder { color: #374151; }
        button:hover { opacity: 0.85; }
      `}</style>

      {/* ── MASTER NAV ── */}
      <div style={{
        background: "linear-gradient(90deg, #060810 0%, #0a0f18 100%)",
        borderBottom: "1px solid #1e2a3a", padding: "0 28px",
        display: "flex", alignItems: "center", gap: 0,
        height: 48, position: "sticky", top: 0, zIndex: 100, backdropFilter: "blur(8px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginRight: 32 }}>
          <div style={{ display: "flex", gap: 2, alignItems: "flex-end" }}>
            {["#3b82f6","#a78bfa","#10b981"].map((c,i) => (
              <div key={i} style={{ width: 3, height: 12+i*5, background: c, borderRadius: 2 }} />
            ))}
          </div>
          <span style={{ fontSize: 11, letterSpacing: "0.2em", color: "#475569", fontFamily: "'DM Mono',monospace" }}>
            MFG<span style={{ color: "#3b82f6" }}>·</span>OPS
          </span>
        </div>
        <div style={{ display: "flex", height: "100%", gap: 0 }}>
          {apps.map(app => (
            <button key={app.id} onClick={() => setActiveApp(app.id)} style={{
              background: "transparent", border: "none",
              borderBottom: activeApp === app.id ? "2px solid #3b82f6" : "2px solid transparent",
              borderTop: "2px solid transparent", padding: "0 20px",
              cursor: "pointer", display: "flex", alignItems: "center", gap: 8, transition: "all .15s",
            }}>
              <span style={{ fontSize: 14, color: activeApp === app.id ? "#60a5fa" : "#334155" }}>{app.icon}</span>
              <div style={{ textAlign: "left" }}>
                <div style={{ fontSize: 10, fontFamily: "'DM Mono',monospace", letterSpacing: "0.1em", color: activeApp === app.id ? "#93c5fd" : "#475569", fontWeight: 700 }}>{app.label}</div>
                <div style={{ fontSize: 8, color: "#1e3a5f", letterSpacing: "0.1em" }}>{app.sub}</div>
              </div>
            </button>
          ))}
        </div>
        <div style={{ marginLeft: "auto", fontSize: 9, color: "#1e3a5f", letterSpacing: "0.15em", fontFamily: "'DM Mono',monospace" }}>
          {PERIOD_LABEL}
        </div>
      </div>

      {/* ── APP CONTENT ── */}
      <div key={activeApp} style={{ animation: "fadeIn 0.2s ease forwards" }}>
        {activeApp === "layout"     && <App1 />}
        {activeApp === "production" && <App2 />}
      </div>
    </div>
  );
}