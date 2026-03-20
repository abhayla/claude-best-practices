# PHASE 1: Incident Detection and Triage

### 1.1 Alert Triage

When an incident is reported or an alert fires:

1. **Identify the signal source** — monitoring alert, user report, automated health check, dependency notification, or internal discovery
2. **Validate the alert** — confirm it is not a false positive by checking at least two independent signals (e.g., error rate + latency spike, or user reports + dashboard anomaly)
3. **Timestamp everything** — record the exact time the incident was detected (UTC), who detected it, and how

### 1.2 Severity Classification

Classify the incident using the SEV1-SEV4 scale. Severity determines response urgency, communication cadence, and escalation requirements.

| Severity | Criteria | Response Time | Example |
|----------|----------|---------------|---------|
| **SEV1 — Critical** | Complete service outage, data loss, security breach, revenue-impacting for all users | Immediate (< 5 min) | Database down, auth system compromised, payment processing failed |
| **SEV2 — Major** | Significant degradation, major feature unavailable, subset of users fully impacted | < 15 min | Search broken, API error rate > 10%, one region down |
| **SEV3 — Minor** | Partial degradation, workaround available, limited user impact | < 1 hour | Slow queries, non-critical feature broken, intermittent errors < 1% |
| **SEV4 — Low** | Cosmetic issue, minor inconvenience, no functional impact | Next business day | UI glitch, non-user-facing log noise, stale cache |

**Severity escalation rules:**
- If impact grows, upgrade severity immediately — never downgrade during active incident
- When in doubt, classify one level higher — over-response is cheaper than under-response
- SEV1 and SEV2 require an incident commander; SEV3-SEV4 can be handled by on-call engineer

### 1.3 Impact Assessment

Quantify the blast radius before proceeding:

1. **Users affected** — percentage of total users, specific segments (geography, plan tier, platform)
2. **Services affected** — list all impacted services and their dependencies
3. **Revenue impact** — estimate per-minute or per-hour cost if applicable
4. **Data integrity** — determine if data loss, corruption, or inconsistency has occurred
5. **Security exposure** — assess if sensitive data has been exposed or unauthorized access gained
6. **SLO impact** — calculate remaining error budget and whether SLOs are breached

Output an impact summary:
```
Impact Assessment:
- Severity: SEV[1-4]
- Users affected: [count/percentage]
- Services: [list]
- Duration so far: [time]
- Revenue impact: [estimate]
- Data integrity: [intact/at-risk/compromised]
- Security: [no exposure/potential exposure/confirmed breach]
- SLO status: [within budget/budget exhausted/SLA breach imminent]
```

---

