# Machine & Mold Maintenance Agent

## Mold Maintenance Scheduling

### Inputs:
- **FinalSched Agent**: PO and production data to identify idle periods.
- **Machine Tracking Agent**: Machine health data to determine the condition of each machine.
- **Predefined Maintenance Library**: A library of fast maintenance tasks with estimated durations.
- **Shift Schedule**: Information to identify optimal maintenance windows.

### Decision-Making Process:
1. **Idle Period Detection**: Detect idle periods after the completion of all active production orders or during off-peak shifts (e.g., Shift 3).
2. **Maintenance Prioritization**: Prioritize machines for fast maintenance based on their remaining time to the next preventive maintenance threshold, current health status, and recent usage intensity.
3. **Task Selection**: Select appropriate fast maintenance tasks that can be completed within the available idle time.
4. **Scheduling Optimization**: Combine multiple tasks and align machine and mold maintenance tasks during the same shift.
5. **Task List Generation**: Generate the maintenance task list and notify the technicians.

### Enhanced Features:
- **Predictive Maintenance**: Forecast maintenance needs and plan proactive tasks during idle periods.
- **Dynamic Scheduling**: Reschedule non-critical tasks if a new production order arises.
- **Shift 3 Optimization**: Utilize Shift 3 for both fast and preventive maintenance tasks, especially when machines are scheduled for mold changes.
- **Real-Time Alerts**: Continuously monitor machine health and issue real-time alerts if urgent maintenance is required.

### Maintenance Task Categories:
- **Routine Maintenance (1-2 hours)**: Lubrication, cleaning, tightening components, inspecting safety mechanisms.
- **Inspection-Based Tasks (2-4 hours)**: Checking wear and tear, calibrating sensors, diagnosing minor issues.
- **Preventive Maintenance (4-8 hours or more)**: Replacing worn-out components, upgrading software, overhauling systems.

### Optimization Strategies:
- **Time Optimization**: Parallel scheduling of tasks, splitting tasks across shifts.
- **Prioritization**: Prioritize machines nearing maintenance thresholds or linked to high-demand orders.
- **Resource Allocation**: Ensure spare parts, tools, and consumables are readily available for fast maintenance.

---

## Mold Maintenance Scheduling

### Input Data:
- **productRecord**: Provides information on the actual usage of each mold, including the number of parts produced and any quality issues (NG rates).
- **moldTrackingRecord**: Provides information on the planned usage of each mold, including ordered quantity.
- **moldInfo**: Contains details about molds, including mold ID, name, type, and cavity standard.

### Workflow:
1. **Analyze Data**: Identify molds with high NG rates or excessive usage (based on the mold cavity standard).
2. **Prioritize Maintenance**: Prioritize molds requiring maintenance based on NG rates and usage.
3. **Usage Threshold Check**: For molds reaching a predefined usage threshold (e.g., 80% of cavity standard), suggest a maintenance schedule.
4. **Cross-Check Production Plan**: Verify if maintenance can be delayed without disrupting production.
5. **Urgent Maintenance**: If maintenance can't be delayed, flag the issue and suggest urgent maintenance for review.

### Predictive Maintenance Based on NG Records and Technical Indicators

#### Core Features:
1. **NG Monitoring**: Track NG types (e.g., cracks, short shots, black spots) and rates in product records.
2. **Technical Indicators**: Monitor mold shot counts, cavity usage, and yield efficiency.
3. **Threshold-Based Predictions**: Define thresholds for NG rates, yield drops, and shot counts.
4. **Prediction Logic**: Use regression or classification models to predict the likelihood of a mold failure based on historical data.

### Integration of Production Priorities

#### Core Features:
1. **Production Order Prioritization**: Use the PO list to check current and upcoming production demands and priorities.
2. **Delay Maintenance**: Delay maintenance when high-priority orders demand production.
3. **Immediate Maintenance**: Recommend immediate maintenance if risk outweighs production urgency.
4. **Trade-Off Analysis**: Introduce a risk score based on NG trends, yield impacts, and mold shot counts.

### Risk Management for Delayed Maintenance

#### Core Features:
1. **Risk Assessment Model**: Evaluate the risk of delaying maintenance based on:
   - NG rates
   - Yield drops
   - High shot counts
2. **Risk Scenarios**:
   - **Low Risk**: Maintenance can be delayed without significant impact.
   - **Moderate Risk**: Maintenance should be scheduled soon.
   - **High Risk**: Immediate maintenance is critical.

### Dynamic Scheduling

#### Core Features:
1. **Real-Time Updates**: Continuously monitor mold performance and NG trends, updating maintenance schedules based on production changes.
2. **Optimal Scheduling Windows**: Identify downtime periods for maintenance and suggest slots that minimize disruptions.

### Administrator Control

#### Core Features:
1. **Recommendation Reports**: Provide actionable maintenance suggestions, including reasons for recommendations and suggested maintenance time.
2. **Manual Overrides**: Allow admins to adjust priorities or override recommendations.
3. **Transparency**: Maintain logs for all recommendations, changes, and overrides for traceability.

---

## Machine & Mold Maintenance Agent Output Format

### Maintenance Schedule:
| Field Name               | Type         | Description                                                   |
|--------------------------|--------------|---------------------------------------------------------------|
| scheduleDate             | Date         | Date of the maintenance schedule.                             |
| shift                    | Integer      | Shift number for scheduled maintenance.                       |
| equipmentType            | String       | Type of equipment (e.g., Mold, Machine).                      |
| equipmentNo              | String       | ID of the equipment (mold or machine).                        |
| maintenanceType          | String       | Type of maintenance (e.g., Fast, Preventive, Corrective).     |
| reasonForMaintenance     | String       | Reason for scheduling maintenance (e.g., High NG Rate).       |
| downtimeExpected         | Float (hours)| Estimated downtime for the maintenance.                       |
| priorityLevel/riskLevel  | Integer      | Priority level (e.g., 1 - High, 2 - Medium, 3 - Low).         |
| comments                 | String       | Additional comments or observations.                          |
| maintenanceApproval      | String       | Approval status (e.g., Applied, Approved, Rejected).          |
| rejectionReason          | String       | Reason for rejection (e.g., Lack of spare parts).             |
| costEstimate             | Float        | Estimated cost of maintenance (if applicable).                |

### Maintenance Logs:
| Mold/MachineID | Risk Factor | Impact on Yield | Urgency | Suggested Action   |
|----------------|-------------|-----------------|---------|--------------------|
| M1234          | 9.5         | -15%            | High    | Immediate repair   |
| M5678          | 7.2         | -8%             | Medium  | Maintenance soon   |
| M9101          | 3.1         | Negligible      | Low     | No action needed   |

---

## Maintenance Request Feedback

- After the **Machine & Mold Maintenance Agent** generates the maintenance schedule, it sends the request to the **Mold Maintenance Department** for cost and resource planning.
- The department evaluates the feasibility, considering resources, personnel, and other constraints, then returns feedback:
  - Approval or rejection of the proposed schedule.
  - Justifications for rejection (e.g., parts shortage).
  - Cost estimates for planned maintenance.

---

## Tracking and Feedback Loop

- **Tracking Agents**: The Mold/Machine Tracking Agents continue to monitor equipment usage and maintenance history in a separate log or database.
- **Feedback Integration**: If maintenance is approved, the system proceeds with the plan; if rejected, the agent reschedules or proposes an alternative plan.
