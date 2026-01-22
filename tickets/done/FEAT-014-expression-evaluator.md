# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want custom Python expressions for complex assertions
So that I can validate conditions that can't be expressed with simple comparisons

**Success Looks Like:**
A safe expression sandbox that evaluates Python expressions with access to response data and context, supporting common operations without security risks.

## 2. Context & Constraints (Required)
**Background:**
Simple equals/contains assertions can't express conditions like "sum of all line items equals total" or "all items have status 'shipped'". Custom expressions enable these validations while maintaining security through sandboxing.

**Scope:**
- **In Scope:** Safe expression evaluation, access to body/headers/context, standard library functions (sum, len, min, max, any, all), list comprehensions
- **Out of Scope:** Full Python execution, imports, file access, network access, arbitrary code execution

**Constraints:**
- MUST NOT allow imports or module access
- MUST NOT allow file system operations
- MUST NOT allow network operations
- Must timeout on long-running expressions
- Must use AST-based sandboxing or RestrictedPython

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Sum expression**
Given body {"entries": [{"amount": 10}, {"amount": 20}, {"amount": 30}]}
And expression: sum([e['amount'] for e in body['entries']]) == 60
When the expression evaluates
Then the result is True

**Scenario: All items check**
Given body {"items": [{"status": "shipped"}, {"status": "shipped"}]}
And expression: all(i['status'] == 'shipped' for i in body['items'])
When the expression evaluates
Then the result is True

**Scenario: Access context variables**
Given context {"expected_total": 100}
And body {"total": 100}
And expression: body['total'] == context['expected_total']
When the expression evaluates
Then the result is True

**Scenario: Block import attempts**
Given expression: __import__('os').system('rm -rf /')
When the expression evaluates
Then execution is blocked
And a security error is raised

**Scenario: Block file access**
Given expression: open('/etc/passwd').read()
When the expression evaluates
Then execution is blocked

**Scenario: Timeout on infinite loop**
Given expression: [x for x in range(10**10)]
When the expression evaluates
Then execution times out
And an error indicates timeout

**Scenario: Access headers**
Given headers {"X-Request-ID": "req_123"}
And expression: headers['X-Request-ID'].startswith('req_')
When the expression evaluates
Then the result is True

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/evaluation/__init__.py
- Create src/windtunnel/evaluation/sandbox.py
- Update assertion evaluation to support expressions

**Must NOT Change:**
- Existing assertion types
- Core action logic

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(evaluation): add safe expression evaluator sandbox for assertions

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Security tests verify sandbox restrictions
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Timeout behavior verified

## 7. Resources
- [RestrictedPython](https://restrictedpython.readthedocs.io/)
- [AST Module](https://docs.python.org/3/library/ast.html)

## Example Expression Assertion
```yaml
assertions:
  - name: line_items_sum_to_total
    type: assert
    expect:
      expression: |
        sum(item['price'] * item['quantity'] for item in body['items']) == body['total']

  - name: all_payments_captured
    type: assert
    expect:
      expression: |
        all(p['status'] == 'captured' for p in body['payments'])

  - name: no_negative_balances
    type: assert
    expect:
      expression: |
        min(a['balance'] for a in body['accounts']) >= 0
```
