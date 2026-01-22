# Testing E-commerce Checkout Flows

This guide walks you through using Turbulence to test e-commerce checkout flows, from simple happy-path validation to load testing with thousands of concurrent users.

## What You'll Learn

- How to model a checkout flow as a Turbulence scenario
- Extracting data between steps (product IDs, cart IDs, order IDs)
- Validating responses with assertions
- Running load tests and analyzing results
- Common patterns and best practices

## Prerequisites

- Turbulence installed (`pip install turbulence`)
- An e-commerce API to test (or use httpbin.org to follow along)

## The Checkout Flow

A typical e-commerce checkout has these steps:

```
Browse Products → Add to Cart → View Cart → Checkout → Payment → Confirm Order
```

Each step depends on data from the previous one:
- **Add to Cart** needs a `product_id` from Browse
- **Checkout** needs a `cart_id` from Add to Cart
- **Payment** needs an `order_id` from Checkout
- **Confirm** verifies the `order_id` has status "confirmed"

Turbulence handles this data flow through **extraction** and **templating**.

## Step 1: Configure Your System Under Test

Create a SUT configuration file that defines your API endpoints:

```yaml
# sut.yaml
name: My E-commerce API

default_headers:
  Accept: application/json
  Content-Type: application/json
  # Correlation ID for tracing requests through your system
  X-Correlation-ID: "{{correlation_id}}"

services:
  api:
    base_url: "https://api.mystore.com"
    timeout_seconds: 30

  # If payment is a separate service
  payments:
    base_url: "https://payments.mystore.com"
    timeout_seconds: 60
    headers:
      Authorization: "Bearer {{env.PAYMENT_API_KEY}}"
```

**Key points:**
- `{{correlation_id}}` is auto-generated per instance for request tracing
- Define separate services if your APIs are on different hosts
- Service-specific headers override default headers

## Step 2: Create the Checkout Scenario

Create a scenario file that defines the checkout flow:

```yaml
# scenarios/checkout.yaml
id: checkout-happy-path
description: Complete checkout flow from browse to order confirmation

flow:
  # Step 1: Browse products
  - type: http
    name: browse_products
    service: api
    method: GET
    path: /api/v1/products
    query:
      category: electronics
      limit: "10"
    extract:
      product_id: "$.products[0].id"
      product_price: "$.products[0].price"

  - type: assert
    name: verify_products_returned
    expect:
      status_code: 200

  # Step 2: Add to cart
  - type: http
    name: add_to_cart
    service: api
    method: POST
    path: /api/v1/cart/items
    body:
      product_id: "{{product_id}}"
      quantity: 1
    extract:
      cart_id: "$.cart_id"

  - type: assert
    name: verify_item_added
    expect:
      status_code: 201

  # Step 3: Start checkout
  - type: http
    name: start_checkout
    service: api
    method: POST
    path: /api/v1/checkout
    body:
      cart_id: "{{cart_id}}"
      shipping_address:
        street: "123 Test Street"
        city: "Testville"
        zip: "12345"
    extract:
      order_id: "$.order_id"
      order_total: "$.total"

  - type: assert
    name: verify_checkout_started
    expect:
      jsonpath: "$.status"
      equals: "pending_payment"

  # Step 4: Submit payment
  - type: http
    name: submit_payment
    service: payments
    method: POST
    path: /api/v1/charges
    body:
      order_id: "{{order_id}}"
      amount: "{{order_total}}"
      payment_method:
        type: card
        token: "tok_test_visa"
    extract:
      payment_id: "$.payment_id"

  - type: assert
    name: verify_payment_success
    expect:
      jsonpath: "$.status"
      equals: "success"

  # Step 5: Verify order confirmation
  - type: http
    name: get_order
    service: api
    method: GET
    path: "/api/v1/orders/{{order_id}}"

# Final assertions run after all flow steps complete
assertions:
  - name: order_is_confirmed
    expect:
      jsonpath: "$.status"
      equals: "confirmed"

  - name: payment_recorded
    expect:
      jsonpath: "$.payment.status"
      equals: "captured"

# Stop immediately if any step fails
stop_when:
  any_action_fails: true
```

## Step 3: Run a Single Instance

Test your scenario with a single instance first:

```bash
turbulence run --sut sut.yaml --scenarios scenarios/ -n 1
```

You'll see output like:

```
Turbulence Run
  Run ID: run_20260122_143052
  Instances: 1
  Parallelism: 10

  Running instances ━━━━━━━━━━━━━━━━━━━━━━━━ 100% 1/1

Execution Summary
  Total instances: 1
  Passed: 1
  Failed: 0
  Pass rate: 100.0%
  Duration: 1250ms
```

## Step 4: Debug Failures with Replay

If an instance fails, use replay to debug:

```bash
# List instances in a run
ls runs/<run_id>/instances/

# Replay a specific instance
turbulence replay --run-id <run_id> --instance-id <instance_id>
```

Replay shows you exactly what happened at each step, including:
- Request sent (method, URL, headers, body)
- Response received (status, headers, body)
- Values extracted
- Assertions evaluated

## Step 5: Run a Load Test

Once the happy path works, scale up:

```bash
# 100 concurrent checkouts
turbulence run --sut sut.yaml --scenarios scenarios/ -n 100 -p 20

# 1000 checkouts with 50 concurrent
turbulence run --sut sut.yaml --scenarios scenarios/ -n 1000 -p 50
```

**Parameters:**
- `-n` / `--n`: Total number of instances to run
- `-p` / `--parallel`: Maximum concurrent instances

## Step 6: Generate Reports

Generate an HTML report for analysis:

```bash
turbulence report --run-id <run_id>
```

The report shows:
- Pass/fail rates by scenario
- Latency distribution per step
- Error breakdown
- Individual instance details

## Common Patterns

### Waiting for Async Operations

If your payment processing is async, use the `wait` action:

```yaml
- type: wait
  name: wait_for_payment
  service: api
  path: "/api/v1/payments/{{payment_id}}"
  interval_seconds: 1
  timeout_seconds: 30
  expect:
    jsonpath: "$.status"
    equals: "completed"
```

### Validating Response Schema

Ensure responses match expected structure:

```yaml
assertions:
  - name: order_schema_valid
    expect:
      schema:
        type: object
        required:
          - order_id
          - status
          - items
          - total
        properties:
          order_id:
            type: string
          status:
            type: string
            enum: ["pending", "confirmed", "shipped"]
          total:
            type: number
            minimum: 0
```

### Using Entry Data for Variation

Provide different data per instance:

```yaml
entry:
  seed_data:
    customer_type: "premium"
    discount_code: "SAVE10"

flow:
  - type: http
    name: apply_discount
    service: api
    method: POST
    path: /api/v1/cart/discount
    body:
      code: "{{entry.seed_data.discount_code}}"
```

### Multiple Assertions Per Step

Check multiple conditions:

```yaml
- type: assert
  name: verify_cart_correct
  expect:
    status_code: 200

- type: assert
  name: verify_item_count
  expect:
    jsonpath: "$.items.length"
    expression: "value >= 1"

- type: assert
  name: verify_total_positive
  expect:
    jsonpath: "$.total"
    expression: "value > 0"
```

### Testing with Authentication

Add auth token flow before checkout:

```yaml
flow:
  # Login first
  - type: http
    name: login
    service: api
    method: POST
    path: /api/v1/auth/login
    body:
      email: "test@example.com"
      password: "testpass123"
    extract:
      auth_token: "$.access_token"

  # Use token in subsequent requests
  - type: http
    name: browse_products
    service: api
    method: GET
    path: /api/v1/products
    headers:
      Authorization: "Bearer {{auth_token}}"
    extract:
      product_id: "$.products[0].id"
```

## Try It Now with httpbin.org

Don't have an API ready? Test the concepts with httpbin.org:

**1. Create SUT config (`httpbin-sut.yaml`):**

```yaml
name: httpbin-demo
services:
  httpbin:
    base_url: "https://httpbin.org"
```

**2. Create scenario (`scenarios/checkout-demo.yaml`):**

```yaml
id: checkout-demo
description: Simulated checkout using httpbin echo

flow:
  - type: http
    name: browse_products
    service: httpbin
    method: GET
    path: /anything/products
    query:
      category: electronics
    extract:
      category: "$.args.category"

  - type: assert
    name: verify_browse
    expect:
      status_code: 200

  - type: http
    name: add_to_cart
    service: httpbin
    method: POST
    path: /anything/cart
    body:
      product_id: "prod_12345"
      quantity: 1
    extract:
      product_id: "$.json.product_id"

  - type: assert
    name: verify_cart
    expect:
      status_code: 200

  - type: http
    name: checkout
    service: httpbin
    method: POST
    path: /anything/checkout
    body:
      product_id: "{{product_id}}"
      order_id: "order_abc123"
      status: "confirmed"

assertions:
  - name: order_confirmed
    expect:
      jsonpath: "$.json.status"
      equals: "confirmed"
```

**3. Run it:**

```bash
turbulence run --sut httpbin-sut.yaml --scenarios scenarios/ -n 10 -p 5
```

## Best Practices

1. **Start small** - Test with 1 instance before scaling up
2. **Use correlation IDs** - Add `X-Correlation-ID: "{{correlation_id}}"` for tracing
3. **Fail fast** - Use `stop_when.any_action_fails: true` to catch issues early
4. **Validate schemas** - Don't just check status codes, validate response structure
5. **Organize scenarios** - Put related scenarios in the same directory
6. **Name steps clearly** - `add_to_cart` is better than `step_2`
7. **Extract what you need** - Only extract values you'll use later

## Troubleshooting

### "Service not found" error
Check that your scenario's `service` field matches a key in your SUT config's `services` section.

### Extraction returns null
- Verify your JSONPath expression against the actual response
- Use replay to see what the API returned
- Check for typos in the path

### Assertions fail unexpectedly
- Check the assertion's `jsonpath` against the response
- Use `expression` for complex conditions: `expression: "value > 0 and value < 100"`

### Timeouts
- Increase `timeout_seconds` in the SUT config
- For wait actions, increase `timeout_seconds` on the action itself

## Next Steps

- [Scenario Authoring Reference](../scenario-authoring.md) - Full syntax documentation
- [Templating Guide](../templating.md) - Advanced variable usage
- [Turbulence (Fault Injection)](../turbulence.md) - Add chaos to your tests
- [Reporting](../reporting.md) - Understanding reports
