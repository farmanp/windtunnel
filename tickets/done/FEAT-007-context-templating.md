# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want {{variable}} templating so that values flow between workflow steps
So that I can chain data from responses into subsequent requests dynamically

**Success Looks Like:**
A context engine that substitutes template variables in paths, bodies, and headers using Jinja2 syntax, populated from entry data and extraction results.

## 2. Context & Constraints (Required)
**Background:**
Workflow steps need to reference values from previous steps—IDs from creation responses, tokens from auth flows, computed values from extractions. The context templating engine provides this data flow while maintaining type fidelity where possible.

**Scope:**
- **In Scope:** Per-instance context dictionary, Jinja2 template substitution, nested access syntax, entry block population, extract result population
- **Out of Scope:** Custom filters/functions (FEAT-014), loops/conditionals in templates, environment variable access

**Constraints:**
- Must use Jinja2 for template rendering
- Must support nested access: {{entry.seed_data.cart_items}}
- Must preserve types when possible (numbers stay numbers)
- Must fail clearly on missing variables

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Substitute simple variable**
Given context with {"user_id": "usr_123"}
And a path template "/users/{{user_id}}"
When the template renders
Then the result is "/users/usr_123"

**Scenario: Substitute in JSON body**
Given context with {"cart_id": "cart_456", "amount": 100}
And a body template {"cart": "{{cart_id}}", "total": "{{amount}}"}
When the template renders
Then the result is {"cart": "cart_456", "total": 100}

**Scenario: Nested access**
Given context with {"entry": {"seed_data": {"customer": "cust_789"}}}
And a template "{{entry.seed_data.customer}}"
When the template renders
Then the result is "cust_789"

**Scenario: Populate from entry block**
Given a scenario with entry.seed_data.email: "test@example.com"
When a new instance starts
Then context["entry"]["seed_data"]["email"] equals "test@example.com"

**Scenario: Populate from extract results**
Given an HTTP action with extract: {order_id: "$.id"}
And the response contains {"id": "ord_001"}
When extraction completes
Then context["order_id"] equals "ord_001"

**Scenario: Missing variable error**
Given context without "missing_key"
And a template "{{missing_key}}"
When the template renders
Then a clear error is raised indicating "missing_key" not found

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/engine/context.py
- Create src/windtunnel/engine/template.py
- Integrate with action runners to provide context

**Must NOT Change:**
- Action runner implementations
- Config loading

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(engine): add context templating engine with Jinja2

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written for substitution scenarios
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Type preservation verified

## 7. Resources
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
