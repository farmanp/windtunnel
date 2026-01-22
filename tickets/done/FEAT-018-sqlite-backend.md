# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want faster querying of run data for large test runs
So that I can efficiently analyze results from runs with thousands of instances

**Success Looks Like:**
Optional SQLite storage backend that maintains the same data model as JSONL while enabling fast queries and filtering.

## 2. Context & Constraints (Required)
**Background:**
JSONL is excellent for streaming writes and human readability, but becomes slow for querying large runs. SQLite provides indexed queries while remaining a single-file, portable format that requires no external database.

**Scope:**
- **In Scope:** --storage sqlite flag, same data model as JSONL, query interface for filtering, migration from JSONL to SQLite
- **Out of Scope:** PostgreSQL/MySQL support, real-time streaming to SQLite, distributed storage

**Constraints:**
- Must be optional (JSONL remains default)
- Must support same queries as JSONL analysis
- Single .db file per run
- Must support migration from existing JSONL runs

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Create SQLite storage**
Given --storage sqlite flag
When a run completes
Then a turbulence.db file is created in run directory
And all instance/step/assertion data is stored

**Scenario: Same data model**
Given a run stored in SQLite
When I query instances
Then the same fields are available as JSONL (instance_id, scenario_id, status, etc.)

**Scenario: Filter instances by status**
Given a SQLite run with 1000 instances
When I query for failed instances
Then only failed instances are returned
And query completes in < 100ms

**Scenario: Filter steps by action type**
Given a SQLite run
When I query for all HTTP actions
Then only http type steps are returned
And related instance data is joinable

**Scenario: Migrate JSONL to SQLite**
Given an existing run stored as JSONL
When I run migration command
Then a SQLite database is created with equivalent data
And original JSONL is preserved

**Scenario: Default remains JSONL**
Given no --storage flag specified
When a run completes
Then JSONL files are created (not SQLite)

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/turbulence/storage/sqlite.py
- Update src/turbulence/storage/__init__.py with storage factory
- Add --storage flag to CLI
- Create migration utility

**Must NOT Change:**
- JSONL storage implementation
- Data models
- Report generation (should work with both backends)

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(storage): add optional SQLite backend for faster querying

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify SQLite storage and queries
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Query performance verified for large runs

## 7. Resources
- [SQLite Python Documentation](https://docs.python.org/3/library/sqlite3.html)

## Schema Design
```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    sut_name TEXT,
    scenario_ids TEXT,  -- JSON array
    seed INTEGER,
    config TEXT  -- JSON
);

CREATE TABLE instances (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES runs(id),
    scenario_id TEXT,
    correlation_id TEXT,
    status TEXT,  -- pass, fail
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    variations TEXT,  -- JSON
    error TEXT
);

CREATE TABLE steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT REFERENCES instances(id),
    step_index INTEGER,
    action_name TEXT,
    action_type TEXT,
    service TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    latency_ms INTEGER,
    status_code INTEGER,
    ok BOOLEAN,
    observation TEXT  -- JSON
);

CREATE TABLE assertions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instance_id TEXT REFERENCES instances(id),
    assertion_name TEXT,
    passed BOOLEAN,
    expected TEXT,
    actual TEXT,
    error TEXT
);

CREATE INDEX idx_instances_status ON instances(status);
CREATE INDEX idx_instances_scenario ON instances(scenario_id);
CREATE INDEX idx_steps_action_type ON steps(action_type);
CREATE INDEX idx_steps_service ON steps(service);
CREATE INDEX idx_assertions_passed ON assertions(passed);
```
