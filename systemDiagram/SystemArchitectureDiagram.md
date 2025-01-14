```
System Architecture Diagram

+-------------------------------------------------------------+
|                         User Interface                      |
|     (Dashboard, Alerts, Reports, Manual Inputs)             |
+-------------------------------------------------------------+
                     ↓                 ↑
+----------------------------- API Layer ----------------------+
                     ↓                 ↑
+--------------------- Functional Agents ----------------------+
|  - Production Monitoring Agent                               |
|  - Machine Management Agent                                  |
|  - Material Management Agent                                 |
|  - NG Analysis Agent                                         |
|  - Mold Schedule Agent                                       |
|  - Inventory Optimization Agent                              |
|  - Inventory Agent                                           |
|  - Scheduling and Planning Agent                             |
|  - Energy Efficiency Agent (Optional)                        |
+--------------------------------------------------------------+
                     ↓                 ↑
+------------------- Database Layer ---------------------------+
|  Static Database       | Dynamic Database    | Main Database |
+-------------------------+---------------------+--------------+
                     ↓                 ↑
+------------------- Shared Database (Relevant Agents) --------+
                     ↓                 ↑
+------------------ Real-Time Data Collection -----------------+
|  - Existing Files                                            |
|  - Manual Logs                                               |
+--------------------------------------------------------------+

```