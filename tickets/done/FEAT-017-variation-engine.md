# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want automatic input variation
So that I can test edge cases without manually writing each scenario variant

**Success Looks Like:**
A deterministic variation engine that fuzzes parameters, toggles journey branches, and adds timing jitter while maintaining reproducibility via seed.

## 2. Context & Constraints (Required)
**Background:**
Manually writing scenarios for every edge case is impractical. The variation engine generates diverse inputs automatically—different quantities, locales, payment methods—to discover failures that only occur with specific combinations.

**Scope:**
- **In Scope:** Parameter fuzzing, journey toggles (apply coupon, remove item), timing jitter, seed-based reproducibility
- **Out of Scope:** ML-based variation, learned distributions, production traffic replay

**Constraints:**
- Must be deterministic given seed
- Variations defined in scenario file
- Must not increase scenario file complexity significantly
- Must log which variations were applied per instance

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Parameter fuzzing - quantities**
Given variation config: quantities: [1, 5, 10, 100]
When 100 instances run
Then cart quantities are distributed across specified values
And distribution is reproducible with same seed

**Scenario: Parameter fuzzing - locales**
Given variation config: locales: ["en-US", "es-MX", "fr-FR", "ja-JP"]
When 100 instances run
Then locales are distributed across specified values

**Scenario: Journey toggles**
Given variation config: toggles: [apply_coupon, remove_item, add_gift_wrap]
When 100 instances run
Then some instances apply coupon, some don't
And toggle combinations vary across instances

**Scenario: Timing jitter**
Given variation config: timing_jitter_ms: {min: 0, max: 500}
When steps execute
Then random delays are added between steps
And delays are deterministic per seed

**Scenario: Seed reproducibility**
Given seed 12345 and variation config
When the run executes twice
Then identical variations are applied to corresponding instances

**Scenario: Log applied variations**
Given a run with variations enabled
When an instance completes
Then its artifact includes which variations were applied
And this enables debugging why a specific instance failed

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/turbulence/variation/__init__.py
- Create src/turbulence/variation/engine.py
- Create src/turbulence/variation/config.py
- Integrate variation with instance creation

**Must NOT Change:**
- Core scenario structure
- Action runner implementations
- Artifact storage format (extend, don't modify)

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(variation): add deterministic variation engine for input fuzzing

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify determinism with seeds
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Variation distribution is reasonable

## 7. Resources
- [Random Seed Documentation](https://docs.python.org/3/library/random.html#random.seed)

## Example Variation Config
```yaml
id: checkout-with-variations

variation:
  parameters:
    cart_quantity:
      type: choice
      values: [1, 2, 5, 10, 50]
    locale:
      type: choice
      values: ["en-US", "es-MX", "fr-FR"]
    payment_method:
      type: choice
      values: ["credit_card", "paypal", "apple_pay"]

  toggles:
    - name: apply_coupon
      probability: 0.3
    - name: add_gift_wrap
      probability: 0.1
    - name: expedited_shipping
      probability: 0.2

  timing:
    jitter_ms:
      min: 0
      max: 500
    step_delay_ms:
      min: 100
      max: 1000

entry:
  seed_data:
    quantity: "{{variation.cart_quantity}}"
    locale: "{{variation.locale}}"
```
