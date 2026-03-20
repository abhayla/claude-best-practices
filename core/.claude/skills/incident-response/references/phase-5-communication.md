# PHASE 5: Communication

### 5.1 Internal Communication Cadence

| Severity | Update Frequency | Audience |
|----------|-----------------|----------|
| SEV1 | Every 15 minutes | Engineering, leadership, support, on-call |
| SEV2 | Every 30 minutes | Engineering, support, on-call |
| SEV3 | Every 2 hours or on resolution | Engineering, on-call |
| SEV4 | On resolution only | Ticket watchers |

### 5.2 Internal Update Template

```
INCIDENT UPDATE — [INCIDENT-ID] — [SEV level] — [timestamp UTC]
Status: [Investigating / Identified / Mitigating / Monitoring / Resolved]
IC: [name]
Duration: [time since detection]

Current state:
- [What is happening right now]

Actions taken since last update:
- [Action 1]
- [Action 2]

Next steps:
- [Planned action 1] — owner: [name] — ETA: [time]

Impact:
- [Current user/revenue impact]
```

### 5.3 Customer-Facing Communication

**Investigating:**
```
We are currently investigating reports of [user-visible symptom].
Some users may experience [specific impact].
We will provide an update within [timeframe].
```

**Identified:**
```
We have identified the cause of [user-visible symptom] and are
implementing a fix. We expect to resolve this within [timeframe].
```

**Resolved:**
```
The issue causing [user-visible symptom] has been resolved.
All services are operating normally. We will publish a full
incident report within [48 hours / 5 business days].
```

**Rules for customer-facing comms:**
- NEVER blame specific teams, individuals, or third parties
- NEVER include technical jargon, stack traces, or internal system names
- ALWAYS state the user-visible impact, not the technical cause
- ALWAYS provide a timeframe for the next update
- Have a second person review SEV1-SEV2 customer comms before publishing

### 5.4 Escalation Paths

Define escalation triggers — do NOT wait for things to get worse:

| Trigger | Escalation Action |
|---------|-------------------|
| SEV1 not mitigated within 30 min | Escalate to VP Engineering |
| SEV2 not mitigated within 1 hour | Escalate to Engineering Manager |
| Security breach suspected | Immediately notify Security team and Legal |
| Data loss confirmed | Notify CTO and Data Protection Officer |
| SLA breach imminent | Notify Customer Success and Account Management |
| IC needs more people | IC requests specific expertise through the war room |

---

