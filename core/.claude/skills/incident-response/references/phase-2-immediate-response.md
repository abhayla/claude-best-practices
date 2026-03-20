# PHASE 2: Immediate Response

### 2.1 Acknowledge and Assign

Within the response time for the severity level:

1. **Acknowledge the incident** — respond in the alerting channel confirming you are investigating
2. **Assign an Incident Commander (IC)** — the IC owns the incident end-to-end; for SEV1-SEV2 this MUST be a senior engineer or on-call lead
3. **Create an incident record** — open a tracking ticket with severity, timestamp, initial description, and IC assignment

### 2.2 Establish Communication Channels

| Severity | Channel Requirements |
|----------|---------------------|
| SEV1 | Dedicated war room (video call), incident Slack channel, status page updated within 10 min |
| SEV2 | Incident Slack channel, status page updated within 20 min |
| SEV3 | Thread in on-call channel, status page optional |
| SEV4 | Ticket only, async communication |

**War room rules (SEV1-SEV2):**
- IC runs the war room and delegates tasks
- One person scribes the timeline in real time
- No side conversations — all findings reported to IC
- Mute unless speaking; keep the channel clear

### 2.3 Status Page Update

For SEV1-SEV3, update the public status page:

```
[INVESTIGATING] We are aware of [brief description of user-visible impact].
Our team is actively investigating. We will provide an update within [30/60] minutes.
```

Never include internal details, stack traces, or speculative root causes in public communications.

---

