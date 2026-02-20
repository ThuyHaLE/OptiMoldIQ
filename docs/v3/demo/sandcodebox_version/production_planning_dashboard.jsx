import { useState } from "react";

// ── RAW JSON — paste API response here, or replace with: const RAW_JSON = await response.json() ──
const RAW_JSON = {
  "producing_pro_plan": [
    { "machineNo": "NO.01", "machineCode": "MD50S-000", "machineName": "MD50S", "machineTonnage": 50, "itemName_poNo": "CT-CA-BASE-NL(NO-PRINT) (IM1901040)", "remainTime": 4.019 },
    { "machineNo": "NO.02", "machineCode": "MD50S-001", "machineName": "MD50S", "machineTonnage": 50, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.03", "machineCode": "EC50ST-000", "machineName": "EC50ST", "machineTonnage": 50, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.04", "machineCode": "J100ADS-000", "machineName": "J100ADS", "machineTonnage": 100, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.05", "machineCode": "J100ADS-001", "machineName": "J100ADS", "machineTonnage": 100, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.06", "machineCode": "MD100S-000", "machineName": "MD100S", "machineTonnage": 100, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.07", "machineCode": "MD100S-001", "machineName": "MD100S", "machineTonnage": 100, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.08", "machineCode": "MD130S-000", "machineName": "MD130S", "machineTonnage": 130, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.09", "machineCode": "MD130S-001", "machineName": "MD130S", "machineTonnage": 130, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.10", "machineCode": "CNS50-000", "machineName": "CNS50", "machineTonnage": 50, "itemName_poNo": null, "remainTime": null },
    { "machineNo": "NO.11", "machineCode": "CNS50-001", "machineName": "CNS50", "machineTonnage": 50, "itemName_poNo": null, "remainTime": null }
  ],
  "producing_mold_plan": [
    { "machineNo": "NO.01", "machineCode": "MD50S-000", "machineName": "MD50S", "machineTonnage": 50, "moldName": "CT-CA-BASE-M-0001", "remainTime": 4.019 },
    { "machineNo": "NO.02", "machineCode": "MD50S-001", "machineName": "MD50S", "machineTonnage": 50, "moldName": null, "remainTime": null },
    { "machineNo": "NO.03", "machineCode": "EC50ST-000", "machineName": "EC50ST", "machineTonnage": 50, "moldName": null, "remainTime": null },
    { "machineNo": "NO.04", "machineCode": "J100ADS-000", "machineName": "J100ADS", "machineTonnage": 100, "moldName": null, "remainTime": null },
    { "machineNo": "NO.05", "machineCode": "J100ADS-001", "machineName": "J100ADS", "machineTonnage": 100, "moldName": null, "remainTime": null },
    { "machineNo": "NO.06", "machineCode": "MD100S-000", "machineName": "MD100S", "machineTonnage": 100, "moldName": null, "remainTime": null },
    { "machineNo": "NO.07", "machineCode": "MD100S-001", "machineName": "MD100S", "machineTonnage": 100, "moldName": null, "remainTime": null },
    { "machineNo": "NO.08", "machineCode": "MD130S-000", "machineName": "MD130S", "machineTonnage": 130, "moldName": null, "remainTime": null },
    { "machineNo": "NO.09", "machineCode": "MD130S-001", "machineName": "MD130S", "machineTonnage": 130, "moldName": null, "remainTime": null },
    { "machineNo": "NO.10", "machineCode": "CNS50-000", "machineName": "CNS50", "machineTonnage": 50, "moldName": null, "remainTime": null },
    { "machineNo": "NO.11", "machineCode": "CNS50-001", "machineName": "CNS50", "machineTonnage": 50, "moldName": null, "remainTime": null }
  ],
  "producing_plastic_plan": [
    { "machineNo": "NO.01", "machineCode": "MD50S-000", "machineName": "MD50S", "machineTonnage": 50, "itemName_poNo": "CT-CA-BASE-NL(NO-PRINT) (IM1901040)", "estimatedOutputQuantity": 38400, "plasticResin": "ABS-PA-758-T.NL", "estimatedPlasticResinQuantity": 87.4752, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.02", "machineCode": "MD50S-001", "machineName": "MD50S", "machineTonnage": 50, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.03", "machineCode": "EC50ST-000", "machineName": "EC50ST", "machineTonnage": 50, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.04", "machineCode": "J100ADS-000", "machineName": "J100ADS", "machineTonnage": 100, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.05", "machineCode": "J100ADS-001", "machineName": "J100ADS", "machineTonnage": 100, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.06", "machineCode": "MD100S-000", "machineName": "MD100S", "machineTonnage": 100, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.07", "machineCode": "MD100S-001", "machineName": "MD100S", "machineTonnage": 100, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.08", "machineCode": "MD130S-000", "machineName": "MD130S", "machineTonnage": 130, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.09", "machineCode": "MD130S-001", "machineName": "MD130S", "machineTonnage": 130, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.10", "machineCode": "CNS50-000", "machineName": "CNS50", "machineTonnage": 50, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 },
    { "machineNo": "NO.11", "machineCode": "CNS50-001", "machineName": "CNS50", "machineTonnage": 50, "itemName_poNo": null, "estimatedOutputQuantity": null, "plasticResin": "NONE", "estimatedPlasticResinQuantity": 0, "colorMasterbatch": "NONE", "estimatedColorMasterbatchQuantity": 0, "additiveMasterbatch": "NONE", "estimatedAdditiveMasterbatchQuantity": 0 }
  ],
  "initial_plan": [
    { "Machine No.": "NO.01", "Machine Code": "MD50S-000", "Assigned Mold": null, "PO No.": null, "Item Name": null, "PO Quantity": 0, "ETA (PO Date)": null, "Mold Lead Time": 0, "Priority in Machine": 0, "Note": "histBased" },
    { "Machine No.": "NO.02", "Machine Code": "MD50S-001", "Assigned Mold": "20102IBE-M-001", "PO No.": "IM1902047", "Item Name": "AB-TP-SMALL-CAP-062-YW", "PO Quantity": 22000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 1, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.03", "Machine Code": "EC50ST-000", "Assigned Mold": null, "PO No.": null, "Item Name": null, "PO Quantity": 0, "ETA (PO Date)": null, "Mold Lead Time": 0, "Priority in Machine": 0, "Note": "histBased" },
    { "Machine No.": "NO.04", "Machine Code": "J100ADS-000", "Assigned Mold": "14000CBR-M-001", "PO No.": "IM1902119", "Item Name": "CT-CAX-CARTRIDGE-BASE", "PO Quantity": 340000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 13, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.05", "Machine Code": "J100ADS-001", "Assigned Mold": "15000CBR-M-001", "PO No.": "IM1902121", "Item Name": "CT-CAX-REEL", "PO Quantity": 410000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 23, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.06", "Machine Code": "MD100S-000", "Assigned Mold": "12000CBS-M-001", "PO No.": "IM1812004", "Item Name": "CT-YA-PRINTER-HEAD-4.2MM", "PO Quantity": 2516, "ETA (PO Date)": "2018-12-31", "Mold Lead Time": 1, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.06", "Machine Code": "MD100S-000", "Assigned Mold": "20101IBE-M-001", "PO No.": "IM1902001", "Item Name": "AB-TP-LARGE-CAP-027-BG", "PO Quantity": 2000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 1, "Priority in Machine": 2, "Note": "histBased" },
    { "Machine No.": "NO.06", "Machine Code": "MD100S-000", "Assigned Mold": "20101IBE-M-001", "PO No.": "IM1902002", "Item Name": "AB-TP-LARGE-CAP-055-YW", "PO Quantity": 15000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 1, "Priority in Machine": 3, "Note": "histBased" },
    { "Machine No.": "NO.07", "Machine Code": "MD100S-001", "Assigned Mold": "10000CBR-M-001", "PO No.": "IM1902118", "Item Name": "CT-CAX-LOWER-CASE-PINK", "PO Quantity": 155000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 16, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.08", "Machine Code": "MD130S-000", "Assigned Mold": "10100CBR-M-001", "PO No.": "IM1902116", "Item Name": "CT-CAX-UPPER-CASE-PINK", "PO Quantity": 180000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 14, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.09", "Machine Code": "MD130S-001", "Assigned Mold": "20400IBE-M-001", "PO No.": "IM1901020", "Item Name": "AB-TP-BODY", "PO Quantity": 10000, "ETA (PO Date)": "2019-01-15", "Mold Lead Time": 1, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.09", "Machine Code": "MD130S-001", "Assigned Mold": "14100CBR-M-001", "PO No.": "IM1902120", "Item Name": "CT-CAX-BASE-COVER", "PO Quantity": 175000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 7, "Priority in Machine": 2, "Note": "histBased" },
    { "Machine No.": "NO.10", "Machine Code": "CNS50-000", "Assigned Mold": "PSSP-M-001", "PO No.": "IM1902134", "Item Name": "CT-PS-SPACER", "PO Quantity": 30000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 1, "Priority in Machine": 1, "Note": "histBased" },
    { "Machine No.": "NO.11", "Machine Code": "CNS50-001", "Assigned Mold": "PXNHC4-M-001", "PO No.": "IM1902129", "Item Name": "CT-PXN-HEAD-COVER-4.2MM", "PO Quantity": 55000, "ETA (PO Date)": "2019-02-20", "Mold Lead Time": 2, "Priority in Machine": 1, "Note": "histBased" }
  ]
};
// ─────────────────────────────────────────────────────────────────────────────

// Map RAW_JSON → internal DATA shape (key names preserved, NaT → null)
const DATA = {
  producing_pro_plan:     RAW_JSON.producing_pro_plan,
  producing_mold_plan:    RAW_JSON.producing_mold_plan,
  producing_plastic_plan: RAW_JSON.producing_plastic_plan,
  initial_plan:           RAW_JSON.initial_plan.map(r => ({
    ...r,
    "ETA (PO Date)": r["ETA (PO Date)"] === "NaT" ? null : r["ETA (PO Date)"],
  })),
};

// ─────────────────────────────────────────────────────────────────────────────
// UI below — nothing changed from original
// ─────────────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "producing", label: "🏭 Producing POs" },
  { id: "pending",   label: "📋 Pending POs"   },
];

const tonnageColor = (t) => {
  if (t >= 130) return "#ff6b35";
  if (t >= 100) return "#f7c59f";
  if (t >= 50)  return "#a8d8ea";
  return "#d4edda";
};

const Badge = ({ children, color = "#334155", bg = "#e2e8f0" }) => (
  <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 9999, fontSize: 11, fontWeight: 700, color, background: bg, letterSpacing: "0.04em", whiteSpace: "nowrap" }}>
    {children}
  </span>
);

const StatusDot = ({ active }) => (
  <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: active ? "#22c55e" : "#94a3b8", boxShadow: active ? "0 0 6px #22c55e" : "none", marginRight: 6, flexShrink: 0 }} />
);

function PendingTab({ allMachinesForPending, totalPendingPOs }) {
  const [expandedMachines, setExpandedMachines] = useState({});
  const toggle = (code) => setExpandedMachines(prev => ({ ...prev, [code]: !prev[code] }));

  const COL_HEADERS = ["Machine", "PO No.", "Item Name", "Mold", "PO Qty", "ETA", "Lead Time", "Priority"];

  const renderPOCells = (p) => (
    <>
      <td style={{ padding: "10px 14px", color: "#fbbf24", fontWeight: 600 }}>{p["PO No."]}</td>
      <td style={{ padding: "10px 14px", color: "#e2e8f0", maxWidth: 220 }}>{p["Item Name"]}</td>
      <td style={{ padding: "10px 14px", color: "#a5f3fc", fontSize: 11 }}>{p["Assigned Mold"]}</td>
      <td style={{ padding: "10px 14px", color: "#f1f5f9", fontWeight: 600, textAlign: "right" }}>{p["PO Quantity"]?.toLocaleString()}</td>
      <td style={{ padding: "10px 14px", whiteSpace: "nowrap" }}>
        {p["ETA (PO Date)"] ? <Badge bg="#1e3a5f" color="#93c5fd">{p["ETA (PO Date)"]}</Badge> : "—"}
      </td>
      <td style={{ padding: "10px 14px", textAlign: "center" }}><Badge bg="#292524" color="#a8a29e">{p["Mold Lead Time"]}d</Badge></td>
      <td style={{ padding: "10px 14px", textAlign: "center" }}>
        <Badge bg={p["Priority in Machine"] === 1 ? "#14532d33" : "#1c1917"} color={p["Priority in Machine"] === 1 ? "#22c55e" : "#78716c"}>
          P{p["Priority in Machine"]}
        </Badge>
      </td>
    </>
  );

  return (
    <div>
      <div style={{ fontSize: 11, color: "#64748b", marginBottom: 16, letterSpacing: "0.1em" }}>
        INITIAL PLAN — {totalPendingPOs} PENDING POs — ALL {allMachinesForPending.length} MACHINES
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#1e293b", color: "#64748b", textAlign: "left" }}>
              {COL_HEADERS.map(h => (
                <th key={h} style={{ padding: "10px 14px", fontWeight: 600, letterSpacing: "0.06em", fontSize: 11, borderBottom: "1px solid #334155", whiteSpace: "nowrap" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allMachinesForPending.map(({ machine, plans }, groupIdx) => {
              const validPlans = plans.filter(p => p["PO No."]);
              const p1 = validPlans[0] || null;
              const extraPlans = validPlans.slice(1);
              const hasExtra = extraPlans.length > 0;
              const isExpanded = !!expandedMachines[machine.machineCode];
              const bgMain = groupIdx % 2 === 0 ? "#0f172a" : "#111827";

              const machineCell = (
                <td style={{ padding: "10px 14px", whiteSpace: "nowrap", verticalAlign: "middle" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <StatusDot active={!!machine.itemName_poNo} />
                    <div>
                      <span style={{ fontWeight: 700, color: "#38bdf8" }}>{machine.machineNo}</span>
                      <span style={{ color: "#475569", marginLeft: 6, fontSize: 10 }}>{machine.machineCode}</span>
                    </div>
                  </div>
                </td>
              );

              return (
                <>
                  <tr key={`${machine.machineCode}-p1`} className="po-row"
                    onClick={hasExtra ? () => toggle(machine.machineCode) : undefined}
                    style={{ borderBottom: isExpanded ? "none" : "1px solid #1e293b", background: bgMain, opacity: p1 ? 1 : 0.45, cursor: hasExtra ? "pointer" : "default" }}>
                    {machineCell}
                    {p1 ? renderPOCells(p1) : (
                      <td colSpan={7} style={{ padding: "10px 14px", color: "#334155", fontStyle: "italic", fontSize: 11 }}>— No pending plan assigned —</td>
                    )}
                  </tr>

                  {hasExtra && (
                    <tr key={`${machine.machineCode}-hint`}
                      style={{ borderBottom: isExpanded ? "none" : "1px solid #1e293b", background: bgMain, cursor: "pointer" }}
                      onClick={() => toggle(machine.machineCode)}>
                      <td style={{ padding: "4px 14px 8px" }}>
                        {isExpanded
                          ? <span style={{ fontSize: 10, color: "#64748b", letterSpacing: "0.06em", display: "inline-flex", alignItems: "center", gap: 5, background: "#1e293b", borderRadius: 6, padding: "3px 10px", border: "1px solid #334155", whiteSpace: "nowrap" }}>▲ collapse</span>
                          : <span style={{ fontSize: 10, color: "#38bdf8", letterSpacing: "0.06em", display: "inline-flex", alignItems: "center", gap: 5, background: "#0c2a3e", borderRadius: 6, padding: "3px 10px", border: "1px solid #1e4d6b", whiteSpace: "nowrap" }}>
                              ▼ +{extraPlans.length} more PO{extraPlans.length > 1 ? "s" : ""} (P{extraPlans.map(e => e["Priority in Machine"]).join(", P")})
                            </span>
                        }
                      </td>
                      <td colSpan={7} />
                    </tr>
                  )}

                  {hasExtra && isExpanded && extraPlans.map((ep, ei) => (
                    <tr key={`${machine.machineCode}-ex-${ei}`} className="po-row"
                      style={{ borderBottom: ei === extraPlans.length - 1 ? "1px solid #1e293b" : "1px solid #0f172a", background: "#0a1628" }}>
                      <td style={{ padding: "8px 14px", verticalAlign: "middle" }}>
                        <span style={{ fontSize: 11, color: "#334155" }}>└ {machine.machineNo}</span>
                      </td>
                      {renderPOCells(ep)}
                    </tr>
                  ))}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("producing");
  const [expandedMachine, setExpandedMachine] = useState(null);

  const machineList = DATA.producing_pro_plan.map(m => {
    const mold    = DATA.producing_mold_plan.find(x => x.machineCode === m.machineCode);
    const plastic = DATA.producing_plastic_plan.find(x => x.machineCode === m.machineCode);
    return { ...m, moldName: mold?.moldName, plastic };
  });

  const pendingByMachine = {};
  DATA.initial_plan.forEach(p => {
    const mc = p["Machine Code"];
    if (!pendingByMachine[mc]) pendingByMachine[mc] = [];
    pendingByMachine[mc].push(p);
  });

  const allMachinesForPending = machineList.map(m => ({
    machine: m,
    plans: pendingByMachine[m.machineCode] || [],
  }));

  const activeMachines = machineList.filter(m => m.itemName_poNo);
  const idleMachines   = machineList.filter(m => !m.itemName_poNo);
  const totalPendingPOs = DATA.initial_plan.filter(p => p["PO No."]).length;

  return (
    <div style={{ minHeight: "100vh", background: "#0f172a", fontFamily: "'IBM Plex Mono', 'Courier New', monospace", color: "#e2e8f0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #1e293b; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
        .tab-btn { cursor: pointer; border: none; background: none; transition: all 0.2s; }
        .tab-btn:hover { background: #1e293b !important; }
        .machine-card { transition: all 0.2s; cursor: pointer; }
        .machine-card:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important; }
        .po-row:hover { background: #162032 !important; }
      `}</style>

      {/* Header */}
      <div style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)", borderBottom: "1px solid #334155", padding: "20px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", letterSpacing: "0.15em", marginBottom: 4 }}>INJECTION MOLDING</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: "#f1f5f9", letterSpacing: "-0.02em" }}>PRODUCTION PLANNING DASHBOARD</div>
        </div>
        <div style={{ display: "flex", gap: 20 }}>
          {[{ label: "ACTIVE", value: activeMachines.length, color: "#22c55e" }, { label: "IDLE", value: idleMachines.length, color: "#64748b" }, { label: "TOTAL", value: machineList.length, color: "#f1f5f9" }].map((s, i) => (
            <>
              {i > 0 && <div key={`div-${i}`} style={{ width: 1, background: "#334155" }} />}
              <div key={s.label} style={{ textAlign: "right" }}>
                <div style={{ fontSize: 10, color: "#64748b", marginBottom: 2 }}>{s.label}</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
              </div>
            </>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid #334155", background: "#0f172a", padding: "0 28px" }}>
        {TABS.map(t => (
          <button key={t.id} className="tab-btn" onClick={() => setTab(t.id)}
            style={{ padding: "12px 20px", fontSize: 12, fontWeight: 600, color: tab === t.id ? "#38bdf8" : "#64748b", borderBottom: tab === t.id ? "2px solid #38bdf8" : "2px solid transparent", letterSpacing: "0.05em", background: tab === t.id ? "#0f1f2e" : "none" }}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ padding: "24px 28px" }}>
        {tab === "producing" && (
          <div>
            <div style={{ fontSize: 11, color: "#64748b", marginBottom: 16, letterSpacing: "0.1em" }}>
              MACHINE STATUS — {activeMachines.length} RUNNING / {idleMachines.length} IDLE
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
              {machineList.map(m => {
                const active = !!m.itemName_poNo;
                const isExpanded = expandedMachine === m.machineCode;
                const plastic = m.plastic;
                return (
                  <div key={m.machineCode} className="machine-card"
                    onClick={() => setExpandedMachine(isExpanded ? null : m.machineCode)}
                    style={{ background: active ? "#0d2137" : "#141c2a", border: active ? "1px solid #1e4d6b" : "1px solid #1e293b", borderRadius: 10, padding: "16px", boxShadow: active ? "0 2px 12px rgba(56,189,248,0.08)" : "none" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <StatusDot active={active} />
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 14, color: "#f1f5f9" }}>{m.machineNo}</div>
                          <div style={{ fontSize: 11, color: "#64748b" }}>{m.machineName}</div>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                        <Badge bg={tonnageColor(m.machineTonnage) + "33"} color={tonnageColor(m.machineTonnage)}>{m.machineTonnage}T</Badge>
                        {active && <Badge bg="#14532d33" color="#22c55e">RUNNING</Badge>}
                      </div>
                    </div>

                    {active ? (
                      <>
                        <div style={{ background: "#0a1628", borderRadius: 7, padding: "10px 12px", marginBottom: 8 }}>
                          <div style={{ fontSize: 10, color: "#64748b", marginBottom: 3, letterSpacing: "0.08em" }}>CURRENT JOB</div>
                          <div style={{ fontSize: 12, color: "#e2e8f0", wordBreak: "break-all", lineHeight: 1.5 }}>{m.itemName_poNo}</div>
                        </div>
                        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                          <div style={{ flex: 1, background: "#0a1628", borderRadius: 7, padding: "8px 10px" }}>
                            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 2 }}>MOLD</div>
                            <div style={{ fontSize: 11, color: "#a5f3fc" }}>{m.moldName || "—"}</div>
                          </div>
                          <div style={{ flex: 1, background: "#0a1628", borderRadius: 7, padding: "8px 10px" }}>
                            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 2 }}>REMAIN (hrs)</div>
                            <div style={{ fontSize: 18, fontWeight: 700, color: "#fbbf24" }}>{m.remainTime?.toFixed(2) ?? "—"}</div>
                          </div>
                        </div>
                        {isExpanded && plastic?.estimatedOutputQuantity && (
                          <div style={{ background: "#0a1628", borderRadius: 7, padding: "10px 12px", marginTop: 4, fontSize: 11 }}>
                            <div style={{ fontSize: 10, color: "#64748b", marginBottom: 6, letterSpacing: "0.08em" }}>PLASTIC DETAILS</div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 12px", color: "#cbd5e1" }}>
                              <div><span style={{ color: "#64748b" }}>Output Qty: </span>{plastic.estimatedOutputQuantity?.toLocaleString()}</div>
                              <div><span style={{ color: "#64748b" }}>Resin: </span><span style={{ color: "#a5f3fc" }}>{plastic.plasticResin}</span></div>
                              <div><span style={{ color: "#64748b" }}>Resin Qty (kg): </span>{plastic.estimatedPlasticResinQuantity}</div>
                              <div><span style={{ color: "#64748b" }}>Color MB: </span>{plastic.colorMasterbatch}</div>
                            </div>
                          </div>
                        )}
                        <div style={{ textAlign: "right", fontSize: 10, color: "#334155", marginTop: 6 }}>{isExpanded ? "▲ collapse" : "▼ expand"}</div>
                      </>
                    ) : (
                      <div style={{ color: "#334155", fontSize: 12, paddingTop: 4 }}>No active job assigned</div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "pending" && (
          <PendingTab allMachinesForPending={allMachinesForPending} totalPendingPOs={totalPendingPOs} />
        )}
      </div>
    </div>
  );
}