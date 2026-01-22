# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want wait actions that poll until a condition is met
So that my workflows can handle asynchronous processes and eventual consistency

**Success Looks Like:**
Wait actions poll endpoints at configurable intervals until an expected condition is met or timeout occurs, with full observability of each poll attempt.

## 2. Context & Constraints (Required)
**Background:**
Many real-world workflows involve asynchronous processes—order processing, payment settlement, notification delivery. Wait actions allow scenarios to poll for expected state changes rather than using arbitrary sleep durations, making tests more reliable and faster.

**Scope:**
- **In Scope:** Polling loop, configurable interval/timeout, JSONPath condition matching, attempt tracking
- **Out of Scope:** Complex condition expressions (FEAT-014), multiple conditions (AND/OR)

**Constraints:**
- Must support equals and contains comparisons
- Must track and report all poll attempts in observation
- Must use async sleep between attempts

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Poll until condition met**
Given a wait action expecting $.status equals "completed"
And the endpoint initially returns {"status": "pending"}
And after 2 seconds returns {"status": "completed"}
When the action executes with interval_seconds: 1
Then the action succeeds after approximately 2-3 polls
And observation.ok is true

**Scenario: Timeout when condition never met**
Given a wait action expecting $.status equals "completed"
And the endpoint always returns {"status": "pending"}
When the action executes with timeout_seconds: 3 and interval_seconds: 1
Then the action fails after timeout
And observation.ok is false
And observation.errors indicates timeout

**Scenario: Record all poll attempts**
Given a wait action that polls 5 times before succeeding
When the action completes
Then observation contains details of all 5 attempts
And each attempt has its own latency and response

**Scenario: Contains comparison**
Given a wait action expecting $.tags contains "shipped"
And the endpoint returns {"tags": ["pending", "shipped", "notified"]}
When the action executes
Then the condition is met
And observation.ok is true

**Scenario: First poll succeeds**
Given a wait action expecting $.ready equals true
And the endpoint immediately returns {"ready": true}
When the action executes
Then the action succeeds on first poll
And no unnecessary waiting occurs

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/actions/wait.py
- Update src/windtunnel/actions/__init__.py to register wait runner

**Must NOT Change:**
- HTTP action implementation from FEAT-004
- ActionRunner protocol

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(actions): add wait action runner with polling and conditions

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written with mocked endpoints and timing verification
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Timeout behavior verified

## 7. Resources
- [asyncio.sleep documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep)
