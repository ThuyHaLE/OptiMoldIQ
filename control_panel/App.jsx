import { useState, useRef, useEffect } from "react";
import { MOCK_WORKFLOWS, MOCK_VIZ_CACHE } from "./data.js";
import InitialPlanningViz  from "./initial_planning_module/initial_planning_module.jsx";
import ProgressTrackingViz from "./progress_tracking_module/progress_tracking_module.jsx";
import AnalyticsViz        from "./analytics_module/analytics_module.jsx";

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  CONFIG
// ╚══════════════════════════════════════════════════════════════════════════════
const USE_MOCK = import.meta.env.DEV;
const API_BASE = import.meta.env.DEV ? "http://localhost:8000" : "";

// ── API layer ─────────────────────────────────────────────────────────────────
const api = USE_MOCK
  ? {
      workflows: () => Promise.resolve(MOCK_WORKFLOWS),
      allViz: () => Promise.resolve(MOCK_VIZ_CACHE),
      execute: (name) => new Promise((res) => setTimeout(() => res({ job_id: Math.random().toString(36).slice(2, 10) }), 400)),
      jobStatus: (jobId) => new Promise((res) => setTimeout(() => res({ status: "success", modules: {} }), 1200)),
    }
  : {
      workflows: () => fetch(`${API_BASE}/api/workflows`).then((r) => r.json()),
      allViz: () => fetch(`${API_BASE}/api/viz`).then((r) => r.json()),
      execute: (name) => fetch(`${API_BASE}/api/execute/${name}`, { method: "POST" }).then((r) => r.json()),
      jobStatus: (jobId) => fetch(`${API_BASE}/api/execute/${jobId}/status`).then((r) => r.json()),
    };

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  HELPERS
// ╚══════════════════════════════════════════════════════════════════════════════
function fmtAgo(epoch) {
  if (!epoch) return "";
  const s = Math.floor(Date.now() / 1000 - epoch);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}
function fmtTs(epoch) {
  if (!epoch) return "—";
  const d = new Date(epoch * 1000);
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map((n) => String(n).padStart(2, "0")).join(":");
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  VIZ REGISTRY — maps module name → { component, dataExtractor }
// ║  dataExtractor: (viz_data) => props for component
// ╚══════════════════════════════════════════════════════════════════════════════
const VIZ_REGISTRY = {
  ProgressTrackingModule: {
    label: "Progress Tracker",
    Component: ProgressTrackingViz,
    extract: (viz_data) => viz_data || null,
  },
  AnalyticsModule: {
    label: "Production Analytics",
    Component: AnalyticsViz,
    extract: (viz_data) => viz_data || null,
  },
  InitialPlanningModule: {
    label: "Planning Dashboard",
    Component: InitialPlanningViz,
    extract: (viz_data) => viz_data || null,
  },
};

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  TERMINAL
// ╚══════════════════════════════════════════════════════════════════════════════
function useTerminal() {
  const [lines, setLines] = useState([
    { ts: "00:00:00", text: "OptiMoldIQ Control Panel initialized", type: "sys" },
    { ts: "00:00:00", text: "ModuleRegistry loaded. Awaiting workflow selection.", type: "sys" },
  ]);
  const push = (text, type = "info") => {
    const now = new Date();
    const ts = [now.getHours(), now.getMinutes(), now.getSeconds()].map((n) => String(n).padStart(2, "0")).join(":");
    setLines((l) => [...l.slice(-120), { ts, text, type }]);
  };
  return { lines, push };
}

function Terminal({ lines }) {
  const ref = useRef(null);
  useEffect(() => { ref.current?.scrollTo(0, ref.current.scrollHeight); }, [lines]);
  const colorMap = { sys: "#6366f1", info: "#a1a1aa", success: "#22c55e", error: "#ef4444", warn: "#f59e0b" };
  return (
    <div ref={ref} style={{ background: "#09090f", border: "1px solid #1e1e2e", borderRadius: 2, padding: "12px 16px", fontFamily: "'IBM Plex Mono',monospace", fontSize: 11, height: 160, overflowY: "auto", lineHeight: 1.7 }}>
      {lines.map((l, i) => (
        <div key={i} style={{ display: "flex", gap: 12 }}>
          <span style={{ color: "#3f3f5a", flexShrink: 0 }}>{l.ts}</span>
          <span style={{ color: colorMap[l.type] || "#a1a1aa" }}>{l.text}</span>
        </div>
      ))}
      <div style={{ color: "#6366f1" }}>▌</div>
    </div>
  );
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  VIZ PANEL (fullscreen overlay)
// ╚══════════════════════════════════════════════════════════════════════════════
function VizPanel({ moduleName, entry, onClose }) {
  const reg = VIZ_REGISTRY[moduleName];
  if (!reg) return null;
  const { Component, extract, label } = reg;
  const data = extract(entry?.viz_data);
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 200, display: "flex", flexDirection: "column", background: "#07070f" }}>
      <div style={{ background: "#09090f", borderBottom: "1px solid #1e1e2e", padding: "0 24px", display: "flex", alignItems: "center", gap: 0, flexShrink: 0 }}>
        <div style={{ padding: "10px 16px", fontSize: 11, color: "#4a4a6a", fontFamily: "'IBM Plex Mono',monospace", cursor: "pointer", borderRight: "1px solid #1e1e2e" }} onClick={onClose}>
          <span style={{ fontSize: 9 }}>←</span> CONTROL PANEL
        </div>
        <div style={{ padding: "10px 16px", fontSize: 11, color: "#a5b4fc", fontFamily: "'IBM Plex Mono',monospace", background: "#0d0d1f", borderRight: "1px solid #1e1e2e", borderBottom: "2px solid #6366f1", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#6366f1", display: "inline-block" }} />
          {label} <span style={{ color: "#3a3a5a", marginLeft: 6, fontSize: 9 }}>[{moduleName}]</span>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          {entry?.timestamp && (
            <span style={{ fontSize: 9, color: "#3a3a5a", fontFamily: "'IBM Plex Mono',monospace" }}>
              run #{entry.execution_id} · {fmtTs(entry.timestamp)}
            </span>
          )}
          <button onClick={onClose} style={{ padding: "4px 12px", background: "transparent", border: "1px solid #2a2a3a", borderRadius: 2, color: "#5a5a7a", fontSize: 11, fontFamily: "'IBM Plex Mono',monospace", cursor: "pointer" }}>✕ CLOSE</button>
        </div>
      </div>
      <div style={{ flex: 1, overflow: "auto" }}>  {/* ← hidden → auto */}
        <Component data={data} />
      </div>
    </div>
  );
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  MODULE ROW
// ╚══════════════════════════════════════════════════════════════════════════════
const STATUS_COLORS = { idle: "#4a4a5a", running: "#f59e0b", success: "#22c55e", failed: "#ef4444", skipped: "#6366f1" };
const STATUS_LABELS = { idle: "IDLE", running: "RUNNING", success: "SUCCESS", failed: "FAILED", skipped: "SKIPPED" };

function ModuleRow({ mod, status, hasVizData, onShowViz }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.idle;
  const canViz = hasVizData && !!VIZ_REGISTRY[mod.module];

function normalizeDependencyPolicy(policy) {
  if (typeof policy === "string") return { name: policy, params: {} };
  return policy;
}

  // Normalize dependency_policy
  const depPolicy = normalizeDependencyPolicy(mod.dependency_policy);
  const policyName = depPolicy.name;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 80px 90px 72px 120px", gap: 12, padding: "8px 12px", borderBottom: "1px solid #13131f", fontFamily: "'IBM Plex Mono',monospace", fontSize: 11, alignItems: "center", background: status === "running" ? "#0f0f1a" : "transparent" }}>
      <span style={{ color: "#5a5a7a", fontSize: 10 }}>{mod.id}</span>
      <span style={{ color: "#c9c9d9" }}>{mod.module}</span>
      <span 
        style={{ color: policyName === "strict" ? "#ef4444" : "#6366f1", fontSize: 9, cursor: "help" }}
        title={JSON.stringify(depPolicy.params, null, 2)}>{policyName.toUpperCase()}
      </span>
      <span style={{ color: mod.required ? "#f59e0b" : "#4a4a6a", fontSize: 9 }}>{mod.required ? "REQUIRED" : "OPTIONAL"}</span>
      <span style={{ color, fontSize: 10, fontWeight: 700, display: "flex", alignItems: "center", gap: 4, justifyContent: "flex-end" }}>
        {status === "running" && <span style={{ width: 6, height: 6, borderRadius: "50%", background: color, animation: "pulse 0.8s ease-in-out infinite" }} />}
        {STATUS_LABELS[status] || "IDLE"}
      </span>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        {canViz ? (
          <button onClick={() => onShowViz(mod.module)}
            style={{ padding: "3px 10px", background: "rgba(99,102,241,0.15)", border: "1px solid #6366f140", borderRadius: 2, color: "#a5b4fc", fontSize: 9, fontFamily: "'IBM Plex Mono',monospace", fontWeight: 700, cursor: "pointer", letterSpacing: 0.5 }}
            onMouseEnter={(e) => (e.target.style.background = "rgba(99,102,241,0.3)")}
            onMouseLeave={(e) => (e.target.style.background = "rgba(99,102,241,0.15)")}>
            ▤ VIEW OUTPUT
          </button>
        ) : (
          <span style={{ fontSize: 9, color: "#2a2a4a" }}>—</span>
        )}
      </div>
    </div>
  );
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  WORKFLOW CARD (sidebar)
// ╚══════════════════════════════════════════════════════════════════════════════
const WF_STATUS_COLOR = { success: "#22c55e", failed: "#ef4444", running: "#f59e0b" };

function WorkflowCard({ wf, isSelected, onClick, entry }) {
  return (
    <div onClick={onClick} style={{ border: `1px solid ${isSelected ? "#6366f1" : "#1e1e2e"}`, borderRadius: 2, padding: "14px 16px", cursor: "pointer", background: isSelected ? "#0d0d1f" : "#0a0a14", transition: "all 0.15s", position: "relative", overflow: "hidden" }}>
      {isSelected && <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 3, background: "#6366f1" }} />}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
        <div style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 11, color: isSelected ? "#a5b4fc" : "#7070a0" }}>{wf.workflow_name}</div>
        {entry && <span style={{ fontSize: 9, color: WF_STATUS_COLOR[entry.status] || "#4a4a6a", fontWeight: 700 }}>{entry.status?.toUpperCase()}</span>}
      </div>
      <div style={{ fontSize: 10, color: "#4a4a6a" }}>{wf.description}</div>
      <div style={{ fontSize: 9, color: "#3a3a5a", marginTop: 6, fontFamily: "'IBM Plex Mono',monospace", display: "flex", justifyContent: "space-between" }}>
        <span>{wf.modules.length} modules</span>
        {entry?.timestamp && <span style={{ color: "#2a2a4a" }}>{fmtAgo(entry.timestamp)}</span>}
      </div>
      {entry?.viz_data && (
        <div style={{ marginTop: 6, fontSize: 8, color: "#4a5a7a", display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 4, height: 4, borderRadius: "50%", background: "#6366f1", display: "inline-block" }} />
          viz data available
        </div>
      )}
    </div>
  );
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  STAT
// ╚══════════════════════════════════════════════════════════════════════════════
function Stat({ label, value, color }) {
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 22, fontWeight: 700, color: color || "#c9c9d9" }}>{value}</div>
      <div style={{ fontSize: 9, color: "#4a4a6a", marginTop: 2, letterSpacing: 1 }}>{label}</div>
    </div>
  );
}

// ╔══════════════════════════════════════════════════════════════════════════════
// ║  APP
// ╚══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [moduleStatuses, setModuleStatuses] = useState({}); // { moduleId: status }
  const [running, setRunning] = useState(false);
  const [runCount, setRunCount] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [failCount, setFailCount] = useState(0);
  const [vizCache, setVizCache] = useState({}); // { workflow_name: entry }
  const [activeViz, setActiveViz] = useState(null); // { moduleName, workflowName }
  const { lines, push } = useTerminal();

  useEffect(() => {
    Promise.all([api.workflows(), api.allViz()])
      .then(([wfs, viz]) => {
        setWorkflows(wfs);
        setSelected(wfs[0] || null);
        setVizCache(viz);
        push(`Loaded ${wfs.length} workflows`, "sys");
        Object.entries(viz).forEach(([name, entry]) => {
          if (entry?.viz_data) push(`Viz cache: ${name} has output data`, "info");
        });
      })
      .catch((err) => push(`Backend unavailable: ${err.message}`, "error"))
      .finally(() => setLoading(false));
  }, []);

  // For each module in current workflow, does viz_data exist for it?
  const currentEntry = selected ? vizCache[selected.workflow_name] || null : null;

  function getLastSuccessfulVizModule() {
    if (!currentEntry?.summary?.modules) return null;
    const moduleEntries = Object.entries(currentEntry.summary.modules);
    // Get the last module with status "success" that also exists in VIZ_REGISTRY
    for (let i = moduleEntries.length - 1; i >= 0; i--) {
      const [moduleName, status] = moduleEntries[i];
      if (status === "success" && VIZ_REGISTRY[moduleName]) {
        return moduleName;
      }
    }
    return null;
  }

  function moduleHasViz(moduleName) {
    if (!currentEntry?.viz_data) return false;
    if (!VIZ_REGISTRY[moduleName]) return false;
    // Only acess viz_data for the last successful module in the workflow that has a viz registered 
    const lastVizModule = getLastSuccessfulVizModule();
    if (moduleName !== lastVizModule) return false;
    return Object.keys(currentEntry.viz_data).length > 0;
  }
  
  const handleSelect = (wf) => {
    if (running) return;
    setSelected(wf);
    setModuleStatuses({});
    push(`Workflow selected: ${wf.workflow_name}`, "sys");
  };

  const handleExecute = async () => {
    if (running || !selected) return;
    setRunning(true);
    setModuleStatuses({});
    setRunCount((c) => c + 1);
    push(`Executing workflow: ${selected.workflow_name}`, "info");

    try {
      const { job_id } = await api.execute(selected.workflow_name);
      push(`Job dispatched — ID: ${job_id}`, "info");

      // Simulate module-by-module progress for mock
      if (USE_MOCK) {
        for (const mod of selected.modules) {
          setModuleStatuses((s) => ({ ...s, [mod.id]: "running" }));
          push(`[${mod.id}] ${mod.module} running...`, "info");
          await new Promise((r) => setTimeout(r, 500 + Math.random() * 400));
          setModuleStatuses((s) => ({ ...s, [mod.id]: "success" }));
          push(`[${mod.id}] completed`, "success");
        }
        push(`Workflow "${selected.workflow_name}" — SUCCESS`, "success");
        setSuccessCount((c) => c + 1);
        const newViz = await api.allViz();
        setVizCache(newViz);
      } else {
        let done = false;
        while (!done) {
          await new Promise((r) => setTimeout(r, 600));
          const job = await api.jobStatus(job_id);
          if (job.modules) {
            Object.entries(job.modules).forEach(([modId, status]) => {
              setModuleStatuses((s) => ({ ...s, [modId]: status }));
              if (status === "success") push(`[${modId}] completed`, "success");
              if (status === "failed") push(`[${modId}] FAILED`, "error");
            });
          }
          if (job.status === "success") {
            push(`Workflow "${selected.workflow_name}" — SUCCESS`, "success");
            setSuccessCount((c) => c + 1);
            const newViz = await api.allViz();
            setVizCache(newViz);
            done = true;
          } else if (job.status === "failed") {
            push(`Workflow "${selected.workflow_name}" — FAILED`, "error");
            setFailCount((c) => c + 1);
            done = true;
          }
        }
      }
    } catch (err) {
      push(`Execution error: ${err.message}`, "error");
      setFailCount((c) => c + 1);
    }
    setRunning(false);
  };

  if (loading) return (
    <div style={{ minHeight: "100vh", background: "#07070f", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono',monospace", color: "#6366f1", fontSize: 13, gap: 12 }}>
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.2}}`}</style>
      <span>▌</span> Connecting to OptiMoldIQ backend...
    </div>
  );

  if (!selected) return null;

  // Viz modules with data
  const vizModulesInWorkflow = selected.modules.filter((m) => moduleHasViz(m.module) && VIZ_REGISTRY[m.module]);

  return (
    <div style={{ minHeight: "100vh", background: "#07070f", color: "#c9c9d9", fontFamily: "system-ui,sans-serif", paddingBottom: 40 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap');
        *{box-sizing:border-box;margin:0;padding:0;}
        ::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-track{background:#0a0a14;} ::-webkit-scrollbar-thumb{background:#2a2a3a;}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        .exec-btn:hover:not(:disabled){background:#4f46e5!important;}
        .exec-btn:disabled{opacity:0.5;cursor:not-allowed;}
      `}</style>

      {/* Viz Panel overlay */}
      {activeViz && (
        <VizPanel
          moduleName={activeViz.moduleName}
          entry={vizCache[activeViz.workflowName]}
          onClose={() => setActiveViz(null)}
        />
      )}

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1e1e2e", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#09090f" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 32, height: 32, background: "#6366f1", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono',monospace", fontSize: 13, fontWeight: 700, color: "#fff", borderRadius: 2 }}>OM</div>
          <div>
            <div style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 14, color: "#a5b4fc", fontWeight: 700 }}>OptiMoldIQ</div>
            <div style={{ fontSize: 9, color: "#3a3a5a", letterSpacing: 1 }}>CONTROL PANEL</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 32 }}>
          <Stat label="EXECUTIONS" value={runCount} color="#a5b4fc" />
          <Stat label="SUCCESS" value={successCount} color="#22c55e" />
          <Stat label="FAILED" value={failCount} color="#ef4444" />
        </div>
      </div>

      <div style={{ maxWidth: 1240, margin: "0 auto", padding: "28px 24px", display: "grid", gridTemplateColumns: "260px 1fr", gap: 24 }}>
        {/* Sidebar */}
        <div>
          <div style={{ fontSize: 9, color: "#3a3a5a", letterSpacing: 2, marginBottom: 12, fontFamily: "'IBM Plex Mono',monospace" }}>WORKFLOWS</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {workflows.map((wf) => (
              <WorkflowCard key={wf.workflow_name} wf={wf} isSelected={selected.workflow_name === wf.workflow_name} onClick={() => handleSelect(wf)} entry={vizCache[wf.workflow_name]} />
            ))}
          </div>

          {/* Viz available indicator */}
          <div style={{ marginTop: 28, padding: 14, background: "#0a0a14", border: "1px solid #1e1e2e", borderRadius: 2 }}>
            <div style={{ fontSize: 9, color: "#3a3a5a", letterSpacing: 2, marginBottom: 10, fontFamily: "'IBM Plex Mono',monospace" }}>VIZ REGISTRY</div>
            {Object.entries(VIZ_REGISTRY).map(([name, reg]) => (
              <div key={name} style={{ fontSize: 9, color: "#4a4a6a", lineHeight: 2, fontFamily: "'IBM Plex Mono',monospace" }}>
                <span style={{ color: "#6366f1" }}>◈</span> {name}
                <span style={{ color: "#2a2a4a", marginLeft: 6 }}>→ {reg.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Main panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Workflow detail */}
          <div style={{ background: "#0a0a14", border: "1px solid #1e1e2e", borderRadius: 2 }}>
            <div style={{ padding: "12px 16px", borderBottom: "1px solid #13131f", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <span style={{ fontFamily: "'IBM Plex Mono',monospace", fontSize: 12, color: "#a5b4fc" }}>{selected.workflow_name}</span>
                <span style={{ fontSize: 11, color: "#4a4a6a", marginLeft: 12 }}>{selected.description}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                {currentEntry && (
                  <span style={{ fontSize: 9, color: "#3a3a5a", fontFamily: "'IBM Plex Mono',monospace" }}>
                    #{currentEntry.execution_id} &nbsp;·&nbsp;
                    <span style={{ color: WF_STATUS_COLOR[currentEntry.status] || "#4a4a6a" }}>
                      {currentEntry.summary.success}/{currentEntry.summary.total} ok
                    </span>
                    &nbsp;·&nbsp; {currentEntry.duration}s
                  </span>
                )}
                <button className="exec-btn" onClick={handleExecute} disabled={running}
                  style={{ background: "#6366f1", color: "#fff", border: "none", padding: "8px 20px", fontFamily: "'IBM Plex Mono',monospace", fontSize: 11, fontWeight: 700, letterSpacing: 1, cursor: "pointer", borderRadius: 2, display: "flex", alignItems: "center", gap: 8 }}>
                  {running && <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#fff", animation: "pulse 0.6s ease-in-out infinite" }} />}
                  {running ? "RUNNING..." : "▶ EXECUTE"}
                </button>
              </div>
            </div>

            {/* Column headers */}
            <div style={{ display: "grid", gridTemplateColumns: "120px 1fr 80px 90px 72px 120px", gap: 12, padding: "6px 12px", borderBottom: "1px solid #13131f", fontSize: 8, color: "#3a3a5a", letterSpacing: 1.5, fontFamily: "'IBM Plex Mono',monospace" }}>
              <span>MODULE ID</span><span>CLASS</span><span>POLICY</span><span>REQUIRED</span>
              <span style={{ textAlign: "right" }}>STATUS</span><span style={{ textAlign: "right" }}>OUTPUT</span>
            </div>

            {selected.modules.map((mod) => (
              <ModuleRow
                key={mod.id}
                mod={mod}
                status={moduleStatuses[mod.id] || "idle"}
                hasVizData={moduleHasViz(mod.module)}
                onShowViz={(moduleName) => setActiveViz({ moduleName, workflowName: selected.workflow_name })}
              />
            ))}
          </div>

          {/* Viz output shortcuts — show when viz data exists */}
          {vizModulesInWorkflow.length > 0 && (
            <div style={{ background: "#0a0a14", border: "1px solid #1e2d45", borderRadius: 2 }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid #13131f", fontSize: 9, color: "#4a5a7a", letterSpacing: 2, fontFamily: "'IBM Plex Mono',monospace", display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#6366f1" }} />
                OUTPUT VISUALIZATIONS
              </div>
              <div style={{ padding: "12px 16px", display: "flex", gap: 10, flexWrap: "wrap" }}>
                {vizModulesInWorkflow.map((mod) => {
                  const reg = VIZ_REGISTRY[mod.module];
                  return (
                    <button key={mod.module} onClick={() => setActiveViz({ moduleName: mod.module, workflowName: selected.workflow_name })}
                      style={{ padding: "8px 16px", background: "rgba(99,102,241,0.1)", border: "1px solid #6366f130", borderRadius: 4, color: "#a5b4fc", fontSize: 10, fontFamily: "'IBM Plex Mono',monospace", cursor: "pointer", display: "flex", alignItems: "center", gap: 8, transition: "all 0.15s" }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(99,102,241,0.25)"; e.currentTarget.style.borderColor = "#6366f1"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(99,102,241,0.1)"; e.currentTarget.style.borderColor = "#6366f130"; }}>
                      <span style={{ fontSize: 14 }}>▤</span>
                      <div style={{ textAlign: "left" }}>
                        <div style={{ fontWeight: 700 }}>{reg.label}</div>
                        <div style={{ fontSize: 8, color: "#4a5a7a", marginTop: 1 }}>{mod.module}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Execution log */}
          <div style={{ background: "#0a0a14", border: "1px solid #1e1e2e", borderRadius: 2 }}>
            <div style={{ padding: "10px 16px", borderBottom: "1px solid #13131f", fontSize: 9, color: "#3a3a5a", letterSpacing: 2, fontFamily: "'IBM Plex Mono',monospace" }}>EXECUTION LOG</div>
            <div style={{ padding: "12px 0" }}>
              <Terminal lines={lines} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}