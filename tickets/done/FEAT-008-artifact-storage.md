# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want all run data persisted as artifacts
So that I can debug failures, analyze results, and replay specific instances

**Success Looks Like:**
A complete artifact storage system writing JSONL files with run manifests, instance data, step observations, and assertion results in a structured directory.

## 2. Context & Constraints (Required)
**Background:**
Reproducibility is a core principle of Windtunnel. Every run must produce artifacts that enable exact replay and deep debugging. The storage format must be efficient for streaming writes during execution while remaining human-readable and queryable after completion.

**Scope:**
- **In Scope:** Directory structure creation, JSONL streaming, manifest.json, instances/steps/assertions files, summary.json
- **Out of Scope:** SQLite storage (FEAT-018), artifact compression, remote storage

**Constraints:**
- Must use JSONL format for streaming writes
- Must create deterministic directory structure
- Must write incrementally (not buffer entire run in memory)
- Must include correlation IDs for tracing

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Create run directory structure**
Given a new run with id "run_20240115_001"
When the run initializes
Then directory runs/run_20240115_001/ is created
And manifest.json is written with run metadata

**Scenario: Write manifest.json**
Given a run starting with sut "ecommerce" and scenarios ["checkout", "refund"]
When the manifest is written
Then it contains run_id, timestamp, sut_name, scenario_ids, seed, config

**Scenario: Stream instance data**
Given instances completing during a run
When each instance completes
Then a line is appended to instances.jsonl
And the file is flushed immediately

**Scenario: Stream step observations**
Given workflow steps executing
When each step completes
Then a line is appended to steps.jsonl
And each line includes instance_id, step_name, observation

**Scenario: Write summary on completion**
Given a run completing with 100 instances (95 pass, 5 fail)
When the run finalizes
Then summary.json is written
And it contains pass_count, fail_count, pass_rate, duration_ms

**Scenario: Artifact structure is deterministic**
Given two runs with the same seed and config
When both runs complete
Then their artifact structures are identical (modulo timestamps)

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/storage/__init__.py
- Create src/windtunnel/storage/artifact.py
- Create src/windtunnel/storage/jsonl.py
- Create src/windtunnel/models/manifest.py

**Must NOT Change:**
- Action runners
- Config loading

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(storage): add JSONL artifact storage with run persistence

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify file structure and content
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Streaming writes verified (not buffered)

## 7. Resources
- [JSONL Format](https://jsonlines.org/)

## Artifact Structure
```
runs/
  run_20240115_001/
    manifest.json       # Run metadata and config
    instances.jsonl     # One line per instance
    steps.jsonl         # One line per step execution
    assertions.jsonl    # One line per assertion result
    summary.json        # Final aggregates
    artifacts/          # Per-instance raw data
      inst_001/
        step_001_request.json
        step_001_response.json
        ...
```
