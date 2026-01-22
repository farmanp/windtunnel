# AI-Ready Spike Template

## 1. Research Question (Required)
**Question:**
How can we provide a type-safe, developer-friendly DSL for defining Turbulence scenarios to replace or augment the current YAML configuration?

**Context:**
The current YAML-based configuration allows "programming in strings" (e.g., Python expressions in `expect: expression: "..."`), which is brittle, error-prone, and lacks IDE support (linting, autocompletion, type checking). As scenarios grow in complexity, maintaining logic in YAML becomes difficult and risky. A Python-based DSL would leverage existing tooling and provide a better developer experience.

## 2. Scope & Timebox
**Timebox:** 2 days

**In Scope:**
- Evaluate Python-based DSL patterns (Fluent Interface vs. Builder Pattern vs. Declarative Classes).
- Prototype a simple scenario definition using the proposed DSL.
- Compare "Configuration as Code" (Python) vs. "Configuration as Data" (YAML) for this specific use case.
- Assess how a Python DSL integrates with the existing Pydantic models.
- Consider security implications of executing user code vs. parsing YAML.

**Out of Scope:**
- Full implementation of the DSL.
- Migration of existing scenarios.
- UI-based scenario builders.

## 3. Success Criteria (Required)
**Deliverables:**
- [ ] Comparison of 2-3 DSL approaches with code examples.
- [ ] Prototype code demonstrating a "Checkout" scenario in the new DSL.
- [ ] Analysis of IDE support (VS Code/PyCharm) for the prototype.
- [ ] Recommendation for the preferred approach.
- [ ] Plan for backward compatibility or migration.

## 4. Research Plan
1. **Pattern Analysis** (3 hours)
   - Review DSLs in other tools (e.g., Locust, K6 (JS), Airflow).
   - Identify which patterns (decorators, context managers, fluent APIs) fit Turbulence's architecture.

2. **Prototyping** (6 hours)
   - **Option A (Fluent):** `Scenario("checkout").step(Http.get(...)).expect(...)`
   - **Option B (Class-based):** `class Checkout(Scenario): ...`
   - **Option C (Decorator):** `@scenario("checkout") def flow(): ...`
   - Implement a small vertical slice of the engine to parse/execute each prototype.

3. **Evaluation** (3 hours)
   - Test "writeability": How easy is it to write?
   - Test "readability": Is the intent clear?
   - Test "tooling": Does `mypy` catch errors? Does "Go to Definition" work?

4. **Documentation** (4 hours)
   - Summarize findings.
   - Draft the design document for the selected approach.

## 5. Findings
*[To be filled after research]*

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| A: Fluent API | concise, reads like English | can be hard to type-check, rigid structure |
| B: Class-based (Locust style) | familiar to Python devs, very flexible | verbose, encourages arbitrary code execution |
| C: Declarative Context Managers | structural clarity, clean nesting | weird variable scoping rules |

**Recommendation:**
*[To be filled after research]*

## 6. Next Steps
*[To be filled after research]*
- [ ] Create FEAT ticket for DSL implementation
- [ ] Update documentation

## 7. Resources
- [Locust.io Documentation](https://docs.locust.io/)
- [Pydantic Models as Configuration](https://docs.pydantic.dev/)
- [Airflow DAGs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)
