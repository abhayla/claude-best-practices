# Verification Checklist

## Verification Checklist

Before reporting monitoring setup complete, verify:

| Check | Status |
|-------|--------|
| All four golden signals instrumented (latency, traffic, errors, saturation) | |
| Metrics follow naming conventions (`_total`, `_seconds`, `_bytes`) | |
| No high-cardinality labels (user IDs, request IDs in labels) | |
| SLOs defined with error budget tracking | |
| Burn rate alerts configured (fast + slow burn) | |
| Every alert has a runbook URL | |
| Alertmanager routing configured with severity levels | |
| Structured JSON logging with correlation IDs | |
| OpenTelemetry tracing with context propagation | |
| Grafana dashboard with standard layout (SLOs, golden signals, dependencies) | |
| Sampling strategy configured for traces | |
| Infrastructure alerts for disk, CPU, memory | |
| Dashboard committed as code (JSON in version control) | |

---

