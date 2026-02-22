# System Diagrams

---

## 1. Architecture Overview — Component Diagram

```mermaid
graph TD
    User(["User / Caller"])

    subgraph Orchestration
        OrchestratorLayer["OptiMoldIQ\n(Master Orchestrator)"]
        ExecutorLayer["WorkflowExecutor"]
    end

    subgraph Configuration
        WorkflowJSON["workflows/definitions/*.json\n(Workflow definitions)"]
        ModuleRegistryYAML["configs/module_registry.yaml\n(Module config registry)"]
    end

    subgraph Registry
        ModuleRegistry["ModuleRegistry"]
        AvailableModules["modules.AVAILABLE_MODULES\n(Python class registry)"]
    end

    subgraph Policies
        PolicyFactory["DependencyPolicyFactory"]
        Strict["StrictWorkflowPolicy"]
        Flexible["FlexibleDependencyPolicy"]
        Hybrid["HybridDependencyPolicy"]
    end

    subgraph Modules
        BaseModule["BaseModule (ABC)"]
        ModuleA["Module A"]
        ModuleB["Module B"]
        ModuleN["Module N ..."]
    end

    SharedDB[("Shared Database\n/ Filesystem")]

    User -->|execute / execute_chain| OrchestratorLayer
    OrchestratorLayer -->|lazy-load executor| ExecutorLayer
    OrchestratorLayer -->|discover & validate| WorkflowJSON

    ExecutorLayer -->|load workflow| WorkflowJSON
    ExecutorLayer -->|get_module_instance| ModuleRegistry
    ExecutorLayer -->|create policy| PolicyFactory

    ModuleRegistry -->|lookup class| AvailableModules
    ModuleRegistry -->|resolve config_path| ModuleRegistryYAML

    PolicyFactory --> Strict
    PolicyFactory --> Flexible
    PolicyFactory --> Hybrid

    ModuleA & ModuleB & ModuleN -->|implements| BaseModule
    BaseModule -->|read/write| SharedDB
```

---

## 2. Workflow Execution — Flow Diagram

```mermaid
flowchart TD
    Start(["execute(workflow_name)"])
    Load["Load workflow JSON"]
    NextModule{"Next module\nin list?"}
    Done(["Return SUCCESS"])

    CacheHit{"In execution\ncache?"}
    ReuseCache["Reuse cached result"]

    Instantiate["Instantiate module\nvia ModuleRegistry"]
    BuildPolicy["Build DependencyPolicy\nvia Factory"]
    ValidateDep["validate_dependencies()"]

    DepValid{"dep_result\n.valid?"}
    Required1{"module\nrequired?"}
    FailDep(["Return FAILED\n(dependency validation)"])
    SkipDep["Record as SKIPPED\n(deps not met)"]

    Execute["module.safe_execute()"]
    ResultFailed{"result\n.is_failed()?"}
    Required2{"module\nrequired?"}
    FailExec(["Return FAILED\n(module failed)"])
    CacheResult["Cache result\nUpdate results dict"]

    Start --> Load --> NextModule
    NextModule -->|yes| CacheHit
    NextModule -->|no more| Done

    CacheHit -->|hit| ReuseCache --> NextModule
    CacheHit -->|miss| Instantiate

    Instantiate --> BuildPolicy --> ValidateDep --> DepValid

    DepValid -->|invalid| Required1
    Required1 -->|true| FailDep
    Required1 -->|false| SkipDep --> NextModule

    DepValid -->|valid| Execute --> ResultFailed

    ResultFailed -->|yes| Required2
    Required2 -->|true| FailExec
    Required2 -->|false| CacheResult

    ResultFailed -->|no| CacheResult --> NextModule
```

---

## 3. Dependency Policy — Flow Diagram

```mermaid
flowchart TD
    Start(["validate(dependencies, workflow_modules)"])
    ForEach["For each dependency"]
    CheckWorkflow{"Found in\nworkflow_modules?"}

    subgraph strict ["strict policy"]
        S_Resolved["resolved ✅\nsource = workflow"]
        S_Error["errors ❌\nreason = workflow_violation"]
    end

    subgraph flexible ["flexible policy"]
        F_Resolved_WF["resolved ✅\nsource = workflow"]
        F_CheckDB{"Found in\ndatabase?"}
        F_CheckAge1{"Within\nmax_age_days?"}
        F_Resolved_DB["resolved ✅\nsource = database"]
        F_TooOld1["errors ❌\nreason = too_old"]
        F_Required{"In\nrequired_deps?"}
        F_Error["errors ❌\nreason = not_found"]
        F_Warning["warnings ⚠️\n(non-blocking)"]
    end

    subgraph hybrid ["hybrid policy"]
        H_Resolved_WF["resolved ✅\nsource = workflow"]
        H_CheckDB{"Found in\ndatabase?"}
        H_CheckAge2{"Within\nmax_age_days?"}
        H_Warn{"prefer_workflow\n= true?"}
        H_Resolved_DB["resolved ✅\nsource = database"]
        H_TooOld2["errors ❌\nreason = too_old"]
        H_Error["errors ❌\nreason = not_found"]
        H_Warning["warnings ⚠️\n(logged, non-blocking)"]
    end

    Result(["DependencyValidationResult\n{ resolved, errors, warnings }"])

    Start --> ForEach

    ForEach -->|strict| CheckWorkflow
    CheckWorkflow -->|yes| S_Resolved --> Result
    CheckWorkflow -->|no| S_Error --> Result

    ForEach -->|flexible| CheckWorkflow
    CheckWorkflow -->|yes| F_Resolved_WF --> Result
    CheckWorkflow -->|no| F_CheckDB
    F_CheckDB -->|yes| F_CheckAge1
    F_CheckAge1 -->|ok| F_Resolved_DB --> Result
    F_CheckAge1 -->|too old| F_TooOld1 --> Result
    F_CheckDB -->|no| F_Required
    F_Required -->|yes| F_Error --> Result
    F_Required -->|no| F_Warning --> Result

    ForEach -->|hybrid| CheckWorkflow
    CheckWorkflow -->|yes| H_Resolved_WF --> Result
    CheckWorkflow -->|no| H_CheckDB
    H_CheckDB -->|yes| H_CheckAge2
    H_CheckAge2 -->|ok| H_Warn
    H_Warn -->|true| H_Warning --> H_Resolved_DB --> Result
    H_Warn -->|false| H_Resolved_DB
    H_CheckAge2 -->|too old| H_TooOld2 --> Result
    H_CheckDB -->|no| H_Error --> Result
```

---

## 4. OptiMoldIQ Orchestrator — Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator as OptiMoldIQ
    participant Executor as WorkflowExecutor
    participant Registry as ModuleRegistry
    participant Policy as DependencyPolicy
    participant Module as BaseModule
    participant DB as Shared Database

    Note over Orchestrator: __init__: discover & validate all workflow JSONs

    User->>Orchestrator: execute("workflow_name")
    Orchestrator->>Orchestrator: _get_or_create_executor()
    Orchestrator->>Executor: execute("workflow_name")

    Executor->>Executor: _load_workflow() → JSON
    
    loop For each module in workflow
        alt cache hit
            Executor->>Executor: reuse _execution_cache[module]
        else cache miss
            Executor->>Registry: get_module_instance(name, config_path)
            Registry->>Module: __init__(config_path)
            Module-->>Executor: module instance

            Executor->>Policy: DependencyPolicyFactory.create(policy_cfg)
            Executor->>Policy: validate(dependencies, workflow_modules)
            Policy-->>Executor: DependencyValidationResult

            alt dep_result invalid
                alt required = true
                    Executor-->>Orchestrator: WorkflowExecutorResult(status=failed)
                else required = false
                    Executor->>Executor: record as SKIPPED, continue
                end
            else dep_result valid
                Executor->>Module: safe_execute()
                Module->>DB: read dependencies
                Module->>DB: write outputs
                Module-->>Executor: ModuleResult

                alt result failed & required = true
                    Executor-->>Orchestrator: WorkflowExecutorResult(status=failed)
                else
                    Executor->>Executor: cache result, continue
                end
            end
        end
    end

    Executor-->>Orchestrator: WorkflowExecutorResult(status=success)
    Orchestrator-->>User: WorkflowExecutorResult
```

---

## 5. Workflow Chaining — Flow Diagram

```mermaid
flowchart LR
    Start(["execute_chain(\nworkflow_names,\nstop_on_failure\n)"])

    W1["execute(workflow_1)"]
    R1{"result\n.is_failed()?"}
    Stop1(["STOP chain\n❌ failed at workflow_1"])

    W2["execute(workflow_2)"]
    R2{"result\n.is_failed()?"}
    Stop2(["STOP chain\n❌ failed at workflow_2"])

    WN["execute(workflow_n)"]
    Done(["Return all results\nDict[name → result]"])

    Start --> W1 --> R1
    R1 -->|"yes &\nstop_on_failure"| Stop1
    R1 -->|no| W2 --> R2
    R2 -->|"yes &\nstop_on_failure"| Stop2
    R2 -->|no| WN --> Done
```