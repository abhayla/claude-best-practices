---
name: trace-test
description: >
  Validate distributed traces with OpenTelemetry and Tracetest by asserting on spans
  instead of just HTTP responses — verify downstream calls, latency per span, error propagation,
  and correlation ID flow. Use when testing microservice integration and observability.
allowed-tools: "Bash Read Grep Glob Write Edit"
triggers:
  - trace test
  - tracetest
  - opentelemetry test
  - distributed trace
  - observability test
argument-hint: "<test-file|endpoint|all> [--verify-spans] [--verify-logs]"
version: "1.0.0"
type: workflow
---

# Trace-Based Testing

Assert on OpenTelemetry distributed traces to verify microservice behavior beyond HTTP responses.

**Arguments:** $ARGUMENTS

---

## Why Trace-Based Testing

Traditional API tests only verify the response. Trace-based tests verify the ENTIRE execution path:

| Traditional Test | Trace-Based Test |
|-----------------|-----------------|
| Response status = 200 | Response status = 200 |
| Response body matches schema | Response body matches schema |
| — | Database query executed in <100ms |
| — | Cache hit occurred (not miss) |
| — | Downstream service called with correct payload |
| — | No error spans in the trace |
| — | Correlation ID propagated through all services |

---

## STEP 1: Setup

### Prerequisites

```bash
# Install Tracetest CLI
curl -L https://raw.githubusercontent.com/kubeshop/tracetest/main/install-cli.sh | bash

# Or via npm
npm install -g @tracetest/cli
```

### Configure Tracetest Server

```yaml
# tracetest.yaml
postgres:
  host: localhost
  port: 5432
  dbname: tracetest

telemetry:
  exporters:
    collector:
      exporter:
        type: otlp
        otlp:
          endpoint: localhost:4317
```

### Instrument Your Services

```python
# FastAPI + OpenTelemetry auto-instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
HTTPXClientInstrumentor().instrument()
```

---

## STEP 2: Writing Trace Tests

### Basic: Verify Downstream Call Happened

```yaml
# tracetest/create-user.yaml
type: Test
spec:
  name: Create User - Verify Full Trace
  trigger:
    type: http
    httpRequest:
      url: http://localhost:8000/api/users
      method: POST
      headers:
        - key: Content-Type
          value: application/json
      body: '{"name": "Jane", "email": "jane@test.com"}'
  specs:
    # Verify HTTP response
    - selector: span[tracetest.span.type="http" name="POST /api/users"]
      assertions:
        - attr:http.status_code = 201

    # Verify database INSERT happened
    - selector: span[tracetest.span.type="database" name="INSERT users"]
      assertions:
        - attr:db.statement contains "INSERT INTO users"
        - attr:tracetest.span.duration < 100ms

    # Verify email service was called
    - selector: span[tracetest.span.type="http" name="POST email-service/send"]
      assertions:
        - attr:http.status_code = 200
        - attr:http.request.body contains "jane@test.com"

    # Verify no error spans in the entire trace
    - selector: span[status.code="ERROR"]
      assertions:
        - attr:tracetest.selected_spans.count = 0
```

### Verify Latency Per Span

```yaml
spec:
  name: Get Orders - Performance
  trigger:
    type: http
    httpRequest:
      url: http://localhost:8000/api/orders?user_id=123
      method: GET
  specs:
    # Total response time
    - selector: span[tracetest.span.type="http" name="GET /api/orders"]
      assertions:
        - attr:tracetest.span.duration < 500ms

    # Database query time
    - selector: span[tracetest.span.type="database" name="SELECT orders"]
      assertions:
        - attr:tracetest.span.duration < 50ms

    # Cache check
    - selector: span[name="redis GET orders:123"]
      assertions:
        - attr:tracetest.span.duration < 5ms
```

### Verify Error Propagation

```yaml
spec:
  name: Create Order - Payment Failure Propagation
  trigger:
    type: http
    httpRequest:
      url: http://localhost:8000/api/orders
      method: POST
      body: '{"items": [{"id": 1}], "payment_method": "invalid"}'
  specs:
    # API returns 422
    - selector: span[name="POST /api/orders"]
      assertions:
        - attr:http.status_code = 422

    # Payment service returned error
    - selector: span[name="POST payment-service/charge"]
      assertions:
        - attr:http.status_code = 400

    # Error is logged with correct correlation ID
    - selector: span[name="POST /api/orders"]
      assertions:
        - attr:app.error.type = "PaymentDeclined"
```

---

## STEP 3: Correlation ID Verification

Verify that trace/correlation IDs flow through the entire request chain:

```yaml
spec:
  name: Verify Correlation ID Propagation
  trigger:
    type: http
    httpRequest:
      url: http://localhost:8000/api/users/123
      method: GET
      headers:
        - key: X-Correlation-ID
          value: test-corr-001
  specs:
    # All spans share the same trace ID
    - selector: span[tracetest.span.type="general"]
      assertions:
        - attr:tracetest.span.type != ""  # All spans exist in trace

    # Downstream calls carry the correlation header
    - selector: span[tracetest.span.type="http"]
      assertions:
        - attr:http.request.header.x_correlation_id = "test-corr-001"
```

---

## STEP 4: Structured Log Assertions

Verify that structured logs are emitted with required fields:

```python
# Test that logs contain required fields during API execution
import json
import subprocess

def test_structured_logging():
    """Verify structured logs have required fields."""
    # Capture logs during test
    result = subprocess.run(
        ["curl", "-s", "http://localhost:8000/api/users/123"],
        capture_output=True
    )

    # Read captured logs (from stdout, file, or log aggregator)
    logs = read_captured_logs()

    for log_entry in logs:
        log = json.loads(log_entry)
        # Required fields
        assert "timestamp" in log, "Missing timestamp"
        assert "level" in log, "Missing log level"
        assert "service" in log, "Missing service name"
        assert "trace_id" in log, "Missing trace_id"
        assert "span_id" in log, "Missing span_id"
        assert "message" in log, "Missing message"

        # No PII in logs
        assert "password" not in log_entry.lower(), "PII detected in logs"
        assert "ssn" not in log_entry.lower(), "PII detected in logs"
```

### Golden Signals as Test Assertions

```yaml
# Assert on the four golden signals during integration tests
spec:
  name: Order API - Golden Signals
  specs:
    # Latency: p99 < 500ms
    - selector: span[name="POST /api/orders"]
      assertions:
        - attr:tracetest.span.duration < 500ms

    # Traffic: request was processed (span exists)
    - selector: span[name="POST /api/orders"]
      assertions:
        - attr:tracetest.selected_spans.count > 0

    # Errors: no 5xx errors
    - selector: span[name="POST /api/orders"]
      assertions:
        - attr:http.status_code < 500

    # Saturation: DB connection pool not exhausted
    - selector: span[tracetest.span.type="database"]
      assertions:
        - attr:db.connection_pool.active < 80
```

---

## STEP 5: Running Tests

```bash
# Run a single trace test
tracetest run test --file tracetest/create-user.yaml

# Run all trace tests in a directory
tracetest run test --file tracetest/

# Run with specific environment variables
tracetest run test --file tracetest/create-user.yaml \
  --vars BASE_URL=http://staging:8000

# Output results as JUnit XML for CI
tracetest run test --file tracetest/ --output junit > trace-results.xml
```

### CI Integration

```yaml
name: Trace-Based Tests
on: [push]
jobs:
  trace-test:
    runs-on: ubuntu-latest
    services:
      jaeger:
        image: jaegertracing/all-in-one:1.53
        ports: ['16686:16686', '4317:4317']
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d  # Start services with OTel instrumentation
      - run: |
          tracetest run test --file tracetest/ \
            --output junit > trace-results.xml
      - uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Trace Tests
          path: trace-results.xml
          reporter: java-junit
```

---

## STEP 6: Report

```
Trace Test Results: [PASSED / FAILED]
  Tests run: N
  Passed: P | Failed: F

  Per-test:
    create-user: PASSED
      ✓ HTTP 201 response
      ✓ DB INSERT < 100ms
      ✓ Email service called
      ✓ No error spans

    get-orders: FAILED
      ✓ HTTP 200 response
      ✗ DB query took 250ms (limit: 50ms)
      ✓ Cache hit verified
```

## RULES

- Instrument all services with OpenTelemetry before writing trace tests
- Assert on spans, not just responses — responses can be correct while internals are broken
- Always verify correlation ID propagation in distributed systems
- Use trace tests to catch N+1 queries (count database spans per request)
- Trace tests complement, not replace, unit and API tests
- Keep span assertions focused — test one behavior per test file
