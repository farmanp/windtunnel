# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want JSON Schema validation in assertions
So that I can verify response structures match expected contracts

**Success Looks Like:**
Schema validation expectation type that validates responses against JSON Schema with clear error messages on validation failure.

## 2. Context & Constraints (Required)
**Background:**
Beyond checking specific values, developers need to verify that API responses conform to expected schemas. This catches contract violations like missing fields, wrong types, or unexpected structure changes that value-based assertions might miss.

**Scope:**
- **In Scope:** Schema expectation type, inline schema definition, $ref to external files, clear validation error messages
- **Out of Scope:** OpenAPI/Swagger integration, schema generation, schema evolution tracking

**Constraints:**
- Must use jsonschema library for validation
- Must support JSON Schema draft-07 or later
- Error messages must identify the failing path and constraint
- $ref must resolve relative to scenario file location

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Validate against inline schema**
Given an assertion with inline schema {"type": "object", "required": ["id", "status"]}
And the response is {"id": 123, "status": "active"}
When the assertion evaluates
Then validation passes

**Scenario: Fail on missing required field**
Given a schema requiring ["id", "status", "timestamp"]
And the response is {"id": 123, "status": "active"}
When the assertion evaluates
Then validation fails
And error indicates "timestamp" is missing

**Scenario: Fail on wrong type**
Given a schema with {"properties": {"count": {"type": "integer"}}}
And the response is {"count": "five"}
When the assertion evaluates
Then validation fails
And error indicates type mismatch at "count"

**Scenario: Reference external schema file**
Given an assertion with schema: {$ref: "schemas/order.json"}
And schemas/order.json exists relative to scenario file
When the assertion evaluates
Then the external schema is loaded and used

**Scenario: Nested object validation**
Given a schema validating nested structure
And the response has invalid data three levels deep
When validation fails
Then the error path shows the full JSON path to the failure

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update src/windtunnel/actions/assert_.py to add schema validation
- Create src/windtunnel/validation/schema.py
- Add jsonschema to dependencies

**Must NOT Change:**
- Existing assertion types
- Action runner protocol

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(assertions): add JSON Schema validation expectation

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests cover pass/fail scenarios
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Error messages are actionable

## 7. Resources
- [jsonschema Python Library](https://python-jsonschema.readthedocs.io/)
- [JSON Schema Specification](https://json-schema.org/)

## Example Schema Assertion
```yaml
assertions:
  - name: order_response_valid
    type: assert
    expect:
      schema:
        type: object
        required: [id, status, items, total]
        properties:
          id:
            type: string
            pattern: "^ord_[a-z0-9]+$"
          status:
            type: string
            enum: [pending, confirmed, shipped, delivered]
          items:
            type: array
            minItems: 1
          total:
            type: number
            minimum: 0
```
