import { useState, useMemo } from "react";

const RAW_JSON = {
    "finishedRecords":[
        {"poReceivedDate":"2018-12-01","poNo":"IM1812001","poETA":"2018-12-31","itemCode":"10236M","itemName":"AB-TP-BODY","itemQuantity":5840,"firstRecord":"2018-12-12","lastRecord":"2018-12-31","itemGoodQuantity":5840,"moldHist":"20400IBE-M-001","proStatus":"finished","is_backlog":true,"itemNGQuantity":280,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
        {"poReceivedDate":"2018-12-01","poNo":"IM1812009","poETA":"2018-12-31","itemCode":"24720316M","itemName":"CT-CAX-UPPER-CASE-NL","itemQuantity":4930,"firstRecord":"2018-12-31","lastRecord":"2018-12-31","itemGoodQuantity":4930,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":true,"itemNGQuantity":110,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
        {"poReceivedDate":"2018-12-01","poNo":"IM1812024","poETA":"2018-12-31","itemCode":"26003170M","itemName":"CT-CA-BASE-NL(NO-PRINT)","itemQuantity":27000,"firstRecord":"2018-12-19","lastRecord":"2018-12-31","itemGoodQuantity":27000,"moldHist":"14000CBQ-M-001","proStatus":"finished","is_backlog":true,"itemNGQuantity":7448,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901005","poETA":"2019-01-15","itemCode":"10315M","itemName":"AB-TP-LARGE-CAP-879-BN","itemQuantity":2500,"firstRecord":"2019-01-02","lastRecord":"2019-01-02","itemGoodQuantity":2500,"moldHist":"20101IBE-M-002","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901006","poETA":"2019-01-15","itemCode":"10318M","itemName":"AB-TP-LARGE-CAP-910-PK","itemQuantity":5000,"firstRecord":"2019-01-02","lastRecord":"2019-01-02","itemGoodQuantity":5000,"moldHist":"20101IBE-M-002","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901023","poETA":"2019-01-15","itemCode":"24720316M","itemName":"CT-CAX-UPPER-CASE-NL","itemQuantity":90000,"firstRecord":"2019-01-02","lastRecord":"2019-01-11","itemGoodQuantity":90000,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901029","poETA":"2019-01-15","itemCode":"24720324M","itemName":"CT-CAX-LOCK-BUTTON-NL","itemQuantity":135000,"firstRecord":"2019-01-02","lastRecord":"2019-01-10","itemGoodQuantity":135000,"moldHist":"16500CBR-M-001","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901007","poETA":"2019-01-30","itemCode":"10332M","itemName":"AB-TP-LARGE-CAP-N15-BK","itemQuantity":2500,"firstRecord":"2019-01-03","lastRecord":"2019-01-03","itemGoodQuantity":2500,"moldHist":"20101IBE-M-002","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901062","poETA":"2019-01-30","itemCode":"290801M","itemName":"CT-PGX-PRINTER-HEAD-4.2MM-GREEN","itemQuantity":85000,"firstRecord":"2019-01-03","lastRecord":"2019-01-07","itemGoodQuantity":85000,"moldHist":"PGXPH42-M-001","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901022","poETA":"2019-01-30","itemCode":"24720312M","itemName":"CT-YA-BASE","itemQuantity":35000,"firstRecord":"2019-01-03","lastRecord":"2019-01-07","itemGoodQuantity":35000,"moldHist":"14000CBS-M-001","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901041","poETA":"2019-01-30","itemCode":"26004620M","itemName":"CT-CA-PRINTER-HEAD-5.0MM-RED","itemQuantity":60000,"firstRecord":"2019-01-07","lastRecord":"2019-01-08","itemGoodQuantity":60000,"moldHist":"12004CBQ-M-002","proStatus":"finished","is_backlog":false,"itemNGQuantity":null,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"}
    ],
    "unfinishedRecords":[
        {"poReceivedDate":"2019-01-02","poNo":"IM1901027","poETA":"2019-01-30","itemCode":"24720321M","itemName":"CT-CAX-LOWER-CASE-LIME","itemQuantity":85000,"itemGoodQuantity":null,"itemRemainQuantity":85000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":5.41},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901028","poETA":"2019-01-30","itemCode":"24720323M","itemName":"CT-CAX-LOWER-CASE-PINK","itemQuantity":50000,"itemGoodQuantity":null,"itemRemainQuantity":50000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":8.59},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901024","poETA":"2019-01-30","itemCode":"24720317M","itemName":"CT-CAX-UPPER-CASE-LIME","itemQuantity":80000,"itemGoodQuantity":40912,"itemRemainQuantity":39088,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.51,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":2.71},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901025","poETA":"2019-01-30","itemCode":"24720318M","itemName":"CT-CAX-UPPER-CASE-BLUE","itemQuantity":100000,"itemGoodQuantity":null,"itemRemainQuantity":100000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":9.66},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901026","poETA":"2019-01-30","itemCode":"24720319M","itemName":"CT-CAX-UPPER-CASE-PINK","itemQuantity":20000,"itemGoodQuantity":null,"itemRemainQuantity":20000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.0,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":11.05},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901038","poETA":"2019-01-30","itemCode":"24720469M","itemName":"CT-YCN-LARGE-GEAR-WHITE","itemQuantity":80000,"itemGoodQuantity":21370,"itemRemainQuantity":58630,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.27,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":3.05},
        {"poReceivedDate":"2018-12-01","poNo":"IM1812004","poETA":"2018-12-31","itemCode":"24720309M","itemName":"CT-YA-PRINTER-HEAD-4.2MM","itemQuantity":2516,"itemGoodQuantity":null,"itemRemainQuantity":2516,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":true,"itemNGQuantity":null,"completionProgress":0.0,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":0.12},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901043","poETA":"2019-01-30","itemCode":"26004670M","itemName":"CT-CA-PRINTER-HEAD-5.0MM-SILVER","itemQuantity":900000,"itemGoodQuantity":470537,"itemRemainQuantity":429463,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.52,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":6.21},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901042","poETA":"2019-01-15","itemCode":"26004650M","itemName":"CT-CA-PRINTER-HEAD-6.0MM-BLUE","itemQuantity":75000,"itemGoodQuantity":39500,"itemRemainQuantity":35500,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.53,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":0.49},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901040","poETA":"2019-01-30","itemCode":"26003170M","itemName":"CT-CA-BASE-NL(NO-PRINT)","itemQuantity":500000,"itemGoodQuantity":196650,"itemRemainQuantity":303350,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.39,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":7.9},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901031","poETA":"2019-01-30","itemCode":"24720326M","itemName":"CT-CAX-CARTRIDGE-BASE","itemQuantity":445000,"itemGoodQuantity":85337,"itemRemainQuantity":359663,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.19,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":12.49},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901032","poETA":"2019-01-15","itemCode":"24720327M","itemName":"CT-CAX-BASE-COVER","itemQuantity":545000,"itemGoodQuantity":179062,"itemRemainQuantity":365938,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.33,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":12.71},
        {"poReceivedDate":"2018-12-20","poNo":"IM1901033","poETA":"2019-01-15","itemCode":"24720328M","itemName":"CT-CAX-REEL","itemQuantity":530000,"itemGoodQuantity":216527,"itemRemainQuantity":313473,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.41,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":10.43},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901020","poETA":"2019-01-15","itemCode":"10236M","itemName":"AB-TP-BODY","itemQuantity":110000,"itemGoodQuantity":92707,"itemRemainQuantity":17293,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.84,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":1.8},
        {"poReceivedDate":"2019-01-02","poNo":"IM1901045","poETA":"2019-01-30","itemCode":"261301M","itemName":"CT-PXN-LARGE-GEAR-4.2&5.0MM","itemQuantity":105000,"itemGoodQuantity":69837,"itemRemainQuantity":35163,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"itemNGQuantity":null,"completionProgress":0.67,"etaStatus":"ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":1.07}
    ]
    };

const allRecords = [
  ...RAW_JSON.finishedRecords.map(r => ({ ...r, category: "finished", completionProgress: 1.0 })),
  ...RAW_JSON.unfinishedRecords.map(r => ({ ...r, category: "unfinished" }))
];

function getEtaColor(status) {
  if (status === "ontime") return "#22c55e";
  if (status === "late") return "#ef4444";
  if (status === "expected_ontime") return "#fbbf24";
  return "#64748b";
}

function getStatusColor(status) {
  if (status === "finished") return "#22c55e";
  if (status === "in_progress") return "#60a5fa";
  if (status === "not_started") return "#475569";
  return "#64748b";
}

function ProgressArc({ pct, warn, size = 52 }) {
  const r = 20, cx = 26, cy = 26;
  const circ = Math.PI * r;
  const filled = circ * Math.min(pct, 1);
  const color = warn ? "#ef4444" : pct >= 1 ? "#22c55e" : pct > 0.5 ? "#60a5fa" : "#fbbf24";
  return (
    <svg width={size} height={size} viewBox="0 0 52 52">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e3a5f" strokeWidth="5" strokeDasharray={circ} strokeDashoffset={0} strokeLinecap="round"
        style={{ transform: "rotate(-90deg)", transformOrigin: "50% 50%" }} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="5"
        strokeDasharray={`${filled} ${circ}`} strokeLinecap="round"
        style={{ transform: "rotate(-90deg)", transformOrigin: "50% 50%", transition: "stroke-dasharray 0.6s ease" }} />
      <text x={cx} y={cy + 4} textAnchor="middle" fill={color} fontSize="10" fontWeight="700" fontFamily="'DM Mono', monospace">
        {Math.round(pct * 100)}%
      </text>
    </svg>
  );
}

function StatCard({ label, value, sub, color, blink }) {
  return (
    <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "14px 18px", borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.15em", marginBottom: 6, fontFamily: "'DM Mono', monospace" }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 32, color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 9, color: "#334155", marginTop: 3, fontFamily: "'DM Mono', monospace" }}>{sub}</div>}
    </div>
  );
}

function EtaBadge({ status }) {
  const color = getEtaColor(status);
  const label = status === "expected_ontime" ? "EXP ON-TIME" : status?.toUpperCase().replace("_", " ");
  return (
    <span style={{ fontSize: 8, padding: "2px 7px", borderRadius: 3, background: color + "22", color, letterSpacing: "0.1em", fontFamily: "'DM Mono', monospace", whiteSpace: "nowrap", border: `1px solid ${color}44` }}>
      {label}
    </span>
  );
}

function StatusBadge({ status }) {
  const color = getStatusColor(status);
  const label = status?.replace("_", " ").toUpperCase();
  return (
    <span style={{ fontSize: 8, padding: "2px 7px", borderRadius: 3, background: color + "22", color, letterSpacing: "0.1em", fontFamily: "'DM Mono', monospace", whiteSpace: "nowrap" }}>
      {label}
    </span>
  );
}

const TH = ({ children, align = "right" }) => (
  <th style={{ padding: "8px 12px", textAlign: align, fontSize: 8, color: "#475569", letterSpacing: "0.15em", fontWeight: 500, fontFamily: "'DM Mono', monospace", borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap" }}>
    {children}
  </th>
);

export default function App() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [etaFilter, setEtaFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("poNo");
  const [sortDir, setSortDir] = useState("asc");
  const [selected, setSelected] = useState(null);

  const stats = useMemo(() => {
    const finished = RAW_JSON.finishedRecords.length;
    const inProg = RAW_JSON.unfinishedRecords.filter(r => r.poStatus === "in_progress").length;
    const notStarted = RAW_JSON.unfinishedRecords.filter(r => r.poStatus === "not_started").length;
    const critical = RAW_JSON.unfinishedRecords.filter(r => r.capacitySeverity === "critical").length;
    const overdue = RAW_JSON.unfinishedRecords.filter(r => r.is_overdue).length;
    const totalQty = allRecords.reduce((s, r) => s + (r.itemQuantity || 0), 0);
    return { finished, inProg, notStarted, critical, overdue, totalQty };
  }, []);

  const filtered = useMemo(() => {
    let data = allRecords;
    if (statusFilter !== "all") data = data.filter(r => r.poStatus === statusFilter || (statusFilter === "finished" && r.category === "finished"));
    if (etaFilter !== "all") data = data.filter(r => r.etaStatus === etaFilter);
    if (search) {
      const q = search.toLowerCase();
      data = data.filter(r => r.poNo?.toLowerCase().includes(q) || r.itemName?.toLowerCase().includes(q) || r.itemCode?.toLowerCase().includes(q));
    }
    return [...data].sort((a, b) => {
      let av = a[sortKey] ?? "", bv = b[sortKey] ?? "";
      if (typeof av === "string") av = av.toLowerCase();
      if (typeof bv === "string") bv = bv.toLowerCase();
      return sortDir === "asc" ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
    });
  }, [statusFilter, etaFilter, search, sortKey, sortDir]);

  const handleSort = (k) => {
    if (sortKey === k) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(k); setSortDir("asc"); }
  };

  const SortIco = ({ k }) => <span style={{ color: sortKey === k ? "#60a5fa" : "#1e3a5f" }}>{sortKey === k ? (sortDir === "asc" ? " ▲" : " ▼") : " ⬦"}</span>;

  return (
    <div style={{ minHeight: "100vh", background: "#020b18", fontFamily: "'DM Mono', 'Courier New', monospace", color: "#e2e8f0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; } ::-webkit-scrollbar-track { background: #0f172a; } ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        .pill { background: transparent; border: 1px solid #1e3a5f; border-radius: 4px; color: #64748b; padding: 5px 12px; cursor: pointer; font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 0.08em; transition: all 0.15s; }
        .pill.active { background: #1d4ed8; border-color: #2563eb; color: #fff; }
        .pill:hover:not(.active) { border-color: #334155; color: #94a3b8; }
        .tr-row:hover td { background: #0a1929 !important; cursor: pointer; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
        .fade-up { animation: fadeUp 0.35s ease forwards; }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
        .blink { animation: blink 1.6s ease-in-out infinite; }
        input::placeholder { color: #334155; }
      `}</style>

      {/* HEADER */}
      <div style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f", padding: "14px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 3, height: 34, background: "#2563eb", borderRadius: 2 }} />
          <div>
            <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 22, letterSpacing: "0.12em", color: "#60a5fa" }}>PRODUCTION ORDER</div>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>MANUFACTURING CONTROL SYSTEM — INJECTION MOLDING</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} className="blink" />
          <span style={{ fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>LIVE · 2019-01-15</span>
        </div>
      </div>

      <div style={{ padding: "20px 28px" }}>
        {/* KPI */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12, marginBottom: 20 }} className="fade-up">
          <StatCard label="FINISHED" value={stats.finished} sub="PO completed" color="#22c55e" />
          <StatCard label="IN PROGRESS" value={stats.inProg} sub="Active" color="#60a5fa" />
          <StatCard label="NOT STARTED" value={stats.notStarted} sub="Pending" color="#fbbf24" />
          <StatCard label="CRITICAL" value={stats.critical} sub="Over capacity" color="#f97316" />
          <StatCard label="OVERDUE" value={stats.overdue} sub="Past ETA" color="#ef4444" />
          <StatCard label="TOTAL QTY" value={(stats.totalQty / 1000).toFixed(0) + "K"} sub="units ordered" color="#818cf8" />
        </div>

        {/* FILTERS */}
        <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "12px 16px", marginBottom: 16, display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
          <input
            placeholder="SEARCH PO / ITEM CODE / NAME..."
            value={search} onChange={e => setSearch(e.target.value)}
            style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 4, padding: "6px 12px", fontSize: 10, color: "#94a3b8", outline: "none", fontFamily: "'DM Mono', monospace", letterSpacing: "0.05em", minWidth: 240 }}
          />
          <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
          {[["all", "ALL STATUS"], ["finished", "FINISHED"], ["in_progress", "IN PROGRESS"], ["not_started", "NOT STARTED"]].map(([v, l]) => (
            <button key={v} className={`pill ${statusFilter === v ? "active" : ""}`} onClick={() => setStatusFilter(v)}>{l}</button>
          ))}
          <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
          {[["all", "ALL ETA"], ["ontime", "ON TIME"], ["late", "LATE"], ["expected_ontime", "EXPECTED"]].map(([v, l]) => (
            <button key={v} className={`pill ${etaFilter === v ? "active" : ""}`} onClick={() => setEtaFilter(v)}>{l}</button>
          ))}
          <span style={{ marginLeft: "auto", fontSize: 9, color: "#334155", letterSpacing: "0.1em" }}>{filtered.length} RECORDS</span>
        </div>

        {/* TABLE */}
        <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }} className="fade-up">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
              <thead>
                <tr>
                  {[["poNo","PO NO","left"],["itemCode","ITEM CODE","left"],["itemName","ITEM NAME","left"],["poETA","ETA","left"],["poStatus","STATUS","left"],["etaStatus","ETA STATUS","left"],["itemQuantity","QTY","right"],["itemGoodQuantity","GOOD QTY","right"],["itemRemainQuantity","REMAIN","right"],["completionProgress","PROGRESS","center"]].map(([k, l, a]) => (
                    <TH key={k}>
                      <span onClick={() => handleSort(k)} style={{ cursor: "pointer", userSelect: "none" }}>
                        {l}<SortIco k={k} />
                      </span>
                    </TH>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r, i) => (
                  <tr key={r.poNo + i} className="tr-row" onClick={() => setSelected(selected?.poNo === r.poNo ? null : r)}
                    style={{ borderBottom: "1px solid #0a1929", background: i % 2 === 0 ? "transparent" : "#060e1a" }}>
                    <td style={{ padding: "9px 12px", fontWeight: 500, color: "#93c5fd", whiteSpace: "nowrap" }}>
                      {r.is_backlog && <span title="Backlog" style={{ color: "#fbbf24", marginRight: 5, fontSize: 10 }}>★</span>}
                      {r.poNo}
                    </td>
                    <td style={{ padding: "9px 12px", color: "#64748b", fontSize: 10 }}>{r.itemCode}</td>
                    <td style={{ padding: "9px 12px", color: "#94a3b8", maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                    <td style={{ padding: "9px 12px", color: "#475569", fontSize: 10, whiteSpace: "nowrap" }}>{r.poETA}</td>
                    <td style={{ padding: "9px 12px" }}><StatusBadge status={r.poStatus} /></td>
                    <td style={{ padding: "9px 12px" }}><EtaBadge status={r.etaStatus} /></td>
                    <td style={{ padding: "9px 12px", textAlign: "right", color: "#60a5fa" }}>{(r.itemQuantity || 0).toLocaleString()}</td>
                    <td style={{ padding: "9px 12px", textAlign: "right", color: "#22c55e" }}>{r.itemGoodQuantity != null ? r.itemGoodQuantity.toLocaleString() : "—"}</td>
                    <td style={{ padding: "9px 12px", textAlign: "right", color: (r.itemRemainQuantity || 0) > 0 ? "#fbbf24" : "#334155" }}>{(r.itemRemainQuantity || 0).toLocaleString()}</td>
                    <td style={{ padding: "9px 12px", textAlign: "center" }}>
                      <ProgressArc pct={r.completionProgress || 0} warn={r.capacityWarning} size={44} />
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={10} style={{ textAlign: "center", padding: 40, color: "#334155", fontSize: 11, letterSpacing: "0.1em" }}>NO RECORDS FOUND</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* DETAIL PANEL */}
        {selected && (
          <div style={{ marginTop: 16, background: "#0c1a2e", border: `1px solid ${selected.is_overdue ? "#ef444466" : selected.poStatus === "finished" ? "#22c55e66" : "#2563eb66"}`, borderRadius: 8, padding: "20px 24px", borderTop: `3px solid ${selected.is_overdue ? "#ef4444" : selected.poStatus === "finished" ? "#22c55e" : "#2563eb"}` }} className="fade-up">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 }}>
              <div>
                <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em", marginBottom: 4 }}>ORDER DETAIL</div>
                <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 28, color: "#93c5fd", letterSpacing: "0.1em" }}>{selected.poNo}</div>
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{selected.itemName} <span style={{ color: "#334155" }}>({selected.itemCode})</span></div>
              </div>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <ProgressArc pct={selected.completionProgress || 0} warn={selected.capacityWarning} size={60} />
                <button onClick={() => setSelected(null)} className="pill">✕ CLOSE</button>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 10 }}>
              {[
                ["PO RECEIVED", selected.poReceivedDate],
                ["ETA DATE", selected.poETA],
                ["FIRST RECORD", selected.firstRecord || "NOT STARTED"],
                ["LAST RECORD", selected.lastRecord || "—"],
                ["ORDER QTY", (selected.itemQuantity || 0).toLocaleString()],
                ["GOOD QTY", selected.itemGoodQuantity != null ? selected.itemGoodQuantity.toLocaleString() : "—"],
                ["NG QTY", selected.itemNGQuantity != null ? selected.itemNGQuantity.toLocaleString() : "—"],
                ["REMAIN QTY", (selected.itemRemainQuantity || 0).toLocaleString()],
                ["MOLD", selected.moldHist || "—"],
                ["CAPACITY", selected.capacitySeverity?.toUpperCase() || "—"],
                ["EST. LEAD TIME", selected.totalEstimatedLeadtime != null ? `${selected.totalEstimatedLeadtime.toFixed(2)}d` : "—"],
                ["BACKLOG", selected.is_backlog ? "YES ★" : "NO"],
              ].map(([l, v]) => (
                <div key={l} style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 6, padding: "10px 14px" }}>
                  <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.15em", marginBottom: 4 }}>{l}</div>
                  <div style={{ fontSize: 12, fontWeight: 500, color: "#94a3b8" }}>{v}</div>
                </div>
              ))}
            </div>

            {selected.capacityWarning && (
              <div style={{ marginTop: 14, background: "#1a0a0a", border: "1px solid #ef444444", borderRadius: 6, padding: "10px 14px", fontSize: 10, color: "#ef4444", display: "flex", gap: 8, alignItems: "center", letterSpacing: "0.05em" }}>
                ⚠ CAPACITY WARNING — {selected.capacityExplanation || "Exceeds max capacity"}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}