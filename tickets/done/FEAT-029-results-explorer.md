# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to filter, compare, and export run results for analysis
So that I can identify trends, investigate regressions, and share findings with my team

**Success Looks Like:**
An interactive results explorer with filtering by pass/fail/slow, side-by-side run comparison, and export capabilities to CSV and JSON formats.

## 2. Context & Constraints (Required)
**Background:**
Individual run views are useful for debugging, but understanding patterns across runs requires filtering and comparison capabilities. Teams need to export data for external analysis tools, reports, and stakeholder communication.

**Scope:**
- **In Scope:** Run filtering (passed/failed/slow), run comparison (side-by-side), result export (CSV/JSON), text search within results
- **Out of Scope:** Custom dashboards, saved filters/queries, alerting on thresholds, integration with external analytics platforms

**Constraints:**
- Must work with existing run detail view (FEAT-023) infrastructure
- Export files should be reasonably sized (aggregate data, not raw observations)
- Comparison limited to 2 runs at a time for clarity
- "Slow" threshold should be configurable (default: p95 latency > baseline)

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Filter by passed runs**
Given I am on the results explorer page
When I select the "Passed" filter
Then only runs where all instances passed are shown
And the run count updates to reflect the filter

**Scenario: Filter by failed runs**
Given I am on the results explorer page
When I select the "Failed" filter
Then only runs with at least one failed instance are shown
And failure counts are visible for each run

**Scenario: Filter by slow runs**
Given I am on the results explorer page with p95 baseline of 500ms
When I select the "Slow" filter
Then only runs where p95 latency exceeds 500ms are shown
And p95 latency values are displayed

**Scenario: Compare two runs side-by-side**
Given I have selected two runs for comparison
When I click the Compare button
Then a side-by-side view shows both runs
And key metrics (pass rate, latency, error counts) are aligned
And differences are highlighted

**Scenario: Export to CSV**
Given I have filtered to a set of runs
When I click Export CSV
Then a CSV file downloads
And it contains run metadata and aggregate metrics
And column headers are clearly labeled

**Scenario: Export to JSON**
Given I have filtered to a set of runs
When I click Export JSON
Then a JSON file downloads
And it contains structured run data
And format is documented and consistent

**Scenario: Search within results**
Given I am on the results explorer
When I type a search query (scenario name, run ID, etc.)
Then results filter to match the query
And search is case-insensitive

**Scenario: Combine filters**
Given I select "Failed" filter
When I also apply a search for "checkout"
Then only failed runs matching "checkout" are shown
And both filters work together

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Add new page in ui/src/pages/ for results explorer
- Add comparison and filter components in ui/src/components/
- Add export utilities (CSV/JSON generation)
- Optionally add backend endpoints for filtered queries

**Must NOT Change:**
- Artifact storage format
- Existing run detail view (FEAT-023)
- Backend artifact reader core logic

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(ui): add results explorer with filtering, comparison, and export

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Filters work independently and combined
- [ ] Comparison view shows meaningful differences
- [ ] CSV export produces valid, importable file
- [ ] JSON export produces valid, parseable file
- [ ] Search filters results correctly
- [ ] Code reviewed

## 7. Resources
- FEAT-023: Run Detail view (dependency/integration)
- [Papa Parse](https://www.papaparse.com/) - CSV generation library
- [FileSaver.js](https://github.com/eligrey/FileSaver.js/) - File download utility
- Existing artifact reader in src/turbulence/api/services/artifact_reader.py
