# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want a CLI with run/report/replay commands
So that I can execute and analyze workflow simulations from the terminal

**Success Looks Like:**
A fully functional CLI that accepts commands and options, displays help text, and returns appropriate exit codes.

## 2. Context & Constraints (Required)
**Background:**
The CLI is the primary interface for Windtunnel. Users will invoke it from terminals and CI pipelines to run simulations, generate reports, and replay specific instances for debugging.

**Scope:**
- **In Scope:** Command structure, argument parsing, help text, exit codes, version display
- **Out of Scope:** Actual command implementation (handled in later tickets), configuration file loading

**Constraints:**
- Must use Typer for CLI framework (consistency with dependency choices)
- Exit codes must be deterministic: 0=success, 1=failure, 2=threshold violation
- Must support --help on all commands

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Run command accepts required options**
Given the CLI is installed
When I run `windtunnel run --help`
Then I see options for --sut, --scenarios, --n, --parallel, --seed
And each option has descriptive help text

**Scenario: Report command accepts run-id**
Given the CLI is installed
When I run `windtunnel report --help`
Then I see --run-id as a required option

**Scenario: Replay command accepts instance identifiers**
Given the CLI is installed
When I run `windtunnel replay --help`
Then I see --run-id and --instance-id options

**Scenario: Version display**
Given the CLI is installed
When I run `windtunnel --version`
Then I see the current version number

**Scenario: Exit codes are correct**
Given a command execution
When the command succeeds
Then exit code is 0
When the command fails
Then exit code is 1
When a threshold is violated
Then exit code is 2

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/cli.py
- Create src/windtunnel/commands/ directory with run.py, report.py, replay.py
- Update src/windtunnel/__init__.py with version
- Update pyproject.toml with entry point

**Must NOT Change:**
- Core dependency versions
- Project structure established in INFRA-001

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(cli): add run, report, replay command scaffolds with typer

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written and passing for CLI argument parsing
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] `windtunnel --help` displays all commands
- [ ] Each command's --help shows relevant options

## 7. Resources
- [Typer Documentation](https://typer.tiangolo.com/)
- [Python CLI Best Practices](https://clig.dev/)
