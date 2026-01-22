# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want workflows that branch based on observations
So that I can model realistic user behavior that adapts to system responses

**Success Looks Like:**
Conditional workflow steps that branch based on observed responses, enabling complex scenario modeling like "if refund denied, open support ticket."

## 2. Context & Constraints (Required)
**Background:**
Real users don't follow linear paths—they retry on failure, take alternative actions when blocked, and make decisions based on system responses. Branching flows enable scenarios that model this adaptive behavior.

**Scope:**
- **In Scope:** Conditional steps (if/else), observation-based branching, rule-based policy definitions, context variable conditions
- **Out of Scope:** Loops (use max_steps instead), ML-driven decisions (see SPIKE-001), goto/jump statements

**Constraints:**
- Branch conditions must be evaluable from context/observations
- Must not create infinite loops (max_steps enforced)
- Policy rules must be declarative (not arbitrary code)
- Branch taken must be logged for debugging

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Simple if condition**
Given a step with condition: "{{status_code}} == 200"
And the previous response had status 200
When the flow executes
Then the conditional step runs

**Scenario: Skip step when condition false**
Given a step with condition: "{{status_code}} == 200"
And the previous response had status 400
When the flow executes
Then the conditional step is skipped
And execution continues to next step

**Scenario: If-else branching**
Given steps with if_branch and else_branch
And condition: "{{refund_status}} == 'approved'"
When refund_status is "denied"
When the flow executes
Then else_branch steps execute (open support ticket)
And if_branch steps are skipped

**Scenario: Nested conditions**
Given a step inside another conditional block
When the outer condition is false
Then the inner step is not evaluated

**Scenario: Log branch decisions**
Given a workflow with conditional steps
When the flow executes
Then observation logs which branch was taken
And the condition that was evaluated

**Scenario: Context variable conditions**
Given context with {"is_premium_user": true}
And a step with condition: "{{is_premium_user}} == true"
When the flow executes
Then the step executes for premium users

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update src/turbulence/engine/executor.py with branching logic
- Update scenario models to support conditions
- Create src/turbulence/engine/conditions.py

**Must NOT Change:**
- Action runner implementations
- Core scenario structure (extend, don't replace)
- Artifact storage format

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(engine): add conditional branching for dynamic workflow paths

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify branch logic
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Infinite loop prevention verified

## 7. Resources
- [State Machine Patterns](https://en.wikipedia.org/wiki/Finite-state_machine)

## Example Branching Flow
```yaml
id: checkout-with-retry-logic

flow:
  - name: attempt_payment
    type: http
    service: payments
    method: POST
    path: /charges
    json:
      amount: "{{total}}"
      payment_method: "{{payment_method}}"
    extract:
      payment_status: "$.status"
      decline_reason: "$.decline_reason"

  - name: handle_payment_result
    type: branch
    condition: "{{payment_status}} == 'declined'"
    if_true:
      - name: check_decline_reason
        type: branch
        condition: "{{decline_reason}} == 'insufficient_funds'"
        if_true:
          - name: try_alternative_payment
            type: http
            service: payments
            method: POST
            path: /charges
            json:
              amount: "{{total}}"
              payment_method: "backup_card"
        if_false:
          - name: notify_customer
            type: http
            service: notifications
            method: POST
            path: /send
            json:
              type: "payment_failed"
              reason: "{{decline_reason}}"
    if_false:
      - name: confirm_order
        type: http
        service: api
        method: POST
        path: /orders/{{cart_id}}/confirm
```
