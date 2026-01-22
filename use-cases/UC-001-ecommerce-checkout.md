# UC-001: E-commerce Checkout Flow

## Overview

| Field | Value |
|-------|-------|
| **Use Case ID** | UC-001 |
| **Title** | E-commerce Checkout Flow |
| **Category** | Sequential HTTP workflow with data extraction |
| **Complexity** | Medium |
| **Current Support** | Full |

## 1. Scenario Description

### Business Context
An e-commerce platform needs to validate that the checkout flow performs correctly under load. The flow represents a typical user journey from browsing products to completing a purchase.

### User Journey
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browse    │───▶│  Add to     │───▶│   Start     │───▶│   Submit    │
│  Products   │    │    Cart     │    │  Checkout   │    │   Payment   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  GET /products     POST /cart/items   POST /checkout    POST /payments
  Extract: id       Extract: cart_id   Extract: order_id  Verify: success
```

### What We're Testing
1. **Functional correctness** - Each step succeeds and returns expected data
2. **Data flow** - Values extracted from one step feed into the next
3. **Latency distribution** - How long does the full checkout take?
4. **Error rates under load** - What breaks when we scale to 1000 concurrent users?
5. **Consistency** - Cart totals, inventory, order state remain correct

### Real-World Concerns
- **Inventory race conditions** - Two users checkout same last item
- **Cart expiration** - Session timeout during checkout
- **Payment failures** - 3rd party payment gateway timeouts
- **Price consistency** - Price changes between cart and checkout

## 2. Turbulence Solution

### How It Maps to Turbulence Concepts

| Checkout Step | Turbulence Action | Key Feature Used |
|---------------|-------------------|------------------|
| Browse products | `http` GET | Basic request |
| Select product | `http` GET + `extract` | JSONPath extraction |
| Add to cart | `http` POST + `extract` | Request body templating |
| View cart | `http` GET + `assert` | Response validation |
| Checkout | `http` POST + `extract` | Chained extraction |
| Payment | `http` POST + `assert` | Final validation |
| Verify order | `http` GET + `assert` (schema) | JSON Schema validation |

### Context Flow
```yaml
# Data flows through the scenario via extraction
step_1: GET /products → extract product_id
step_2: POST /cart (product_id) → extract cart_id
step_3: POST /checkout (cart_id) → extract order_id
step_4: POST /payments (order_id) → extract payment_id
step_5: GET /orders/{order_id} → assert status = "confirmed"
```

## 3. Sample Implementation

### SUT Configuration
See: `use-cases/sut/mock-ecommerce.yaml`

### Scenario File
See: `use-cases/scenarios/ecommerce-checkout.yaml`

### Running the Test
```bash
# Single instance (debug)
turbulence run \
  --sut use-cases/sut/mock-ecommerce.yaml \
  --scenarios use-cases/scenarios/ \
  -n 1

# Load test (1000 users, 50 concurrent)
turbulence run \
  --sut use-cases/sut/mock-ecommerce.yaml \
  --scenarios use-cases/scenarios/ \
  -n 1000 \
  -p 50

# Generate report
turbulence report --run-id <run_id>
```

### Actual Test Results (httpbin.org)
Tested against httpbin.org using the echo variant scenario:

```
# Single instance
turbulence run --sut use-cases/sut/httpbin.yaml \
  --scenarios use-cases/scenarios/httpbin-test/ -n 1

Execution Summary
  Total instances: 1
  Passed: 1
  Duration: 1043ms

# 10 instances, parallelism 5
turbulence run --sut use-cases/sut/httpbin.yaml \
  --scenarios use-cases/scenarios/httpbin-test/ -n 10 -p 5

Execution Summary
  Total instances: 10
  Passed: 10
  Pass rate: 100.0%
  Duration: 5103ms
```

## 4. Expected Observations

### Happy Path Metrics
| Step | Expected Latency | Success Criteria |
|------|------------------|------------------|
| Browse products | < 200ms | 200 OK, non-empty array |
| Add to cart | < 300ms | 201 Created, cart_id present |
| Start checkout | < 500ms | 200 OK, order_id present |
| Submit payment | < 1000ms | 200 OK, status = "success" |
| Verify order | < 200ms | 200 OK, status = "confirmed" |

### Failure Modes to Detect
| Failure | How Detected | Turbulence Feature |
|---------|--------------|-------------------|
| Product not found | 404 response | `assert` status_code |
| Cart expired | 410 Gone | `assert` status_code |
| Payment declined | status != "success" | `assert` jsonpath |
| Inventory exhausted | 409 Conflict | `assert` status_code |
| Order not found | 404 response | `assert` status_code |

## 5. Gaps Identified

### Works Well
- [x] Sequential HTTP flow with extraction
- [x] JSONPath extraction from responses
- [x] Template variables in requests
- [x] Response assertions (status, body)
- [x] JSON Schema validation
- [x] Parallel execution of many instances

### Awkward / Missing

| Gap | Severity | Workaround | Feature Request? |
|-----|----------|------------|------------------|
| Assertions must be separate actions | Low | Add `assert` step after each `http` | Consider inline assert option |
| No built-in retry on transient failures | Medium | Manual retry logic in scenario | FEAT: Retry policies |
| Can't branch on response (if payment fails, retry) | Medium | Separate scenarios | FEAT-019: Branching |
| No test data generation (random emails, etc.) | Low | Pre-generate in entry data | FEAT-017: Variation |
| Can't share cart across scenarios | Low | Single scenario design | N/A (by design) |
| `--scenarios` takes directory, not file | Low | Organize scenarios in folders | CLI enhancement |

### Questions Raised
1. **Entry data** - How do we vary user credentials per instance?
2. **Cleanup** - Should we delete test orders after run?
3. **Idempotency** - How to test duplicate payment protection?

## 6. Variations to Test

### Variation A: Guest Checkout (No Auth)
Same flow but without authentication headers.

### Variation B: Authenticated User
Add login step, extract token, use in subsequent requests.

### Variation C: Multi-Item Cart
Add multiple products before checkout.

### Variation D: Payment Failure Recovery
Payment fails → retry → succeeds (requires branching - FEAT-019).

## 7. Verdict

### Current Turbulence Rating: **Good Fit**

| Aspect | Rating | Notes |
|--------|--------|-------|
| Expressiveness | 4/5 | YAML captures flow well |
| Ease of use | 4/5 | Extraction syntax clear |
| Assertions | 4/5 | JSONPath + Schema covers most cases |
| Load testing | 5/5 | Parallel execution works well |
| Debugging | 3/5 | Replay helps, but need better error context |
| Realism | 3/5 | Need variation engine for realistic data |

### Recommendation
E-commerce checkout is a **primary use case** for Turbulence. Current capabilities handle it well. Priority enhancements:
1. FEAT-017 (Variation) - For realistic test data
2. FEAT-019 (Branching) - For error recovery flows
3. Better error messages showing which step failed and why

## 8. Related Resources

- Scenario file (ideal): `use-cases/scenarios/ecommerce-checkout.yaml`
- Scenario file (httpbin): `use-cases/scenarios/httpbin-test/ecommerce-checkout-httpbin.yaml`
- SUT config (mock): `use-cases/sut/mock-ecommerce.yaml`
- SUT config (httpbin): `use-cases/sut/httpbin.yaml`
