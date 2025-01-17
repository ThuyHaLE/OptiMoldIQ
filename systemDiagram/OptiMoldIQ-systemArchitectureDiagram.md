#System Architecture Diagram
+----------------------------------------------------------------------+
|                         User Interface                               |
|     (Dashboard, Alerts, Reports, Manual Inputs)                      |
+----------------------------------------------------------------------+
                     ↓                 ↑
+-------------------------------- API Layer ---------------------------+
                     ↓                 ↑
+------------------------ Functional Agents ---------------------------+
|  - AutoStatus Agent                                                  |
|  - InitialSched Agent                                                |
|  - FinalSched Agent                                                  |
|  - Resin Tracking Agent                                              |
|  - Mold Tracking Agent                                               |
|  - Machine Tracking Agent                                            |
|  - ResinRestock Agent                                                |
|  - MaintenanceScheduler Agent                                        |
|  - YieldOptimization Agent                                           |
|  - DashBoardBuilderAgent                                             |
|  - Energy Efficiency Agent (Optional)                                |
+----------------------------------------------------------------------+
                     ↓                 ↑
+---------------------------- Database Layer --------------------------+
| Static Database  | Dynamic Database  | Main Data  | Shared Database  |
|                  |                   |            | (Agent reports)  |
+----------------------------+------------------------+----------------+
                     ↓                 ↑
+------------------- Shared Database (Relevant Agents) ----------------+
                     ↓                 ↑
+------------------ Real-Time Data Collection -------------------------+
|  - Existing Files                                                    |
|  - Manual Logs                                                       |
+----------------------------------------------------------------------+

```