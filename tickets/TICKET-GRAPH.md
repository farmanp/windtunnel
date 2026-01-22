# Turbulence Ticket Dependency Graph

This document defines ticket dependencies and parallel execution batches for autonomous implementation.

## Dependency Legend

```
A → B    : B depends on A (A must complete before B starts)
A | B    : A and B can run in parallel (no dependency)
[batch]  : Tickets in same batch can be worked in parallel
[DONE]   : Batch or ticket is fully implemented
```

## Full Dependency Graph

```
                                    INFRA-001 [DONE]
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               FEAT-001 [DONE]      FEAT-002 [DONE]      FEAT-003 [DONE]
               (CLI)            (SUT Config)         (Scenario Loader)
                    │                    │                    │
                    └────────────────────┴────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               FEAT-004 [DONE]      FEAT-005 [DONE]      FEAT-006 [DONE]
            (HTTP Action)        (Wait Action)        (Assert Action)
                    │                    │                    │
                    └────────────────────┴────────────────────┘
                                         │
                                         ▼
                                    FEAT-007 [DONE]
                               (Context Templating)
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               FEAT-008 [DONE]      FEAT-009 [DONE]      FEAT-010 [DONE]
            (Artifact Store)     (HTML Report)          (Replay)
                    │                    │                    │
                    └───────┬────────────┴───────┬────────────┘
                            │                    │
                    ┌───────┴────────────┬───────┴────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               FEAT-011 [DONE]      FEAT-012 [DONE]  FEAT-013 [DONE] | FEAT-014 [DONE]
            (Parallel Exec)       (Pressure)     (Schema)      | (Expressions)
                    │                    │                    │
                    └───────┬────────────┴───────┬────────────┘
                            │                    │
                    ┌───────┴────────────┬───────┴────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               FEAT-015             FEAT-016             FEAT-017
              (Reports)            (CI Gate)           (Variation)
                    │                    │                    │
                    └───────┬────────────┴───────┬────────────┘
                            │                    │
            ┌───────────────┴──────────┬─────────┴───────────────┐
            │                          │                         │
            ▼                          ▼                         ▼
       FEAT-018                   FEAT-019                   SPIKE-001
       (SQLite)                  (Branching)               (LLM Actor)
            │                          │                         │
            └──────────────────────────┼─────────────────────────┘
                                       │
                                       ▼
                                   FEAT-020 [DONE]
                                 (Web Analytics Suite)
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
               FEAT-021 [DONE]    FEAT-022 [DONE]    FEAT-023 [DONE]
              (FastAPI)           (Run List)         (Run Detail)
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                                       ▼
                                   FEAT-024 [DONE]
                                (Instance Timeline)
                                       │
                                       ▼
                                   FEAT-025 [DONE]
                                (Real-time WS)
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
       FEAT-026                   FEAT-027                   FEAT-029
   (Live Progress)            (Visualizer)               (Results Explorer)
            │                          │
            └──────────────────────────┘
                          │
                          ▼
                     FEAT-028
                 (Quick Launcher)
```

## Parallel Execution Batches

Execute each batch to completion before starting the next. Within a batch, all tickets can be worked in parallel.

### Batch 0: Foundation [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| INFRA-001 | Project setup and Python package scaffolding | None | Medium | DONE |

**Batch Notes:** Must complete before any other work. Sets up the development environment.

---

### Batch 1: CLI & Configuration [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-001 | CLI scaffold with run, report, replay commands | INFRA-001 | Medium | DONE |
| FEAT-002 | SUT config loader | INFRA-001 | Low | DONE |
| FEAT-003 | Scenario loader and YAML parser | INFRA-001 | Medium | DONE |

**Batch Notes:** All three tickets only depend on INFRA-001. Can be developed and tested independently.

---

### Batch 2: Action Runners [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-004 | HTTP action runner with extraction | FEAT-002, FEAT-003 | Medium | DONE |
| FEAT-005 | Wait action runner with polling | FEAT-002, FEAT-003 | Medium | DONE |
| FEAT-006 | Assert action with basic expectations | FEAT-002, FEAT-003 | Low | DONE |

**Batch Notes:** Action runners share the same interface. Can be developed in parallel with mock configs.

---

### Batch 3: Context Engine [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-007 | Context templating engine | FEAT-004, FEAT-005, FEAT-006 | Medium | DONE |

**Batch Notes:** Sequential - requires action runners to integrate with. This is the glue that connects entry data → actions → extractions.

---

### Batch 4: Persistence & Output [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-008 | JSONL artifact storage and run persistence | FEAT-007 | Medium | DONE |
| FEAT-009 | Basic HTML report generation | FEAT-007 | Medium | DONE |
| FEAT-010 | Replay command implementation | FEAT-007, FEAT-001 | Medium | DONE |

**Batch Notes:** All depend on context engine but don't depend on each other. FEAT-010 also needs CLI from FEAT-001.

---

### Batch 5: Scale & Resilience [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-011 | Parallel execution engine | FEAT-008 | High | DONE |
| FEAT-012 | Pressure engine v0 | FEAT-004 | Medium | DONE |
| FEAT-013 | Schema validation expectation | FEAT-006 | Low | DONE |
| FEAT-014 | Custom expression evaluator | FEAT-006 | High | DONE |

**Batch Notes:**
- FEAT-011 needs artifact storage for concurrent writes
- FEAT-012 wraps HTTP actions for fault injection
- FEAT-013/014 extend assertion capabilities

---

### Batch 6: Polish & CI
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-015 | Enhanced report aggregations | FEAT-009, FEAT-011 | Medium | DONE |
| FEAT-016 | CI gating with fail-on thresholds | FEAT-011 | Low | TODO |
| FEAT-017 | Deterministic variation engine | FEAT-007 | Medium | TODO |

**Batch Notes:**
- FEAT-015 needs basic reports + parallel execution data
- FEAT-016 needs run metrics from parallel execution
- FEAT-017 only needs context engine (variation feeds into context)

---

### Batch 7: Advanced Engine
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-018 | SQLite backend for run storage | FEAT-008 | Medium | TODO |
| FEAT-019 | Branching flows and actor policies | FEAT-007, FEAT-006 | High | TODO |
| SPIKE-001 | LLM-driven actor policy research | FEAT-017, FEAT-019 | Research | TODO |
| SPIKE-002 | Python DSL for scenarios | FEAT-003 | Medium | TODO |
| SPIKE-003 | Multi-protocol transport architecture | FEAT-007, FEAT-008 | Research | TODO |

**Batch Notes:** These are optional enhancements. Can be deferred or worked based on priority. SPIKE-002 added as a potential future scenario definition method.

---

### Batch 8: Web Intelligence Suite [DONE]
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-020 | Web UI Foundation (Vite/React/Tailwind) | FEAT-021 | Medium | DONE |
| FEAT-021 | FastAPI Backend for Artifacts | FEAT-008 | Medium | DONE |
| FEAT-022 | Executive Dashboard (Run List) | FEAT-021 | Medium | DONE |
| FEAT-023 | Deep Investigation View (Run Detail) | FEAT-021 | High | DONE |
| FEAT-024 | Simulation Trace Timeline | FEAT-023 | High | DONE |
| FEAT-025 | Real-time WebSocket Streaming | FEAT-021, FEAT-024 | High | DONE |

**Batch Notes:** This batch focuses on providing a web-based interface for Turbulence. FEAT-021 provides the API layer, FEAT-020 sets up the frontend framework, and subsequent tickets build out specific UI components. FEAT-025 is the final piece for real-time updates.

---

### Batch 9: Web UI Enhancements
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-026 | Run Dashboard Live Progress | FEAT-025 | Medium | TODO |
| FEAT-027 | Scenario Visualizer | FEAT-021 | High | TODO |
| FEAT-028 | Quick Run Launcher | FEAT-021, FEAT-027 | High | TODO |
| FEAT-029 | Results Explorer | FEAT-023 | Medium | TODO |

**Batch Notes:** This batch enhances the Web UI with interactive features. FEAT-026 requires WebSocket streaming from FEAT-025. FEAT-027 and FEAT-029 can start in parallel once their dependencies are met. FEAT-028 depends on both FastAPI backend and the scenario visualizer for preview functionality.

---

### Batch 10: Enterprise Readiness
| Ticket | Title | Dependencies | Estimated Complexity | Status |
|--------|-------|--------------|---------------------|--------|
| FEAT-030 | Retry policies for HTTP actions | FEAT-004 | Medium | DONE |
| FEAT-031 | Environment variable support | FEAT-002, FEAT-003 | Low | DONE |
| FEAT-032 | Environment profiles | FEAT-031 | Medium | DONE |

**Batch Notes:** This batch addresses enterprise requirements for production use. FEAT-031 (env vars) is foundational and should be prioritized. FEAT-032 (profiles) builds on env var support. FEAT-030 (retry) is independent and can be worked in parallel. These features enable secure, multi-environment testing workflows.

---

## Dependency Matrix

| Ticket | Depends On | Blocks |
|--------|-----------|--------|
| INFRA-001 | - | FEAT-001, FEAT-002, FEAT-003 |
| FEAT-001 | INFRA-001 | FEAT-010 |
| FEAT-002 | INFRA-001 | FEAT-004, FEAT-005, FEAT-006, FEAT-031 |
| FEAT-003 | INFRA-001 | FEAT-004, FEAT-005, FEAT-006, SPIKE-002, FEAT-031 |
| FEAT-004 | FEAT-002, FEAT-003 | FEAT-007, FEAT-012, FEAT-030 |
| FEAT-005 | FEAT-002, FEAT-003 | FEAT-007 |
| FEAT-006 | FEAT-002, FEAT-003 | FEAT-007, FEAT-013, FEAT-014, FEAT-019 |
| FEAT-007 | FEAT-004, FEAT-005, FEAT-006 | FEAT-008, FEAT-009, FEAT-010, FEAT-017, FEAT-019 |
| FEAT-008 | FEAT-007 | FEAT-011, FEAT-018, FEAT-021 |
| FEAT-009 | FEAT-007 | FEAT-015 |
| FEAT-010 | FEAT-007, FEAT-001 | - |
| FEAT-011 | FEAT-008 | FEAT-015, FEAT-016 |
| FEAT-012 | FEAT-004 | - |
| FEAT-013 | FEAT-006 | - |
| FEAT-014 | FEAT-006 | - |
| FEAT-015 | FEAT-009, FEAT-011 | - |
| FEAT-016 | FEAT-011 | - |
| FEAT-017 | FEAT-007 | SPIKE-001 |
| FEAT-018 | FEAT-008 | FEAT-020 |
| FEAT-019 | FEAT-007, FEAT-006 | SPIKE-001, FEAT-020 |
| SPIKE-001 | FEAT-017, FEAT-019 | FEAT-020 |
| SPIKE-002 | FEAT-003 | - |
| SPIKE-003 | FEAT-007, FEAT-008 | - |
| FEAT-020 | FEAT-018, FEAT-019, SPIKE-001 | FEAT-021 |
| FEAT-021 | FEAT-008, FEAT-020 | FEAT-022, FEAT-023, FEAT-025, FEAT-027, FEAT-028 |
| FEAT-022 | FEAT-021 | - |
| FEAT-023 | FEAT-021 | FEAT-024, FEAT-029 |
| FEAT-024 | FEAT-023 | FEAT-025 |
| FEAT-025 | FEAT-021, FEAT-024 | FEAT-026 |
| FEAT-026 | FEAT-025 | FEAT-028 |
| FEAT-027 | FEAT-021 | FEAT-028 |
| FEAT-028 | FEAT-021, FEAT-027 | - |
| FEAT-029 | FEAT-023 | - |
| FEAT-030 | FEAT-004 | - |
| FEAT-031 | FEAT-002, FEAT-003 | FEAT-032 |
| FEAT-032 | FEAT-031 | - |

## Critical Path

The longest dependency chain remains:

```
INFRA-001 → FEAT-002 → FEAT-004 → FEAT-007 → FEAT-008 → FEAT-011 → FEAT-015
    │           │           │           │           │           │         │
  Batch 0    Batch 1    Batch 2    Batch 3    Batch 4    Batch 5   Batch 6
```

**Critical path length: 7 sequential batches**

## AI Agent Execution Instructions

### For Each Batch:
1. Check all dependencies are complete (previous batch done)
2. Start all tickets in the batch in parallel
3. For each ticket:
   - Read the ticket file
   - Implement according to acceptance criteria
   - Write tests
   - Verify acceptance criteria pass
   - Mark ticket complete
4. Only proceed to next batch when ALL tickets in current batch are complete

### Completion Checklist per Ticket:
- [ ] All acceptance criteria satisfied
- [ ] Unit tests written and passing
- [ ] Integration points with dependencies verified
- [ ] No regressions in dependent tickets
- [ ] Code follows project patterns (from INFRA-001)

### Handling Blockers:
- If blocked on a dependency not in the ticket graph, document and ask for clarification
- If a ticket's scope needs adjustment, note the reason and propose changes
- If tests fail due to dependency issues, check the dependent ticket first

## AI Agent Status

Turbulence core and Web UI foundation are stable. Reporting and environments are enhanced.
**Current Frontier:** Polish & CI (Batch 6), Advanced Engine (Batch 7), Web UI Enhancements (Batch 9), and CI Gating (FEAT-016).
