# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want HTTP actions to make requests and extract values from responses
So that my workflow scenarios can interact with services and chain data between steps

**Success Looks Like:**
HTTP requests executed asynchronously with full observability, supporting method/path/headers/body configuration and JSONPath extraction into context.

## 2. Context & Constraints (Required)
**Background:**
HTTP actions are the primary way Windtunnel interacts with services. Each action must capture complete request/response data for debugging and replay, while extracting specified values into the workflow context for use in subsequent steps.

**Scope:**
- **In Scope:** Async HTTP execution, all HTTP methods, headers/query/json body, JSONPath extraction, Observation recording
- **Out of Scope:** Retry logic (FEAT-012), timeout injection (FEAT-012), parallel requests within a single action

**Constraints:**
- Must use httpx async client for HTTP requests
- Must use jsonpath-ng for extraction
- Observation must capture: ok, status_code, latency_ms, headers, body, errors

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Execute GET request**
Given an HTTP action with method GET and path /users/123
When the action executes
Then a GET request is made to service_base_url/users/123
And the response is captured in an Observation

**Scenario: Execute POST with JSON body**
Given an HTTP action with method POST and json body {"name": "test"}
When the action executes
Then the request includes Content-Type: application/json
And the body is serialized correctly

**Scenario: Extract values with JSONPath**
Given an HTTP action with extract: {user_id: "$.id", email: "$.email"}
When the response body is {"id": 123, "email": "test@example.com"}
Then context["user_id"] equals 123
And context["email"] equals "test@example.com"

**Scenario: Record latency**
Given an HTTP action that takes 150ms to complete
When the action executes
Then observation.latency_ms is approximately 150

**Scenario: Handle HTTP errors**
Given an HTTP action targeting a service that returns 500
When the action executes
Then observation.ok is false
And observation.status_code is 500
And observation.errors contains the error details

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Create src/windtunnel/actions/__init__.py
- Create src/windtunnel/actions/http.py
- Create src/windtunnel/actions/base.py with ActionRunner protocol
- Create src/windtunnel/models/observation.py

**Must NOT Change:**
- Config loading from FEAT-002/FEAT-003
- CLI structure from FEAT-001

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(actions): add HTTP action runner with JSONPath extraction

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests written with mocked HTTP responses
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Async execution verified with pytest-asyncio

## 7. Resources
- [httpx Documentation](https://www.python-httpx.org/)
- [jsonpath-ng Documentation](https://github.com/h2non/jsonpath-ng)
