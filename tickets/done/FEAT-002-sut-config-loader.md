# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want to define my system under test in a YAML config
So that Windtunnel knows which services to target and how to communicate with them

**Success Looks Like:**
A validated SUT configuration loaded from YAML with proper Pydantic models, supporting variable interpolation for correlation IDs.

## 2. Context & Constraints (Required)
**Background:**
The SUT (System Under Test) configuration defines the services that Windtunnel will interact with during simulations. This includes base URLs, default headers, and service-specific settings. The config must support dynamic values like `{{run_id}}` and `{{correlation_id}}` for request tracing.

**Scope:**
- **In Scope:** YAML parsing, Pydantic models, validation, header templating
- **Out of Scope:** Service health checks, authentication flows, secret management

**Constraints:**
- Must use Pydantic v2 for validation
- Must support YAML format (PyYAML via pydantic-settings or direct)
- Template variables use Jinja2-style `{{variable}}` syntax

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Load valid SUT config**
Given a sut.yaml file with name, default_headers, and services
When I load the configuration
Then a validated SUTConfig object is returned
And all services are accessible by name

**Scenario: Validate service base_url is required**
Given a sut.yaml with a service missing base_url
When I load the configuration
Then a validation error is raised
And the error message indicates the missing field

**Scenario: Support header templates**
Given a sut.yaml with `X-Correlation-ID: "{{correlation_id}}"` in default_headers
When I load the configuration
Then the header value is preserved as a template string
And it can be rendered with context later

**Scenario: Multiple services defined**
Given a sut.yaml with api, payments, and notifications services
When I load the configuration
Then all three services are available
And each has its own base_url and optional headers

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/config/__init__.py
- Create src/windtunnel/config/sut.py with Pydantic models
- Create src/windtunnel/config/loader.py for YAML loading

**Must NOT Change:**
- CLI structure from FEAT-001
- Core dependency versions

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(config): add SUT config loader with pydantic validation

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written for valid configs, invalid configs, and edge cases
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Example sut.yaml provided in tests/fixtures/

## 7. Resources
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)

## Example SUT Config
```yaml
name: ecommerce-checkout
default_headers:
  X-Run-ID: "{{run_id}}"
  X-Correlation-ID: "{{correlation_id}}"
  Content-Type: "application/json"

services:
  api:
    base_url: "https://api.example.com"
  payments:
    base_url: "https://payments.example.com"
    headers:
      X-API-Key: "{{env.PAYMENTS_API_KEY}}"
  notifications:
    base_url: "https://notifications.example.com"
```
