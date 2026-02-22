# 🚀 Quickstart – OptiMoldIQ

OptiMoldIQ is a workflow orchestration engine for production planning & analytics.

This guide helps you run OptiMoldIQ locally in under 3 minutes.

--- 

## Project Structure
```
OptiMoldIQ/
├── main.py                      # Demo entrypoint
├── modules/                     # Business logic modules
├── optiMoldMaster/              # Core orchestrator engine
├── workflows/
│   ├── definitions/             # Workflow definitions (JSON)
│   ├── dependency_policies/     # Execution policies
│   ├── executor.py              # Workflow execution engine
│   └── registry/                # Module registry
└── requirements.txt
```

---

## 1. Clone Repository

```Bash
!git clone https://github.com/ThuyHaLE/OptiMoldIQ.git
%cd OptiMoldIQ
```

---

## 2. Install Dependencies

Make sure you are using Python 3.9+.

```Bash
pip install -r requirements.txt
```

---

## 3. Run the Built-in Demo

`main.py` is a ready-to-run entrypoint.

```Bash
python main.py
```

You should see something similar to:

```Code
Available workflows:
['analyze_production_records',
 'build_production_dashboard',
 'extract_historical_features',
 'process_initial_planning',
 'track_order_progress',
 'update_database_flexible',
 'update_database_hybrid',
 'update_database_strict']
```

After listing available workflows, the demo executes:

```Code
update_database_strict
```

---

## 4. Execute a Different Workflow

Open `main.py` and modify:

```Bash
result = orchestrator.execute("process_initial_planning")
```

Then run:

```Bash
python main.py
```

---

# 5. Run Without Cache

To force re-execution:

```Python
result = orchestrator.execute(
    "update_database_strict",
    clear_cache=True
)
```

---

## 6. Where Things Live

### Modules

Business logic lives in:

```Code
modules/
```

Each module implements a single execution unit.

---

### Workflow Definitions

Workflow configuration files:

```Code
workflows/definitions/
```

Each JSON file defines:

- Execution order
- Modules involved
- Dependency policy

---

### Dependency Policies

Located in:

```Code
workflows/dependency_policies/
```

Available modes:

- flexible
- hybrid
- strict

Each workflow selects its own policy.

---

## 7. Create a New Workflow

### 1. Add a new JSON file under:

```Code
workflows/definitions/
```

### 2. Define modules and dependency policy.

### 3. Execute it:

```Code
orchestrator.execute("your_new_workflow")
```

---

## 8. Troubleshooting

### Module not found

- Ensure it is registered in the module registry.

### Workflow not listed

- Verify the file exists in workflows/definitions/.
- Ensure the file name matches the workflow name.

### Dependency failure (strict mode)

- Check dependency configuration.
- Try running a flexible or hybrid policy if appropriate.