# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want latency and error aggregations in the report
So that I can identify performance bottlenecks and error patterns across my run

**Success Looks Like:**
Enhanced HTML reports with latency percentiles, error categorization, timeline visualization, and clickable drill-down to instance details.

## 2. Context & Constraints (Required)
**Background:**
Beyond pass/fail rates, developers need performance insights—which services are slow, where latency spikes occur, what error patterns emerge. Enhanced reports enable data-driven optimization and debugging.

**Scope:**
- **In Scope:** Latency percentiles (p50, p95, p99), error categorization, per-instance timeline, drill-down links
- **Out of Scope:** Real-time dashboards, external analytics integration, custom report plugins

**Constraints:**
- Must calculate percentiles efficiently
- Must remain a self-contained HTML file
- Timeline visualization must work without JavaScript frameworks
- Must handle large runs (10k+ instances) without browser performance issues

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Latency percentiles by action**
Given a run with 1000 instances of "checkout" scenario
When the report generates
Then latency p50, p95, p99 are shown for each action type
And values are displayed in milliseconds

**Scenario: Latency percentiles by service**
Given a run hitting api, payments, and notifications services
When the report generates
Then each service has its own latency distribution
And slowest service is highlighted

**Scenario: Error categorization**
Given errors including timeouts, 5xx responses, and validation failures
When the report generates
Then errors are grouped by type
And counts are shown for each category

**Scenario: Instance timeline visualization**
Given an instance with 5 steps taking [100ms, 500ms, 50ms, 200ms, 150ms]
When I view the instance details
Then a timeline shows relative duration of each step
And step names and latencies are labeled

**Scenario: Drill-down to instance**
Given the report showing a failed assertion
When I click on the failure
Then I navigate to the specific instance details
And all steps and their observations are visible

**Scenario: Handle large runs**
Given a run with 10,000 instances
When the report generates
Then the HTML file is < 10MB
And the report loads in a browser within 5 seconds

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update src/turbulence/report/html.py
- Update report template with new sections
- Add percentile calculation utilities
- Add CSS for timeline visualization

**Must NOT Change:**
- Artifact storage format
- Basic report structure from FEAT-009
- CLI interface

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(report): add latency percentiles, error categories, and timeline visualization

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify percentile calculations
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Report performance acceptable for large runs

## 7. Resources
- [Percentile Calculation](https://en.wikipedia.org/wiki/Percentile)
- [CSS Grid for Timelines](https://css-tricks.com/snippets/css/complete-guide-grid/)
