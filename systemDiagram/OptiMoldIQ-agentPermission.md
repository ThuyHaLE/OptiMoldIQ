# **Agent Permission Definitions**
This document outlines the permissions required for each agent in the **OptiMoldIQ system**.

---

## 🔑 Permission Levels
- **🔵 Read** → Can view data only.  
- **🟢 Write** → Can modify existing records.  
- **🟠 Update** → Can change specific fields.  
- **🔴 Delete** → Can remove records.  

---

## 🎯 **Agent Permissions Table**
| Agent Name                 | Read | Write | Update | Delete | Notes |
|----------------------------|------|-------|--------|--------|-------|
| **AutoStatus Agent**       | ✅   | ✅    | ✅     | ❌     | Updates production status reports. |
| **InitialSched Agent**     | ✅   | ✅    | ✅     | ❌     | Reads production orders and schedules initial plans. |
| **FinalSched Agent**       | ✅   | ✅    | ✅     | ❌     | Refines schedules based on resource tracking agents. |
| **ResinTracking Agent**    | ✅   | ✅    | ✅     | ❌     | Tracks resin consumption and stock. |
| **MoldTracking Agent**     | ✅   | ✅    | ✅     | ❌     | Tracks mold usage and maintenance needs. |
| **MachineTracking Agent**  | ✅   | ✅    | ✅     | ❌     | Monitors machine conditions and availability. |
| **DashBoardBuilder Agent** | ✅   | ❌    | ❌     | ❌     | Read-only access for data visualization. |

---

## **1. AutoStatus Agent**
Responsible for generating production status reports based on real-time updates.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `productRecords` |
| **Write**    | `productionStatus` (update status) |
| **No Access** | `auditLogs`, `userAccounts` |

---

## **2. InitialSched Agent**
Creates the initial production schedule based on pending POs and available resources.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `moldInfo`, `machineInfo`, `resinInfo`, `PO_list` |
| **Write**    | `initialSchedulePlan` |
| **No Access** | `auditLogs`, `userPermissions` |

---

## **3. FinalSched Agent**
Optimizes the production schedule using reports from tracking agents.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `initialSchedulePlan`, `resinTrackingReport`, `moldTrackingReport`, `machineTrackingReport` |
| **Write**    | `finalSchedulePlan` |
| **No Access** | `userAccounts`, `auditLogs` |

---

## **4. ResinTracking Agent**
Monitors resin stock levels and tracks usage.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `resinInfo`, `productionStatus`, `resinStockLevels` |
| **Write**    | `resinTrackingReport` |
| **No Access** | `userPermissions`, `auditLogs` |

---

## **5. MoldTracking Agent**
Tracks mold usage, maintenance, and shot count.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `moldInfo`, `productionStatus`, `moldMaintenanceHistory` |
| **Write**    | `moldTrackingReport` |
| **No Access** | `userPermissions`, `auditLogs` |

---

## **6. MachineTracking Agent**
Monitors machine status and logs operational history.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `machineInfo`, `productionStatus`, `machineMaintenanceHistory` |
| **Write**    | `machineTrackingReport` |
| **No Access** | `userAccounts`, `auditLogs` |

---

## **7. ResinRestock Agent**
Schedules resin restocking based on inventory and production needs.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `resinStockLevels`, `productionStatus`, `resinTrackingReport` |
| **Write**    | `resinRestockSchedule` |
| **No Access** | `userPermissions`, `auditLogs` |

---

## **8. MaintenanceScheduler Agent**
Schedules mold and machine maintenance based on reports and predefined thresholds.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `moldTrackingReport`, `machineTrackingReport`, `maintenanceHistory` |
| **Write**    | `maintenanceSchedule` |
| **No Access** | `userAccounts`, `auditLogs` |

---

## **9. DashBoardBuilder Agent**
Builds the production dashboard by aggregating data from various sources.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `initialSchedulePlan`, `finalSchedulePlan`, `resinTrackingReport`, `moldTrackingReport`, `machineTrackingReport` |
| **Write**    | `dashboardDataCache` |
| **No Access** | `userPermissions`, `auditLogs` |

---

## **10. QualityControl Agent**
Analyzes NG (non-good) rates and provides feedback on production quality.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `productRecords`, `NG_analysis` |
| **Write**    | `qualityControlReport` |
| **No Access** | `userAccounts`, `auditLogs` |

---

## **11. YieldOptimization Agent**
Optimizes cycle time while minimizing NG risks.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `productRecords`, `qualityControlReport` |
| **Write**    | `optimizedCycleTimePlan` |
| **No Access** | `userAccounts`, `auditLogs` |

---

## **12. ChangeTracking Agent**
Tracks and logs modifications to production records, ensuring changes are approved before updating the main database.

| Permission Type | Access Scope |
|---------------|--------------------------------------------------|
| **Read**     | `productionStatus`, `permissionControl`, `staticDatabase` |
| **Write**    | `changeLogReport`, `unauthorizedModificationLog` |
| **No Access** | `userAccounts`, `auditLogs` |
