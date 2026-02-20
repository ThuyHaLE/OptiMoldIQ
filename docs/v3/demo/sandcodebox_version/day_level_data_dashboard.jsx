import { useState } from "react";

// ── RAW JSON — paste API response here, or replace with: const RAW_JSON = await response.json() ──
const RAW_JSON = {
  "moldBasedRecords": [
    {"machineInfo": "NO.01 (MD50S-000)", "workingShift": 1, "moldNo": "14000CBQ-M-001", "moldShot": 1271.0, "moldCavity": 8.0, "itemTotalQuantity": 10168, "itemGoodQuantity": 8553, "changeType": "no_change", "defectQuantity": 1615, "defectRate": 15.8831628638867},
    {"machineInfo": "NO.01 (MD50S-000)", "workingShift": 2, "moldNo": "14000CBQ-M-001", "moldShot": 1333.0, "moldCavity": 8.0, "itemTotalQuantity": 10664, "itemGoodQuantity": 10664, "changeType": "no_change", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.01 (MD50S-000)", "workingShift": 3, "moldNo": "14000CBQ-M-001", "moldShot": 1307.0, "moldCavity": 8.0, "itemTotalQuantity": 10456, "itemGoodQuantity": 10263, "changeType": "no_change", "defectQuantity": 193, "defectRate": 1.845830145371079},
    {"machineInfo": "NO.02 (MD50S-001)", "workingShift": 1, "moldNo": "15300CBG-M-001", "moldShot": 1678.0, "moldCavity": 2.0, "itemTotalQuantity": 3356, "itemGoodQuantity": 3320, "changeType": "no_change", "defectQuantity": 36, "defectRate": 1.072705601907032},
    {"machineInfo": "NO.02 (MD50S-001)", "workingShift": 2, "moldNo": "15300CBG-M-001", "moldShot": 1650.0, "moldCavity": 2.0, "itemTotalQuantity": 3300, "itemGoodQuantity": 3300, "changeType": "no_change", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.02 (MD50S-001)", "workingShift": 3, "moldNo": "15300CBG-M-001", "moldShot": 1665.0, "moldCavity": 2.0, "itemTotalQuantity": 3330, "itemGoodQuantity": 3330, "changeType": "no_change", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.03 (EC50ST-000)", "workingShift": 1, "moldNo": "PXNHC4-M-001", "moldShot": 1445.0, "moldCavity": 8.0, "itemTotalQuantity": 11560, "itemGoodQuantity": 11423, "changeType": "no_change", "defectQuantity": 137, "defectRate": 1.185121107266436},
    {"machineInfo": "NO.03 (EC50ST-000)", "workingShift": 2, "moldNo": "PXNHC4-M-001", "moldShot": 1542.0, "moldCavity": 8.0, "itemTotalQuantity": 12336, "itemGoodQuantity": 12018, "changeType": "no_change", "defectQuantity": 318, "defectRate": 2.577821011673151},
    {"machineInfo": "NO.03 (EC50ST-000)", "workingShift": 3, "moldNo": "PXNHC4-M-001", "moldShot": 1520.0, "moldCavity": 8.0, "itemTotalQuantity": 12160, "itemGoodQuantity": 11964, "changeType": "no_change", "defectQuantity": 196, "defectRate": 1.611842105263158},
    {"machineInfo": "NO.04 (J100ADS-000)", "workingShift": 1, "moldNo": "12004CBQ-M-002", "moldShot": 0.0, "moldCavity": null, "itemTotalQuantity": 0, "itemGoodQuantity": 0, "changeType": "machine_idle", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.04 (J100ADS-000)", "workingShift": 2, "moldNo": "12004CBQ-M-002", "moldShot": 0.0, "moldCavity": null, "itemTotalQuantity": 0, "itemGoodQuantity": 0, "changeType": "machine_idle", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.04 (J100ADS-000)", "workingShift": 3, "moldNo": "12004CBQ-M-002", "moldShot": 0.0, "moldCavity": null, "itemTotalQuantity": 0, "itemGoodQuantity": 0, "changeType": "machine_idle", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.05 (J100ADS-001)", "workingShift": 1, "moldNo": "14102CAJ-M-003", "moldShot": 1287.0, "moldCavity": 12.0, "itemTotalQuantity": 15444, "itemGoodQuantity": 15264, "changeType": "no_change", "defectQuantity": 180, "defectRate": 1.165501165501166},
    {"machineInfo": "NO.05 (J100ADS-001)", "workingShift": 2, "moldNo": "14102CAJ-M-003", "moldShot": 1308.0, "moldCavity": 12.0, "itemTotalQuantity": 15696, "itemGoodQuantity": 15126, "changeType": "no_change", "defectQuantity": 570, "defectRate": 3.631498470948012},
    {"machineInfo": "NO.05 (J100ADS-001)", "workingShift": 3, "moldNo": "14102CAJ-M-003", "moldShot": 274.0, "moldCavity": 12.0, "itemTotalQuantity": 3288, "itemGoodQuantity": 2327, "changeType": "no_change", "defectQuantity": 961, "defectRate": 29.22749391727494},
    {"machineInfo": "NO.06 (MD100S-000)", "workingShift": 1, "moldNo": "13100CAG-M-002", "moldShot": 1819.0, "moldCavity": 4.0, "itemTotalQuantity": 7276, "itemGoodQuantity": 5413, "changeType": "no_change", "defectQuantity": 1863, "defectRate": 25.6047278724574},
    {"machineInfo": "NO.06 (MD100S-000)", "workingShift": 2, "moldNo": "13100CAG-M-002", "moldShot": 1549.0, "moldCavity": 4.0, "itemTotalQuantity": 6196, "itemGoodQuantity": 4497, "changeType": "no_change", "defectQuantity": 1699, "defectRate": 27.42091672046482},
    {"machineInfo": "NO.06 (MD100S-000)", "workingShift": 3, "moldNo": "13100CAG-M-002", "moldShot": 1319.0, "moldCavity": 4.0, "itemTotalQuantity": 5276, "itemGoodQuantity": 3883, "changeType": "no_change", "defectQuantity": 1393, "defectRate": 26.40257771038666},
    {"machineInfo": "NO.07 (MD100S-001)", "workingShift": 2, "moldNo": "PSSCH-M-001", "moldShot": 590.0, "moldCavity": 8.0, "itemTotalQuantity": 4720, "itemGoodQuantity": 4323, "changeType": "no_change", "defectQuantity": 397, "defectRate": 8.411016949152543},
    {"machineInfo": "NO.07 (MD100S-001)", "workingShift": 3, "moldNo": "PSSCH-M-001", "moldShot": 834.0, "moldCavity": 8.0, "itemTotalQuantity": 6672, "itemGoodQuantity": 6534, "changeType": "no_change", "defectQuantity": 138, "defectRate": 2.068345323741007},
    {"machineInfo": "NO.08 (MD130S-000)", "workingShift": 1, "moldNo": "10100CBR-M-001", "moldShot": 580.5, "moldCavity": 4.0, "itemTotalQuantity": 4644, "itemGoodQuantity": 4424, "changeType": "color_change", "defectQuantity": 220, "defectRate": 4.737295434969854},
    {"machineInfo": "NO.08 (MD130S-000)", "workingShift": 2, "moldNo": "10100CBR-M-001", "moldShot": 1363.0, "moldCavity": 4.0, "itemTotalQuantity": 5452, "itemGoodQuantity": 5432, "changeType": "no_change", "defectQuantity": 20, "defectRate": 0.3668378576669112},
    {"machineInfo": "NO.08 (MD130S-000)", "workingShift": 3, "moldNo": "10100CBR-M-001", "moldShot": 1340.0, "moldCavity": 4.0, "itemTotalQuantity": 5360, "itemGoodQuantity": 5304, "changeType": "no_change", "defectQuantity": 56, "defectRate": 1.044776119402985},
    {"machineInfo": "NO.09 (MD130S-001)", "workingShift": 1, "moldNo": "14100CBR-M-001", "moldShot": 1265.0, "moldCavity": 8.0, "itemTotalQuantity": 10120, "itemGoodQuantity": 9977, "changeType": "no_change", "defectQuantity": 143, "defectRate": 1.41304347826087},
    {"machineInfo": "NO.09 (MD130S-001)", "workingShift": 2, "moldNo": "14100CBR-M-001", "moldShot": 1365.0, "moldCavity": 8.0, "itemTotalQuantity": 10920, "itemGoodQuantity": 10920, "changeType": "no_change", "defectQuantity": 0, "defectRate": 0.0},
    {"machineInfo": "NO.09 (MD130S-001)", "workingShift": 3, "moldNo": "14100CBR-M-001", "moldShot": 1327.0, "moldCavity": 8.0, "itemTotalQuantity": 10616, "itemGoodQuantity": 10419, "changeType": "no_change", "defectQuantity": 197, "defectRate": 1.855689525244913}
  ],
  "itemBasedRecords": [
    {"itemInfo": "24720317M (CT-CAX-UPPER-CASE-LIME)", "itemTotalQuantity": 13892, "itemGoodQuantity": 13816, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 3473, "avgCavity": 4.0, "usedComponentNums": 1, "defectQuantity": 76, "defectRate": 0.5470774546501583},
    {"itemInfo": "24720319M (CT-CAX-UPPER-CASE-PINK)", "itemTotalQuantity": 1564, "itemGoodQuantity": 1344, "usedMachineNums": 1, "totalShifts": 1, "usedMoldNums": 1, "moldTotalShots": 391, "avgCavity": 4.0, "usedComponentNums": 1, "defectQuantity": 220, "defectRate": 14.06649616368287},
    {"itemInfo": "24720327M (CT-CAX-BASE-COVER)", "itemTotalQuantity": 31656, "itemGoodQuantity": 31316, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 3957, "avgCavity": 8.0, "usedComponentNums": 1, "defectQuantity": 340, "defectRate": 1.074045994440233},
    {"itemInfo": "24720470M (CT-YCN-CLUCH-NL)", "itemTotalQuantity": 9986, "itemGoodQuantity": 9950, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 4993, "avgCavity": 2.0, "usedComponentNums": 1, "defectQuantity": 36, "defectRate": 0.3605047065892249},
    {"itemInfo": "26001122M (CT-CA-BASE-T.SMOKE(NO-PRINT))", "itemTotalQuantity": 31288, "itemGoodQuantity": 29480, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 3911, "avgCavity": 8.0, "usedComponentNums": 1, "defectQuantity": 1808, "defectRate": 5.778573254922015},
    {"itemInfo": "26004630M (CT-CA-PRINTER-HEAD-5.0MM-LIGHT-BLUE)", "itemTotalQuantity": 0, "itemGoodQuantity": 0, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 0, "avgCavity": null, "usedComponentNums": 1, "defectQuantity": 0, "defectRate": 0.0},
    {"itemInfo": "260501M (CT-PXN-HEAD-COVER-4.2MM)", "itemTotalQuantity": 36056, "itemGoodQuantity": 35405, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 4507, "avgCavity": 8.0, "usedComponentNums": 1, "defectQuantity": 651, "defectRate": 1.805524739294431},
    {"itemInfo": "261101M (CT-PXN-BASE-COVER-4.2&5.0MM)", "itemTotalQuantity": 34428, "itemGoodQuantity": 32717, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 2869, "avgCavity": 12.0, "usedComponentNums": 1, "defectQuantity": 1711, "defectRate": 4.969792029743232},
    {"itemInfo": "280301M (CT-PS-SLIDE-COVER-CLEAR)", "itemTotalQuantity": 18748, "itemGoodQuantity": 13793, "usedMachineNums": 1, "totalShifts": 3, "usedMoldNums": 1, "moldTotalShots": 4687, "avgCavity": 4.0, "usedComponentNums": 1, "defectQuantity": 4955, "defectRate": 26.42948581181993},
    {"itemInfo": "280601M (CT-PS-SCRAPER-HOLDER)", "itemTotalQuantity": 11392, "itemGoodQuantity": 10857, "usedMachineNums": 1, "totalShifts": 2, "usedMoldNums": 1, "moldTotalShots": 1424, "avgCavity": 8.0, "usedComponentNums": 1, "defectQuantity": 535, "defectRate": 4.696278089887641}
  ]
};
// ─────────────────────────────────────────────────────────────────────────────

// Map raw JSON fields → internal shape
const moldData = RAW_JSON.moldBasedRecords.map(r => ({
  machine:    r.machineInfo,
  shift:      r.workingShift,
  mold:       r.moldNo,
  shots:      r.moldShot,
  cavity:     r.moldCavity ?? null,
  total:      r.itemTotalQuantity,
  good:       r.itemGoodQuantity,
  defect:     r.defectQuantity,
  defectRate: r.defectRate,
  changeType: r.changeType,
}));

const itemData = RAW_JSON.itemBasedRecords.map(r => {
  const [code, ...rest] = r.itemInfo.split(" ");
  const name = rest.join(" ").replace(/^\(|\)$/g, "");
  return {
    item:       code,
    name,
    total:      r.itemTotalQuantity,
    good:       r.itemGoodQuantity,
    defect:     r.defectQuantity,
    defectRate: r.defectRate,
    machines:   r.usedMachineNums,
    shifts:     r.totalShifts,
    shots:      r.moldTotalShots,
    cavity:     r.avgCavity ?? null,
  };
});

const machines = [...new Set(moldData.map(r => r.machine))];

function getDefectColor(rate) {
  if (rate === 0) return "#22c55e";
  if (rate < 2) return "#86efac";
  if (rate < 5) return "#fbbf24";
  if (rate < 15) return "#f97316";
  return "#ef4444";
}

function getMachineStats(machine) {
  const rows = moldData.filter(r => r.machine === machine);
  const totalPcs = rows.reduce((s, r) => s + r.total, 0);
  const goodPcs = rows.reduce((s, r) => s + r.good, 0);
  const defectPcs = rows.reduce((s, r) => s + r.defect, 0);
  const defectRate = totalPcs > 0 ? (defectPcs / totalPcs) * 100 : 0;
  const isIdle = rows.every(r => r.changeType === "machine_idle");
  return { totalPcs, goodPcs, defectPcs, defectRate, isIdle, rows };
}

function MiniBar({ value, max, color }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div style={{ width: "100%", height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
    </div>
  );
}

function DefectGauge({ rate }) {
  const angle = Math.min(rate / 30, 1) * 180;
  const color = getDefectColor(rate);
  const r = 28;
  const cx = 36, cy = 36;
  const toRad = (deg) => (deg - 180) * Math.PI / 180;
  const x1 = cx + r * Math.cos(toRad(0));
  const y1 = cy + r * Math.sin(toRad(0));
  const x2 = cx + r * Math.cos(toRad(angle));
  const y2 = cy + r * Math.sin(toRad(angle));
  const large = angle > 90 ? 1 : 0;
  return (
    <svg width="72" height="42" viewBox="0 0 72 42">
      <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="#1e293b" strokeWidth="5" />
      {rate > 0 && <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${x2} ${y2}`} fill="none" stroke={color} strokeWidth="5" strokeLinecap="round" />}
      <text x={cx} y={cy - 4} textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="'DM Mono', monospace">{rate.toFixed(1)}%</text>
    </svg>
  );
}

export default function App() {
  const [view, setView] = useState("machine");
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [shiftFilter, setShiftFilter] = useState(0);

  const totalProduced = moldData.reduce((s, r) => s + r.total, 0);
  const totalGood = moldData.reduce((s, r) => s + r.good, 0);
  const totalDefect = moldData.reduce((s, r) => s + r.defect, 0);
  const overallDefectRate = totalProduced > 0 ? (totalDefect / totalProduced) * 100 : 0;

  const filteredMoldData = shiftFilter === 0 ? moldData : moldData.filter(r => r.shift === shiftFilter);

  return (
    <div style={{
      minHeight: "100vh", background: "#020b18",
      fontFamily: "'DM Mono', 'Courier New', monospace",
      color: "#e2e8f0", padding: "0"
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #0f172a; } ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        .card { background: #0c1a2e; border: 1px solid #1e3a5f; border-radius: 8px; transition: border-color 0.2s; }
        .card:hover { border-color: #2563eb; }
        .pill-btn { background: transparent; border: 1px solid #1e3a5f; border-radius: 4px; color: #64748b; padding: 5px 14px; cursor: pointer; font-family: inherit; font-size: 11px; letter-spacing: 0.05em; transition: all 0.15s; }
        .pill-btn.active { background: #1d4ed8; border-color: #2563eb; color: #fff; }
        .pill-btn:hover:not(.active) { border-color: #334155; color: #94a3b8; }
        .row-hover:hover { background: #0f1f35 !important; }
        @keyframes fadeIn { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }
        .fade-in { animation: fadeIn 0.4s ease forwards; }
        .alert-blink { animation: blink 1.5s ease-in-out infinite; }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
      `}</style>

      {/* HEADER */}
      <div style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f", padding: "16px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 3, height: 32, background: "#2563eb", borderRadius: 2 }} />
          <div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: "0.12em", color: "#60a5fa" }}>INJECTION MOLDING</div>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>PRODUCTION MONITORING SYSTEM</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} className="alert-blink" />
          <span style={{ fontSize: 10, color: "#475569", letterSpacing: "0.1em" }}>LIVE</span>
        </div>
      </div>

      <div style={{ padding: "20px 28px" }}>

        {/* KPI ROW */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }} className="fade-in">
          {[
            { label: "TOTAL PRODUCED", value: totalProduced.toLocaleString(), sub: "pcs", color: "#60a5fa" },
            { label: "GOOD OUTPUT", value: totalGood.toLocaleString(), sub: "pcs", color: "#22c55e" },
            { label: "TOTAL DEFECTS", value: totalDefect.toLocaleString(), sub: "pcs", color: "#f97316" },
            { label: "OVERALL DEFECT RATE", value: overallDefectRate.toFixed(2) + "%", sub: "avg", color: getDefectColor(overallDefectRate) },
          ].map(k => (
            <div key={k.label} className="card" style={{ padding: "14px 18px" }}>
              <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.15em", marginBottom: 6 }}>{k.label}</div>
              <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color: k.color, lineHeight: 1 }}>{k.value}</div>
              <div style={{ fontSize: 9, color: "#334155", marginTop: 2 }}>{k.sub}</div>
            </div>
          ))}
        </div>

        {/* VIEW TOGGLE */}
        <div style={{ display: "flex", gap: 6, marginBottom: 16, alignItems: "center" }}>
          <button className={`pill-btn ${view === "machine" ? "active" : ""}`} onClick={() => { setView("machine"); setSelectedMachine(null); }}>MACHINE VIEW</button>
          <button className={`pill-btn ${view === "item" ? "active" : ""}`} onClick={() => { setView("item"); setSelectedMachine(null); }}>ITEM VIEW</button>
          {view === "machine" && (
            <>
              <div style={{ width: 1, height: 20, background: "#1e3a5f", margin: "0 4px" }} />
              {[0, 1, 2, 3].map(s => (
                <button key={s} className={`pill-btn ${shiftFilter === s ? "active" : ""}`} onClick={() => setShiftFilter(s)}>
                  {s === 0 ? "ALL SHIFTS" : `SHIFT ${s}`}
                </button>
              ))}
            </>
          )}
        </div>

        {view === "machine" && !selectedMachine && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }} className="fade-in">
            {machines.map(machine => {
              const { totalPcs, goodPcs, defectPcs, defectRate, isIdle, rows } = getMachineStats(machine);
              const mNum = machine.split(" ")[0];
              const filteredRows = shiftFilter === 0 ? rows : rows.filter(r => r.shift === shiftFilter);
              const filtTotal = filteredRows.reduce((s, r) => s + r.total, 0);
              const filtGood = filteredRows.reduce((s, r) => s + r.good, 0);
              const filtDefect = filteredRows.reduce((s, r) => s + r.defect, 0);
              const filtRate = filtTotal > 0 ? (filtDefect / filtTotal) * 100 : 0;
              return (
                <div key={machine} className="card" style={{ padding: "16px", cursor: "pointer", opacity: isIdle ? 0.5 : 1, position: "relative", overflow: "hidden" }}
                  onClick={() => !isIdle && setSelectedMachine(machine)}>
                  {isIdle && <div style={{ position: "absolute", top: 8, right: 10, fontSize: 8, background: "#1e293b", color: "#64748b", padding: "2px 8px", borderRadius: 3, letterSpacing: "0.1em" }}>IDLE</div>}
                  {rows.some(r => r.changeType === "color_change") && <div style={{ position: "absolute", top: 8, right: 10, fontSize: 8, background: "#1e3a5f", color: "#60a5fa", padding: "2px 8px", borderRadius: 3, letterSpacing: "0.1em" }}>COLOR CHG</div>}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 20, color: "#93c5fd", letterSpacing: "0.08em" }}>{mNum}</div>
                      <div style={{ fontSize: 9, color: "#475569" }}>{machine.replace(mNum + " ", "")}</div>
                    </div>
                    <DefectGauge rate={filtRate} />
                  </div>
                  <div style={{ fontSize: 9, color: "#475569", marginBottom: 4 }}>MOLD: <span style={{ color: "#64748b" }}>{rows[0]?.mold}</span></div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginTop: 10 }}>
                    {[
                      { l: "TOTAL", v: filtTotal.toLocaleString(), c: "#60a5fa" },
                      { l: "GOOD", v: filtGood.toLocaleString(), c: "#22c55e" },
                      { l: "DEFECT", v: filtDefect.toLocaleString(), c: filtDefect > 0 ? "#f97316" : "#22c55e" },
                    ].map(s => (
                      <div key={s.l} style={{ textAlign: "center" }}>
                        <div style={{ fontSize: 14, fontWeight: 500, color: s.c }}>{s.v}</div>
                        <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.1em" }}>{s.l}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <MiniBar value={filtGood} max={filtTotal} color="#22c55e" />
                  </div>
                  {!isIdle && <div style={{ marginTop: 8, fontSize: 8, color: "#334155", textAlign: "right" }}>CLICK FOR DETAILS →</div>}
                </div>
              );
            })}
          </div>
        )}

        {view === "machine" && selectedMachine && (() => {
          const rows = moldData.filter(r => r.machine === selectedMachine);
          const { totalPcs, goodPcs, defectPcs, defectRate } = getMachineStats(selectedMachine);
          return (
            <div className="fade-in">
              <button className="pill-btn" style={{ marginBottom: 16 }} onClick={() => setSelectedMachine(null)}>← BACK TO ALL MACHINES</button>
              <div className="card" style={{ padding: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, color: "#93c5fd", letterSpacing: "0.1em" }}>{selectedMachine}</div>
                    <div style={{ fontSize: 9, color: "#475569" }}>MOLD: {rows[0]?.mold} | CAVITY: {rows[0]?.cavity ?? "N/A"}</div>
                  </div>
                  <DefectGauge rate={defectRate} />
                </div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #1e3a5f" }}>
                      {["SHIFT", "SHOTS", "CAVITY", "TOTAL PCS", "GOOD PCS", "DEFECT PCS", "DEFECT RATE", "STATUS"].map(h => (
                        <th key={h} style={{ padding: "6px 10px", textAlign: h === "SHIFT" ? "center" : "right", fontSize: 8, color: "#475569", letterSpacing: "0.12em", fontWeight: 500 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i} className="row-hover" style={{ borderBottom: "1px solid #0f1f35" }}>
                        <td style={{ padding: "10px", textAlign: "center" }}>
                          <div style={{ display: "inline-block", width: 24, height: 24, borderRadius: "50%", background: "#1e3a5f", color: "#93c5fd", fontSize: 11, lineHeight: "24px", fontWeight: 500 }}>{r.shift}</div>
                        </td>
                        {[r.shots, r.cavity ?? "—", r.total.toLocaleString(), r.good.toLocaleString()].map((v, j) => (
                          <td key={j} style={{ padding: "10px", textAlign: "right", color: "#94a3b8" }}>{v}</td>
                        ))}
                        <td style={{ padding: "10px", textAlign: "right", color: r.defect > 0 ? "#f97316" : "#334155" }}>{r.defect.toLocaleString()}</td>
                        <td style={{ padding: "10px", textAlign: "right" }}>
                          <span style={{ color: getDefectColor(r.defectRate), fontWeight: 500 }}>{r.defectRate.toFixed(2)}%</span>
                        </td>
                        <td style={{ padding: "10px", textAlign: "right" }}>
                          <span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: r.changeType === "machine_idle" ? "#1e293b" : r.changeType === "color_change" ? "#1e3a5f" : "#0a2a0a", color: r.changeType === "machine_idle" ? "#64748b" : r.changeType === "color_change" ? "#60a5fa" : "#22c55e", letterSpacing: "0.08em" }}>
                            {r.changeType === "machine_idle" ? "IDLE" : r.changeType === "color_change" ? "CLR CHG" : "RUNNING"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr style={{ borderTop: "1px solid #1e3a5f", background: "#060f1c" }}>
                      <td colSpan={3} style={{ padding: "10px", fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>TOTAL</td>
                      <td style={{ padding: "10px", textAlign: "right", color: "#60a5fa", fontWeight: 500 }}>{totalPcs.toLocaleString()}</td>
                      <td style={{ padding: "10px", textAlign: "right", color: "#22c55e", fontWeight: 500 }}>{goodPcs.toLocaleString()}</td>
                      <td style={{ padding: "10px", textAlign: "right", color: defectPcs > 0 ? "#f97316" : "#334155", fontWeight: 500 }}>{defectPcs.toLocaleString()}</td>
                      <td style={{ padding: "10px", textAlign: "right", color: getDefectColor(defectRate), fontWeight: 500 }}>{defectRate.toFixed(2)}%</td>
                      <td />
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          );
        })()}

        {view === "item" && (
          <div className="fade-in">
            <div className="card" style={{ overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f" }}>
                    {["ITEM CODE", "DESCRIPTION", "TOTAL PCS", "GOOD PCS", "DEFECT PCS", "DEFECT RATE", "SHOTS", "CAVITY", "SHIFTS"].map(h => (
                      <th key={h} style={{ padding: "10px 14px", textAlign: h === "ITEM CODE" || h === "DESCRIPTION" ? "left" : "right", fontSize: 8, color: "#475569", letterSpacing: "0.12em", fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {itemData.map((item, i) => (
                    <tr key={i} className="row-hover" style={{ borderBottom: "1px solid #0a1a2e", background: i % 2 === 0 ? "transparent" : "#060e1a" }}>
                      <td style={{ padding: "10px 14px", color: "#93c5fd", fontWeight: 500 }}>{item.item}</td>
                      <td style={{ padding: "10px 14px", color: "#64748b", fontSize: 10, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.name}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: "#94a3b8" }}>{item.total.toLocaleString()}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: "#22c55e" }}>{item.good.toLocaleString()}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: item.defect > 0 ? "#f97316" : "#334155" }}>{item.defect.toLocaleString()}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
                          <div style={{ width: 60, height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                            <div style={{ width: `${Math.min(item.defectRate / 30 * 100, 100)}%`, height: "100%", background: getDefectColor(item.defectRate), borderRadius: 2 }} />
                          </div>
                          <span style={{ color: getDefectColor(item.defectRate), fontWeight: 500, minWidth: 45, textAlign: "right" }}>{item.defectRate.toFixed(2)}%</span>
                        </div>
                      </td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: "#64748b" }}>{item.shots.toLocaleString()}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right", color: "#64748b" }}>{item.cavity ?? "—"}</td>
                      <td style={{ padding: "10px 14px", textAlign: "right" }}>
                        <div style={{ display: "flex", gap: 3, justifyContent: "flex-end" }}>
                          {[1, 2, 3].map(s => <div key={s} style={{ width: 8, height: 8, borderRadius: 2, background: item.shifts >= s ? "#1d4ed8" : "#1e293b" }} />)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}