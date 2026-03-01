import { useState, useMemo } from "react";
import {STATUS_CFG, ETA_CFG, PO_COLS, GANTT_COLORS, COL_W} from "./config.js";
import { DATA as MOCK_DATA } from "./data.js";

const USE_MOCK = false;

let DAILY_JSON, PO_JSON;
let TODAY, todayDate, ganttStart, GANTT_START, GANTT_DAYS, REPORT_DATE;
let MACHINE_COUNT, ALL_MACHINES, DATA_MAP, FULL_DATA;
let GANTT_DATES, TODAY_D;
let MACHINE_JOBS_MAP;

// ============================================================
//  ⚙️  SHARED UTILS
// ============================================================
function progColor(p) {
  if (p === null || p === undefined) return "#2a3245";
  if (p >= 90) return "#10b981";
  if (p >= 60) return "#3b82f6";
  if (p >= 30) return "#f59e0b";
  return "#ef4444";
}
function fmt(n) { return (n || 0).toLocaleString(); }
function fmtNum(n) {
  if (!n && n !== 0) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + "K";
  return String(n);
}
function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d)) return "—";
  return `${String(d.getMonth()+1).padStart(2,"0")}/${String(d.getDate()).padStart(2,"0")}/${d.getFullYear()}`;
}
function parseD(s) {
  if (!s || s === "—") return null;
  const parts = s.split("-");
  if (parts[0].length === 4) return new Date(+parts[0], +parts[1]-1, +parts[2]);
  return new Date(+parts[2], +parts[0]-1, +parts[1]);
}
function parseConfigDate(s) {
  if (!s) return new Date();
  const parts = s.split("-");
  if (parts[0].length === 4) return new Date(+parts[0], +parts[1]-1, +parts[2]);
  return new Date(+parts[2], +parts[0]-1, +parts[1]);
}
function genDates(startDate, n) {
  const out = []; const dt = new Date(startDate);
  for (let i = 0; i < n; i++) { out.push(new Date(dt)); dt.setDate(dt.getDate()+1); }
  return out;
}

// ============================================================
//  PO DETAIL PANEL
// ============================================================
function DetailPanel({ row }) {
  const cfg = STATUS_CFG[row.proStatus] || STATUS_CFG.PENDING;
  const dayEntries   = Object.entries(row.dayQuantityMap   || {});
  const shiftEntries = Object.entries(row.shiftQuantityMap || {});
  const machEntries  = Object.entries(row.machineQuantityMap || {});
  const maxDay   = Math.max(...dayEntries.map(([,v]) => v), 1);
  const maxShift = Math.max(...shiftEntries.map(([,v]) => v), 1);

  const Section = ({ title, children, accent="#3b82f6" }) => (
    <div style={{ marginBottom:10 }}>
      <div style={{ fontSize:8, color:accent, letterSpacing:"0.1em", fontWeight:600, borderBottom:`1px solid ${accent}25`, paddingBottom:3, marginBottom:6, textTransform:"uppercase" }}>{title}</div>
      {children}
    </div>
  );
  const KV = ({ k, v, vc }) => (
    <div style={{ display:"flex", justifyContent:"space-between", gap:8, marginBottom:3 }}>
      <span style={{ fontSize:9, color:"#4a6a8a", whiteSpace:"nowrap" }}>{k}</span>
      <span style={{ fontSize:9, color:vc||"#c9d1e0", fontWeight:500, textAlign:"right" }}>{v||"—"}</span>
    </div>
  );
  const Tag = ({ v, c }) => (
    <span style={{ display:"inline-block", padding:"1px 6px", borderRadius:2, background:`${c||"#3b82f6"}18`, border:`1px solid ${c||"#3b82f6"}30`, color:c||"#3b82f6", fontSize:9, marginRight:4, marginBottom:3 }}>{v}</span>
  );

  return (
    <tr style={{ background:"#080e1a" }}>
      <td colSpan={PO_COLS.length} style={{ padding:0, borderBottom:"2px solid #1e3a5f" }}>
        <div style={{ padding:"12px 14px 12px 36px", display:"grid", gridTemplateColumns:"200px 200px 1fr 1fr", gap:"0 20px", borderLeft:`3px solid ${cfg.color}` }}>
          <div>
            <Section title="Production Info" accent={cfg.color}>
              <KV k="Item Type"    v={row.itemType} />
              <KV k="PO Received"  v={fmtDate(row.poReceivedDate)} />
              <KV k="Total Days"   v={row.totalDay   ? `${row.totalDay} day${row.totalDay>1?"s":""}` : "—"} />
              <KV k="Total Shifts" v={row.totalShift ? `${row.totalShift} shifts` : "—"} />
              <KV k="Total Shots"  v={row.totalMoldShot ? fmt(row.totalMoldShot) : "—"} />
              <KV k="Last Record"  v={fmtDate(row.lastestRecordTime)} />
              <KV k="Last Machine" v={row.lastestMachineNo} />
              <KV k="Last Mold"    v={row.lastestMoldNo} />
            </Section>
            {row.warningNotes && (
              <div style={{ padding:"5px 8px", background:"rgba(239,68,68,0.08)", border:"1px solid #ef444430", borderRadius:3, fontSize:9, color:"#ef4444", lineHeight:1.5 }}>⚠ {row.warningNotes}</div>
            )}
          </div>
          <div>
            <Section title="Mold Setup" accent="#8b5cf6">
              {(row.moldHist||[]).map((m,i) => (
                <div key={m} style={{ marginBottom:5 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:2 }}>
                    <span style={{ fontSize:9, color:"#8b5cf6" }}>{m}</span>
                    <span style={{ fontSize:9, color:"#5a6a8a" }}>cav: {row.moldCavity?.[i]??"—"}</span>
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between" }}>
                    <span style={{ fontSize:8, color:"#4a5a7a" }}>shots</span>
                    <span style={{ fontSize:9, color:"#c9d1e0", fontWeight:500 }}>{fmt(row.moldShotMap?.[m]??0)}</span>
                  </div>
                </div>
              ))}
            </Section>
            <Section title="Machine Output" accent="#06b6d4">
              {machEntries.length ? machEntries.map(([m,q]) => (
                <div key={m} style={{ marginBottom:4 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", marginBottom:1 }}>
                    <span style={{ fontSize:9, color:"#06b6d4" }}>{m}</span>
                    <span style={{ fontSize:9, color:"#c9d1e0", fontWeight:500 }}>{fmt(q)}</span>
                  </div>
                  <div style={{ height:4, background:"#1a2438", borderRadius:2, overflow:"hidden" }}>
                    <div style={{ width:`${(q/(row.itemQuantity||1))*100}%`, height:"100%", background:"#06b6d4", borderRadius:2 }} />
                  </div>
                </div>
              )) : <div style={{ fontSize:9, color:"#3a4a65" }}>No data yet</div>}
            </Section>
          </div>
          <div>
            <Section title="Daily Output" accent="#f59e0b">
              {dayEntries.length ? dayEntries.map(([date,qty]) => (
                <div key={date} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:3 }}>
                  <span style={{ fontSize:8, color:"#4a5a7a", width:64, flexShrink:0 }}>{date.slice(5)}</span>
                  <div style={{ flex:1, height:10, background:"#1a2438", borderRadius:2, overflow:"hidden" }}>
                    <div style={{ width:`${(qty/maxDay)*100}%`, height:"100%", background:"#f59e0b", borderRadius:2, opacity:0.8 }} />
                  </div>
                  <span style={{ fontSize:9, color:"#f59e0b", width:40, textAlign:"right", flexShrink:0 }}>{fmtNum(qty)}</span>
                </div>
              )) : <div style={{ fontSize:9, color:"#3a4a65" }}>No production days recorded</div>}
            </Section>
          </div>
          <div>
            <Section title="Shift Breakdown" accent="#ec4899">
              {shiftEntries.length ? shiftEntries.map(([k,qty]) => {
                const [date, ...rest] = k.split("_shift_");
                return (
                  <div key={k} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:3 }}>
                    <span style={{ fontSize:8, color:"#4a5a7a", width:80, flexShrink:0 }}>{date.slice(5)} S{rest[0]}</span>
                    <div style={{ flex:1, height:10, background:"#1a2438", borderRadius:2, overflow:"hidden" }}>
                      <div style={{ width:`${(qty/maxShift)*100}%`, height:"100%", background:rest[0]==="1"?"#ec4899":"#8b5cf6", borderRadius:2, opacity:0.8 }} />
                    </div>
                    <span style={{ fontSize:9, color:rest[0]==="1"?"#ec4899":"#8b5cf6", width:40, textAlign:"right", flexShrink:0 }}>{fmtNum(qty)}</span>
                  </div>
                );
              }) : <div style={{ fontSize:9, color:"#3a4a65" }}>No shift data</div>}
            </Section>
            <Section title="Material Components" accent="#10b981">
              {(row.materialComponentMap||[]).map((m,i) => (
                <div key={i} style={{ marginBottom:6 }}>
                  {m.plasticResinCode       && <div style={{ marginBottom:2 }}><Tag v={`Resin: ${m.plasticResinCode}`}             c="#10b981" /></div>}
                  {m.colorMasterbatchCode   && <div style={{ marginBottom:2 }}><Tag v={`Color MB: ${m.colorMasterbatchCode}`}      c="#3b82f6" /></div>}
                  {m.additiveMasterbatchCode && <div>                           <Tag v={`Additive MB: ${m.additiveMasterbatchCode}`} c="#f59e0b" /></div>}
                  {!m.colorMasterbatchCode && !m.additiveMasterbatchCode && <span style={{ fontSize:9, color:"#3a4a65" }}>No masterbatch</span>}
                </div>
              ))}
            </Section>
          </div>
        </div>
      </td>
    </tr>
  );
}

// ============================================================
//  DAILY REPORT PANEL
// ============================================================
function DailyReportPanel() {
  const [filter, setFilter]               = useState("all");
  const [machineFilter, setMachineFilter] = useState("");
  const [search, setSearch]               = useState("");
  const [subTab, setSubTab]               = useState("table");
  const [selectedRow, setSelectedRow]     = useState(null);
  const [showIdle, setShowIdle]           = useState(true);

  // FLAT_DATA: flatten all jobs per machine into individual rows for table
  // Each row tagged with _machineJobIndex (0-based) and _machineTotalJobs
  const FLAT_DATA = useMemo(() => {
    const rows = [];
    ALL_MACHINES.forEach(m => {
      const jobs = DATA_MAP[m];
      if (jobs && jobs.length > 0) {
        // Sort by startedDate ascending so sequential jobs appear in order
        const sorted = [...jobs].sort((a, b) => new Date(a.startedDate) - new Date(b.startedDate));
        sorted.forEach((job, ji) => {
          rows.push({
            ...job,
            idle: false,
            _machineJobIndex: ji,
            _machineTotalJobs: sorted.length,
            _isFirstJob: ji === 0,
          });
        });
      } else {
        rows.push({
          lastestMachineNo: m, poNo: "—", itemName: "— NO ACTIVE JOB —",
          lastestMoldNo: "—", poETA: "—", progress: null, startedDate: "—",
          actualFinishedDate: "—", itemQuantity: 0, estimatedCapacity: 0,
          totalDay: 0, itemRemain: 0, idle: true,
          _machineJobIndex: 0, _machineTotalJobs: 1, _isFirstJob: true,
        });
      }
    });
    return rows;
  }, []);

  const filtered = useMemo(() => {
    // Filter at machine level: if any job of a machine passes, include all its jobs
    // Strategy: filter then dedupe by machine for counts, but show all sub-rows
    return FLAT_DATA.filter(r => {
      if (!showIdle && r.idle) return false;
      if (machineFilter && r.lastestMachineNo !== machineFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        const match = r.itemName.toLowerCase().includes(q) ||
          r.poNo.toLowerCase().includes(q) ||
          r.lastestMachineNo.toLowerCase().includes(q);
        if (!match) return false;
      }
      if (filter === "complete")   return !r.idle && r.progress >= 95;
      if (filter === "inprogress") return !r.idle && r.progress > 0 && r.progress < 95;
      if (filter === "notstarted") return !r.idle && r.progress === 0;
      if (filter === "overdue")    return !r.idle && r.progress < 90 && r.totalDay > 6;
      if (filter === "idle")       return r.idle;
      return true;
    });
  }, [filter, machineFilter, search, showIdle, FLAT_DATA]);

  // For counts, use FULL_DATA (1 row per machine)
  const activeData = FULL_DATA.filter(r => !r.idle);
  const idleCount  = FULL_DATA.filter(r => r.idle).length;

  const totals = useMemo(() => {
    const active = filtered.filter(r => !r.idle);
    return {
      qty: active.reduce((a, r) => a + r.itemQuantity, 0),
      cap: active.reduce((a, r) => a + r.estimatedCapacity, 0),
      rem: active.reduce((a, r) => a + r.itemRemain, 0),
      avgProg: active.length ? (active.reduce((a, r) => a + r.progress, 0) / active.length).toFixed(1) : 0,
    };
  }, [filtered]);

  const FILTER_BTNS = [
    { k:"all",        label:"All",         count: FULL_DATA.length },
    { k:"inprogress", label:"In Progress",  count: activeData.filter(r => r.progress>0&&r.progress<95).length },
    { k:"complete",   label:"≥95% Done",    count: activeData.filter(r => r.progress>=95).length },
    { k:"notstarted", label:"Not Started",  count: activeData.filter(r => r.progress===0).length },
    { k:"overdue",    label:"Long Run",     count: activeData.filter(r => r.progress<90&&r.totalDay>6).length },
    { k:"idle",       label:"Idle",         count: idleCount },
  ];

  return (
    <div style={{ display:"flex", flexDirection:"column", flex:1, overflow:"hidden" }}>
      {/* Sub-toolbar */}
      <div style={{ background:"#101520", borderBottom:"1px solid #1a2438", padding:"5px 14px", display:"flex", alignItems:"center", gap:6, flexShrink:0, flexWrap:"wrap" }}>
        {FILTER_BTNS.map(b => (
          <button key={b.k} onClick={() => { setFilter(b.k); if(b.k==="idle") setShowIdle(true); }}
            style={{ padding:"3px 9px", border:"1px solid", borderRadius:3, cursor:"pointer", fontSize:10, background:filter===b.k?(b.k==="idle"?"#1a2438":"#1d4ed8"):"transparent", borderColor:filter===b.k?(b.k==="idle"?"#4a5a7a":"#3b82f6"):"#2a3245", color:filter===b.k?(b.k==="idle"?"#6a7a9a":"#fff"):"#7a8aaa", fontFamily:"inherit", transition:"all .15s" }}>
            {b.label} <span style={{ opacity:0.6 }}>({b.count})</span>
          </button>
        ))}
        <div style={{ width:1, height:16, background:"#1e2d45", margin:"0 2px" }} />
        <button onClick={() => setShowIdle(!showIdle)}
          style={{ padding:"3px 9px", border:"1px solid", borderRadius:3, cursor:"pointer", fontSize:10, background:showIdle?"rgba(74,90,122,0.15)":"transparent", borderColor:showIdle?"#4a5a7a":"#2a3245", color:showIdle?"#6a7a9a":"#4a5a7a", fontFamily:"inherit" }}>
          {showIdle ? "⊙ Showing Idle" : "⊘ Idle Hidden"}
        </button>
        <div style={{ width:1, height:16, background:"#1e2d45", margin:"0 2px" }} />
        <select value={machineFilter} onChange={e => setMachineFilter(e.target.value)}
          style={{ padding:"3px 6px", background:"#0c1018", border:"1px solid #2a3245", borderRadius:3, color:"#c9d1e0", fontSize:10, fontFamily:"inherit" }}>
          <option value="">All Machines</option>
          {ALL_MACHINES.map(m => <option key={m} value={m}>{m}{DATA_MAP[m] ? "" : " (idle)"}</option>)}
        </select>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search goods / PO..."
          style={{ padding:"3px 8px", background:"#0c1018", border:"1px solid #2a3245", borderRadius:3, color:"#c9d1e0", fontSize:10, fontFamily:"inherit", width:160 }} />
        <div style={{ marginLeft:"auto", display:"flex", gap:4 }}>
          {[["table","Table"],["gantt","Gantt"],["both","Both"]].map(([k,l]) => (
            <button key={k} onClick={() => setSubTab(k)}
              style={{ padding:"3px 9px", border:"1px solid", borderRadius:3, cursor:"pointer", fontSize:10, background:subTab===k?"#0f2d4a":"transparent", borderColor:subTab===k?"#0ea5e9":"#2a3245", color:subTab===k?"#0ea5e9":"#7a8aaa", fontFamily:"inherit" }}>{l}</button>
          ))}
        </div>
      </div>

      {/* Summary bar */}
      <div style={{ background:"#0e1622", borderBottom:"1px solid #1a2438", padding:"4px 14px", display:"flex", gap:24, flexShrink:0 }}>
        {[
          ["Total Qty",       fmt(totals.qty),  "#c9d1e0"],
          ["Total Capacity",  fmt(totals.cap),  "#8b9ab5"],
          ["Total Remaining", fmt(totals.rem),  totals.rem > 500000 ? "#ef4444" : "#f59e0b"],
        ].map(([l,v,c]) => (
          <div key={l} style={{ display:"flex", alignItems:"center", gap:6 }}>
            <span style={{ fontSize:9, color:"#4a5a7a", letterSpacing:"0.04em" }}>{l}</span>
            <span style={{ fontSize:11, fontWeight:600, color:c }}>{v}</span>
          </div>
        ))}
        <div style={{ marginLeft:"auto", fontSize:9, color:"#4a5a7a", alignSelf:"center" }}>
          {filtered.filter(r=>!r.idle).length} jobs · {filtered.filter(r=>r.idle).length} idle machines
        </div>
      </div>

      {/* Content */}
      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>
        {(subTab==="table"||subTab==="both") && (
          <div style={{ flex:subTab==="both"?"0 0 640px":1, overflow:"auto", borderRight:subTab==="both"?"2px solid #1a2438":"none" }}>
            <table style={{ borderCollapse:"collapse", width:"100%", fontSize:10.5 }}>
              <thead>
                <tr style={{ background:"#101926", position:"sticky", top:0, zIndex:10 }}>
                  {[["Machine",52],["PO #",88],["Goods Name",190],["Mold",90],["Output",72],["Progress",100],["Start",70],["End",70],["Qty",65],["Cap/Day",65],["W.Days",50],["Remain",65]].map(([h,w]) => (
                    <th key={h} style={{ width:w, padding:"4px 5px", textAlign:"left", color:"#4a5a7a", fontWeight:600, fontSize:9, textTransform:"uppercase", letterSpacing:"0.05em", borderBottom:"2px solid #1a2d45", borderRight:"1px solid #1a2438", whiteSpace:"nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => {
                  const pc = progColor(row.progress);
                  const isSel = selectedRow === i;
                  const isSubRow = !row._isFirstJob; // continuation row for same machine
                  const isLastJobOfMachine = row._machineJobIndex === row._machineTotalJobs - 1;

                  return (
                    <tr
                      key={row.lastestMachineNo + row.poNo + i}
                      className={"row-hover" + (isSel ? " row-sel" : "") + (row.idle ? " row-idle" : "")}
                      onClick={() => setSelectedRow(isSel ? null : i)}
                      style={{
                        borderBottom: isLastJobOfMachine
                          ? "2px solid rgba(26,36,56,0.9)"   // thick separator between machines
                          : "1px solid rgba(59,130,246,0.12)", // subtle between jobs of same machine
                        cursor: row.idle ? "default" : "pointer",
                        background: isSel
                          ? "rgba(59,130,246,0.12)"
                          : isSubRow
                          ? "rgba(14,20,36,0.6)"             // slightly darker for sub-rows
                          : "transparent",
                      }}
                    >
                      {/* Machine column: only show on first job row, with rowspan visual via border */}
                      <td style={{
                        padding: "3px 5px",
                        fontWeight: 600,
                        color: row.idle ? "#2a3a55" : isSubRow ? "transparent" : "#3b82f6",
                        borderLeft: isSubRow ? "3px solid rgba(59,130,246,0.25)" : "3px solid transparent",
                        position: "relative",
                      }}>
                        {!isSubRow && row.lastestMachineNo}
                        {/* multi-job badge on first row */}
                        {!isSubRow && row._machineTotalJobs > 1 && (
                          <span style={{
                            display: "inline-block",
                            marginLeft: 3,
                            padding: "0px 4px",
                            borderRadius: 2,
                            background: "rgba(59,130,246,0.18)",
                            border: "1px solid rgba(59,130,246,0.3)",
                            color: "#60a5fa",
                            fontSize: 7.5,
                            fontWeight: 700,
                            verticalAlign: "middle",
                          }}>
                            ×{row._machineTotalJobs}
                          </span>
                        )}
                      </td>
                      <td style={{ padding:"3px 5px", color:row.idle?"#2a3a55":"#4a5a7a", fontSize:9.5 }}>{row.poNo}</td>
                      <td style={{ padding:"3px 5px", color:row.idle?"#2a3a55":"#e8edf5", maxWidth:190, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", fontStyle:row.idle?"italic":"normal" }} title={row.itemName}>{row.itemName}</td>
                      <td style={{ padding:"3px 5px", color:"#6a7a9a", fontSize:9 }}>{row.lastestMoldNo}</td>
                      <td style={{ padding:"3px 5px", color:"#5a6a8a", fontSize:9 }}>{row.poETA}</td>
                      <td style={{ padding:"3px 5px" }}>
                        {row.idle ? (
                          <div style={{ fontSize:8, color:"#2a3a55", letterSpacing:"0.08em", fontStyle:"italic", paddingLeft:2 }}>IDLE</div>
                        ) : (
                          <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                            <div style={{ flex:1, height:9, background:"#1a2438", borderRadius:2, overflow:"hidden", border:"1px solid #2a3245" }}>
                              <div style={{ width:row.progress+"%", height:"100%", background:pc, borderRadius:2 }} />
                            </div>
                            <span style={{ color:pc, fontSize:9, width:32, textAlign:"right" }}>{row.progress}%</span>
                          </div>
                        )}
                      </td>
                      <td style={{ padding:"3px 5px", color:"#7a8aaa", fontSize:9 }}>{row.startedDate}</td>
                      <td style={{ padding:"3px 5px", color: row.actualFinishedDate && row.actualFinishedDate !== "—" ? "#10b981" : "#5a6a8a", fontSize:9 }}>{row.actualFinishedDate || "—"}</td>
                      <td style={{ padding:"3px 5px", textAlign:"right", fontWeight:600, color:row.idle?"#2a3a55":"#c9d1e0" }}>{row.idle?"—":fmt(row.itemQuantity)}</td>
                      <td style={{ padding:"3px 5px", textAlign:"right", color:"#6a7a9a" }}>{row.idle?"—":fmt(row.estimatedCapacity)}</td>
                      <td style={{ padding:"3px 5px", textAlign:"center" }}>
                        {!row.idle && (
                          <span style={{ padding:"1px 5px", borderRadius:2, fontSize:9, fontWeight:600, background:row.totalDay>=8?"rgba(239,68,68,0.15)":row.totalDay>=5?"rgba(245,158,11,0.15)":"rgba(16,185,129,0.12)", color:row.totalDay>=8?"#ef4444":row.totalDay>=5?"#f59e0b":"#10b981" }}>{row.totalDay}</span>
                        )}
                      </td>
                      <td style={{ padding:"3px 5px", textAlign:"right", fontWeight:600, color:row.idle?"#2a3a55":row.itemRemain>50000?"#ef4444":row.itemRemain>10000?"#f59e0b":"#10b981" }}>{row.idle?"—":fmt(row.itemRemain)}</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr style={{ background:"#101926", position:"sticky", bottom:0, borderTop:"2px solid #1a2d45" }}>
                  <td colSpan={8} style={{ padding:"4px 5px", color:"#4a5a7a", fontSize:9, textAlign:"right", letterSpacing:"0.05em" }}>TOTALS (ACTIVE ONLY)</td>
                  <td style={{ padding:"4px 5px", textAlign:"right", fontWeight:600, color:"#3b82f6" }}>{fmt(totals.qty)}</td>
                  <td style={{ padding:"4px 5px", textAlign:"right", color:"#6a7a9a" }}>{fmt(totals.cap)}</td>
                  <td />
                  <td style={{ padding:"4px 5px", textAlign:"right", fontWeight:600, color:"#f59e0b" }}>{fmt(totals.rem)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        {(subTab==="gantt"||subTab==="both") && (
          <div style={{ flex:1, overflow:"auto" }}>
            <div style={{ minWidth:GANTT_DATES.length*COL_W+100 }}>
              <table style={{ borderCollapse:"collapse", width:"100%" }}>
                <thead style={{ position:"sticky", top:0, zIndex:10 }}>
                  <tr style={{ background:"#0c1018" }}>
                    {subTab==="gantt" && <th style={{ width:90, background:"#101926", borderRight:"2px solid #1a2d45", borderBottom:"1px solid #1a2438" }} />}
                    {(() => {
                      let cur=null, span=0, cells=[];
                      GANTT_DATES.forEach((d,i) => {
                        const mon = new Date(d); mon.setDate(d.getDate()-((d.getDay()+6)%7));
                        const key = `${mon.getMonth()+1}/${mon.getDate()}`;
                        if (key!==cur) { if(cur) cells.push({key:cur,span}); cur=key; span=1; } else span++;
                        if (i===GANTT_DATES.length-1) cells.push({key:cur,span});
                      });
                      return cells.map(c => (
                        <th key={c.key} colSpan={c.span} style={{ textAlign:"center", padding:"2px 0", fontSize:9, fontWeight:600, color:"#3b82f6", borderRight:"1px solid #1a2438", borderBottom:"1px solid #1a2438", background:"#0c1018", letterSpacing:"0.04em" }}>
                          {c.key}
                        </th>
                      ));
                    })()}
                  </tr>
                  <tr style={{ background:"#101926" }}>
                    {subTab==="gantt" && <th style={{ width:90, padding:"3px 6px", textAlign:"left", fontSize:9, color:"#4a5a7a", fontWeight:600, letterSpacing:"0.05em", borderRight:"2px solid #1a2d45", borderBottom:"2px solid #1a2d45" }}>MACHINE</th>}
                    {GANTT_DATES.map((d,i) => {
                      const isToday = d.toDateString()===TODAY_D.toDateString();
                      const isWE = d.getDay()===0||d.getDay()===6;
                      const days = ["Su","Mo","Tu","We","Th","Fr","Sa"];
                      return (
                        <th key={i} style={{ width:COL_W, padding:"3px 0", textAlign:"center", fontSize:8, color:isToday?"#f59e0b":isWE?"#2a3a55":"#5a6a8a", borderRight:"1px solid #1a2438", borderBottom:`2px solid ${isToday?"#f59e0b":"#1a2d45"}`, background:isToday?"rgba(245,158,11,0.08)":"transparent", whiteSpace:"nowrap" }}>
                          <div>{days[d.getDay()]}</div>
                          <div style={{ fontWeight:600 }}>{d.getDate()}</div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {FULL_DATA.map((row, ri) => {
                    const jobs = MACHINE_JOBS_MAP[row.lastestMachineNo] || [];

                    return (
                      <tr key={row.lastestMachineNo + ri} className="row-hover"
                        style={{ borderBottom:"2px solid rgba(26,36,56,0.9)", height: Math.max(28, jobs.length * 22 + 8), opacity: row.idle ? 0.35 : 1 }}>

                        {subTab === "gantt" && (
                          <td style={{ padding:"2px 5px", fontSize:9.5, fontWeight:600, color: row.idle ? "#2a3a55" : "#3b82f6", borderRight:"2px solid #1a2d45", whiteSpace:"nowrap", verticalAlign:"middle" }}>
                            {row.lastestMachineNo}
                            {jobs.length > 1 && (
                              <span style={{ display:"block", fontSize:7.5, color:"#3b82f6", opacity:0.6, marginTop:1 }}>
                                {jobs.length} jobs
                              </span>
                            )}
                          </td>
                        )}

                        {GANTT_DATES.map((d, di) => {
                          const isToday = d.toDateString() === TODAY_D.toDateString();
                          const isWE    = d.getDay() === 0 || d.getDay() === 6;

                          const barsHere = jobs
                            .map((job, ji) => {
                              const start = parseD(job.startedDate);
                              const end   = parseD(job.actualFinishedDate);
                              if (!start || !end) return null;
                              if (d.toDateString() !== start.toDateString()) return null;
                              const diff = Math.round((end - start) / 864e5) + 1;
                              const span = Math.min(Math.max(1, diff), GANTT_DATES.length - di);
                              return { job, ji, span };
                            })
                            .filter(Boolean);

                          return (
                            <td key={di} style={{
                              position: "relative",
                              width: COL_W,
                              background: isToday
                                ? "rgba(245,158,11,0.05)"
                                : isWE
                                ? "repeating-linear-gradient(45deg,rgba(26,36,56,0.3),rgba(26,36,56,0.3) 2px,transparent 2px,transparent 6px)"
                                : row.idle
                                ? "repeating-linear-gradient(135deg,rgba(20,28,44,0.4),rgba(20,28,44,0.4) 2px,transparent 2px,transparent 8px)"
                                : "transparent",
                              borderRight: `1px solid ${isToday ? "rgba(245,158,11,0.3)" : "rgba(26,36,56,0.5)"}`,
                              overflow: "visible",
                            }}>
                              {barsHere.map(({ job, ji, span }) => (
                                <div key={ji} style={{
                                  position: "absolute",
                                  top: jobs.length > 1 ? 3 + ji * 22 : 5,
                                  left: 2,
                                  width: span * COL_W - 4,
                                  height: 18,
                                  borderRadius: 2,
                                  background: GANTT_COLORS[(ri * 3 + ji) % GANTT_COLORS.length],
                                  opacity: 0.85,
                                  zIndex: 2,
                                  cursor: "pointer",
                                  overflow: "hidden",
                                }}
                                  title={`${row.lastestMachineNo}: ${job.itemName}\n${job.startedDate} → ${job.actualFinishedDate}\n${job.progress}%`}
                                >
                                  <div style={{ position:"absolute", top:0, left:0, width: job.progress + "%", height:"100%", background:"rgba(255,255,255,0.18)", borderRadius:2 }} />
                                  {span >= 3 && (
                                    <div style={{ position:"absolute", top:"50%", left:4, transform:"translateY(-50%)", fontSize:7.5, color:"rgba(255,255,255,0.9)", whiteSpace:"nowrap", fontWeight:600 }}>
                                      {job.progress}% · {job.itemName.slice(0, 18)}
                                    </div>
                                  )}
                                </div>
                              ))}
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

// ============================================================
//  PO STATUS BOARD PANEL
// ============================================================
function POStatusPanel() {
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterETA,    setFilterETA]    = useState("all");
  const [search,       setSearch]       = useState("");
  const [sortKey,      setSortKey]      = useState("poNo");
  const [sortAsc,      setSortAsc]      = useState(true);
  const [expanded,     setExpanded]     = useState(new Set());

  const stats = useMemo(() => ({
    total:   PO_JSON.length,
    molding: PO_JSON.filter(r => r.proStatus==="MOLDING").length,
    molded:  PO_JSON.filter(r => r.proStatus==="MOLDED").length,
    paused:  PO_JSON.filter(r => r.proStatus==="PAUSED").length,
    pending: PO_JSON.filter(r => r.proStatus==="PENDING").length,
    late:    PO_JSON.filter(r => r.etaStatus==="LATE").length,
    avgProg: (PO_JSON.reduce((a,r) => a+r.progress, 0)/PO_JSON.length).toFixed(1),
  }), []);

  const filtered = useMemo(() => {
    let d = [...PO_JSON];
    if (filterStatus!=="all") d = d.filter(r => r.proStatus===filterStatus);
    if (filterETA   !=="all") d = d.filter(r => r.etaStatus===filterETA);
    if (search) {
      const q = search.toLowerCase();
      d = d.filter(r => r.poNo.toLowerCase().includes(q)||r.itemName.toLowerCase().includes(q)||r.itemCode.toLowerCase().includes(q)||r.moldList.toLowerCase().includes(q));
    }
    d.sort((a,b) => {
      let av=a[sortKey]??"", bv=b[sortKey]??"";
      if (typeof av==="number") return sortAsc?av-bv:bv-av;
      return sortAsc?String(av).localeCompare(String(bv)):String(bv).localeCompare(String(av));
    });
    return d;
  }, [filterStatus, filterETA, search, sortKey, sortAsc]);

  function doSort(k) { if(sortKey===k) setSortAsc(a=>!a); else { setSortKey(k); setSortAsc(true); } }
  function sortIco(k) {
    if (sortKey!==k) return <span style={{ color:"#293a55", fontSize:8 }}> ⇅</span>;
    return <span style={{ color:"#3b82f6", fontSize:8 }}>{sortAsc?" ↑":" ↓"}</span>;
  }
  function toggleExpand(poNo) {
    setExpanded(prev => { const s=new Set(prev); s.has(poNo)?s.delete(poNo):s.add(poNo); return s; });
  }

  const FBNS = [
    { k:"all",     label:"All",     n:stats.total   },
    { k:"MOLDING", label:"Molding", n:stats.molding },
    { k:"MOLDED",  label:"Molded",  n:stats.molded  },
    { k:"PAUSED",  label:"Paused",  n:stats.paused  },
    { k:"PENDING", label:"Pending", n:stats.pending },
  ];

  return (
    <div style={{ display:"flex", flexDirection:"column", flex:1, overflow:"hidden" }}>
      <div style={{ background:"#0e1622", borderBottom:"1px solid #1a2438", padding:"4px 14px", display:"flex", gap:22, flexShrink:0, alignItems:"center" }}>
        {[
          ["TOTAL",   stats.total,         "#c9d1e0"],
          ["MOLDING", stats.molding,        "#3b82f6"],
          ["PAUSED",  stats.paused,         "#f59e0b"],
          ["MOLDED",  stats.molded,         "#10b981"],
          ["LATE",    stats.late,           "#ef4444"],
          ["AVG",     stats.avgProg+"%",    progColor(+stats.avgProg)],
        ].map(([l,v,c]) => (
          <div key={l} style={{ display:"flex", alignItems:"center", gap:6 }}>
            <span style={{ fontSize:8, color:"#4a5a7a", letterSpacing:"0.06em" }}>{l}</span>
            <span style={{ fontSize:11, fontWeight:600, color:c }}>{v}</span>
          </div>
        ))}
        <div style={{ marginLeft:"auto", fontSize:9, color:"#3a4a65" }}>{filtered.length}/{PO_JSON.length} rows</div>
      </div>

      <div style={{ background:"#101520", borderBottom:"1px solid #1a2438", padding:"5px 14px", display:"flex", alignItems:"center", gap:5, flexShrink:0, flexWrap:"wrap" }}>
        {FBNS.map(b => {
          const cfg = STATUS_CFG[b.k];
          const on  = filterStatus===b.k;
          return (
            <button key={b.k} onClick={() => setFilterStatus(b.k)}
              style={{ padding:"3px 9px", border:"1px solid", borderRadius:3, cursor:"pointer", fontSize:10, fontFamily:"inherit", transition:"all .15s", background:on?(cfg?cfg.bg:"rgba(59,130,246,0.18)"):"transparent", borderColor:on?(cfg?cfg.border:"#3b82f650"):"#2a3245", color:on?(cfg?cfg.color:"#7ac8f8"):"#7a8aaa" }}>
              {b.label} <span style={{ opacity:0.5 }}>({b.n})</span>
            </button>
          );
        })}
        <div style={{ width:1, height:16, background:"#1e2d45", margin:"0 4px" }} />
        {[["all","ETA: All"],["ONTIME","On Time"],["LATE","Late"]].map(([k,l]) => (
          <button key={k} onClick={() => setFilterETA(k)}
            style={{ padding:"3px 9px", border:"1px solid", borderRadius:3, cursor:"pointer", fontSize:10, fontFamily:"inherit", background:filterETA===k?"rgba(59,130,246,0.14)":"transparent", borderColor:filterETA===k?"#3b82f650":"#2a3245", color:filterETA===k?(k==="LATE"?"#ef4444":k==="ONTIME"?"#10b981":"#7ac8f8"):"#7a8aaa" }}>
            {l}
          </button>
        ))}
        <div style={{ width:1, height:16, background:"#1e2d45", margin:"0 4px" }} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search PO / item / code / mold…"
          style={{ padding:"3px 9px", background:"#0c1018", border:"1px solid #2a3245", borderRadius:3, color:"#c9d1e0", fontSize:10, fontFamily:"inherit", width:210 }} />
        <div style={{ marginLeft:"auto", display:"flex", gap:8, alignItems:"center" }}>
          {expanded.size>0 && (
            <button onClick={() => setExpanded(new Set())}
              style={{ padding:"3px 8px", border:"1px solid #2a3a55", borderRadius:3, background:"transparent", color:"#4a6a8a", fontSize:9, cursor:"pointer", fontFamily:"inherit" }}>
              collapse all ({expanded.size})
            </button>
          )}
        </div>
      </div>

      <div style={{ flex:1, overflow:"auto" }}>
        <table style={{ borderCollapse:"collapse", width:"100%", fontSize:10.5 }}>
          <thead>
            <tr style={{ background:"#0f1826", position:"sticky", top:0, zIndex:10 }}>
              {PO_COLS.map(({ key, label, w, noSort }) => (
                <th key={key} onClick={noSort?undefined:()=>doSort(key)}
                  style={{ width:w, padding:"4px 5px", textAlign:"left", color:"#4a6a8a", fontWeight:600, fontSize:9, textTransform:"uppercase", letterSpacing:"0.05em", borderBottom:"2px solid #1a2d45", borderRight:"1px solid #1a2438", whiteSpace:"nowrap", cursor:noSort?"default":"pointer", userSelect:"none" }}>
                  {label}{!noSort&&sortIco(key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row,i) => {
              const cfg   = STATUS_CFG[row.proStatus]||STATUS_CFG.PENDING;
              const eta   = ETA_CFG[row.etaStatus]  ||ETA_CFG.PENDING;
              const pc    = progColor(row.progress);
              const isExp = expanded.has(row.poNo);
              return (
                <>
                  <tr key={row.poNo} className={"rh"+(isExp?" rexp":"")}
                    style={{ borderBottom:isExp?"none":"1px solid rgba(20,30,50,0.75)", background:isExp?"rgba(14,22,38,0.9)":i%2===0?"transparent":"rgba(9,14,24,0.4)" }}>
                    <td style={{ padding:"3px 4px", textAlign:"center" }}>
                      <button className="exp-btn" onClick={() => toggleExpand(row.poNo)}
                        style={{ width:18, height:18, borderRadius:3, border:`1px solid ${isExp?cfg.border:"#2a3245"}`, background:isExp?cfg.bg:"transparent", color:isExp?cfg.color:"#3a4a65", cursor:"pointer", fontSize:9, display:"inline-flex", alignItems:"center", justifyContent:"center", fontFamily:"inherit", lineHeight:1, transition:"all .15s" }}>
                        {isExp?"▾":"▸"}
                      </button>
                    </td>
                    <td style={{ padding:"3px 5px", fontWeight:600, color:"#3b82f6", fontSize:10, whiteSpace:"nowrap", cursor:"pointer" }} onClick={() => toggleExpand(row.poNo)}>{row.poNo}</td>
                    <td style={{ padding:"3px 5px", color:"#5a7a9a", fontSize:9.5 }}>{row.itemCode}</td>
                    <td style={{ padding:"3px 5px", color:"#7a8aaa", fontSize:9, maxWidth:130, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }} title={row.itemType}>{row.itemType}</td>
                    <td style={{ padding:"3px 5px", color:"#d0d8e8", maxWidth:200, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }} title={row.itemName}>{row.itemName}</td>
                    <td style={{ padding:"3px 5px", color:"#6a7a9a", fontSize:9, maxWidth:120, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }} title={row.moldList}>{row.moldList}</td>
                    <td style={{ padding:"3px 5px" }}>
                      <span style={{ display:"inline-flex", alignItems:"center", gap:4, padding:"1px 6px", borderRadius:3, background:cfg.bg, color:cfg.color, border:`1px solid ${cfg.border}`, fontSize:9, fontWeight:600, letterSpacing:"0.04em" }}>
                        <span style={{ width:5, height:5, borderRadius:"50%", background:cfg.dot, animation:row.proStatus==="MOLDING"?"blink 1.4s infinite":"none" }} />
                        {cfg.label}
                      </span>
                    </td>
                    <td style={{ padding:"3px 5px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:5 }}>
                        <div style={{ flex:1, height:8, background:"#1a2438", borderRadius:2, overflow:"hidden", border:"1px solid #232f45" }}>
                          <div style={{ width:row.progress+"%", height:"100%", background:pc, borderRadius:2 }} />
                        </div>
                        <span style={{ color:pc, fontSize:9, width:36, textAlign:"right", fontWeight:600 }}>{row.progress.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td style={{ padding:"3px 5px" }}><span style={{ color:eta.color, fontSize:9, fontWeight:600 }}>{eta.label}</span></td>
                    <td style={{ padding:"3px 5px", color:"#7a8aaa", fontSize:9, whiteSpace:"nowrap" }}>{fmtDate(row.poETA)}</td>
                    <td style={{ padding:"3px 5px", color:"#6a7a9a", fontSize:9, whiteSpace:"nowrap" }}>{fmtDate(row.startedDate)}</td>
                    <td style={{ padding:"3px 5px", fontSize:9, whiteSpace:"nowrap", color:row.actualFinishedDate?"#10b981":"#384a65" }}>{fmtDate(row.actualFinishedDate)}</td>
                    <td style={{ padding:"3px 5px", textAlign:"right", fontWeight:600, color:"#c9d1e0" }}>{fmtNum(row.itemQuantity)}</td>
                    <td style={{ padding:"3px 5px", textAlign:"right", fontWeight:600, color:row.itemRemain>100000?"#ef4444":row.itemRemain>10000?"#f59e0b":row.itemRemain>0?"#10b981":"#384a65" }}>
                      {row.itemRemain>0?fmtNum(row.itemRemain):"—"}
                    </td>
                  </tr>
                  {isExp && <DetailPanel key={row.poNo+"_detail"} row={row} />}
                </>
              );
            })}
          </tbody>
          <tfoot>
            <tr style={{ background:"#0f1826", position:"sticky", bottom:0, borderTop:"2px solid #1a2d45" }}>
              <td colSpan={12} style={{ padding:"4px 5px", color:"#3a4a65", fontSize:9, textAlign:"right", letterSpacing:"0.05em" }}>FILTERED TOTALS</td>
              <td style={{ padding:"4px 5px", textAlign:"right", fontWeight:600, color:"#3b82f6" }}>{fmtNum(filtered.reduce((a,r)=>a+r.itemQuantity,0))}</td>
              <td style={{ padding:"4px 5px", textAlign:"right", fontWeight:600, color:"#f59e0b" }}>{fmtNum(filtered.reduce((a,r)=>a+r.itemRemain,0))}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

// ============================================================
//  ProgressTrackingViz
// ============================================================
export default function ProgressTrackingViz({ data }) {
  const source = USE_MOCK ? MOCK_DATA : data;

  DAILY_JSON = source.ProgressTracker.productionStatus.daily_data;
  PO_JSON    = source.ProgressTracker.productionStatus.tracking_data;

  REPORT_DATE = new Date().toLocaleDateString("en-US", {weekday:"short", month:"short", day:"numeric", year:"numeric"});

  TODAY = DAILY_JSON[0]?.lastestRecordTime ?? null;
  todayDate  = new Date(TODAY);
  ganttStart = new Date(todayDate.getFullYear(), todayDate.getMonth(), 1);
  GANTT_START = `${ganttStart.getFullYear()}-${String(ganttStart.getMonth()+1).padStart(2,"0")}-01`;
  GANTT_DAYS = new Date(todayDate.getFullYear(), todayDate.getMonth() + 1, 0).getDate();
  GANTT_DATES = genDates(parseConfigDate(GANTT_START), GANTT_DAYS);
  TODAY_D = parseConfigDate(TODAY);

  MACHINE_COUNT = new Set(DAILY_JSON.map(r => r.lastestMachineNo)).size;
  ALL_MACHINES = Array.from({ length: MACHINE_COUNT }, (_, i) => `NO.${String(i + 1).padStart(2, "0")}`);

  // DATA_MAP: machine → array of all jobs
  DATA_MAP = {};
  DAILY_JSON.forEach(r => {
    if (!DATA_MAP[r.lastestMachineNo]) DATA_MAP[r.lastestMachineNo] = [];
    DATA_MAP[r.lastestMachineNo].push(r);
  });

  // FULL_DATA: 1 row per machine (latest job) — used for Gantt row list & stats
  FULL_DATA = ALL_MACHINES.map(m => {
    if (DATA_MAP[m] && DATA_MAP[m].length > 0) {
      const jobs = [...DATA_MAP[m]].sort((a, b) =>
        new Date(b.actualFinishedDate || b.startedDate) - new Date(a.actualFinishedDate || a.startedDate));
      return { ...jobs[0], idle: false };
    }
    return {
      lastestMachineNo: m, poNo: "—", itemName: "— NO ACTIVE JOB —",
      lastestMoldNo: "—", poETA: "—", progress: null, startedDate: "—",
      actualFinishedDate: "—", itemQuantity: 0, estimatedCapacity: 0,
      totalDay: 0, itemRemain: 0, idle: true,
    };
  });

  // MACHINE_JOBS_MAP: machine → sorted jobs with valid start+end for Gantt bars
  MACHINE_JOBS_MAP = {};
  ALL_MACHINES.forEach(m => {
    MACHINE_JOBS_MAP[m] = (DATA_MAP[m] || [])
      .filter(r => r.startedDate && r.actualFinishedDate)
      .sort((a, b) => new Date(a.startedDate) - new Date(b.startedDate));
  });

  const [mainTab, setMainTab] = useState("daily");

  const dailyActive = FULL_DATA.filter(r => !r.idle);
  const dailyIdle   = FULL_DATA.filter(r => r.idle).length;
  const dailyAvgProg = dailyActive.length
    ? (dailyActive.reduce((a, r) => a + r.progress, 0) / dailyActive.length).toFixed(1)
    : 0;

  return (
    <div style={{ fontFamily:"'IBM Plex Mono',monospace", background:"#0c1018", color:"#c9d1e0", height:"100vh", display:"flex", flexDirection:"column", overflow:"hidden", fontSize:11 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:5px;height:5px;}
        ::-webkit-scrollbar-track{background:#0c1018;}
        ::-webkit-scrollbar-thumb{background:#2a3245;border-radius:3px;}
        ::-webkit-scrollbar-thumb:hover{background:#3a4a65;}
        .row-hover:hover{background:rgba(30,37,53,0.8)!important;}
        .row-sel{background:rgba(59,130,246,0.15)!important;}
        .row-idle{opacity:0.45;}
        .row-idle:hover{opacity:0.7!important;}
        .rh:hover{background:rgba(22,34,54,0.95)!important;}
        .rexp{background:rgba(20,32,52,0.6)!important;}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
        input:focus{outline:1px solid #2a4a7a!important;}
        .exp-btn:hover{background:rgba(59,130,246,0.2)!important;color:#7ac8f8!important;}
        .main-tab-btn{transition:all .2s;}
        .main-tab-btn:hover{background:rgba(59,130,246,0.08)!important;}
      `}</style>

      {/* UNIFIED HEADER */}
      <div style={{ background:"#0d1520", borderBottom:"2px solid #1a2d45", padding:"0 14px", display:"flex", alignItems:"stretch", justifyContent:"space-between", flexShrink:0 }}>
        <div style={{ display:"flex", alignItems:"center", gap:12, padding:"8px 0" }}>
          <div style={{ width:28, height:28, borderRadius:4, background:"linear-gradient(135deg,#1d4ed8,#7c3aed)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12, fontWeight:700, color:"#fff", letterSpacing:"-0.05em", flexShrink:0 }}>IM</div>
          <div>
            <div style={{ fontSize:13, fontWeight:600, color:"#e8edf5", letterSpacing:"0.08em" }}>INJECTION MOLDING DASHBOARD</div>
            <div style={{ fontSize:8, color:"#3a4a65", marginTop:1, letterSpacing:"0.06em" }}>PRODUCTION MONITORING SYSTEM &nbsp;·&nbsp; {REPORT_DATE}</div>
          </div>
        </div>

        <div style={{ display:"flex", alignItems:"stretch", gap:0 }}>
          {[
            ["daily", "DAILY REPORT", `${dailyActive.length}/${ALL_MACHINES.length} active · ${dailyIdle} idle`],
            ["po",    "PO STATUS BOARD", `${PO_JSON.length} orders · ${PO_JSON.filter(r=>r.etaStatus==="LATE").length} late`],
          ].map(([k, label, sub]) => {
            const active = mainTab===k;
            return (
              <button key={k} className="main-tab-btn" onClick={() => setMainTab(k)}
                style={{ padding:"0 20px", border:"none", borderBottom:`3px solid ${active?"#3b82f6":"transparent"}`, borderTop:"3px solid transparent", background:active?"rgba(59,130,246,0.08)":"transparent", cursor:"pointer", fontFamily:"inherit", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:2 }}>
                <span style={{ fontSize:10, fontWeight:600, color:active?"#60a5fa":"#4a5a7a", letterSpacing:"0.07em" }}>{label}</span>
                <span style={{ fontSize:8, color:active?"#3b82f6":"#2a3a55", letterSpacing:"0.04em" }}>{sub}</span>
              </button>
            );
          })}
        </div>

        <div style={{ display:"flex", gap:18, alignItems:"center", padding:"8px 0" }}>
          {mainTab==="daily" ? [
            ["ACTIVE",   `${dailyActive.length}/${ALL_MACHINES.length}`, "#10b981"],
            ["AVG PROG", dailyAvgProg+"%", progColor(+dailyAvgProg)],
            ["IDLE",     `${dailyIdle}`,   "#4a5a7a"],
          ].map(([l,v,c]) => (
            <div key={l} style={{ textAlign:"right" }}>
              <div style={{ fontSize:8, color:"#3a4a65", letterSpacing:"0.06em" }}>{l}</div>
              <div style={{ fontSize:11, fontWeight:600, color:c }}>{v}</div>
            </div>
          )) : [
            ["TOTAL",  PO_JSON.length,                                    "#c9d1e0"],
            ["MOLDED", PO_JSON.filter(r=>r.proStatus==="MOLDED").length,  "#10b981"],
            ["LATE",   PO_JSON.filter(r=>r.etaStatus==="LATE").length,    "#ef4444"],
          ].map(([l,v,c]) => (
            <div key={l} style={{ textAlign:"right" }}>
              <div style={{ fontSize:8, color:"#3a4a65", letterSpacing:"0.06em" }}>{l}</div>
              <div style={{ fontSize:11, fontWeight:600, color:c }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      {mainTab==="daily" ? <DailyReportPanel /> : <POStatusPanel />}
    </div>
  );
}
