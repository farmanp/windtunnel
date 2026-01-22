# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want to define workflow scenarios in YAML
So that Windtunnel can execute realistic user journeys against my services

**Success Looks Like:**
Scenarios loaded from YAML files with validated structure, including entry context, flow steps, and assertions.

## 2. Context & Constraints (Required)
**Background:**
Scenarios are the heart of Windtunnel. Each scenario defines a complete user journey—from initial context through a series of actions to final assertions. Scenarios must be flexible enough to express complex workflows while remaining readable and maintainable.

**Scope:**
- **In Scope:** YAML parsing, scenario directory scanning, Pydantic models for Scenario/Action/Assertion, validation
- **Out of Scope:** Action execution (FEAT-004+), assertion evaluation (FEAT-006), context templating (FEAT-007)

**Constraints:**
- Must use Pydantic v2 for validation
- Scenarios stored as *.yaml files in a directory
- Must support all action types: http, wait, assert

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Load scenarios from directory**
Given a scenarios/ directory with checkout.yaml and refund.yaml
When I load scenarios from the directory
Then both scenarios are returned as validated objects

**Scenario: Parse scenario structure**
Given a scenario YAML with id, entry, flow, and assertions
When I parse the scenario
Then all fields are accessible on the Scenario object
And flow contains a list of Action objects
And assertions contains a list of Assertion objects

**Scenario: Validate required fields**
Given a scenario YAML missing the id field
When I attempt to load it
Then a validation error is raised
And the error identifies the missing field

**Scenario: Support action types**
Given a scenario with http, wait, and assert actions in flow
When I parse the scenario
Then each action has the correct type discriminator
And type-specific fields are validated

**Scenario: Optional fields have defaults**
Given a scenario without max_steps defined
When I parse the scenario
Then max_steps defaults to a reasonable value (e.g., 100)

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/config/scenario.py with Pydantic models
- Update src/windtunnel/config/loader.py to add scenario loading
- Create tests/fixtures/scenarios/ with example files

**Must NOT Change:**
- SUT config structure from FEAT-002
- CLI structure from FEAT-001

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(config): add scenario loader and YAML parser with validation

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written for valid scenarios, invalid scenarios, and edge cases
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Example scenarios provided in tests/fixtures/scenarios/

## 7. Resources
- [Pydantic Discriminated Unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions)

## Example Scenario
```yaml
id: checkout-happy-path
description: Complete checkout flow with payment

entry:
  seed_data:
    cart_items:
      - sku: "WIDGET-001"
        quantity: 2
        price: 29.99
    customer_id: "cust_{{uuid}}"

flow:
  - name: create_cart
    type: http
    service: api
    method: POST
    path: /carts
    json:
      customer_id: "{{entry.seed_data.customer_id}}"
      items: "{{entry.seed_data.cart_items}}"
    extract:
      cart_id: "$.id"
      total: "$.total"

  - name: process_payment
    type: http
    service: payments
    method: POST
    path: /charges
    json:
      amount: "{{total}}"
      cart_id: "{{cart_id}}"
    extract:
      payment_id: "$.id"
      status: "$.status"

  - name: wait_for_confirmation
    type: wait
    service: api
    method: GET
    path: /orders/{{cart_id}}
    interval_seconds: 1
    timeout_seconds: 30
    expect:
      jsonpath: "$.status"
      equals: "confirmed"

assertions:
  - name: payment_completed
    type: assert
    expect:
      status_code: 200
      jsonpath: "$.payment_status"
      equals: "captured"

stop_when:
  any_assertion_fails: true

max_steps: 50
```
