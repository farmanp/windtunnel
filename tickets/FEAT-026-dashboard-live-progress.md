# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to see live progress during runs with pass/fail counts at a glance
So that I can monitor test execution in real-time and drill down to failures immediately

**Success Looks Like:**
The run dashboard shows real-time progress bars, live pass/fail counts, and clickable failure indicators that navigate directly to instance details.

## 2. Context & Constraints (Required)
**Background:**
Currently, users must wait for runs to complete before seeing results. Real-time feedback during execution enables faster debugging cycles—users can identify failing scenarios early and investigate without waiting for the full run to finish.

**Scope:**
- **In Scope:** Progress bar during active runs, live pass/fail counters, clickable failure links, WebSocket integration
- **Out of Scope:** Notification systems (email, Slack), run cancellation from UI, custom progress views

**Constraints:**
- Must use WebSocket infrastructure from FEAT-025
- Progress updates should not overwhelm the UI (throttle/debounce as needed)
- Must remain responsive with 1000+ concurrent instances
- Clickable failures must navigate to existing instance detail view (FEAT-024)

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Live progress bar**
Given an active run with 100 instances
When 50 instances have completed
Then the progress bar shows 50% completion
And updates in real-time as more instances complete

**Scenario: Live pass/fail counts**
Given an active run with mixed results
When 30 instances pass and 10 fail
Then the dashboard shows "30 passed" and "10 failed"
And counts update within 500ms of instance completion

**Scenario: Click to view failure**
Given a failed instance appears in the live dashboard
When I click on the failure indicator
Then I navigate to the instance timeline view
And all step details are visible

**Scenario: Run completion**
Given an active run reaches 100% completion
When all instances finish
Then the progress bar shows complete state
And final pass/fail counts are displayed
And the run status changes to "completed"

**Scenario: Multiple concurrent runs**
Given two runs are executing simultaneously
When I view the dashboard
Then each run shows its own progress independently
And updates don't interfere with each other

**Scenario: Reconnection handling**
Given I lose WebSocket connection during a run
When the connection is restored
Then the progress state syncs correctly
And no updates are lost or duplicated

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update ui/src/pages/ (dashboard components)
- Add WebSocket client handlers in ui/src/api/
- Update ui/src/components/ for progress indicators
- Add live state management hooks

**Must NOT Change:**
- WebSocket server implementation (FEAT-025)
- Existing run detail/timeline views
- Backend artifact storage format
- CLI interface

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(ui): add live progress monitoring to run dashboard

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Progress updates work with 100+ concurrent instances
- [ ] WebSocket reconnection handles gracefully
- [ ] Click-through to failures navigates correctly
- [ ] No memory leaks from WebSocket subscriptions
- [ ] Code reviewed

## 7. Resources
- FEAT-025: Real-time WebSocket Streaming (dependency)
- FEAT-024: Instance Timeline view (integration point)
- [React useWebSocket patterns](https://react.dev/reference/react/useEffect)
