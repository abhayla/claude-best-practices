---
name: incident-response
description: >
  Manage incident response through detection, triage, severity classification,
  mitigation, communication, post-mortem, and on-call handoff. Use when responding to
  production incidents, generating runbooks, conducting post-mortems, or preparing
  on-call handoff documents.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<incident-description or 'postmortem' or 'runbook <failure-mode>' or 'handoff'>"
version: "1.0.0"
type: reference
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


**Read:** `references/phase-1-incident-detection-and-triage.md` for detailed phase 1: incident detection and triage reference material.

## PHASE 2: Immediate Response


**Read:** `references/phase-2-immediate-response.md` for detailed phase 2: immediate response reference material.

## PHASE 3: Diagnosis Workflow


**Read:** `references/phase-3-diagnosis-workflow.md` for detailed phase 3: diagnosis workflow reference material.

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


**Read:** `references/phase-5-communication.md` for detailed phase 5: communication reference material.

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


**Read:** `references/phase-7-post-mortem.md` for detailed phase 7: post-mortem reference material.

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

## PHASE 10: Incident Tracking and Metrics


**Read:** `references/phase-10-incident-tracking-and-metrics.md` for detailed phase 10: incident tracking and metrics reference material.

## PHASE 11: Anti-Patterns

Avoid these common incident response anti-patterns:


**Read:** `references/phase-11-anti-patterns.md` for detailed phase 11: anti-patterns reference material.

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
