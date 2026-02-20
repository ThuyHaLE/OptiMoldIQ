import { useState } from "react";

const RAW_JSON = {
    "machineLayoutChange":[
        {"2018-11-01":null,"2019-01-15":"NO.10","machineName":"CNS50","machineCode":"CNS50-000"},
        {"2018-11-01":null,"2019-01-15":"NO.11","machineName":"CNS50","machineCode":"CNS50-001"},
        {"2018-11-01":"NO.03","2019-01-15":"NO.03","machineName":"EC50","machineCode":"EC50ST-000"},
        {"2018-11-01":"NO.04","2019-01-15":"NO.04","machineName":"J100","machineCode":"J100ADS-000"},
        {"2018-11-01":"NO.05","2019-01-15":"NO.05","machineName":"J100","machineCode":"J100ADS-001"},
        {"2018-11-01":"NO.06","2019-01-15":"NO.06","machineName":"MD100","machineCode":"MD100S-000"},
        {"2018-11-01":"NO.07","2019-01-15":"NO.07","machineName":"MD100","machineCode":"MD100S-001"},
        {"2018-11-01":"NO.08","2019-01-15":"NO.08","machineName":"MD130","machineCode":"MD130S-000"},
        {"2018-11-01":"NO.09","2019-01-15":"NO.09","machineName":"MD130","machineCode":"MD130S-001"},
        {"2018-11-01":"NO.01","2019-01-15":"NO.01","machineName":"MD50","machineCode":"MD50S-000"},
        {"2018-11-01":"NO.02","2019-01-15":"NO.02","machineName":"MD50","machineCode":"MD50S-001"}
    ]
};

const DATE_A = "2018-11-01";
const DATE_B = "2019-01-15";

const machines = RAW_JSON.machineLayoutChange.map(m => ({
  name: m.machineName,
  code: m.machineCode,
  posA: m[DATE_A],
  posB: m[DATE_B],
  isNew: m[DATE_A] === null,
  moved: m[DATE_A] !== null && m[DATE_A] !== m[DATE_B],
  unchanged: m[DATE_A] !== null && m[DATE_A] === m[DATE_B],
}));

// Group by machineName for color coding
const machineTypes = [...new Set(machines.map(m => m.name))];
const typeColors = {
  CNS50:  { line: "#a78bfa", bg: "#1e1040", border: "#7c3aed" },
  EC50:   { line: "#34d399", bg: "#052e16", border: "#059669" },
  J100:   { line: "#60a5fa", bg: "#0c1a2e", border: "#2563eb" },
  MD100:  { line: "#f97316", bg: "#1c0d00", border: "#c2410c" },
  MD130:  { line: "#fbbf24", bg: "#1c1400", border: "#b45309" },
  MD50:   { line: "#f472b6", bg: "#1c0614", border: "#be185d" },
};

// Build slot grid: positions NO.01 ~ NO.11
const allSlots = Array.from({ length: 11 }, (_, i) => `NO.${String(i + 1).padStart(2, "0")}`);

function MachineCard({ m, highlight }) {
  const c = typeColors[m.name] || { line: "#64748b", bg: "#0c1a2e", border: "#334155" };
  const tag = m.isNew ? { label: "NEW", color: "#a78bfa" }
    : m.moved ? { label: "MOVED", color: "#fbbf24" }
    : { label: "FIXED", color: "#22c55e" };

  return (
    <div style={{
      background: c.bg, border: `1px solid ${highlight ? c.line : c.border}`,
      borderLeft: `3px solid ${c.line}`,
      borderRadius: 8, padding: "14px 16px",
      boxShadow: highlight ? `0 0 16px ${c.line}44` : "none",
      transition: "all 0.2s",
      opacity: highlight === false ? 0.35 : 1,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div>
          <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 20, color: c.line, letterSpacing: "0.1em" }}>{m.name}</div>
          <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.12em" }}>{m.code}</div>
        </div>
        <span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: tag.color + "22", color: tag.color, border: `1px solid ${tag.color}44`, letterSpacing: "0.1em" }}>
          {tag.label}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 24px 1fr", alignItems: "center", gap: 4 }}>
        {/* Position A */}
        <div style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
          <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.12em", marginBottom: 3 }}>{DATE_A}</div>
          {m.posA
            ? <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 18, color: "#64748b", letterSpacing: "0.08em" }}>{m.posA}</div>
            : <div style={{ fontSize: 10, color: "#1e3a5f", letterSpacing: "0.1em" }}>—</div>
          }
        </div>

        {/* Arrow */}
        <div style={{ textAlign: "center" }}>
          {m.isNew ? (
            <span style={{ fontSize: 14, color: "#a78bfa" }}>+</span>
          ) : m.moved ? (
            <span style={{ fontSize: 12, color: "#fbbf24" }}>→</span>
          ) : (
            <span style={{ fontSize: 10, color: "#1e3a5f" }}>＝</span>
          )}
        </div>

        {/* Position B */}
        <div style={{ background: "#060f1c", border: `1px solid ${m.isNew ? "#7c3aed55" : m.moved ? "#b4530955" : "#1e3a5f"}`, borderRadius: 6, padding: "8px 10px", textAlign: "center" }}>
          <div style={{ fontSize: 8, color: "#334155", letterSpacing: "0.12em", marginBottom: 3 }}>{DATE_B}</div>
          <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 18, color: m.isNew ? "#a78bfa" : m.moved ? "#fbbf24" : "#22c55e", letterSpacing: "0.08em" }}>{m.posB}</div>
        </div>
      </div>
    </div>
  );
}

// Floor plan grid view
function FloorPlan({ activeType }) {
  const cols = 4;
  const rows = 3;

  const getMachineAtSlot = (slot, date) =>
    machines.find(m => (date === "A" ? m.posA : m.posB) === slot);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
      {[["A", DATE_A], ["B", DATE_B]].map(([key, date]) => (
        <div key={key} style={{ background: "#060f1c", border: "1px solid #1e3a5f", borderRadius: 10, padding: "16px" }}>
          <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em", marginBottom: 12 }}>
            FLOOR LAYOUT — <span style={{ color: "#60a5fa" }}>{date}</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
            {allSlots.map(slot => {
              const m = getMachineAtSlot(slot, key);
              const c = m ? (typeColors[m.name] || { line: "#64748b", bg: "#0c1a2e", border: "#334155" }) : null;
              const dimmed = activeType && m && m.name !== activeType;
              const glow = activeType && m && m.name === activeType;
              return (
                <div key={slot} style={{
                  background: m ? c.bg : "#0a1120",
                  border: `1px solid ${m ? (glow ? c.line : c.border) : "#0f1e2e"}`,
                  borderRadius: 6, padding: "8px 6px", textAlign: "center",
                  boxShadow: glow ? `0 0 12px ${c.line}55` : "none",
                  opacity: dimmed ? 0.25 : 1,
                  transition: "all 0.2s",
                  minHeight: 64,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                }}>
                  <div style={{ fontSize: 8, color: "#1e3a5f", letterSpacing: "0.1em", marginBottom: 4 }}>{slot}</div>
                  {m ? (
                    <>
                      <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 14, color: c.line, letterSpacing: "0.08em", lineHeight: 1 }}>{m.name}</div>
                      <div style={{ fontSize: 7, color: "#334155", marginTop: 2 }}>{m.code.split("-")[1]}</div>
                    </>
                  ) : (
                    <div style={{ fontSize: 8, color: "#1e293b", letterSpacing: "0.05em" }}>EMPTY</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("cards");
  const [activeType, setActiveType] = useState(null);
  const [filterChange, setFilterChange] = useState("all");

  const filteredMachines = machines.filter(m => {
    if (filterChange === "new") return m.isNew;
    if (filterChange === "moved") return m.moved;
    if (filterChange === "fixed") return m.unchanged;
    return true;
  }).filter(m => !activeType || m.name === activeType);

  const stats = {
    total: machines.length,
    newM: machines.filter(m => m.isNew).length,
    moved: machines.filter(m => m.moved).length,
    fixed: machines.filter(m => m.unchanged).length,
  };

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
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)} }
        .fade-up { animation: fadeUp 0.3s ease forwards; }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0.3} }
        .blink { animation: blink 1.6s ease-in-out infinite; }
        .type-btn { background: transparent; border: 1px solid; border-radius: 4px; padding: 4px 12px; cursor: pointer; font-family: 'DM Mono',monospace; font-size: 10px; letter-spacing: 0.08em; transition: all 0.15s; }
      `}</style>

      {/* HEADER */}
      <div style={{ background: "#060f1c", borderBottom: "1px solid #1e3a5f", padding: "14px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 3, height: 34, background: "#2563eb", borderRadius: 2 }} />
          <div>
            <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 22, letterSpacing: "0.12em", color: "#60a5fa" }}>MACHINE LAYOUT</div>
            <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>FLOOR CONFIGURATION CHANGE LOG — INJECTION MOLDING</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.1em" }}>
            <span style={{ color: "#334155" }}>FROM</span> <span style={{ color: "#60a5fa" }}>{DATE_A}</span>
            <span style={{ color: "#1e3a5f", margin: "0 8px" }}>→</span>
            <span style={{ color: "#334155" }}>TO</span> <span style={{ color: "#fbbf24" }}>{DATE_B}</span>
          </div>
          <div style={{ width: 1, height: 16, background: "#1e3a5f" }} />
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} className="blink" />
        </div>
      </div>

      <div style={{ padding: "20px 28px" }}>
        {/* KPI */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 18 }} className="fade-up">
          {[
            { label: "TOTAL MACHINES", value: stats.total, color: "#60a5fa", sub: "in layout" },
            { label: "NEWLY ADDED", value: stats.newM, color: "#a78bfa", sub: `as of ${DATE_B}` },
            { label: "POSITION CHANGED", value: stats.moved, color: "#fbbf24", sub: "slot reassigned" },
            { label: "UNCHANGED", value: stats.fixed, color: "#22c55e", sub: "same slot" },
          ].map(k => (
            <div key={k.label} style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderLeft: `3px solid ${k.color}`, borderRadius: 8, padding: "14px 18px" }}>
              <div style={{ fontSize: 9, color: "#475569", letterSpacing: "0.15em", marginBottom: 6 }}>{k.label}</div>
              <div style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 36, color: k.color, lineHeight: 1 }}>{k.value}</div>
              <div style={{ fontSize: 9, color: "#334155", marginTop: 3 }}>{k.sub}</div>
            </div>
          ))}
        </div>

        {/* MACHINE TYPE LEGEND + FILTERS */}
        <div style={{ background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, padding: "12px 16px", marginBottom: 14, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
          <button className={`pill ${view === "cards" ? "active" : ""}`} onClick={() => setView("cards")}>CARD VIEW</button>
          <button className={`pill ${view === "floor" ? "active" : ""}`} onClick={() => setView("floor")}>FLOOR PLAN</button>
          <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
          {/* Type filter */}
          {machineTypes.map(t => {
            const c = typeColors[t] || { line: "#64748b", border: "#334155" };
            const isActive = activeType === t;
            return (
              <button key={t} onClick={() => setActiveType(isActive ? null : t)} className="type-btn"
                style={{ borderColor: isActive ? c.line : c.border, color: isActive ? c.line : "#475569", background: isActive ? c.line + "22" : "transparent" }}>
                {t}
              </button>
            );
          })}
          {view === "cards" && (
            <>
              <div style={{ width: 1, height: 20, background: "#1e3a5f" }} />
              {[["all","ALL"],["new","NEW"],["moved","MOVED"],["fixed","FIXED"]].map(([v,l]) => (
                <button key={v} className={`pill ${filterChange===v?"active":""}`} onClick={() => setFilterChange(v)}>{l}</button>
              ))}
            </>
          )}
          <span style={{ marginLeft: "auto", fontSize: 9, color: "#334155", letterSpacing: "0.1em" }}>
            {activeType ? `${activeType} ·` : ""} {view === "cards" ? `${filteredMachines.length} MACHINES` : `${machines.length} MACHINES`}
          </span>
        </div>

        {/* CHANGE LEGEND */}
        <div style={{ display: "flex", gap: 16, marginBottom: 14, alignItems: "center" }}>
          {[
            { color: "#a78bfa", sym: "+", label: "New machine added" },
            { color: "#fbbf24", sym: "→", label: "Position reassigned" },
            { color: "#22c55e", sym: "＝", label: "Position unchanged" },
          ].map(l => (
            <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 9, color: "#475569", letterSpacing: "0.05em" }}>
              <span style={{ color: l.color, fontSize: 13, fontWeight: 700 }}>{l.sym}</span>
              {l.label}
            </div>
          ))}
        </div>

        {/* CARD VIEW */}
        {view === "cards" && (
          <div className="fade-up">
            {filteredMachines.length === 0 ? (
              <div style={{ textAlign: "center", padding: 60, color: "#334155", fontSize: 11, letterSpacing: "0.1em" }}>NO MACHINES MATCH FILTER</div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
                {filteredMachines.map(m => (
                  <MachineCard key={m.code} m={m} highlight={activeType ? m.name === activeType : null} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* FLOOR PLAN VIEW */}
        {view === "floor" && (
          <div className="fade-up">
            <FloorPlan activeType={activeType} />

            {/* Diff table */}
            <div style={{ marginTop: 16, background: "#0c1a2e", border: "1px solid #1e3a5f", borderRadius: 8, overflow: "hidden" }}>
              <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e3a5f", fontSize: 9, color: "#475569", letterSpacing: "0.2em" }}>
                POSITION CHANGE SUMMARY
              </div>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                <thead>
                  <tr>
                    {["MACHINE TYPE","CODE","SLOT — 2018-11-01","SLOT — 2019-01-15","CHANGE"].map(h => (
                      <th key={h} style={{ padding: "8px 14px", textAlign: "left", fontSize: 8, color: "#475569", letterSpacing: "0.12em", fontWeight: 500, borderBottom: "1px solid #1e3a5f", background: "#060f1c", whiteSpace: "nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {machines.map((m, i) => {
                    const c = typeColors[m.name] || { line: "#64748b" };
                    const tag = m.isNew ? { label: "NEW", color: "#a78bfa" }
                      : m.moved ? { label: "MOVED", color: "#fbbf24" }
                      : { label: "FIXED", color: "#22c55e" };
                    const dimmed = activeType && m.name !== activeType;
                    return (
                      <tr key={i} style={{ borderBottom: "1px solid #0a1929", background: i%2===0?"transparent":"#060e1a", opacity: dimmed ? 0.3 : 1, transition: "opacity 0.2s" }}>
                        <td style={{ padding: "9px 14px" }}>
                          <span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 16, color: c.line, letterSpacing: "0.08em" }}>{m.name}</span>
                        </td>
                        <td style={{ padding: "9px 14px", fontSize: 10, color: "#64748b" }}>{m.code}</td>
                        <td style={{ padding: "9px 14px" }}>
                          {m.posA
                            ? <span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 16, color: "#475569", letterSpacing: "0.08em" }}>{m.posA}</span>
                            : <span style={{ fontSize: 9, color: "#1e3a5f" }}>NOT INSTALLED</span>
                          }
                        </td>
                        <td style={{ padding: "9px 14px" }}>
                          <span style={{ fontFamily: "'Bebas Neue',sans-serif", fontSize: 16, color: c.line, letterSpacing: "0.08em" }}>{m.posB}</span>
                        </td>
                        <td style={{ padding: "9px 14px" }}>
                          <span style={{ fontSize: 8, padding: "2px 8px", borderRadius: 3, background: tag.color + "22", color: tag.color, border: `1px solid ${tag.color}44`, letterSpacing: "0.1em" }}>
                            {tag.label}
                          </span>
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
    </div>
  );
}