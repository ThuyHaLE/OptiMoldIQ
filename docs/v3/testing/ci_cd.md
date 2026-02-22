# CI/CD Integration

## Overview

OptiMoldIQ uses a single GitHub Actions workflow (`.github/workflows/ci.yml`) triggered on every push and pull request to `main`. The pipeline is split into **4 jobs** running in parallel after an initial gate, with a final summary report.

```
push/PR to main
       │
       ▼
 [smoke-tests]  ← gate (5 min)
  /     |     \
 ▼      ▼      ▼
[module] [workflow] [agent]  ← parallel (disabled)
  \      /
   ▼    ▼
  [report]
```

---

## Jobs

### Job 1 — Smoke Tests (gate)

**Timeout**: 5 minutes  
**Blocks**: all other jobs  
**Purpose**: fast structural check before running anything expensive

Two steps run sequentially:

1. **Import check** — `python -c "import agents; import modules; import configs"`. Fails immediately if there's a broken import anywhere.

2. **Structure tests** — runs `tests/agents_tests/test_all_agents_structure.py::TestAllAgentsStructure`. These tests use the `smoke` marker and check agent interface compliance without executing any real logic.

If either step fails, module-tests and workflow-tests are never triggered.

---

### Job 2 — Module Tests

**Timeout**: 10 minutes  
**Needs**: `smoke-tests`  
**Coverage flag**: `modules`

Runs the full module test suite excluding integration and agent-dependent tests:

```bash
pytest tests/modules_tests/ \
  -m "not integration and not requires_agent" \
  --cov=modules \
  --cov-report=xml
```

The `-m "not integration and not requires_agent"` filter skips the `@pytest.mark.integration` full pipeline test and any test marked `requires_agent`. Everything else — unit tests, dependency graph tests, smoke tests, `requires_dependencies` tests — runs here.

Coverage is uploaded to Codecov under the `modules` flag.

---

### Job 3 — Workflow Tests

**Timeout**: 30 minutes  
**Needs**: `smoke-tests`  
**Coverage flag**: `workflows`

Runs the entire workflow test suite with no marker filtering:

```bash
pytest tests/workflows_tests/ \
  --cov=workflows \
  --cov-report=xml
```

All 177 tests run here — dependency policy tests, executor tests, registry tests, orchestrator tests, and the full end-to-end integration tests. The 30-minute timeout is conservative given actual runtime of ~2.4s.

Coverage is uploaded to Codecov under the `workflows` flag.

---

### Job 4 — Agent Tests ⚠️ DISABLED

**Timeout**: 90 minutes  
**Needs**: `smoke-tests`  
**Status**: `if: false` — currently disabled

When re-enabled, this job runs `tests/agents_tests/` with `--maxfail=1`. The 90-minute timeout reflects that agent tests trigger real dependency execution via the `dependency_provider` fixture — no manual setup is needed since tests handle it automatically.

On failure, shared DB files and logs are archived as artifacts with 7-day retention.

To re-enable: remove the `if: false` line from the `agent-tests` job.

---

### Job 5 — Report

**Needs**: `smoke-tests`, `module-tests`, `workflow-tests`  
**Runs**: always (even if earlier jobs fail)

Generates a GitHub Step Summary table showing pass/fail for each suite. Prints `✅ All Tests Passed` only if all three active jobs succeed.

---

## Working Directory Detection

All jobs auto-detect the project root at runtime to support both flat and nested repo layouts:

```
Flat:   <repo_root>/agents, modules, configs, tests  →  WORKING_DIR=$(pwd)
Nested: <repo_root>/OptiMoldIQ/agents, ...           →  WORKING_DIR=$(pwd)/OptiMoldIQ
```

If neither structure is found, the step exits with error code 1.

---

## Dependencies Installed Per Job

| Package | Smoke | Module | Workflow | Agent |
|---|---|---|---|---|
| `pytest` | ✓ | ✓ | ✓ | ✓ |
| `pyyaml` | ✓ | ✓ | ✓ | ✓ |
| `loguru` | ✓ | ✓ | ✓ | ✓ |
| `pandas` | ✓ | ✓ | ✓ | — |
| `pytest-cov` | — | ✓ | ✓ | ✓ |
| `pytest-mock` | — | ✓ | ✓ | — |
| `openpyxl` | — | ✓ | ✓ | — |
| `requirements.txt` | if non-empty | if exists | if exists | if non-empty |

Smoke installs a minimal set intentionally — if a structural test accidentally requires a heavy dependency, it should fail visibly here.

---

## Pytest Markers in CI

The markers defined in `pytest.ini` map to CI usage as follows:

| Marker | Where it runs in CI |
|---|---|
| `smoke` | Job 1 (structure tests) and Jobs 2–3 (not filtered out) |
| `unit` | Jobs 2–3 |
| `integration` | **Excluded** from Job 2 (`-m "not integration"`), runs in Job 3 |
| `requires_agent` | **Excluded** from Job 2, runs in Job 4 (disabled) |
| `slow` | Jobs 2–3 (not explicitly filtered, but timeouts enforce limits) |
| `heavy` | Jobs 2–3 (same as slow) |
| `performance` | Jobs 2–3 (advanced policy tests with timing assertions) |

To run only fast tests locally, mirroring what Job 2 does:

```bash
pytest tests/modules_tests/ -m "not integration and not requires_agent"
```

To run everything except agent tests:

```bash
pytest tests/modules_tests/ tests/workflows_tests/ -m "not requires_agent"
```

---

## Re-enabling Agent Tests

1. Remove `if: false` from the `agent-tests` job in `.github/workflows/ci.yml`
2. Add `agent-tests` to the `needs` list of the `report` job
3. Update the summary table in the report step to show agent test status dynamically instead of the hardcoded `⏸️ DISABLED` row

---

## Running the Full CI Suite Locally

```bash
# Job 1 equivalent
python -c "import agents; import modules; import configs"
pytest tests/agents_tests/test_all_agents_structure.py::TestAllAgentsStructure -v --tb=short

# Job 2 equivalent
pytest tests/modules_tests/ -m "not integration and not requires_agent" \
  --cov=modules --cov-report=term-missing -v

# Job 3 equivalent
pytest tests/workflows_tests/ \
  --cov=workflows --cov-report=term-missing -v

# Full suite (minus agent tests)
pytest tests/modules_tests/ tests/workflows_tests/ \
  -m "not requires_agent" \
  --cov=modules --cov=workflows --cov-report=term-missing -v
```