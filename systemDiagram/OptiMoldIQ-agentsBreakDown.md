# Workflows for All Agents in the OptiMoldIQ System

<<<<<<< HEAD
### 1. AutoStatus Agent
#### Role: 
Tracks and updates real-time production status.
#### Input: 
- PO_list
- productRecord
#### Process:
- Summarize productRecord by PO and working day
- Cross-check data with moldInfo to validate mold usage for each PO
- Log invalidations (e.g., incorrect mold usage, data inconsistencies)
#### Output:
- Generate productionStatus
- Log invalidations for review
#### Key Scalable Features: 
Logs inconsistencies for validation and future auditing, critical for building trust in the data pipeline.
#### Healing System Actions: 
Recheck invalid entries and auto-correct based on predefined rules.

### 2. InitialSched Agent
#### Role: 
Drafts the initial production plan.
#### Input:
productionStatus (report) from AutoStatus Agent
#### Process:
- Analyze current production status and pending POs
- Generate a draft production plan, including:
  - Allocation of molds and machines
  - Resin requirements per PO
  - Highlight potential issues (e.g., resource shortages) in logs
#### Output:
- Draft Production Plan
- Logs highlighting flagged issues
#### Key Scalable Features: 
Flags resource shortages and issues for cross-agent review.
#### Healing System Actions: 
Retry plan generation if errors occur in flagged data.

### 3. FinalSched Agent
#### Role: 
Refines and optimizes the production plan.
#### Input:
- Draft plan (report) from InitialSched Agent
- Reports from Resin Tracking Agent, Mold Tracking Agent, and Machine Tracking Agent
#### Process:
Optimize the draft plan by addressing flagged issues and integrating tracking reports. Ensure:
- Resin quantities align with stock capacity (e.g., limited to 3–4 days of production)
- Over-capacity POs are distributed across multiple molds or machines if possible
- Molds with larger cavities are prioritized
- Continuous production by prioritizing molds/machines already in use
- Consolidate small-quantity POs to minimize machine downtime
#### Output:
Optimized Production Plan
#### Key Scalable Features: 
Incorporates multi-agent feedback and balances workloads dynamically.
#### Healing System Actions: 
Auto-adjust plans when critical data changes (e.g., sudden stock depletion or machine failure).

### 4. Resin Tracking Agent
#### Role: 
Monitors resin stock and usage trends.
#### Input: 
- PO_list
- productRecord
- historical resin usage data
#### Process:
- Track resin stock levels and consumption trends
- Identify risks (e.g., low stock) based on active and upcoming POs
- Generate a report highlighting stock risks and restocking needs
#### Output:
Resin Stock Report with flagged risks
#### Key Scalable Features: 
Predictive analytics for resin restocking based on historical trends and upcoming demands.
#### Healing System Actions: 
Highlight and adjust for mismatched resin data.

### 5. Mold Tracking Agent
#### Role: 
Tracks mold usage and maintenance.
#### Input: 
- PO_list
- productRecord
- historical mold maintenance data
#### Process:
- Track mold usage, including accumulated shots and maintenance history
- Identify molds nearing maintenance thresholds
- Highlight molds used incorrectly or beyond capacity
#### Output:
Mold Usage Report with flagged risks
#### Key Scalable Features: 
Maintenance scheduling triggers can scale with reinforcement learning for better predictions.
#### Healing System Actions: 
Log and alert for molds exceeding shot thresholds or incorrect usage.

### 6. Machine Tracking Agent
#### Role: 
Tracks machine availability and performance.
#### Input: 
- PO_list
- productRecord
- historical machine operation data
#### Process:
- Track machine operating hours and maintenance schedules
- Identify machines requiring maintenance or showing performance issues
- Highlight machine-related risks or inefficiencies
#### Output:
Machine Usage Report with flagged risks.
#### Key Scalable Features: 
Integrate machine learning to predict machine failures.
#### Healing System Actions: 
Auto-update schedules if machine downtime exceeds thresholds.

### 7. Resin Coordinate Agent
#### Role:
Optimizes resin usage and manages runner recycling.
#### Input:
- Optimized Production Plan from FinalSched Agent
- Resin Stock Report from Resin Tracking Agent
- Historical Runner Data
- Granulator/Shredder Processing Rate
#### Process:
- Forecast resin usage, accounting for new and recycled resin
- Automate runner recycling with granulators/shredders
- Predict optimal resin reuse ratios using historical data
- Integrate runner reuse data with Yield Optimization Agent
#### Output:
Resin Usage and Recycling Report
#### Key Scalable Features:
- Automated runner recycling workflow
- Predictive reuse models for resin optimization
- Integration with Yield Optimization for production efficiency
#### Healing System Actions:
- Adjust resin forecasts based on recycling efficiency and yield optimization data

### 8. MaintenanceScheduler Agent
#### Role: 
Schedules mold and machine maintenance.
#### Input:
- Optimized Production Plan from FinalSched Agent
- Mold and Machine Usage Reports from tracking agents
#### Process:
- Develop a maintenance schedule for molds and machines
- Ensure maintenance aligns with production needs to minimize downtime
#### Output:
Maintenance Schedule
#### Key Scalable Features: 
Aligns with production needs to minimize downtime.
#### Healing System Actions: 
Proactively reschedule based on real-time agent feedback.

### 9. Quality Control Agent
#### Role: 
Monitors production quality.
#### Input: 
- productRecord
- historical quality data
#### Process:
- Track NG rates and identify trends or recurring quality issues
- Highlight potential causes (e.g., specific molds or machines)
#### Output:
Quality Control Report for long-term insights
#### Key Scalable Features: 
Root cause analysis and tracking for recurring issues.
#### Healing System Actions: 
Auto-flag issues for immediate resolution.

### 10. YieldOptimization Agent
#### Role: 
Optimizes yield and resin allocation.
#### Input:
- productRecord
- historical yield data.
#### Process:
- Monitor actual yield versus default yield
- Evaluate impact of cycle time changes on yield and NG rates
- Suggest optimized cycle times for better efficiency
#### Output:
Yield Optimization Report for long-term insights
#### Key Scalable Features: 
Analysis of cycle times for efficiency trade-offs and NG minimization.
#### Healing System Actions: 
Revert to default settings if optimizations lead to excessive NG rates.

### 11. DashBoardBuilderAgent
#### Role: 
Visualizes system data for decision-making.
#### Input: 
Reports from all agents
#### Process:
- Generate daily production reports using AutoStatus Agent data
- Visualize plans (Production, Mold, Material, Machine) from FinalSched Agent, ResinRestock Agent, and MaintenanceScheduler Agent
- Provide insights from Quality Control Agent and YieldOptimization Agent for decision-making
- Optionally visualize logs/flags for quick issue identification
#### Output:
Comprehensive dashboards for daily operations, plans, and long-term insights
#### Key Scalable Features: 
Expand dashboard capabilities with AI-driven insights and prediction models.
#### Healing System Actions: 
Highlight inconsistencies or missing data in reports for quick resolution.

#### Note:
1. Shared Database Implementation:
- Consider a hybrid approach (SQL + NoSQL) where structured data (production status, schedules) remains in SQL, while flexible, high-volume data (logs, agent reports) uses NoSQL for better performance.

2. Agent Communication & Coordination:
- Define an event-driven mechanism where agents trigger actions based on specific conditions (e.g., machine failure prompts rescheduling).
- Use a message queue system (e.g., RabbitMQ, Kafka) for efficient agent interaction in real-time.

3. Healing System Enhancements:
- Implement automated rollback mechanisms in case of faulty optimizations (e.g., if YieldOptimization Agent suggests a cycle time that increases NG rates).
- Introduce periodic agent health checks to detect slow performance or missing updates.

4. Reinforcement Learning (RL) Roadmap:
- Phase 1: Collect historical feedback data for supervised learning.
- Phase 2: Integrate RL into YieldOptimization Agent to refine cycle times dynamically.
- Phase 3: Expand RL to FinalSched Agent for optimizing production sequences.

5. Performance & Scalability:
- Introduce parallel processing for critical agents (e.g., FinalSched Agent, MaintenanceScheduler Agent).
- Optimize database queries for agents requiring frequent updates (e.g., AutoStatus Agent).
=======
## 1. AutoStatus Agent

- Role: <Br>Monitors and updates production status by summarizing PO and product records.

- Input:

	- PO_list
	- productRecord

- Process:

	- Summarize productRecord by PO and working day.
	- Cross-check data with moldInfo to validate mold usage for each PO.
	- Log invalidations (e.g., incorrect mold usage, data inconsistencies).

- Output:

	- productionStatus report.
	- Logs of invalidations for review.

## 2. InitialSched Agent

- Role:
	- Drafts the initial production plan based on productionStatus.

- Input:

	- productionStatus from AutoStatus Agent.

- Process:

	- Analyze current production status and pending POs.
	- Generate a draft production plan, including:
	- Allocation of molds and machines.
	- Resin requirements per PO.
	- Highlight potential issues (e.g., resource shortages) in logs.

- Output:

	- Draft Production Plan.
	- Logs highlighting flagged issues.

## 3. FinalSched Agent

- Role:
	- Optimizes and finalizes the production schedule using integrated data from tracking agents.

- Input:

	- Draft plan from InitialSched Agent.
	- Reports from Resin Tracking Agent, Mold Tracking Agent, and Machine Tracking Agent.

- Process:

	- Optimize the draft plan by addressing flagged issues and integrating tracking reports.
	- Ensure:
		- Resin quantities align with stock capacity (e.g., limited to 3–4 days of production).
		- Over-capacity POs are distributed across multiple molds or machines, if possible.
		- Molds with larger cavities are prioritized.
		- Continuous production by prioritizing molds/machines already in use.
		- Consolidate small-quantity POs to minimize machine downtime.

- Output:

	- Optimized Production Plan.

## 4. Resin Tracking Agent

- Role:
	- Monitors resin stock levels, usage trends, and identifies restocking needs.

- Input:

	- PO_list.
	- productRecord.
	- Historical resin usage data.

- Process:

	- Track resin stock levels and consumption trends (e.g., efficiency in continuous production, waste in small batch sizes).
	- Identify risks (e.g., low stock) based on active and upcoming POs.
	- Highlight discrepancies between actual resin usage and default values.

- Output:

	- Resin Stock Report with flagged risks.

## 5. Mold Tracking Agent

- Role:
	- Tracks mold usage and maintenance requirements.

- Input:

	- PO_list.
	- productRecord.
	- Historical mold maintenance data.

- Process:

	- Track mold usage, including accumulated shots and maintenance history.
	- Identify molds nearing maintenance thresholds.
	- Highlight molds used incorrectly or beyond capacity.

- Output:

	- Mold Usage Report with flagged risks.

## 6. Machine Tracking Agent

- Role:
	- Tracks machine availability and maintenance schedules.

- Input:

	- PO_list.
	- productRecord.
	- Historical machine operation data.

- Process:

	- Track machine operating hours and maintenance schedules.
	- Identify machines requiring maintenance or showing performance issues.
	- Highlight machine-related risks or inefficiencies.

- Output:

	- Machine Usage Report with flagged risks.

## 7. ResinRestock Agent

- Role:
	- Creates and prioritizes resin restocking schedules.

- Input:

	- Optimized Production Plan from FinalSched Agent.
	- Resin Stock Report from Resin Tracking Agent.

- Process:

	- Create a resin restocking schedule based on production demand and stock levels.
	- Prioritize restocking actions to prevent production delays.

- Output:

	- Resin Restocking Schedule.

## 8. MaintenanceScheduler Agent

- Role:
	- Schedules machine and mold maintenance to reduce downtime.

- Input:

	- Optimized Production Plan from FinalSched Agent.
	- Mold and Machine Usage Reports from tracking agents.

- Process:

	- Develop a maintenance schedule for molds and machines.
	- Ensure maintenance aligns with production needs to minimize downtime.

- Output:

	- Maintenance Schedule.

## 9. Quality Control Agent

- Role:
	- Monitors and evaluates production quality metrics.

- Input:

	- productRecord.
	- Historical quality data.

- Process:

	- Track NG rates and identify trends or recurring quality issues.
	- Highlight potential causes (e.g., specific molds or machines).

- Output:

	- Quality Control Report for long-term insights.

## 10. YieldOptimization Agent

- Role:
	- Optimizes yield by analyzing efficiency and resin usage patterns.

- Input:

	- productRecord.
	- Historical yield and resin usage data.

- Process:

	- Monitor actual yield versus default yield.
	- Evaluate resin usage patterns, including:
	- Reduced resin usage in continuous production.
	- Increased resin usage in small batches or re-molding.
	- Suggest optimized resin allocation for specific molds, machines, or items.
	- Evaluate the impact of cycle time changes on yield and NG rates.

- Output:

	- Yield Optimization Report for long-term resin and yield efficiency.

## 11. DashBoardBuilderAgent

- Role:
	- Visualizes and provides insights from various reports for daily operations and long-term decision-making.

- Input:

	- Reports from all agents.

- Process:

	- Generate daily production reports using AutoStatus Agent data.
	- Visualize plans (Production, Mold, Material, Machine) from FinalSched Agent, ResinRestock Agent, and MaintenanceScheduler Agent.
	- Provide insights from Quality Control Agent and YieldOptimization Agent for decision-making.
	- Optionally visualize logs/flags for quick issue identification.

- Output:

	- Interactive Dashboard for real-time monitoring and decision-making.
>>>>>>> f700e24ee9ee512b0be3f739658b371775a46203
