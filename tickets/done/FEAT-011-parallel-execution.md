# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want parallel workflow execution
So that I can run thousands of instances efficiently and stress test my services

**Success Looks Like:**
Concurrent execution of workflow instances with configurable parallelism, progress display, and graceful cancellation support.

## 2. Context & Constraints (Required)
**Background:**
Windtunnel's value comes from running many workflow instances to surface rare failures. Sequential execution would be impractically slow for meaningful sample sizes. Parallel execution must balance throughput with resource constraints and provide visibility into progress.

**Scope:**
- **In Scope:** Async execution with semaphore, --parallel flag, rich progress display, Ctrl+C handling
- **Out of Scope:** Distributed execution, rate limiting per service, adaptive parallelism

**Constraints:**
- Must use asyncio semaphore for concurrency limiting
- Must not exceed --parallel concurrent instances
- Must gracefully cancel in-flight instances on Ctrl+C
- Must update progress in real-time

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Limit concurrency with semaphore**
Given --parallel 10 with 100 instances to run
When execution proceeds
Then at most 10 instances execute concurrently
And all 100 instances eventually complete

**Scenario: Progress display**
Given a run with 1000 instances and --parallel 50
When execution is in progress
Then a progress bar shows completion percentage
And current/total counts are displayed
And estimated time remaining is shown

**Scenario: Graceful Ctrl+C cancellation**
Given a run in progress with 500 remaining instances
When the user presses Ctrl+C
Then currently executing instances complete or timeout
And no new instances start
And partial results are saved to artifacts

**Scenario: Default parallelism**
Given the --parallel flag is not specified
When the run starts
Then a sensible default (e.g., 10) is used

**Scenario: High parallelism stress test**
Given --parallel 100 and 10000 instances
When the run completes
Then all instances are executed
And memory usage remains bounded
And artifact writes don't corrupt

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/engine/executor.py
- Update src/windtunnel/commands/run.py to use executor
- Add progress display with rich

**Must NOT Change:**
- Action runner implementations
- Artifact storage format
- Individual instance execution logic

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(engine): add parallel execution with configurable concurrency

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify concurrency limits
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Memory usage acceptable under load

## 7. Resources
- [asyncio Semaphore](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore)
- [Rich Progress](https://rich.readthedocs.io/en/latest/progress.html)
