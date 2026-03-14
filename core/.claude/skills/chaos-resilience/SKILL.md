---
name: chaos-resilience
description: >
  Chaos engineering and resilience testing workflow: inject controlled failures
  (service crash, network partition, OOM, disk full), verify graceful degradation,
  validate circuit breakers and retry policies, and produce a structured findings
  report. Covers both local Docker Compose environments and Kubernetes clusters.
triggers:
  - chaos-resilience
  - chaos test
  - resilience test
  - failure injection
  - chaos engineering
  - fault injection
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<target-service> [--type crash|network|latency|disk|oom|dependency] [--env local|k8s] [--duration 60s] [--abort-on-critical]"
---

# Chaos Resilience — Failure Injection and Resilience Verification

Run controlled chaos experiments against a service to verify resilience under failure conditions. Follows the scientific method: define steady state, hypothesize, inject, observe, analyze, document.

**Target:** $ARGUMENTS

---

## STEP 1: Define Steady State

Before injecting any failure, establish baseline behavior so deviations are measurable.

```bash
# Verify target service is healthy
curl -sf http://localhost:${PORT}/health || echo "UNHEALTHY"

# Capture baseline response time (10 requests)
for i in $(seq 1 10); do
  curl -o /dev/null -s -w "%{time_total}\n" http://localhost:${PORT}/${ENDPOINT}
done

# Capture baseline error rate from logs
docker compose logs --since 5m ${SERVICE} 2>&1 | grep -ci "error" || echo "0"
```

Record the steady state: service health, avg/P99 response time, error rate, memory usage, CPU usage. These become the comparison baseline.

---

## STEP 2: Form Hypothesis

State what SHOULD happen when the failure is injected. A chaos experiment without a hypothesis is just breaking things.

```
Hypothesis:
  Failure type: {e.g., database becomes unreachable}
  Expected behavior: {e.g., service returns cached data, circuit breaker trips within 5s}
  Recovery expectation: {e.g., resumes normal operation within 30s of DB recovery}
  Unacceptable outcomes: {e.g., data corruption, silent data loss, cascade failure}
```

---

## STEP 3: Inject Failure

Select from the failure injection catalog based on `--type`:

| Type | Tool | Command | Blast Radius |
|------|------|---------|--------------|
| **Service crash** | Docker Compose | `docker compose kill ${SERVICE}` | Single service |
| **Network partition** | tc | `tc qdisc add dev eth0 root netem loss 100%` | Single container NIC |
| **Latency injection** | tc | `tc qdisc add dev eth0 root netem delay 500ms 100ms` | Single container NIC |
| **Disk full** | fallocate | `fallocate -l $(df --output=avail / \| tail -1)k /tmp/fill` | Single container FS |
| **Dependency timeout** | iptables | `iptables -A OUTPUT -p tcp --dport ${DEP_PORT} -j DROP` | Outbound to one port |
| **OOM pressure** | stress-ng | `stress-ng --vm 1 --vm-bytes ${LIMIT} --timeout ${DURATION}` | Single container |
| **CPU exhaustion** | stress-ng | `stress-ng --cpu $(nproc) --timeout ${DURATION}` | Single container |
| **DNS failure** | iptables | `iptables -A OUTPUT -p udp --dport 53 -j DROP` | All DNS from container |

### Kubernetes Environments

For `--env k8s`, use **Chaos Mesh** (`PodChaos` with `action: pod-kill`) or **Litmus** (`ChaosEngine` with experiment `pod-network-latency`). Apply the manifest with `kubectl apply -f`, observe, then delete.

### Execute

```bash
echo "Injecting: ${FAILURE_TYPE} at $(date -u +%H:%M:%S)"
${INJECTION_COMMAND}
sleep ${DURATION}
${ROLLBACK_COMMAND}
echo "Injection removed at $(date -u +%H:%M:%S)"
```

---

## STEP 4: Observe Behavior During Failure

While the failure is active, monitor the system:

```bash
# Health check loop
while true; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health)
  echo "$(date +%H:%M:%S) health=$STATUS"
  sleep 2
done

# Watch for circuit breaker trips, retries, fallbacks
docker compose logs -f ${SERVICE} 2>&1 | grep -iE "circuit|retry|fallback|timeout|degraded"

# Check dependent services for cascade effects
docker compose ps
```

Capture: time to detect failure, circuit breaker status, retry behavior (backoff vs. storm), degraded mode activation, error response codes, cascade effects, log anomalies.

---

## STEP 5: Analyze Results

Compare observations against the hypothesis and steady state.

### Resilience Checklist

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Circuit breaker trips within expected time | | |
| Retries use exponential backoff (not retry storm) | | |
| Graceful degradation active (cached/fallback response) | | |
| Error responses are user-friendly (not stack traces) | | |
| Queue backpressure prevents overload | | |
| No data corruption or silent data loss | | |
| No cascade failure to unrelated services | | |
| Recovery within expected time after injection removed | | |
| Metrics and alerts fired correctly | | |

### Severity Classification

| Severity | Definition |
|----------|-----------|
| **Critical** | Data loss, security breach, unrecoverable state, full cascade failure |
| **Major** | No graceful degradation, retry storms, slow recovery (>5min), misleading errors |
| **Minor** | Missing metrics, unhelpful log messages, suboptimal timeout values |

---

## STEP 6: Document Findings

```
CHAOS EXPERIMENT REPORT
========================

Experiment: {descriptive name}
Date: {YYYY-MM-DD}
Target: {service name} | Environment: {local / staging / k8s}

Hypothesis: {what we expected}
Failure: {type} via {command} | Blast radius: {scope} | Duration: {Xs}

Baseline:            During failure:        Delta:
  Response: {X}ms      Response: {Y}ms        +{Z}ms
  Error rate: {X}%     Error rate: {Y}%       +{Z}%

Circuit breaker: {tripped at Xs / did not trip}
Degraded mode: {active / not implemented}
Recovery time: {X}s after injection removed

Findings:
  F1 [{severity}]: {title}
    Observed: {what happened}
    Expected: {what should have happened}
    Recommendation: {specific fix}

  F2 [{severity}]: ...

Verdict: {RESILIENT / DEGRADED-GRACEFULLY / VULNERABLE}

Action items:
  [ ] {action — owner, priority}
```

---

## STEP 7: Gameday Planning (Optional)

For coordinated team chaos exercises, define before starting:

- **Scope**: which services, which failure types, which environment (staging or production-canary)
- **Blast radius controls**: affected vs. unaffected services, max concurrent failures
- **Abort criteria**: customer error rate > X%, P99 > Xms, any data corruption, on-call page for unrelated service, any participant calls abort
- **Rollback procedure**: remove injections, restart services, verify health, confirm metrics return to baseline
- **Communication**: notify stakeholders before start, post updates every N minutes, send summary after completion

---

## CRITICAL RULES

- **Hypothesis first** — MUST define expected behavior before injecting any failure. Breaking things without a hypothesis teaches nothing.
- **Blast radius awareness** — MUST identify what will be affected before injection. Limit scope to the target service.
- **Rollback ready** — MUST have a tested rollback command before every injection. If rollback fails, abort.
- **One variable at a time** — MUST inject only one failure type per experiment. Combining failures prevents root cause analysis.
- **Steady state baseline** — MUST capture baseline metrics before injection. Without a baseline, observations are meaningless.
- **Time-boxed** — MUST set a maximum duration for every injection. Never leave a failure running indefinitely.
- **Evidence-based** — MUST back every finding with observed data. "Circuit breaker did not trip within 10s" is evidence; "might not work" is not.

## MUST NOT DO

- MUST NOT run chaos experiments against production without explicit written approval from the service owner and on-call engineer. Use staging or local environments by default.
- MUST NOT inject failures without a rollback plan — every injection command must have a corresponding removal command tested beforehand.
- MUST NOT leave failure injections running after the experiment ends — always clean up `tc` rules, `iptables` entries, stress processes, and disk fills.
- MUST NOT inject multiple failure types simultaneously — isolate cause and effect by testing one variable at a time.
- MUST NOT skip the steady state baseline — without it, there is no way to measure impact.
- MUST NOT ignore cascade effects — always verify services outside the blast radius remain healthy.
- MUST NOT treat a passing experiment as proof of total resilience — it only proves resilience against that specific failure mode.
- MUST NOT run resource exhaustion experiments (OOM, CPU, disk fill) without container resource limits — unbounded consumption can crash the host.

---

## CI-EMBEDDED CHAOS EXPERIMENTS

Run chaos experiments as pipeline stages — every deployment is resilient by design.

### Pipeline Integration Pattern

```yaml
# GitHub Actions: chaos gate before production deploy
chaos-gate:
  needs: [e2e-tests]
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to staging
      run: kubectl apply -f k8s/ --namespace staging

    - name: Run chaos experiments
      run: |
        # Kill a random pod in the service
        kubectl delete pod -l app=api-server -n staging --grace-period=0 --wait=false
        sleep 10
        # Verify service recovered
        curl --retry 5 --retry-delay 2 http://staging:8000/health | grep "ok"

    - name: Network partition test
      run: |
        # Simulate network partition to database
        kubectl exec -n staging deploy/api-server -- \
          iptables -A OUTPUT -p tcp --dport 5432 -j DROP
        sleep 5
        # Verify circuit breaker activated (503, not 500)
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://staging:8000/api/users)
        [ "$STATUS" = "503" ] || exit 1
        # Restore network
        kubectl exec -n staging deploy/api-server -- \
          iptables -D OUTPUT -p tcp --dport 5432 -j DROP
```

### LocalStack Chaos (AWS Services)

Test AWS failure modes locally without cloud costs:

```bash
# Enable LocalStack chaos extension
export LOCALSTACK_CHAOS_ENABLED=1

# Simulate S3 failures
curl -X POST http://localhost:4566/_chaos/faults \
  -d '{"service": "s3", "operation": "GetObject", "error_code": 500, "percentage": 50}'

# Simulate DynamoDB throttling
curl -X POST http://localhost:4566/_chaos/faults \
  -d '{"service": "dynamodb", "operation": "PutItem", "error_code": "ProvisionedThroughputExceededException", "percentage": 30}'

# Simulate Lambda timeouts
curl -X POST http://localhost:4566/_chaos/faults \
  -d '{"service": "lambda", "operation": "Invoke", "latency_ms": 30000}'

# Run tests against chaos-injected services
pytest tests/resilience/ --tb=short
# Verify: retries work, circuit breakers activate, fallbacks return gracefully

# Clear all faults
curl -X DELETE http://localhost:4566/_chaos/faults
```

### Resilience Assertions

```python
# Define resilience requirements as testable assertions
def test_service_recovers_from_db_failure():
    """Service recovers within 30s of database failure."""
    # Inject fault
    inject_db_failure()

    # Verify circuit breaker activates (503, not 500)
    response = requests.get(f"{BASE_URL}/api/users")
    assert response.status_code == 503

    # Restore database
    restore_db()

    # Verify recovery within 30s
    recovered = False
    for _ in range(30):
        response = requests.get(f"{BASE_URL}/api/users")
        if response.status_code == 200:
            recovered = True
            break
        time.sleep(1)

    assert recovered, "Service did not recover within 30 seconds"
```
