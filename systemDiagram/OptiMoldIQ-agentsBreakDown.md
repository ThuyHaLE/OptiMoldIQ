# Workflows for All Agents in the OptiMoldIQ System

## 1. AutoStatus Agent

- Role: <Br>Monitors and updates production status by summarizing PO and product records.

- Input:

	- PO_liít
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