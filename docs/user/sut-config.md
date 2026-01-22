# SUT Configuration

The System Under Test (SUT) config describes the services Windtunnel will call.
It is required for every run.

## Schema Overview

```yaml
name: ecommerce-checkout

default_headers:
  X-Run-ID: "{{run_id}}"
  X-Correlation-ID: "{{correlation_id}}"
  Content-Type: "application/json"

services:
  api:
    base_url: "https://api.example.com"
    timeout_seconds: 30
  payments:
    base_url: "https://payments.example.com"
    headers:
      X-API-Key: "your-api-key"
    timeout_seconds: 10
```

## Fields

- `name` (required): Display name for the system under test.
- `default_headers` (optional): Headers merged into every request. Templates are
  rendered at runtime using the workflow context.
- `services` (required): Map of service names to service configs.

### Service Config

- `base_url` (required): Base URL for the service. A trailing slash is stripped.
- `headers` (optional): Service-specific headers that override defaults.
- `timeout_seconds` (optional): Per-service request timeout (default: 30.0).

## Header Merge Order

When a request executes, headers are merged in this order:

1. `default_headers`
2. `services.<service>.headers`
3. Action-level `headers`

Later values override earlier values.
