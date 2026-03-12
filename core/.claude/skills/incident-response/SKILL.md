---
name: incident-response
description: >
  Comprehensive incident response workflow: detection, triage, severity classification,
  mitigation, communication, post-mortem, and on-call handoff. Use when responding to
  production incidents, generating runbooks, conducting post-mortems, or preparing
  on-call handoff documents.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<incident-description or 'postmortem' or 'runbook <failure-mode>' or 'handoff'>"
triggers:
  - /incident
  - /incident-response
  - /postmortem
---

# Incident Response

Handle a production incident or generate incident-related documentation.

**Request:** $ARGUMENTS

---

## PHASE 1: Incident Detection and Triage

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

## PHASE 2: Immediate Response

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

## PHASE 3: Diagnosis Workflow

### 3.1 Structured Diagnosis Checklist

Work through these in order — most incidents are caused by recent changes:

| # | Check | Command / Action | Finding |
|---|-------|-----------------|---------|
| 1 | Recent deployments | Check CI/CD pipeline for deploys in the last 4 hours | |
| 2 | Recent config changes | Review config management for changes in the last 24 hours | |
| 3 | Error logs | Search application logs for new error patterns | |
| 4 | Metrics dashboards | Check error rate, latency, CPU, memory, disk, connections | |
| 5 | Dependency status | Verify third-party service status pages and internal dependencies | |
| 6 | Infrastructure | Check cloud provider status, DNS, load balancers, certificates | |
| 7 | Database | Check connection pools, slow queries, replication lag, locks | |
| 8 | Traffic patterns | Look for unusual traffic spikes, DDoS indicators, bot activity | |
| 9 | Cron/scheduled jobs | Check if a scheduled job is running or failed recently | |
| 10 | Feature flags | Review recently toggled feature flags | |

### 3.2 Log Analysis

```bash
# Recent errors (adapt to your logging system)
# Structured logs (JSON)
cat /var/log/app/error.log | jq 'select(.level == "ERROR")' | tail -100

# Search for specific error patterns
grep -i "exception\|error\|fatal\|panic\|timeout" /var/log/app/app.log | tail -50

# Check for OOM kills
dmesg | grep -i "out of memory\|oom"

# Database connection issues
grep -i "connection refused\|too many connections\|deadlock" /var/log/app/app.log
```

### 3.3 Blast Radius Assessment

Map the dependency graph of the affected service:

1. **Direct dependencies** — what does the broken service call?
2. **Reverse dependencies** — what calls the broken service?
3. **Shared resources** — database, cache, message queue, shared storage
4. **Cross-region impact** — is the issue isolated to one region or global?

Document the blast radius visually if possible:
```
[Affected Service] --> [DB: impacted] --> [Service B: degraded]
                  --> [Cache: healthy]
                  --> [Service C: healthy]
[Service D] --> [Affected Service] --> [degraded]
[Service E] --> [Affected Service] --> [degraded]
```

---

## PHASE 4: Mitigation Strategies

Choose the fastest safe mitigation. Speed matters more than elegance during an incident.

### 4.1 Rollback Deployment

**When to use:** Incident correlates with a recent deployment.

```bash
# Identify the last known good deployment
git log --oneline -10

# Rollback to previous version (adapt to your deployment system)
# Kubernetes
kubectl rollout undo deployment/<service-name> -n <namespace>

# Verify rollback
kubectl rollout status deployment/<service-name> -n <namespace>
```

**Verification after rollback:**
- [ ] Error rate returning to baseline
- [ ] Latency returning to baseline
- [ ] No new error patterns introduced
- [ ] User-facing functionality restored

### 4.2 Feature Flag Disable

**When to use:** Incident correlates with a recently enabled feature.

1. Identify the suspect feature flag
2. Disable the flag (this should take effect without a deployment)
3. Monitor for recovery within 2-5 minutes
4. If no improvement, the flag is not the cause — re-enable and try another mitigation

### 4.3 Traffic Rerouting

**When to use:** Issue is region-specific or affects specific infrastructure.

- Shift traffic away from the affected region/zone using DNS or load balancer config
- Enable maintenance mode for the affected component if partial rerouting is not possible
- Verify the healthy region can handle the additional load before rerouting

### 4.4 Scaling Up

**When to use:** Issue is caused by capacity exhaustion (CPU, memory, connections).

```bash
# Kubernetes horizontal scaling
kubectl scale deployment/<service-name> --replicas=<N> -n <namespace>

# Verify new pods are healthy
kubectl get pods -n <namespace> -l app=<service-name>
```

**Warning:** Scaling up masks the root cause. Always investigate why capacity was exhausted even after scaling resolves the symptoms.

### 4.5 Circuit Breaker / Dependency Isolation

**When to use:** A downstream dependency is failing and causing cascading failures.

1. Enable circuit breaker for the failing dependency
2. Serve degraded responses (cached data, default values, graceful error messages)
3. Monitor upstream services for recovery
4. Re-enable the dependency connection gradually once it recovers

### 4.6 Database Emergency Procedures

```bash
# Kill long-running queries (PostgreSQL)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND query NOT LIKE '%pg_stat_activity%';

# Check replication lag
SELECT client_addr, state, sent_lsn, write_lsn, replay_lsn,
       (sent_lsn - replay_lsn) AS replication_lag
FROM pg_stat_replication;

# Check for locks
SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query,
       blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_catalog.pg_locks bl
JOIN pg_stat_activity blocked ON bl.pid = blocked.pid
JOIN pg_catalog.pg_locks kl ON bl.locktype = kl.locktype
  AND bl.relation = kl.relation AND bl.pid != kl.pid
JOIN pg_stat_activity blocking ON kl.pid = blocking.pid
WHERE NOT bl.granted;
```

---

## PHASE 5: Communication

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

## PHASE 6: Runbook Generation

Use this phase to generate step-by-step runbooks for known failure modes.

### 6.1 Runbook Template

```markdown
# Runbook: [Failure Mode Name]

## Trigger
[What alert or symptom triggers this runbook]

## Prerequisites
- Access to: [systems, dashboards, tools]
- Permissions: [required roles]

## Diagnosis Steps
1. [Step with specific command]
   - Expected output: [what healthy looks like]
   - If unhealthy: proceed to step 2
2. [Next step]

## Mitigation Steps
1. [Action with specific command]
2. [Verification command]
   - Expected output: [what success looks like]
3. [Rollback if mitigation fails]

## Verification
- [ ] [Metric] has returned to baseline
- [ ] [Error rate] is below [threshold]
- [ ] [User-facing check] confirms resolution

## Escalation
If this runbook does not resolve the issue within [timeframe]:
- Escalate to: [team/person]
- Provide: [what context to include]

## History
| Date | Operator | Notes |
|------|----------|-------|
| | | |
```

### 6.2 Common Runbook Categories

Generate runbooks for these common failure modes when requested:

1. **Service unresponsive** — health check failures, no response from endpoints
2. **High error rate** — sudden spike in 5xx errors
3. **Database connection exhaustion** — connection pool saturated
4. **Memory leak** — gradual memory increase leading to OOM
5. **Certificate expiry** — TLS/SSL certificate expired or about to expire
6. **Disk space exhaustion** — storage volume at capacity
7. **DNS resolution failure** — service discovery or DNS lookup failures
8. **Message queue backlog** — consumer lag growing, messages not being processed
9. **Cache failure** — Redis/Memcached down or eviction storm
10. **Authentication/authorization failure** — auth service down or token validation failing

### 6.3 Pre-Written Diagnostic Scripts

```bash
# System health snapshot
echo "=== System Health Snapshot ==="
echo "--- CPU ---"
top -bn1 | head -5
echo "--- Memory ---"
free -h
echo "--- Disk ---"
df -h
echo "--- Network Connections ---"
ss -tuln | head -20
echo "--- Recent OOM ---"
dmesg | grep -i oom | tail -5
echo "--- Load Average ---"
uptime
```

```bash
# Application health check
echo "=== Application Health ==="
echo "--- HTTP Health Check ---"
curl -s -o /dev/null -w "%{http_code} %{time_total}s" http://localhost:8080/health
echo ""
echo "--- Process Status ---"
ps aux | grep -E "[a]pp|[s]erver" | head -10
echo "--- Open File Descriptors ---"
ls /proc/$(pgrep -f "app")/fd 2>/dev/null | wc -l
echo "--- Active Connections ---"
ss -tn state established | wc -l
```

---

## PHASE 7: Post-Mortem

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
# Post-Mortem: [Incident Title]

**Date:** [YYYY-MM-DD]
**Severity:** [SEV1-SEV4]
**Duration:** [detection to resolution]
**IC:** [name]
**Author:** [name]
**Status:** [Draft / Review / Final]

## Summary
[2-3 sentence summary: what happened, impact, resolution]

## Impact
- Users affected: [count/percentage]
- Duration of impact: [time]
- Revenue impact: [estimate if applicable]
- SLO impact: [error budget consumed]
- Data impact: [none/details]

## Timeline
[Detailed timeline from Phase 7.1]

## Root Cause
[5 Whys analysis from Phase 7.2]

## Contributing Factors
[List from Phase 7.3]

## What Went Well
- [Thing that worked during the response]
- [Another thing]

## What Went Poorly
- [Thing that slowed response or increased impact]
- [Another thing]

## Action Items
| # | Action | Owner | Priority | Due Date | Status |
|---|--------|-------|----------|----------|--------|
| 1 | [Action] | [name] | P0/P1/P2 | [date] | Open |
| 2 | [Action] | [name] | P0/P1/P2 | [date] | Open |

## Lessons Learned
[Key takeaways for the team]

## Appendix
- [Links to dashboards, logs, Slack threads, related incidents]
```

### 7.5 Blameless Post-Mortem Principles

- **Focus on systems, not individuals** — Ask "how did the system allow this?" not "who did this?"
- **Assume good intent** — Everyone involved was trying to do the right thing with the information they had
- **No counterfactuals** — Avoid "if only X had done Y" — focus on systemic improvements
- **Celebrate detection and response** — Acknowledge what went well, not just what failed
- **Action items MUST be concrete** — "Improve monitoring" is not an action item; "Add alert for replication lag > 30s on the orders database" is
- **Follow up on action items** — Schedule a review 2 weeks after the post-mortem to track completion

---

## PHASE 8: Rollback Procedures

### 8.1 Deployment Rollback

```bash
# Git-based rollback — identify last known good commit
git log --oneline --since="24 hours ago"
git revert <bad-commit-sha> --no-edit

# Container-based rollback
docker pull <registry>/<image>:<previous-tag>
docker-compose up -d

# Kubernetes rollback
kubectl rollout undo deployment/<name> -n <namespace>
kubectl rollout status deployment/<name> -n <namespace>

# Serverless rollback (AWS Lambda)
aws lambda update-function-code --function-name <name> \
  --s3-bucket <bucket> --s3-key <previous-version-key>
```

### 8.2 Database Rollback

**CAUTION:** Database rollbacks are inherently risky. Always back up before rolling back.

```bash
# Run the down migration (framework-specific)
# Django
python manage.py migrate <app_name> <previous_migration_number>

# Rails
rails db:rollback STEP=1

# Alembic (SQLAlchemy)
alembic downgrade -1

# Manual SQL rollback from backup
pg_dump -h <host> -U <user> <dbname> > pre_rollback_backup.sql
psql -h <host> -U <user> <dbname> < rollback_script.sql
```

**Database rollback checklist:**
- [ ] Backup taken before rollback
- [ ] Application code is compatible with the rolled-back schema
- [ ] Data inserted since the migration is accounted for
- [ ] Replication is healthy after rollback
- [ ] Application connection pools are recycled

### 8.3 Configuration Rollback

```bash
# Check config version history (adapt to your config management)
git log --oneline -- config/

# Revert config to previous version
git checkout <previous-commit> -- config/<file>

# If using a config service, revert via API
curl -X PUT https://config-service/api/v1/config/<key> \
  -H "Content-Type: application/json" \
  -d '{"value": "<previous-value>", "reason": "incident rollback"}'
```

### 8.4 Data Recovery

1. **Identify the data loss window** — exact time range of affected data
2. **Check automated backups** — locate the most recent backup before the incident
3. **Point-in-time recovery** — if available, restore to the last consistent state
4. **Reconciliation** — compare restored data with any data created during the incident window
5. **Validation** — run integrity checks on restored data before serving it to users

---

## PHASE 9: On-Call Handoff

### 9.1 Handoff Document Template

When handing off an ongoing or recently resolved incident:

```markdown
# On-Call Handoff — [Date]

## Active Incidents
| ID | Severity | Status | Summary | IC |
|----|----------|--------|---------|----|
| | | | | |

## Recently Resolved (last 24h)
| ID | Severity | Resolved At | Summary | Follow-up Needed |
|----|----------|-------------|---------|-----------------|
| | | | | |

## Ongoing Concerns
- [System or service that is degraded but not yet an incident]
- [Elevated error rates being monitored]

## Recent Changes (last 48h)
- [Deployments]
- [Config changes]
- [Infrastructure changes]

## Known Issues
- [Issue 1 — workaround: ...]
- [Issue 2 — tracking ticket: ...]

## Useful Context
- [Anything the next on-call should know]
- [Upcoming maintenance windows]
- [Expiring certificates or credentials]
```

### 9.2 Handoff Best Practices

- **Synchronous handoff for SEV1-SEV2** — verbal handoff via call, not just a document
- **Walk through active incidents** — do not just send a link
- **Confirm access** — verify the incoming on-call has access to all required systems
- **Share mental model** — explain what you think might happen next, not just what has happened
- **Provide escalation contacts** — who to call if things get worse

---

## PHASE 10: Incident Tracking and Metrics

### 10.1 Key Metrics

Track these metrics across all incidents to measure and improve response capability:

| Metric | Definition | Target |
|--------|-----------|--------|
| **MTTD** (Mean Time to Detect) | Time from incident start to first alert | < 5 min |
| **MTTA** (Mean Time to Acknowledge) | Time from alert to first human response | < 5 min (SEV1), < 15 min (SEV2) |
| **MTTR** (Mean Time to Resolve) | Time from detection to resolution | < 1 hour (SEV1), < 4 hours (SEV2) |
| **MTTM** (Mean Time to Mitigate) | Time from detection to user-impact mitigation | < 30 min (SEV1) |
| **Incident frequency** | Number of incidents per week/month by severity | Trending down |
| **SLO burn rate** | Error budget consumed per incident | Within monthly budget |
| **Post-mortem completion rate** | Percentage of SEV1-SEV2 incidents with completed post-mortems | 100% |
| **Action item completion rate** | Percentage of post-mortem action items completed on time | > 80% |

### 10.2 Incident Tracking Checklist

For every incident, ensure:

- [ ] Incident record created with severity, timestamps, and IC
- [ ] Timeline documented in real time (not reconstructed afterward)
- [ ] Status page updated (SEV1-SEV3)
- [ ] Post-mortem scheduled within 48 hours (SEV1-SEV2)
- [ ] Post-mortem completed within 5 business days (SEV1-SEV2)
- [ ] Action items assigned with owners and due dates
- [ ] Action items reviewed at 2-week mark
- [ ] Metrics updated in incident tracking system

### 10.3 Monthly Incident Review

Hold a monthly review covering:

1. **Incident count by severity** — trend over time
2. **MTTR / MTTD trends** — are we getting faster?
3. **Repeat incidents** — same root cause appearing multiple times?
4. **Action item completion** — are we following through?
5. **SLO health** — error budget status across services
6. **On-call burden** — pages per shift, off-hours pages, toil assessment

---

## PHASE 11: Anti-Patterns

Avoid these common incident response anti-patterns:

### 11.1 Response Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **Hero debugging** | One person debugs alone while others wait | IC coordinates parallel investigation streams |
| **Blame culture** | People hide mistakes or avoid reporting incidents | Blameless post-mortems, celebrate early detection |
| **No IC assigned** | Chaotic response with no coordination | Always assign an IC, even for SEV3 |
| **Skipping severity assessment** | Under-response to serious incidents | Classify severity first, respond accordingly |
| **Fixing forward under pressure** | Deploying untested fixes during an active incident | Rollback first, fix forward after stabilization |
| **Silent investigation** | Debugging without updating the incident channel | Post findings every 15 min (SEV1) or 30 min (SEV2) |
| **Premature all-clear** | Declaring resolution before verifying stability | Monitor for at least 15 min after mitigation before resolving |

### 11.2 Post-Mortem Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **No post-mortem** | Same incidents repeat because root causes are not addressed | Mandatory post-mortem for all SEV1-SEV2 incidents |
| **Blame-oriented post-mortem** | People become defensive, hide information | Blameless analysis focused on systemic improvements |
| **Vague action items** | "Improve monitoring" — never gets done | Specific, measurable actions with owners and due dates |
| **No follow-up on action items** | Post-mortem is written but nothing changes | 2-week review meeting to track action item progress |
| **Delayed post-mortem** | Details are forgotten, less accurate analysis | Complete within 5 business days of resolution |

### 11.3 Organizational Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **No runbooks** | Every incident starts from scratch | Maintain runbooks for known failure modes, update after each incident |
| **Tribal knowledge** | Only one person knows how to fix the system | Document procedures, cross-train team members |
| **Alert fatigue** | Too many low-priority alerts, real alerts get ignored | Tune alerting thresholds, eliminate noisy alerts |
| **No on-call handoff** | Context lost between shifts | Structured handoff document and verbal briefing |
| **Ignoring near-misses** | Only react to full outages, miss preventive opportunities | Track and analyze near-misses with the same rigor as incidents |

---

## CRITICAL RULES

- **Mitigate first, diagnose second** — restore service before understanding root cause
- **Never skip severity classification** — it determines everything else: response time, communication, escalation
- **Rollback is the default mitigation** — unless rollback is known to be unsafe, prefer it over fixing forward
- **Communicate proactively** — silence during an incident erodes trust faster than bad news
- **Every SEV1-SEV2 gets a post-mortem** — no exceptions, completed within 5 business days
- **Action items need owners and due dates** — unowned action items do not get done
- **Blameless culture is non-negotiable** — blame prevents learning, learning prevents recurrence
- **Timestamp everything** — accurate timelines are essential for post-mortems and metric tracking
- **Do not declare resolution prematurely** — monitor for at least 15 minutes after mitigation before closing
- **Escalate early, not late** — the cost of escalating unnecessarily is far lower than the cost of escalating too late
