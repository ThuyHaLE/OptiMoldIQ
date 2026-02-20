import { useState, useMemo } from "react";

const RAW_JSON = {
  "finishedRecords":[
    {"poReceivedDate":"2018-12-01","poNo":"IM1812001","poETA":"2018-12-31","itemCode":"10236M","itemName":"AB-TP-BODY","itemQuantity":5840,"firstRecord":"2018-12-12","lastRecord":"2018-12-31","itemGoodQuantity":5840,"itemNGQuantity":280,"moldHist":"20400IBE-M-001","proStatus":"finished","is_backlog":true,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2018-12-01","poNo":"IM1812009","poETA":"2018-12-31","itemCode":"24720316M","itemName":"CT-CAX-UPPER-CASE-NL","itemQuantity":4930,"firstRecord":"2018-12-31","lastRecord":"2018-12-31","itemGoodQuantity":4930,"itemNGQuantity":110,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":true,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2018-12-01","poNo":"IM1812024","poETA":"2018-12-31","itemCode":"26003170M","itemName":"CT-CA-BASE-NL(NO-PRINT)","itemQuantity":27000,"firstRecord":"2018-12-19","lastRecord":"2018-12-31","itemGoodQuantity":27000,"itemNGQuantity":7448,"moldHist":"14000CBQ-M-001","proStatus":"finished","is_backlog":true,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901005","poETA":"2019-01-15","itemCode":"10315M","itemName":"AB-TP-LARGE-CAP-879-BN","itemQuantity":2500,"firstRecord":"2019-01-02","lastRecord":"2019-01-02","itemGoodQuantity":2500,"itemNGQuantity":24,"moldHist":"20101IBE-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901006","poETA":"2019-01-15","itemCode":"10318M","itemName":"AB-TP-LARGE-CAP-910-PK","itemQuantity":5000,"firstRecord":"2019-01-02","lastRecord":"2019-01-02","itemGoodQuantity":5000,"itemNGQuantity":48,"moldHist":"20101IBE-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901023","poETA":"2019-01-15","itemCode":"24720316M","itemName":"CT-CAX-UPPER-CASE-NL","itemQuantity":90000,"firstRecord":"2019-01-02","lastRecord":"2019-01-11","itemGoodQuantity":90000,"itemNGQuantity":4760,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901029","poETA":"2019-01-15","itemCode":"24720324M","itemName":"CT-CAX-LOCK-BUTTON-NL","itemQuantity":135000,"firstRecord":"2019-01-02","lastRecord":"2019-01-10","itemGoodQuantity":135000,"itemNGQuantity":821,"moldHist":"16500CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901032","poETA":"2019-01-15","itemCode":"24720327M","itemName":"CT-CAX-BASE-COVER","itemQuantity":545000,"firstRecord":"2019-01-02","lastRecord":"2019-01-31","itemGoodQuantity":545000,"itemNGQuantity":12064,"moldHist":"14100CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901033","poETA":"2019-01-15","itemCode":"24720328M","itemName":"CT-CAX-REEL","itemQuantity":530000,"firstRecord":"2019-01-02","lastRecord":"2019-01-31","itemGoodQuantity":530000,"itemNGQuantity":11091,"moldHist":"15000CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901042","poETA":"2019-01-15","itemCode":"26004650M","itemName":"CT-CA-PRINTER-HEAD-6.0MM-BLUE","itemQuantity":75000,"firstRecord":"2019-01-02","lastRecord":"2019-01-18","itemGoodQuantity":75000,"itemNGQuantity":2600,"moldHist":"12005CBQ-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901024","poETA":"2019-01-30","itemCode":"24720317M","itemName":"CT-CAX-UPPER-CASE-LIME","itemQuantity":80000,"firstRecord":"2019-01-11","lastRecord":"2019-01-19","itemGoodQuantity":80000,"itemNGQuantity":4324,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901025","poETA":"2019-01-30","itemCode":"24720318M","itemName":"CT-CAX-UPPER-CASE-BLUE","itemQuantity":100000,"firstRecord":"2019-01-21","lastRecord":"2019-01-30","itemGoodQuantity":100000,"itemNGQuantity":2672,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901026","poETA":"2019-01-30","itemCode":"24720319M","itemName":"CT-CAX-UPPER-CASE-PINK","itemQuantity":20000,"firstRecord":"2019-01-30","lastRecord":"2019-01-31","itemGoodQuantity":20000,"itemNGQuantity":1800,"moldHist":"10100CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901027","poETA":"2019-01-30","itemCode":"24720321M","itemName":"CT-CAX-LOWER-CASE-LIME","itemQuantity":85000,"firstRecord":"2019-01-16","lastRecord":"2019-01-25","itemGoodQuantity":85000,"itemNGQuantity":1358,"moldHist":"10000CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901028","poETA":"2019-01-30","itemCode":"24720323M","itemName":"CT-CAX-LOWER-CASE-PINK","itemQuantity":50000,"firstRecord":"2019-01-25","lastRecord":"2019-01-31","itemGoodQuantity":50000,"itemNGQuantity":403,"moldHist":"10000CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901031","poETA":"2019-01-30","itemCode":"24720326M","itemName":"CT-CAX-CARTRIDGE-BASE","itemQuantity":445000,"firstRecord":"2019-01-12","lastRecord":"2019-01-31","itemGoodQuantity":445000,"itemNGQuantity":9728,"moldHist":"14000CBR-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901036","poETA":"2019-01-30","itemCode":"24720467M","itemName":"CT-YCN-PRINTER-HEAD-2.5MM-NL","itemQuantity":90000,"firstRecord":"2019-01-09","lastRecord":"2019-01-15","itemGoodQuantity":90000,"itemNGQuantity":3052,"moldHist":"12000CBG-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901037","poETA":"2019-01-30","itemCode":"24720468M","itemName":"CT-YCN-SMALL-GEAR-NL","itemQuantity":75000,"firstRecord":"2019-01-08","lastRecord":"2019-01-12","itemGoodQuantity":75000,"itemNGQuantity":2252,"moldHist":"11100CBG-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901038","poETA":"2019-01-30","itemCode":"24720469M","itemName":"CT-YCN-LARGE-GEAR-WHITE","itemQuantity":80000,"firstRecord":"2019-01-14","lastRecord":"2019-01-22","itemGoodQuantity":80000,"itemNGQuantity":1540,"moldHist":"11000CBG-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901039","poETA":"2019-01-30","itemCode":"24720470M","itemName":"CT-YCN-CLUCH-NL","itemQuantity":80000,"firstRecord":"2019-01-10","lastRecord":"2019-01-23","itemGoodQuantity":80000,"itemNGQuantity":4990,"moldHist":"15300CBG-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901041","poETA":"2019-01-30","itemCode":"26004620M","itemName":"CT-CA-PRINTER-HEAD-5.0MM-RED","itemQuantity":60000,"firstRecord":"2019-01-07","lastRecord":"2019-01-08","itemGoodQuantity":60000,"itemNGQuantity":1360,"moldHist":"12004CBQ-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901043","poETA":"2019-01-30","itemCode":"26004670M","itemName":"CT-CA-PRINTER-HEAD-5.0MM-SILVER","itemQuantity":900000,"firstRecord":"2019-01-08","lastRecord":"2019-01-25","itemGoodQuantity":900000,"itemNGQuantity":2928,"moldHist":"12004CBQ-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901044","poETA":"2019-01-30","itemCode":"260501M","itemName":"CT-PXN-HEAD-COVER-4.2MM","itemQuantity":138000,"firstRecord":"2019-01-28","lastRecord":"2019-01-31","itemGoodQuantity":138000,"itemNGQuantity":537,"moldHist":"PXNHC4-M-001/PXNHC4-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"late"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901045","poETA":"2019-01-30","itemCode":"261301M","itemName":"CT-PXN-LARGE-GEAR-4.2&5.0MM","itemQuantity":105000,"firstRecord":"2019-01-12","lastRecord":"2019-01-17","itemGoodQuantity":105000,"itemNGQuantity":4074,"moldHist":"PXNLG5-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901046","poETA":"2019-01-30","itemCode":"261501M","itemName":"CT-PXN-SMALL-GEAR-4.2&5.0MM","itemQuantity":50000,"firstRecord":"2019-01-14","lastRecord":"2019-01-15","itemGoodQuantity":50000,"itemNGQuantity":4440,"moldHist":"PXNSG5-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901049","poETA":"2019-01-30","itemCode":"280301M","itemName":"CT-PS-SLIDE-COVER-CLEAR","itemQuantity":15000,"firstRecord":"2019-01-15","lastRecord":"2019-01-16","itemGoodQuantity":15000,"itemNGQuantity":3752,"moldHist":"PSSC-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901062","poETA":"2019-01-30","itemCode":"290801M","itemName":"CT-PGX-PRINTER-HEAD-4.2MM-GREEN","itemQuantity":85000,"firstRecord":"2019-01-03","lastRecord":"2019-01-07","itemGoodQuantity":85000,"itemNGQuantity":848,"moldHist":"PGXPH42-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901063","poETA":"2019-01-30","itemCode":"291103M","itemName":"CT-PGX-REEL-5.0MM-BLUE","itemQuantity":21000,"firstRecord":"2019-01-15","lastRecord":"2019-01-16","itemGoodQuantity":21000,"itemNGQuantity":640,"moldHist":"15001CAF-M-002","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901064","poETA":"2019-01-30","itemCode":"303001M","itemName":"CT-YCN-CORE-BLUE","itemQuantity":55000,"firstRecord":"2019-01-25","lastRecord":"2019-01-29","itemGoodQuantity":55000,"itemNGQuantity":488,"moldHist":"16200CBG-M-001","proStatus":"finished","is_backlog":false,"itemRemainQuantity":0,"poStatus":"finished","etaStatus":"ontime"}
  ],
  "unfinishedRecords":[
    {"poReceivedDate":"2019-01-25","poNo":"IM1902118","poETA":"2019-02-20","itemCode":"24720323M","itemName":"CT-CAX-LOWER-CASE-PINK","itemQuantity":155000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":155000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":9.87,"moldList":"10000CBR-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902116","poETA":"2019-02-20","itemCode":"24720319M","itemName":"CT-CAX-UPPER-CASE-PINK","itemQuantity":180000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":180000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":12.5,"moldList":"10100CBR-M-001"},
    {"poReceivedDate":"2018-12-01","poNo":"IM1812004","poETA":"2018-12-31","itemCode":"24720309M","itemName":"CT-YA-PRINTER-HEAD-4.2MM","itemQuantity":2516,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":2516,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":true,"completionProgress":0.0,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":0.12,"moldList":"12000CBS-M-001"},
    {"poReceivedDate":"2019-01-02","poNo":"IM1901040","poETA":"2019-01-30","itemCode":"26003170M","itemName":"CT-CA-BASE-NL(NO-PRINT)","itemQuantity":500000,"itemGoodQuantity":383733,"itemNGQuantity":11302,"itemRemainQuantity":116267,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"completionProgress":0.77,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":3.03,"moldList":"14000CBQ-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902119","poETA":"2019-02-20","itemCode":"24720326M","itemName":"CT-CAX-CARTRIDGE-BASE","itemQuantity":340000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":340000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":11.81,"moldList":"14000CBR-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902120","poETA":"2019-02-20","itemCode":"24720327M","itemName":"CT-CAX-BASE-COVER","itemQuantity":175000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":175000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":6.08,"moldList":"14100CBR-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902121","poETA":"2019-02-20","itemCode":"24720328M","itemName":"CT-CAX-REEL","itemQuantity":410000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":410000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":13.64,"moldList":"15000CBR-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902001","poETA":"2019-02-20","itemCode":"10241M","itemName":"AB-TP-LARGE-CAP-027-BG","itemQuantity":2000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":2000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":0.12,"moldList":"20101IBE-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902002","poETA":"2019-02-20","itemCode":"10242M","itemName":"AB-TP-LARGE-CAP-055-YW","itemQuantity":15000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":15000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":1.03,"moldList":"20101IBE-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902047","poETA":"2019-02-20","itemCode":"10350M","itemName":"AB-TP-SMALL-CAP-062-YW","itemQuantity":22000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":22000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":1.15,"moldList":"20102IBE-M-001"},
    {"poReceivedDate":"2018-12-20","poNo":"IM1901020","poETA":"2019-01-15","itemCode":"10236M","itemName":"AB-TP-BODY","itemQuantity":110000,"itemGoodQuantity":100000,"itemNGQuantity":5208,"itemRemainQuantity":10000,"poStatus":"in_progress","proStatus":"unfinished","is_backlog":false,"completionProgress":0.91,"etaStatus":"late","capacityWarning":true,"capacitySeverity":"critical","is_overdue":true,"totalEstimatedLeadtime":1.04,"moldList":"20400IBE-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902134","poETA":"2019-02-20","itemCode":"281709M","itemName":"CT-PS-SPACER","itemQuantity":30000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":30000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":0.91,"moldList":"PSSP-M-001"},
    {"poReceivedDate":"2019-01-25","poNo":"IM1902129","poETA":"2019-02-20","itemCode":"260501M","itemName":"CT-PXN-HEAD-COVER-4.2MM","itemQuantity":55000,"itemGoodQuantity":null,"itemNGQuantity":null,"itemRemainQuantity":55000,"poStatus":"not_started","proStatus":"unfinished","is_backlog":false,"completionProgress":0.0,"etaStatus":"expected_ontime","capacityWarning":false,"capacitySeverity":"normal","is_overdue":false,"totalEstimatedLeadtime":1.51,"moldList":"PXNHC4-M-001"}
  ]
};

const allRecords = [
  ...RAW_JSON.finishedRecords.map(r => ({ ...r, category: "finished", completionProgress: 1.0 })),
  ...RAW_JSON.unfinishedRecords.map(r => ({ ...r, category: "unfinished" }))
];

function getEtaColor(s) {
  if (s === "ontime") return "#22c55e";
  if (s === "late") return "#ef4444";
  if (s === "expected_ontime") return "#fbbf24";
  return "#64748b";
}
function getStatusColor(s) {
  if (s === "finished") return "#22c55e";
  if (s === "in_progress") return "#60a5fa";
  if (s === "not_started") return "#475569";
  return "#64748b";
}

function ngRate(r) {
  const total = r.itemGoodQuantity != null ? (r.itemGoodQuantity + (r.itemNGQuantity || 0)) : r.itemQuantity;
  if (!r.itemNGQuantity || total === 0) return 0;
  return (r.itemNGQuantity / total) * 100;
}

function getNGColor(rate) {
  if (rate === 0) return "#22c55e";
  if (rate < 2) return "#86efac";
  if (rate < 5) return "#fbbf24";
  if (rate < 10) return "#f97316";
  return "#ef4444";
}

function ProgressArc({ pct, warn, size = 44 }) {
  const r = 16, cx = 22, cy = 22;
  const circ = 2 * Math.PI * r * 0.75;
  const filled = circ * Math.min(pct, 1);
  const color = warn ? "#ef4444" : pct >= 1 ? "#22c55e" : pct > 0.5 ? "#60a5fa" : "#fbbf24";
  const rot = "rotate(135, 22, 22)";
  return (
    <svg width={size} height={size} viewBox="0 0 44 44">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1e3a5f" strokeWidth="4"
        strokeDasharray={`${circ} ${2 * Math.PI * r}`} strokeLinecap="round"
        transform={rot} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="4"
        strokeDasharray={`${filled} ${2 * Math.PI * r}`} strokeLinecap="round"
        transform={rot} style={{ transition: "stroke-dasharray 0.5s ease" }} />
      <text x={cx} y={cy + 4} textAnchor="middle" fill={color} fontSize="9" fontWeight="700" fontFamily="'DM Mono',monospace">
        {Math.round(pct * 100)}%
      </text>
    </svg>
  );
}

function NGGauge({ rate }) {
  const color = getNGColor(rate);
  const r = 14, cx = 18, cy = 18;
  const circ = Math.PI * r;
  const filled = circ * Math.min(rate / 30, 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width="36" height="22" viewBox="0 0 36 22">
        <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="#1e3a5f" strokeWidth="4" />
        {rate > 0 && (
          <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r * Math.cos(Math.PI * (1 - Math.min(rate/30,1)))} ${cy - r * Math.sin(Math.PI * (1 - Math.min(rate/30,1)))}`}
            fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" />
        )}
        <text x={cx} y={cy - 3} textAnchor="middle" fill={color} fontSize="8" fontWeight="700" fontFamily="'DM Mono',monospace">
          {rate.toFixed(1)}%
        </text>
      </svg>
    </div>
  );
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "14px 18px", borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.15em", marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: "'Bebas Neue', sans-serif", fontSize: 30, color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 9, color: "#334155", marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

function Badge({ label, color }) {
  return (
    <span style={{ fontSize: 8, padding: "2px 7px", borderRadius: 3, background: color + "22", color, letterSpacing: "0.1em", border: `1px solid ${color}44`, whiteSpace: "nowrap" }}>
      {label}
    </span>
  );
}

const TH = ({ children, onClick, sorted, dir }) => (
  <th onClick={onClick} style={{ padding: "8px 12px", textAlign: "left", fontSize: 8, color: sorted ? "#93c5fd" : "#475569", letterSpacing: "0.15em", fontWeight: 500, borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap", cursor: onClick ? "pointer" : "default", userSelect: "none" }}>
    {children}{sorted ? (dir === "asc" ? " ▲" : " ▼") : <span style={{ color: "#1e3a5f" }}> ⬦</span>}
  </th>
);

export default function App() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [etaFilter, setEtaFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("poNo");
  const [sortDir, setSortDir] = useState("asc");
  const [selected, setSelected] = useState(null);
  const [view, setView] = useState("table");

  const stats = useMemo(() => {
    const fin = RAW_JSON.finishedRecords.length;
    const inP = RAW_JSON.unfinishedRecords.filter(r => r.poStatus === "in_progress").length;
    const ns = RAW_JSON.unfinishedRecords.filter(r => r.poStatus === "not_started").length;
    const crit = RAW_JSON.unfinishedRecords.filter(r => r.capacitySeverity === "critical").length;
    const od = RAW_JSON.unfinishedRecords.filter(r => r.is_overdue).length;
    const totalQty = allRecords.reduce((s, r) => s + (r.itemQuantity || 0), 0);
    const totalGood = RAW_JSON.finishedRecords.reduce((s, r) => s + (r.itemGoodQuantity || 0), 0);
    const totalNG = RAW_JSON.finishedRecords.reduce((s, r) => s + (r.itemNGQuantity || 0), 0);
    const ngRate = totalGood + totalNG > 0 ? (totalNG / (totalGood + totalNG)) * 100 : 0;
    return { fin, inP, ns, crit, od, totalQty, ngRate };
  }, []);

  const filtered = useMemo(() => {
    let data = allRecords;
    if (statusFilter !== "all") data = data.filter(r => r.poStatus === statusFilter);
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

  const handleSort = k => {
    if (sortKey === k) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(k); setSortDir("asc"); }
  };

  // NG rate top 10 for chart view
  const ngChartData = useMemo(() => {
    return [...RAW_JSON.finishedRecords]
      .filter(r => r.itemNGQuantity > 0)
      .map(r => ({ poNo: r.poNo, name: r.itemName, qty: r.itemQuantity, ngQty: r.itemNGQuantity, rate: (r.itemNGQuantity / (r.itemGoodQuantity + r.itemNGQuantity)) * 100 }))
      .sort((a, b) => b.rate - a.rate)
      .slice(0, 12);
  }, []);

  const maxNGQty = Math.max(...ngChartData.map(d => d.ngQty));

  return (
    <div style={{ minHeight: "100vh", background: "#020b18", fontFamily: "'DM Mono','Courier New',monospace", color: "#e2e8f0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Bebas+Neue&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        .pill { background: transparent; border: 1px solid #1e3a5f; border-radius: 4px; color: #64748b; padding: 5px 12px; cursor: pointer; font-family: 'DM Mono',monospace; font-size: 10px; letter-spacing: 0.08em; transition: all 0.15s; }
        .pill.active { background: #1d4ed8; border-color: #2563eb; color: #fff; }
        .pill:hover:not(.active) { border-color: #334155; color: #94a3b8; }
        .tr-row:hover td { background: #0a1929 !important; cursor: pointer; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        .fade-up { animation: fadeUp 0.3s ease forwards; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0.3} }
        .blink { animation: blink 1.6s ease-in-out infinite; }
        input::placeholder { color: #334155; }
      `}</style>

      {/* HEADER */}
      <div style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f", padding: "14px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 3, height: 34, background: "#2563eb", borderRadius: 2 }} />
          <div>
            <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 22, letterSpacing: "0.12em", color: "#60a5fa" }}>PRODUCTION ORDER</div>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>MANUFACTURING CONTROL SYSTEM — INJECTION MOLDING</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontSize: 9, color: "#334155", letterSpacing: "0.1em" }}>{allRecords.length} TOTAL PO</span>
          <div style={{ width: 1, height: 16, background: "#1e3a5f" }} />
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} className="blink" />
          <span style={{ fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>LIVE</span>
        </div>
      </div>

      <div style={{ padding: "20px 28px" }}>
        {/* KPI */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 10, marginBottom: 18 }} className="fade-up">
          <StatCard label="FINISHED" value={stats.fin} sub="completed" color="#22c55e" />
          <StatCard label="IN PROGRESS" value={stats.inP} sub="active" color="#60a5fa" />
          <StatCard label="NOT STARTED" value={stats.ns} sub="pending" color="#94a3b8" />
          <StatCard label="CRITICAL" value={stats.crit} sub="over capacity" color="#f97316" />
          <StatCard label="OVERDUE" value={stats.od} sub="past ETA" color="#ef4444" />
          <StatCard label="TOTAL QTY" value={(stats.totalQty / 1000).toFixed(0) + "K"} sub="units ordered" color="#818cf8" />
          <StatCard label="AVG NG RATE" value={stats.ngRate.toFixed(1) + "%"} sub="finished POs" color={getNGColor(stats.ngRate)} />
        </div>

        {/* VIEW + FILTERS */}
        <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "12px 16px", marginBottom: 14, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
          <button className={`pill ${view === "table" ? "active" : ""}`} onClick={() => setView("table")}>TABLE VIEW</button>
          <button className={`pill ${view === "ng" ? "active" : ""}`} onClick={() => setView("ng")}>NG ANALYSIS</button>
          <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
          {view === "table" && <>
            <input placeholder="SEARCH PO / CODE / NAME..." value={search} onChange={e => setSearch(e.target.value)}
              style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 4, padding: "5px 12px", fontSize: 10, color: "#94a3b8", outline: "none", fontFamily: "'DM Mono',monospace", letterSpacing: "0.05em", minWidth: 220 }} />
            <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
            {[["all","ALL"],["finished","FINISHED"],["in_progress","IN PROG"],["not_started","NOT STARTED"]].map(([v,l]) => (
              <button key={v} className={`pill ${statusFilter===v?"active":""}`} onClick={() => setStatusFilter(v)}>{l}</button>
            ))}
            <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
            {[["all","ALL ETA"],["ontime","ON TIME"],["late","LATE"],["expected_ontime","EXPECTED"]].map(([v,l]) => (
              <button key={v} className={`pill ${etaFilter===v?"active":""}`} onClick={() => setEtaFilter(v)}>{l}</button>
            ))}
            <span style={{ marginLeft: "auto", fontSize: 9, color: "#334155", letterSpacing: "0.1em" }}>{filtered.length} ROWS</span>
          </>}
        </div>

        {/* TABLE VIEW */}
        {view === "table" && (
          <div className="fade-up">
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }}>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr>
                      {[["poNo","PO NO"],["itemCode","CODE"],["itemName","ITEM NAME"],["poETA","ETA"],["poStatus","STATUS"],["etaStatus","ETA STATUS"],["itemQuantity","QTY"],["itemGoodQuantity","GOOD"],["itemNGQuantity","NG QTY"],["completionProgress","PROGRESS"]].map(([k,l]) => (
                        <TH key={k} onClick={() => handleSort(k)} sorted={sortKey===k} dir={sortDir}>{l}</TH>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((r, i) => {
                      const nr = ngRate(r);
                      return (
                        <tr key={r.poNo+i} className="tr-row" onClick={() => setSelected(selected?.poNo===r.poNo?null:r)}
                          style={{ borderBottom: "1px solid #0a1929", background: i%2===0?"transparent":"#060e1a" }}>
                          <td style={{ padding: "9px 12px", fontWeight: 500, color: "#93c5fd", whiteSpace: "nowrap" }}>
                            {r.is_backlog && <span style={{ color: "#fbbf24", marginRight: 5, fontSize: 10 }}>★</span>}
                            {r.poNo}
                          </td>
                          <td style={{ padding: "9px 12px", color: "#64748b", fontSize: 10 }}>{r.itemCode}</td>
                          <td style={{ padding: "9px 12px", color: "#94a3b8", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                          <td style={{ padding: "9px 12px", color: "#475569", fontSize: 10, whiteSpace: "nowrap" }}>{r.poETA}</td>
                          <td style={{ padding: "9px 12px" }}><Badge label={r.poStatus?.replace("_"," ").toUpperCase()} color={getStatusColor(r.poStatus)} /></td>
                          <td style={{ padding: "9px 12px" }}>
                            <Badge label={r.etaStatus==="expected_ontime"?"EXP ON-TIME":r.etaStatus?.toUpperCase()} color={getEtaColor(r.etaStatus)} />
                          </td>
                          <td style={{ padding: "9px 12px", textAlign: "right", color: "#60a5fa" }}>{(r.itemQuantity||0).toLocaleString()}</td>
                          <td style={{ padding: "9px 12px", textAlign: "right", color: "#22c55e" }}>{r.itemGoodQuantity!=null?r.itemGoodQuantity.toLocaleString():"—"}</td>
                          <td style={{ padding: "9px 12px", textAlign: "right" }}>
                            {r.itemNGQuantity != null ? (
                              <span style={{ color: getNGColor(nr), fontWeight: 500 }}>{r.itemNGQuantity.toLocaleString()}</span>
                            ) : "—"}
                          </td>
                          <td style={{ padding: "6px 12px" }}>
                            <ProgressArc pct={r.completionProgress||0} warn={r.capacityWarning} size={40} />
                          </td>
                        </tr>
                      );
                    })}
                    {filtered.length === 0 && (
                      <tr><td colSpan={10} style={{ textAlign: "center", padding: 40, color: "#334155", fontSize: 11, letterSpacing: "0.1em" }}>NO RECORDS FOUND</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* DETAIL PANEL */}
            {selected && (
              <div style={{ marginTop: 14, background: "#0c1a2e", border: `1px solid ${selected.is_overdue?"#ef444466":selected.poStatus==="finished"?"#22c55e66":"#2563eb66"}`, borderRadius: 8, padding: "20px 24px", borderTop: `3px solid ${selected.is_overdue?"#ef4444":selected.poStatus==="finished"?"#22c55e":"#2563eb"}` }} className="fade-up">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em", marginBottom: 4 }}>ORDER DETAIL</div>
                    <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 26, color: "#93c5fd", letterSpacing: "0.1em" }}>{selected.poNo}</div>
                    <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{selected.itemName} <span style={{ color: "#334155" }}>({selected.itemCode})</span></div>
                  </div>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <ProgressArc pct={selected.completionProgress||0} warn={selected.capacityWarning} size={56} />
                    {selected.itemNGQuantity != null && <NGGauge rate={ngRate(selected)} />}
                    <button onClick={() => setSelected(null)} className="pill">✕ CLOSE</button>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(145px, 1fr))", gap: 8 }}>
                  {[
                    ["PO RECEIVED", selected.poReceivedDate],
                    ["ETA DATE", selected.poETA],
                    ["FIRST RECORD", selected.firstRecord||"NOT STARTED"],
                    ["LAST RECORD", selected.lastRecord||"—"],
                    ["ORDER QTY", (selected.itemQuantity||0).toLocaleString()],
                    ["GOOD QTY", selected.itemGoodQuantity!=null?selected.itemGoodQuantity.toLocaleString():"—"],
                    ["NG QTY", selected.itemNGQuantity!=null?selected.itemNGQuantity.toLocaleString():"—"],
                    ["NG RATE", selected.itemNGQuantity!=null?ngRate(selected).toFixed(2)+"%":"—"],
                    ["REMAIN QTY", (selected.itemRemainQuantity||0).toLocaleString()],
                    ["MOLD", selected.moldHist||selected.moldList||"—"],
                    ["CAPACITY", selected.capacitySeverity?.toUpperCase()||"—"],
                    ["EST. LEAD TIME", selected.totalEstimatedLeadtime!=null?selected.totalEstimatedLeadtime.toFixed(2)+"d":"—"],
                    ["BACKLOG", selected.is_backlog?"YES ★":"NO"],
                    ["OVERDUE", selected.is_overdue?"YES ⚠":"NO"],
                  ].map(([l,v]) => (
                    <div key={l} style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 6, padding: "10px 12px" }}>
                      <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.12em", marginBottom: 4 }}>{l}</div>
                      <div style={{ fontSize: 12, fontWeight: 500, color: "#94a3b8" }}>{v}</div>
                    </div>
                  ))}
                </div>
                {selected.capacityWarning && (
                  <div style={{ marginTop: 12, background: "#1a0a0a", border: "1px solid #ef444444", borderRadius: 6, padding: "9px 14px", fontSize: 10, color: "#ef4444", letterSpacing: "0.05em" }}>
                    ⚠ CAPACITY WARNING — {selected.capacityExplanation||"Exceeds max capacity"}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* NG ANALYSIS VIEW */}
        {view === "ng" && (
          <div className="fade-up">
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "20px 24px", marginBottom: 14 }}>
              <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em", marginBottom: 14 }}>TOP NG RATE — FINISHED POs</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {ngChartData.map((d, i) => {
                  const color = getNGColor(d.rate);
                  const barPct = (d.ngQty / maxNGQty) * 100;
                  return (
                    <div key={i} style={{ display: "grid", gridTemplateColumns: "140px 1fr 80px 60px 60px", gap: 10, alignItems: "center" }}>
                      <div style={{ fontSize: 9, color: "#64748b", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }} title={d.name}>{d.poNo}</div>
                      <div style={{ background: "#060f1c", borderRadius: 3, height: 10, overflow: "hidden" }}>
                        <div style={{ width: `${barPct}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.5s ease" }} />
                      </div>
                      <div style={{ fontSize: 10, color, fontWeight: 500, textAlign: "right" }}>{d.ngQty.toLocaleString()}</div>
                      <div style={{ fontSize: 10, color: "#475569", textAlign: "right" }}>{d.rate.toFixed(1)}%</div>
                      <div><NGGauge rate={d.rate} /></div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* NG Table */}
            <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }}>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                  <thead>
                    <tr>
                      {["PO NO","ITEM NAME","ORDER QTY","GOOD QTY","NG QTY","NG RATE","MOLD","ETA STATUS"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: h.includes("QTY")||h.includes("RATE")?"right":"left", fontSize: 8, color: "#475569", letterSpacing: "0.12em", fontWeight: 500, borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {RAW_JSON.finishedRecords
                      .sort((a, b) => {
                        const ra = (a.itemNGQuantity||0) / (a.itemGoodQuantity + (a.itemNGQuantity||0));
                        const rb = (b.itemNGQuantity||0) / (b.itemGoodQuantity + (b.itemNGQuantity||0));
                        return rb - ra;
                      })
                      .map((r, i) => {
                        const nr = ngRate(r);
                        return (
                          <tr key={i} style={{ borderBottom: "1px solid #0a1929", background: i%2===0?"transparent":"#060e1a" }}>
                            <td style={{ padding: "8px 12px", color: "#93c5fd", fontWeight: 500, fontSize: 10 }}>{r.poNo}</td>
                            <td style={{ padding: "8px 12px", color: "#64748b", fontSize: 10, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.itemName}</td>
                            <td style={{ padding: "8px 12px", textAlign: "right", color: "#60a5fa" }}>{r.itemQuantity.toLocaleString()}</td>
                            <td style={{ padding: "8px 12px", textAlign: "right", color: "#22c55e" }}>{r.itemGoodQuantity.toLocaleString()}</td>
                            <td style={{ padding: "8px 12px", textAlign: "right", color: getNGColor(nr) }}>{(r.itemNGQuantity||0).toLocaleString()}</td>
                            <td style={{ padding: "8px 12px", textAlign: "right" }}>
                              <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 6 }}>
                                <div style={{ width: 50, height: 4, background: "#1e293b", borderRadius: 2, overflow: "hidden" }}>
                                  <div style={{ width: `${Math.min(nr/30*100,100)}%`, height: "100%", background: getNGColor(nr), borderRadius: 2 }} />
                                </div>
                                <span style={{ color: getNGColor(nr), fontWeight: 500, minWidth: 42, textAlign: "right" }}>{nr.toFixed(2)}%</span>
                              </div>
                            </td>
                            <td style={{ padding: "8px 12px", color: "#475569", fontSize: 9 }}>{r.moldHist||"—"}</td>
                            <td style={{ padding: "8px 12px" }}>
                              <Badge label={r.etaStatus==="ontime"?"ON TIME":r.etaStatus?.toUpperCase()} color={getEtaColor(r.etaStatus)} />
                            </td>
                          </tr>
                        );
                      })
                    }
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}