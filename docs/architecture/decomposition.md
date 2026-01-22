# System Decomposition: Windtunnel

This document provides a high-level architectural decomposition of the Windtunnel framework into its constituent Services (functional components) and Resources (data entities).

## 1. Services

Services represent the active functional modules of the system that perform operations.

### 1.1 CLI Service
**Location:** `src/windtunnel/cli.py`, `src/windtunnel/commands/`
**Responsibility:**
*   Acts as the primary entry point for the user.
*   Parses command-line arguments and flags (using `typer`).
*   Dispatches control to specific commands (`run`, `report`, `replay`).
*   Handles top-level error reporting and version display.

### 1.2 Configuration Service
**Location:** `src/windtunnel/config/`
**Responsibility:**
*   **SUT Loader:** Loads and validates System Under Test configurations (`sut.yaml`).
*   **Scenario Loader:** Loads and validates simulation scenarios (`*.yaml`).
*   **Validation:** Ensures configurations adhere to defined schemas (using `pydantic`).

### 1.3 Execution Engine
**Location:** `src/windtunnel/engine/`
**Responsibility:**
*   **Orchestrator:** Manages the lifecycle of the simulation run.
*   **Parallel Executor:** Handles concurrent execution of workflow instances using `asyncio` semaphores.
*   **Context Management:** Manages variable scope and template rendering for dynamic values.
*   **Progress Tracking:** Provides real-time feedback to the console (using `rich`).

### 1.4 Action Runners
**Location:** `src/windtunnel/actions/`
**Responsibility:**
*   **Protocol:** Defines the standard interface (`ActionRunner`) for all actions.
*   **Implementations:**
    *   `HTTP`: Executes HTTP requests against the SUT.
    *   `Wait`: Pauses execution for a specified duration.
    *   `Assert`: Evaluates conditions against execution state.
*   **Observation:** Captures the raw output of an action (e.g., HTTP response, elapsed time).

### 1.5 Storage Service
**Location:** `src/windtunnel/storage/`
**Responsibility:**
*   **Persistence:** Saves simulation artifacts to disk.
*   **Format:** Uses JSONL (JSON Lines) for efficient, append-only logging of high-volume data (steps, instances).
*   **Manifesting:** Creates run manifests and summaries to index stored data.

### 1.6 Reporting Service
**Location:** `src/windtunnel/report/`
**Responsibility:**
*   **Analysis:** Aggregates raw artifact data to calculate statistics (pass rates, latency distributions).
*   **Generation:** Produces human-readable HTML reports from the aggregated data.

### 1.7 Turbulence Service
**Location:** `src/windtunnel/turbulence/`
**Responsibility:**
*   **Injection:** Introduces controlled faults or delays into the system (e.g., network latency, error spikes) to test resilience.

---

## 2. Resources

Resources represent the data models and artifacts that flow through the services.

### 2.1 Configuration Resources
**Location:** `src/windtunnel/config/`, `src/windtunnel/models/`
*   **SUT Config:** Defines the target system's base URL and global settings.
*   **Scenario Config:** Defines the workflow steps, concurrency, and duration.
*   **Run Config:** Snapshot of the runtime flags (seed, parallelism) used for a specific execution.

### 2.2 Run Artifacts
**Location:** `src/windtunnel/models/manifest.py`
These are persisted to the `runs/<run_id>/` directory.
*   **Manifest (`manifest.json`):** Metadata identifying the run (ID, timestamp, SUT, Scenarios).
*   **Instance Record (`instances.jsonl`):** High-level status of a single workflow iteration (Pass/Fail, Duration).
*   **Step Record (`steps.jsonl`):** detailed trace of a single action within an instance (Request/Response data).
*   **Assertion Record (`assertions.jsonl`):** Result of specific validation checks.
*   **Run Summary (`summary.json`):** Aggregated metrics for the entire run.

### 2.3 Runtime State
**Location:** `src/windtunnel/engine/context.py`, `src/windtunnel/models/observation.py`
*   **Context:** A dictionary of variables available to the current workflow instance (includes `user`, `iteration`, extracted variables).
*   **Observation:** The raw result of an action execution, used to update the Context.

## 3. Data Flow

1.  **CLI** invokes **Config Service** to load SUT and Scenarios.
2.  **CLI** initializes **Storage Service** to prepare the run directory.
3.  **CLI** passes everything to the **Execution Engine**.
4.  **Engine** spawns concurrent tasks.
5.  Each task utilizes **Action Runners** to interact with the SUT.
6.  **Action Runners** produce **Observations**.
7.  **Engine** updates **Context** and streams results to **Storage Service**.
8.  **Storage Service** writes to **Run Artifacts** (JSONL files).
9.  (Post-run) **Reporting Service** reads **Run Artifacts** to generate an HTML report.
