# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want to inject turbulence into workflows
So that I can test my system's resilience to real-world conditions like latency and failures

**Success Looks Like:**
Configurable turbulence injection that adds latency, forces timeouts, and triggers retry storms to stress test service resilience.

## 2. Context & Constraints (Required)
**Background:**
Production systems experience turbulence—network latency, service timeouts, clients retrying failed requests. Windtunnel must simulate these conditions to verify that systems handle them gracefully without data corruption or cascading failures.

**Scope:**
- **In Scope:** Injected latency (configurable range), forced timeouts, retry storms, per-action and per-service configuration
- **Out of Scope:** Network partition simulation, data corruption injection, dependency failure injection

**Constraints:**
- Turbulence must be deterministic given seed
- Must not modify actual service responses
- Configuration can be global, per-service, or per-action
- Must record injected turbulence in observations

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Inject latency before request**
Given turbulence config with latency_ms: {min: 50, max: 200}
When an HTTP action executes
Then an artificial delay of 50-200ms occurs before the request
And the injected latency is recorded in observation

**Scenario: Force timeout**
Given turbulence config with timeout_after_ms: 100
And a service that normally responds in 500ms
When the action executes
Then the request is aborted after 100ms
And observation shows timeout error

**Scenario: Retry storm**
Given turbulence config with retry_count: 3
When an HTTP action executes
Then the request is made 4 times (1 original + 3 retries)
And all attempts are recorded in observation

**Scenario: Per-service turbulence**
Given turbulence config targeting only "payments" service
When executing actions against "api" and "payments"
Then only "payments" actions experience turbulence
And "api" actions execute normally

**Scenario: Per-action turbulence**
Given turbulence config for action "process_payment" only
When the workflow executes all steps
Then only "process_payment" experiences turbulence

**Scenario: Deterministic with seed**
Given seed 12345 and latency_ms: {min: 50, max: 200}
When the same instance runs twice
Then the same latency values are injected each time

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/turbulence/__init__.py
- Create src/windtunnel/turbulence/engine.py
- Create src/windtunnel/turbulence/config.py
- Integrate turbulence with action runners

**Must NOT Change:**
- Core action runner logic (wrap, don't modify)
- Artifact storage format
- CLI command structure

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(turbulence): add turbulence engine with latency, timeout, and retry injection

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify each turbulence type
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Determinism verified with seed

## 7. Resources
- [Chaos Engineering Principles](https://principlesofchaos.org/)

## Example Turbulence Config
```yaml
turbulence:
  global:
    latency_ms:
      min: 10
      max: 100
  services:
    payments:
      latency_ms:
        min: 100
        max: 500
      timeout_after_ms: 2000
  actions:
    process_payment:
      retry_count: 2
```
