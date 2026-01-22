# Spike: Python DSL for Scenario Definition

## Research Question
How can we provide a type-safe, developer-friendly DSL for defining Turbulence scenarios to replace or augment the current YAML configuration?

## DSL Prototypes

### Option A: Fluent API (Builder Pattern)
Concise and readable, inspired by libraries like `requests` or `Pytest`.

```python
from turbulence import Scenario, Http, Wait, Assert

checkout = (
    Scenario("ecommerce-checkout")
    .description("Complete checkout flow")
    .step(
        Http.post("/api/login")
        .name("login")
        .body({"user": "test", "pass": "secret"})
        .extract("token", "$.token")
    )
    .step(
        Http.get("/api/products")
        .name("get_products")
        .headers({"Authorization": "Bearer {{token}}"})
    )
    .step(
        Wait.for_path("/api/order/123")
        .expect(status_code=200, jsonpath="$.status", equals="shipped")
    )
)
```

### Option B: Class-based (Locust Style)
Familiar to Python developers, provides excellent IDE support and logical grouping.

```python
from turbulence import Scenario, HttpAction, WaitAction, AssertAction

class CheckoutFlow(Scenario):
    id = "ecommerce-checkout"
    description = "Complete checkout flow"

    flow = [
        HttpAction(
            name="login",
            method="POST",
            path="/api/login",
            body={"user": "test", "pass": "secret"},
            extract={"token": "$.token"}
        ),
        HttpAction(
            name="get_products",
            path="/api/products",
            headers={"Authorization": "Bearer {{token}}"}
        ),
        WaitAction(
            name="wait_for_shipping",
            path="/api/order/123",
            expect={"status_code": 200, "jsonpath": "$.status", "equals": "shipped"}
        )
    ]
```

### Option C: Decorator-based (Procedural)
Uses function syntax, potentially allows using native Python `if/else` instead of `BranchAction`.

```python
from turbulence import scenario, http, wait, branch

@scenario("ecommerce-checkout")
def checkout_flow(ctx):
    """Complete checkout flow"""
    
    # Step 1: Login
    resp = http.post("/api/login", json={"user": "test", "pass": "secret"})
    ctx.token = resp.body.token
    
    # Step 2: Get Products
    http.get("/api/products", headers={"Authorization": f"Bearer {ctx.token}"})
    
    # Step 3: Conditional Branching using native Python!
    if ctx.is_premium:
        http.get("/api/premium-deals")
    else:
        http.get("/api/standard-deals")
```

## Comparative Analysis

| Feature | Option A (Fluent) | Option B (Class) | Option C (Decorator) |
|---------|-------------------|------------------|----------------------|
| **IDE Support** | High (method chaining) | Excellent (class attributes) | Good (function args) |
| **Readability** | High (reads like a script) | Medium (declarative list) | High (procedural) |
| **Complexity** | Low | Low | High (requires AST transformation or proxy objects) |
| **Branching** | Explicit (`.branch()`) | Explicit (`BranchAction()`) | Native (`if/else`) |
| **Integration** | Direct to Models | Direct to Models | Complex |

## Recommendation: Option B (Class-based) with a dash of Option A

The **Class-based approach** is the most robust because it maps 1:1 to our existing Pydantic models. It is easy to implement, provides immediate IDE benefits (autocompletion, validation), and handles large scenarios gracefully.

To improve readability, we can provide **Builder helpers** (Option A) that can be used within the `flow` list.

## Implementation Plan (FEAT-033)

1.  **Core DSL Package:** Create `src/turbulence/dsl/` with base classes.
2.  **Model Integration:** Ensure DSL classes can be exported to standard `Scenario` Pydantic models.
3.  **Discovery:** Update `ScenarioLoader` to import `.py` files and discover `Scenario` subclasses.
4.  **CLI Support:** Add support for `--scenarios scenarios/` where the directory contains both `.yaml` and `.py` files.

## Security Considerations
Executing Python code from scenarios introduces risk if scenarios are user-provided. 
- **Sandboxing:** We should investigate `RestrictedPython` if we choose Option C.
- **Data-only:** For Option B, we can treat the classes as static configuration, avoiding execution of arbitrary logic during "loading".