# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want assertion actions to validate service state at any point in a workflow
So that I can verify invariants and detect failures during simulation

**Success Looks Like:**
Named assertions that evaluate expectations against context/responses and report clear pass/fail results with detailed failure information.

## 2. Context & Constraints (Required)
**Background:**
Assertions are how Windtunnel validates that workflows produce correct results. Unlike test frameworks that stop on first failure, Windtunnel assertions are observations that contribute to pass rate metrics. Clear assertion naming and detailed failure messages are critical for debugging.

**Scope:**
- **In Scope:** Status code assertions, JSONPath equals/contains, named assertions, pass/fail reporting
- **Out of Scope:** Schema validation (FEAT-013), custom expressions (FEAT-014), composite assertions

**Constraints:**
- Assertions must be named for reporting
- Must capture both expected and actual values on failure
- Must support assertions on current response or context values

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Status code assertion passes**
Given an assertion expecting status_code: 200
And the last response had status code 200
When the assertion evaluates
Then the assertion passes
And observation.ok is true

**Scenario: Status code assertion fails**
Given an assertion expecting status_code: 200
And the last response had status code 404
When the assertion evaluates
Then the assertion fails
And observation includes expected: 200, actual: 404

**Scenario: JSONPath equals assertion**
Given an assertion with jsonpath: "$.total" equals: 100
And the response body is {"total": 100, "items": 3}
When the assertion evaluates
Then the assertion passes

**Scenario: JSONPath contains assertion**
Given an assertion with jsonpath: "$.status" contains: "complete"
And the response body is {"status": "order_complete"}
When the assertion evaluates
Then the assertion passes

**Scenario: Named assertions in report**
Given an assertion with name: "payment_captured"
When the assertion fails
Then the failure is reported as "payment_captured" in results
And the full path/expectation is included

**Scenario: Assert on context values**
Given an assertion with context_path: "extracted_user_id" equals: 123
And context["extracted_user_id"] is 123
When the assertion evaluates
Then the assertion passes

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/actions/assert_.py (underscore to avoid keyword)
- Update src/windtunnel/actions/__init__.py to register assert runner
- Create src/windtunnel/models/assertion_result.py

**Must NOT Change:**
- HTTP/Wait action implementations
- ActionRunner protocol

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(actions): add assert action with status code and JSONPath expectations

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written for pass/fail scenarios
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Failure messages are clear and actionable

## 7. Resources
- [jsonpath-ng Documentation](https://github.com/h2non/jsonpath-ng)
