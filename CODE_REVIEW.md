# Turbulence Codebase Assessment

## Executive Summary

The **Turbulence** codebase demonstrates a solid foundation with strong typing, clear modularity, and modern Python practices (asyncio, Pydantic, Typer). The architecture cleanly separates configuration, execution, and reporting. However, as the feature set has grown (retries, profiles, replay), some components have become overloaded, and logic has started to duplicate across boundaries. Refactoring is recommended to maintain velocity and reliability.

## 1. Architecture & Separation of Concerns

**Strengths:**
- **Modular Design:** Clear separation between `actions`, `config`, `engine`, and `storage`.
- **Pydantic Usage:** Strong data validation and schema definition throughout the system.
- **Protocol-based Actions:** The `BaseActionRunner` pattern allows for easy extensibility.

**Weaknesses:**
- **Scenario Execution Duplication:** The core logic for iterating through a scenario's steps, managing context, and executing actions is duplicated between:
    - `src/turbulence/commands/run.py` (Main execution loop)
    - `src/turbulence/engine/replay.py` (Replay execution loop)
    This violates DRY and risks inconsistent behavior between "run" and "replay" modes (e.g., if one updates how context is merged but the other doesn't).
- **CLI leaking into Engine:** `src/turbulence/commands/run.py` contains significant business logic (turbulence injection, artifact writing orchestration) that belongs in a dedicated `Engine` or `ScenarioRunner` class.

**Recommendation:**
- Extract a `ScenarioRunner` class in `src/turbulence/engine/` that handles the step iteration, context management, and action execution. Both `run` command and `ReplayEngine` should delegate to this.

## 2. Component Complexity

**Strengths:**
- **Focused Action Runners:** `WaitActionRunner` and `AssertActionRunner` are relatively focused and single-purpose.

**Weaknesses:**
- **Overloaded `HttpActionRunner`:** The `src/turbulence/actions/http.py` file is becoming a "god class" for HTTP operations. It currently handles:
    - Request construction (headers, body, query params).
    - HTTP client execution.
    - Retry logic (fixed & exponential backoff loops).
    - JSONPath extraction.
    - Error categorization.
    - Context updating.
    The retry logic specifically obscures the core "execute request" responsibility.

**Recommendation:**
- Extract retry logic into a generic `RetryDecorator` or `RetryPolicy` utility that can wrap any async function.
- Move JSONPath extraction into a dedicated `Extractor` utility.

## 3. Error Handling

**Strengths:**
- **Custom Exceptions:** Use of `ConfigLoadError`, `InstanceNotFoundError` provides clarity.

**Weaknesses:**
- **Generic Exception Catching:** There is a heavy reliance on `except Exception as e` in high-level loops (`executor.py`, `run.py`). While necessary to prevent crashes during parallel execution, it can mask `NameError` or `TypeError` bugs (as seen during recent development of FEAT-015/030).
- **Error Propagation:** Errors are sometimes converted to string messages too early, losing stack trace information for debugging.

**Recommendation:**
- Catch specific expected exceptions (`httpx.RequestError`, `JsonPathParserError`) where possible.
- Log full stack traces for unexpected exceptions to a debug log, even if the UI only shows the error message.

## 4. Concurrency

**Strengths:**
- **Robust Parallelism:** `ParallelExecutor` correctly uses `asyncio.Semaphore` to limit concurrency and `asyncio.as_completed` for efficient processing.
- **Signal Handling:** Graceful shutdown on SIGINT/SIGTERM is implemented.

**Weaknesses:**
- **Resource Management:** `httpx.AsyncClient` lifecycle is managed manually in loops. While context managers are used, passing clients around (e.g., into `HttpActionRunner`) creates some ambiguity about who owns the client lifecycle.

## 5. Testing

**Strengths:**
- **High Coverage:** Most features have dedicated test files with high coverage.
- **Fixture Usage:** Good use of `pytest` fixtures for SUT configs and mock artifacts.

**Weaknesses:**
- **Mocking vs. Integration:** Some tests rely heavily on mocking `httpx`, which is good for speed but might miss real-world connection nuances.
- **Test file corruption:** (Minor process issue) Recent edits caused temporary file corruption; ensuring atomic writes or linting checks before commit is crucial.

## Prioritized Refactoring Plan

1.  **Refactor `ScenarioRunner`:** Consolidate execution logic from `commands/run.py` and `engine/replay.py`.
2.  **Modularize `HttpActionRunner`:** Extract retry and extraction logic.
3.  **Harden Error Handling:** Review `try/except Exception` blocks and ensure critical failures are logged with traces.
