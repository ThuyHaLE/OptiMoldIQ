// ============================================================
// app.js — Root App component
// Depends on: window.MOCK_WORKFLOWS, window.MOCK_VIZ_CACHE
//             window.AnalyticsViz, window.ProgressTrackingViz
//             window.InitialPlanningViz
// ============================================================

(function() {
  const { useState } = React;

  const WORKFLOW_COMPONENT_MAP = {
    analyze_production_records_strict: window.AnalyticsViz,
    track_order_progress_strict:       window.ProgressTrackingViz,
    process_initial_planning_strict:   window.InitialPlanningViz,
  };

  function App() {
    const workflows = window.MOCK_WORKFLOWS || [];
    const vizCache  = window.MOCK_VIZ_CACHE  || {};

    const [activeId, setActiveId] = useState(workflows[0]?.workflow_name || null);

    const active = workflows.find(w => w.workflow_name === activeId);
    const vizData = activeId ? vizCache[activeId] : null;
    const VizComponent = activeId ? WORKFLOW_COMPONENT_MAP[activeId] : null;

    return React.createElement('div', { style: { minHeight:"100vh", background:"#07090f", fontFamily:"monospace", display:"flex", flexDirection:"column" } },
      // Top nav
      React.createElement('div', { style: { background:"#0d1117", borderBottom:"1px solid #1c2333", padding:"0 24px", display:"flex", alignItems:"center", height:52, gap:0, position:"sticky", top:0, zIndex:200 } },
        React.createElement('div', { style: { fontSize:12, fontWeight:700, color:"#3b82f6", letterSpacing:"0.15em", marginRight:32 } }, "OPTIMOLDIQ"),
        React.createElement('div', { style: { display:"flex", height:"100%", gap:0, overflowX:"auto" } },
          ...workflows.map(w => {
            const active = w.workflow_name === activeId;
            return React.createElement('button', { key: w.workflow_name, onClick: () => setActiveId(w.workflow_name),
              style: {
                padding:"0 20px", border:"none", background:"transparent",
                borderBottom: active ? "2px solid #3b82f6" : "2px solid transparent",
                borderTop: "2px solid transparent",
                color: active ? "#93c5fd" : "#4b5563",
                cursor:"pointer", fontSize:11, fontFamily:"monospace",
                letterSpacing:"0.06em", whiteSpace:"nowrap",
                transition:"all .15s",
              }
            }, w.display_name || w.workflow_name);
          })
        )
      ),
      // Content
      React.createElement('div', { style: { flex:1, overflow:"auto" } },
        VizComponent && vizData
          ? React.createElement(VizComponent, { data: vizData })
          : React.createElement('div', { style: { display:"flex", alignItems:"center", justifyContent:"center", height:"60vh", color:"#4b5563", fontSize:13, letterSpacing:"0.1em" } },
              activeId ? `No visualization data for: ${activeId}` : "Select a workflow above"
            )
      )
    );
  }

  ReactDOM.render(React.createElement(App), document.getElementById("root"));
})();
