# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to upload or paste YAML scenarios and see them rendered as flowcharts
So that I can understand scenario structure visually before running tests

**Success Looks Like:**
A visual flowchart representation of YAML scenarios showing the happy path and branches, with clickable steps revealing configuration details and distinct visual treatment for different action types.

## 2. Context & Constraints (Required)
**Background:**
Complex scenarios with many steps, branches, and dependencies are hard to understand from YAML alone. A visual representation helps users quickly grasp flow structure, identify potential issues, and communicate test designs to stakeholders.

**Scope:**
- **In Scope:** YAML paste/upload interface, flowchart rendering, step click details, action type differentiation (colors/icons), branch visualization
- **Out of Scope:** YAML editing within the visualizer, live validation, export to image, YAML generation from diagrams

**Constraints:**
- Must parse YAML client-side for instant feedback (no server roundtrip for basic visualization)
- Backend endpoint needed for advanced validation via FastAPI (FEAT-021)
- Flowchart library must be lightweight (prefer existing dependencies or small additions)
- Must handle scenarios with up to 50 steps without performance issues
- Responsive design for various screen sizes

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Paste YAML to visualize**
Given I am on the scenario visualizer page
When I paste valid YAML into the input area
Then a flowchart renders showing all steps in order
And the flowchart updates within 200ms of paste

**Scenario: Upload YAML file**
Given I am on the scenario visualizer page
When I upload a .yaml file
Then the file content is parsed
And the flowchart renders the scenario structure

**Scenario: Action type differentiation**
Given a scenario with HTTP, Wait, and Assert actions
When the flowchart renders
Then each action type has a distinct color
And each action type shows an appropriate icon
And a legend explains the color coding

**Scenario: Click step for details**
Given a rendered flowchart
When I click on a step node
Then a panel shows the step's full configuration
And I can see extract mappings, assertions, and timeouts

**Scenario: Branch visualization**
Given a scenario with conditional branching
When the flowchart renders
Then branches are shown as parallel paths
And branch conditions are labeled on the edges

**Scenario: Invalid YAML handling**
Given I paste malformed YAML
When the parser fails
Then an error message shows the parse error location
And previously rendered flowchart is preserved

**Scenario: Large scenario performance**
Given a scenario with 50 steps
When the flowchart renders
Then rendering completes within 1 second
And pan/zoom interactions remain smooth

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Add new page in ui/src/pages/ for visualizer
- Add flowchart components in ui/src/components/
- Add YAML parsing utilities
- Optionally add backend validation endpoint in src/turbulence/api/routes/

**Must NOT Change:**
- Existing scenario loader logic
- CLI scenario validation
- FastAPI core setup

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(ui): add scenario visualizer with YAML-to-flowchart rendering

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Flowchart renders correctly for sample scenarios
- [ ] Action types visually differentiated
- [ ] Step click reveals configuration
- [ ] Error handling for invalid YAML
- [ ] Performance acceptable for large scenarios
- [ ] Code reviewed

## 7. Resources
- [React Flow](https://reactflow.dev/) - potential flowchart library
- [js-yaml](https://github.com/nodeca/js-yaml) - YAML parsing in JavaScript
- FEAT-021: FastAPI Backend (dependency for validation endpoint)
- Existing scenario examples in docs/ or tests/
