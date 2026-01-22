# Research: Python DSL for Windtunnel

**Date:** 2026-01-21
**Related Ticket:** SPIKE-002

## Objective
To identify the optimal Python Domain Specific Language (DSL) pattern for Windtunnel. The goal is to improve developer experience (IDE support, type safety) while generating the underlying `Scenario` Pydantic models used by the existing execution engine.

**Constraint:** The DSL must produce static configuration (the `Scenario` model) to be executed by the existing async engine. It should not require a rewrite of the execution engine to support imperative, blocking Python code (like Locust).

---

## Option 1: The Fluent Builder

A method-chaining approach where operations return the builder instance.

### Concept
```python
from windtunnel import Scenario, Http, Wait

# Definition
checkout_flow = (
    Scenario("checkout_flow")
    .with_description("User buys an item")
    .step(
        Http.get("get_products")
        .url("/api/products")
        .expect_status(200)
        .extract("first_product_id", "$.products[0].id")
    )
    .step(
        Wait.for_duration(seconds=1)
    )
    .step(
        Http.post("add_to_cart")
        .url("/api/cart")
        .json({"product_id": "${first_product_id}"})
    )
)
```

### Analysis
*   **Pros:**
    *   **Immutability:** Easy to implement as immutable transformations.
    *   **Discoverability:** IDE autocomplete (`.`) guides the user to the next valid method (e.g., typing `.expect` after `.url`).
    *   **Structure:** Visually resembles the YAML structure, making migration easy.
*   **Cons:**
    *   **Verbosity:** Can get visually cluttered with deeply nested parenthesis.
    *   **Variables:** "Programming in strings" (e.g., `"${first_product_id}"`) is still required unless we build a complex symbol reference system.

---

## Option 2: The Imperative Generator (Locust Style)

Users write a class or function that *looks* like it's executing code, but it actually records operations to a registry.

### Concept
```python
from windtunnel import Scenario, task

class CheckoutScenario(Scenario):
    name = "checkout_flow"
    
    def definition(self):
        # This doesn't execute HTTP; it creates an HttpAction model and appends it to self.steps
        product_resp = self.http.get(
            name="get_products",
            url="/api/products"
        )
        
        # Validates response AND extracts data for the next step
        product_id = product_resp.json["products"][0]["id"]
        
        self.wait(seconds=1)
        
        self.http.post(
            name="add_to_cart",
            url="/api/cart",
            json={"product_id": product_id}  # Passing the reference, not the value
        )
```

### Analysis
*   **Pros:**
    *   **Familiarity:** Extremely intuitive for Python developers.
    *   **Variable Flow:** Solves the "stringly typed" variable problem. `product_id` can be a proxy object that resolves to a template string `{{ extracted.var_1 }}` at build time.
    *   **Cleanliness:** No visual noise from chaining or nesting.
*   **Cons:**
    *   **Magic:** Relies on "proxy objects" (lazy evaluation) to handle data flow between steps, which can be confusing to debug.
    *   **Control Flow Trap:** Users might try to use Python `if` statements or `for` loops. Since this runs at *definition time* (to generate the static config), loops would unroll immediately, which might not be what the user intends for a dynamic test.

---

## Option 3: The Context Manager

Using Python's `with` statement to define scope and hierarchy.

### Concept
```python
from windtunnel import Flow, actions

with Flow("checkout_flow") as flow:
    
    with flow.group("Browsing"):
        actions.http.get(
            name="get_products",
            url="/api/products"
        )
    
    actions.wait(seconds=1)
    
    # Late-binding variable reference
    actions.http.post(
        name="add_to_cart", 
        url="/api/cart",
        json={"product_id": flow.var("product_id")}
    )
```

### Analysis
*   **Pros:**
    *   **Hierarchy:** clearly visualizes groups or phases of a test.
    *   **Scope:** Good for defining shared configuration (headers, auth) that applies only within the `with` block.
*   **Cons:**
    *   **Variable Scope:** Doesn't inherently solve the data passing problem better than Option 1.
    *   **Indentation:** Can lead to "arrow code" (deep indentation) if nested heavily.

---

## Recommendation: Option 2 (The Imperative Generator)

**Why?**
The biggest pain point identified in the architecture review was **"Programming in strings"** (e.g., `expression: "response.id == context.id"`).

Option 2 offers the best path to solve this by using **Proxy Objects**.

**How it works (Simplified):**
1.  `self.http.get(...)` returns a `StepResultProxy`.
2.  `product_resp.json["id"]` returns a `DataReference` object, effectively `{{ step.get_products.json.id }}`.
3.  When `self.http.post(..., json=product_id)` is called, the DSL compiler sees the `DataReference` and serializes it into the correct internal template string.

**Result:**
The user gets full IDE autocomplete and type checking for data flow, but the output is still the safe, standard `Scenario` Pydantic model that the existing engine knows how to run.
