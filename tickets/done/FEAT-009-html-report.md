# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want a static HTML report generated for each run
So that I can visually review results and share them with my team

**Success Looks Like:**
A self-contained HTML file with overall metrics, scenario breakdowns, failing assertions, and service-level failure groupings.

## 2. Context & Constraints (Required)
**Background:**
While JSONL artifacts enable programmatic analysis, humans need visual reports for quick comprehension. The HTML report should provide at-a-glance metrics while enabling drill-down into failures. Reports must be self-contained (no external dependencies) for easy sharing.

**Scope:**
- **In Scope:** HTML generation with Jinja2 templates, overall pass rate, per-scenario breakdown, top failing assertions, service failure grouping
- **Out of Scope:** Latency charts (FEAT-015), interactive filtering, real-time updates

**Constraints:**
- Must be self-contained (inline CSS/JS)
- Must use Jinja2 for HTML templating
- Must be viewable offline
- Must be generated from JSONL artifacts

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Generate report file**
Given a completed run with artifacts
When I run `windtunnel report --run-id <id>`
Then report.html is created in the run directory

**Scenario: Display overall pass rate**
Given a run with 950 passes and 50 failures
When the report generates
Then the overall pass rate shows "95.0%"
And pass/fail counts are displayed

**Scenario: Show per-scenario breakdown**
Given a run with checkout (98% pass) and refund (85% pass) scenarios
When the report generates
Then each scenario has its own pass rate displayed
And scenarios are sorted by failure rate (worst first)

**Scenario: List top failing assertions**
Given a run where "payment_captured" failed 30 times and "order_confirmed" failed 10 times
When the report generates
Then "payment_captured" appears first in failing assertions
And failure counts are shown

**Scenario: Group failures by service**
Given failures occurring in api (20), payments (15), notifications (5)
When the report generates
Then failures are grouped and counted by service
And services are sorted by failure count

**Scenario: Self-contained HTML**
Given a generated report.html
When I open it in a browser without internet
Then all styles render correctly
And no external resources are requested

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/report/__init__.py
- Create src/windtunnel/report/html.py
- Create src/windtunnel/report/templates/report.html.j2
- Update CLI report command to call report generation

**Must NOT Change:**
- Artifact storage format
- CLI command structure

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(report): add basic HTML report generation with pass rates

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify report content
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Report renders correctly in major browsers

## 7. Resources
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
