# STEP 5: Production Readiness Review (PRR)

### 5.1 Reliability

- [ ] Health endpoint returns 200 when ready
- [ ] Readiness probe configured (K8s)
- [ ] Liveness probe configured (K8s)
- [ ] Graceful shutdown handles SIGTERM
- [ ] Request timeouts configured
- [ ] Circuit breaker on external dependencies
- [ ] Retry with exponential backoff on transient failures

### 5.2 Observability

- [ ] Structured logging to stdout
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Request duration histogram
- [ ] Error rate counter
- [ ] Custom business metrics
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Dashboard in Grafana
- [ ] Alert rules for SLO violation

### 5.3 Security

- [ ] Secrets in vault / sealed secrets (not env vars in manifests)
- [ ] Network policies restrict pod-to-pod communication
- [ ] Container runs as non-root
- [ ] Read-only filesystem where possible
- [ ] Resource limits set (CPU, memory)
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] DAST scan passed

### 5.4 Data

- [ ] Database backup schedule configured
- [ ] Point-in-time recovery tested
- [ ] Migration rollback tested
- [ ] Seed data for staging environment
- [ ] PII handling documented

### 5.5 Operations

- [ ] Runbook for common incidents
- [ ] On-call rotation defined
- [ ] SLOs defined with error budgets
- [ ] Incident response process documented
- [ ] Rollback procedure documented and tested

### 5.6 Report

```markdown
