# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want to replay a specific workflow instance
So that I can debug failures by re-executing with the same conditions

**Success Looks Like:**
The replay command re-executes a specific instance using stored artifacts, with the same seed, context, and correlation ID, producing step-by-step output for debugging.

## 2. Context & Constraints (Required)
**Background:**
When a workflow instance fails, developers need to understand what happened. Replay enables re-execution of a specific instance with identical inputs, allowing observation of actual service responses at the time of debugging. The correlation ID is preserved for log correlation.

**Scope:**
- **In Scope:** Load instance from artifacts, re-execute with same seed/context, preserve correlation_id, step-by-step output
- **Out of Scope:** Diff against original execution, mock responses, time travel debugging

**Constraints:**
- Must use same correlation_id for tracing
- Must load entry context from original instance
- Must output each step's result as it executes
- Services may return different responses than original run

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Replay by run and instance ID**
Given a completed run "run_001" with instance "inst_042"
When I run `windtunnel replay --run-id run_001 --instance-id inst_042`
Then the instance is loaded from artifacts
And re-executed with original entry context

**Scenario: Preserve correlation ID**
Given instance "inst_042" had correlation_id "corr_abc123"
When I replay the instance
Then all requests use correlation_id "corr_abc123"
And the header is included in default_headers

**Scenario: Step-by-step output**
Given a scenario with 5 steps
When I replay the instance
Then each step is logged as it executes
And the output shows step name, action type, and result

**Scenario: Show differences from original**
Given the original step_3 returned status 200
And during replay step_3 returns status 500
When the step completes
Then the output indicates the difference
And execution continues to subsequent steps

**Scenario: Invalid instance ID**
Given run "run_001" does not contain instance "inst_999"
When I run `windtunnel replay --run-id run_001 --instance-id inst_999`
Then an error message indicates the instance was not found
And exit code is 1

**Scenario: Rich formatted output**
Given a replay in progress
When steps execute
Then output uses rich formatting (colors, tables)
And progress is clearly visible

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update src/windtunnel/commands/replay.py with full implementation
- Create src/windtunnel/engine/replay.py for replay logic
- Update CLI to wire replay command

**Must NOT Change:**
- Artifact storage format
- Run command implementation
- Other CLI commands

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(cli): implement replay command for instance debugging

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify replay loads correct instance data
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Output is readable and helpful for debugging

## 7. Resources
- [Rich Documentation](https://rich.readthedocs.io/)
