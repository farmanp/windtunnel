# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to launch test runs directly from the web UI without using the terminal
So that I can quickly start tests with visual configuration and immediate feedback

**Success Looks Like:**
A web interface with dropdowns for SUT config and scenario selection, sliders for instance count and parallelism, a preview of the selected scenario, and a Run button that triggers execution with real-time progress display.

## 2. Context & Constraints (Required)
**Background:**
The CLI is powerful but requires terminal access and familiarity with command syntax. A web-based launcher lowers the barrier to entry, enables non-technical stakeholders to trigger tests, and integrates naturally with the existing dashboard for immediate result viewing.

**Scope:**
- **In Scope:** SUT config selector, scenario selector (single/multiple), instance count slider, parallelism slider, scenario preview integration, run execution trigger, progress display
- **Out of Scope:** SUT config editor, scenario editor, scheduled runs, run templates/presets

**Constraints:**
- Backend must expose APIs to list available SUT configs and scenarios
- Run execution must be async to not block the UI
- Must integrate with scenario visualizer (FEAT-027) for preview
- Must integrate with live progress (FEAT-026) for execution feedback
- Reasonable defaults for sliders (count: 10, parallelism: 5)

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Select SUT configuration**
Given I am on the run launcher page
When I click the SUT dropdown
Then I see all available SUT configurations from the sut configs directory
And I can select one

**Scenario: Select scenario**
Given I have selected a SUT config
When I click the scenario dropdown
Then I see all available scenarios
And I can select one or more scenarios

**Scenario: Preview selected scenario**
Given I have selected a scenario
When I click the preview button
Then the scenario visualizer shows the flowchart
And I can see the scenario structure before running

**Scenario: Configure run parameters**
Given I have selected SUT and scenario
When I adjust the instance count slider
Then the slider shows values from 1 to 1000
And the selected value updates in real-time
When I adjust the parallelism slider
Then the slider shows values from 1 to 100
And the selected value updates in real-time

**Scenario: Launch run**
Given I have configured SUT, scenario, count, and parallelism
When I click the Run button
Then a new run starts on the backend
And I am navigated to the run detail page
And live progress shows the execution status

**Scenario: Validation before run**
Given I have not selected a SUT config or scenario
When I click the Run button
Then the button is disabled or shows validation error
And I cannot launch an incomplete run

**Scenario: Run with multiple scenarios**
Given I have selected 3 scenarios
When I launch the run
Then all 3 scenarios execute in the run
And progress shows combined instance counts

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Add new page in ui/src/pages/ for launcher
- Add launcher components in ui/src/components/
- Add backend endpoints for listing configs/scenarios in src/turbulence/api/routes/
- Add run trigger endpoint in src/turbulence/api/routes/

**Must NOT Change:**
- Core execution engine (executor.py)
- Existing CLI run command logic (reuse where possible)
- Scenario visualizer implementation (integrate via import)

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(api): add endpoints for listing configs and triggering runs
- feat(ui): add quick run launcher with visual configuration

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] SUT and scenario lists populated correctly
- [ ] Scenario preview shows visualizer
- [ ] Run executes with selected parameters
- [ ] Navigation to progress works
- [ ] Validation prevents incomplete runs
- [ ] Code reviewed

## 7. Resources
- FEAT-021: FastAPI Backend (dependency)
- FEAT-027: Scenario Visualizer (integration for preview)
- FEAT-026: Live Progress (integration for execution feedback)
- Existing run command implementation in src/turbulence/commands/run.py
