# PHASE 7: Post-Mortem

### 7.1 Post-Mortem Timeline

Construct a detailed timeline of the incident. Every entry MUST include a UTC timestamp.

```
YYYY-MM-DD HH:MM UTC — [Event description] — [Source: alert/person/system]
```

Example:
```
2026-03-10 14:23 UTC — Monitoring alert fires: API error rate > 5% — Source: Datadog
2026-03-10 14:25 UTC — On-call engineer acknowledges alert — Source: PagerDuty
2026-03-10 14:28 UTC — IC assigned: [name], war room opened — Source: Slack
2026-03-10 14:35 UTC — Root cause identified: bad migration in deploy v2.4.1 — Source: IC
2026-03-10 14:38 UTC — Rollback initiated to v2.4.0 — Source: CI/CD
2026-03-10 14:42 UTC — Rollback complete, error rate dropping — Source: Datadog
2026-03-10 14:55 UTC — Error rate at baseline, incident resolved — Source: Datadog
```

### 7.2 Root Cause Analysis — 5 Whys

Drill down to the systemic root cause, not the proximate cause:

```
Why 1: Why did the API return 500 errors?
  → A database migration added a NOT NULL column without a default value.

Why 2: Why was the migration deployed without catching this?
  → The migration was not tested against a production-like dataset.

Why 3: Why wasn't it tested against production-like data?
  → Our staging environment uses a minimal seed dataset, not a production snapshot.

Why 4: Why does staging use minimal seed data?
  → Production data contains PII and we haven't set up anonymization.

Why 5: Why haven't we set up data anonymization for staging?
  → It was deprioritized in favor of feature work last quarter.

ROOT CAUSE: No process for maintaining production-representative staging data.
```

### 7.3 Contributing Factors

List all factors that contributed to the incident, even if they are not the root cause:

- **Detection gap** — Was there a monitoring gap that delayed detection?
- **Process gap** — Was there a missing review, test, or approval step?
- **Knowledge gap** — Was institutional knowledge missing or siloed?
- **Tooling gap** — Did inadequate tooling slow diagnosis or mitigation?
- **Communication gap** — Was the right information shared with the right people at the right time?

### 7.4 Post-Mortem Document Template

```markdown
