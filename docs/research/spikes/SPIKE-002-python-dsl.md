# Spike Report: Python DSL for Scenario Definition

**Ticket:** SPIKE-002
**Status:** Decided
**Recommendation:** Option 2 (Imperative Generator / Proxy Pattern)

## 1. Executive Summary
After analyzing the architectural limitations of Windtunnel's current YAML-based configuration, we have decided to implement a Python-based DSL. This DSL will act as a "compiler" that generates the existing `Scenario` Pydantic models. We have selected the **Imperative Generator** pattern (similar to Locust or Pulumi) because it provides the most idiomatic developer experience while solving the core problem of "string-based programming" in configuration files.

## 2. Problem Statement
The current YAML architecture forces developers to:
1.  **Code in Strings:** Logic for assertions and data extraction is written as Python expressions inside YAML strings (e.g., `expression: "res.status == 200"`).
2.  **Sacrifice IDE Support:** There is no autocompletion, linting, or type checking for variable names, JSONPaths, or HTTP methods.
3.  **Manual Data Flow:** Passing data between steps (e.g., taking an ID from a POST response and using it in a GET request) requires manual template syntax (`{{ var }}`) which is prone to typos.

## 3. Options Evaluated

### Option 1: Fluent Builder
*   **Pattern:** `Scenario("name").step(Http.get(...)).step(...)`
*   **Pros:** Clean, predictable structure.
*   **Cons:** Does not solve the data-passing problem without returning to string-based templates.

### Option 2: Imperative Generator (Selected)
*   **Pattern:**
    ```python
    class MyScenario(Scenario):
        def flow(self):
            user = self.http.get("/me").json["username"]
            self.http.post("/profile", json={"name": user})
    ```
*   **Pros:**
    *   **Native Python Syntax:** Users use standard variables for data flow.
    *   **Proxy Pattern:** The `user` variable in the example above is a "Proxy Object" that automatically serializes to the internal Windtunnel template syntax (e.g., `{{ steps.get_me.json.username }}`).
    *   **Full IDE Support:** Type hints and "Go to Definition" work out of the box.
*   **Cons:** Requires a more complex DSL engine to handle lazy-evaluation of variables.

### Option 3: Declarative Context Managers
*   **Pattern:** `with Flow("name"): actions.http.get(...)`
*   **Pros:** Clear visual hierarchy of steps.
*   **Cons:** Verbose and doesn't solve the data flow issues as elegantly as Option 2.

## 4. Decision Rationale

### The "Proxy Object" Breakthrough
The deciding factor for Option 2 is the ability to use Python variables to represent "Future Data." 

When a user writes `id = response.json["id"]`, the DSL engine creates a `DataReference` object. When that `id` is later used in another step, the DSL engine knows exactly which step produced it and can generate the correct internal linkage. This eliminates an entire class of "typo" bugs common in YAML configurations.

### Preservation of the Async Engine
By choosing a "Generator" pattern, we ensure that the DSL only runs *once* at startup to build the execution plan. The actual heavy lifting of running thousands of concurrent requests remains with the high-performance `asyncio` engine. We get the developer benefits of Python without the performance bottleneck of running a full Python interpreter loop for every virtual user.

## 5. Implementation Strategy (Draft)
1.  **Phase 1: Proxy Core:** Implement the `ProxyObject` and `DataReference` classes that can track indexing and attribute access.
2.  **Phase 2: Step Registry:** Create the `Scenario` base class that records calls to `self.http`, `self.wait`, etc.
3.  **Phase 3: Serializer:** Create the logic to convert the recorded steps into the existing Pydantic `Scenario` model.
4.  **Phase 4: CLI Integration:** Add a `windtunnel run scenario.py` command that imports the file and executes the generator.

## 6. Risks & Mitigations
*   **Risk:** Users might try to use Python `if` or `for` logic that depends on runtime data.
*   **Mitigation:** The DSL will provide specific `flow.If()` and `flow.ForEach()` constructs that translate to the engine's branching logic, and documentation will clearly distinguish between "Definition Time" and "Run Time" logic.
