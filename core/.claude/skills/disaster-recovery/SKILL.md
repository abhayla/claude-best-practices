---
name: disaster-recovery
description: >
  Create disaster recovery plans with RTO/RPO targets derived from NFRs. Covers backup
  schedules, restore procedures, failover runbooks, and DR drill planning. Use when a
  project needs a formal DR plan, backup strategy, or failover architecture.
triggers:
  - disaster-recovery
  - dr-plan
  - backup strategy
  - failover runbook
  - rto rpo
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<prd-or-nfr-path> [--scope db|storage|secrets|all] [--multi-region] [--drill]"
version: "1.0.0"
type: workflow
---

# Disaster Recovery Plan

Create a disaster recovery plan with backup strategies, restore procedures, and failover runbooks.

**Request:** $ARGUMENTS

---

## STEP 1: Extract RTO/RPO Targets from NFRs

1. Read the PRD or NFR document provided in the arguments
2. Identify availability and durability requirements (look for SLA percentages, uptime targets, data loss tolerances)
3. Classify each critical service into a recovery tier:

### RTO/RPO Classification Table

| Tier | RTO (Recovery Time) | RPO (Recovery Point) | Applies To | Example |
|------|--------------------|--------------------|------------|---------|
| **Tier 1 — Critical** | < 1 hour | < 15 minutes | Revenue-generating services, auth, payment processing | API gateway, payment service, user auth |
| **Tier 2 — Important** | < 4 hours | < 1 hour | Core business logic, internal tools with SLAs | Order processing, notification service, admin dashboard |
| **Tier 3 — Standard** | < 24 hours | < 4 hours | Non-critical services, batch jobs, reporting | Analytics pipeline, email digests, log aggregation |

If the PRD does not specify RTO/RPO explicitly, derive from the stated SLA: 99.99% implies Tier 1 (hot standby), 99.9% implies Tier 1-2, 99.5% implies Tier 2 (warm standby), 99% implies Tier 3 (cold restore).

Document each service: name, tier, RTO/RPO targets, justification, and upstream dependencies.

---

## STEP 2: Inventory Critical Services

1. Scan the project for infrastructure definitions (`docker-compose.yml`, `terraform/`, `k8s/`, `serverless.yml`, cloud config)
2. Identify all stateful components:
   - Databases (PostgreSQL, MySQL, MongoDB, Redis with persistence)
   - File/object storage (S3, GCS, local volumes)
   - Message queues with durable messages (RabbitMQ, Kafka)
   - Secrets and certificates (Vault, KMS, TLS certs)
   - Configuration state (feature flags, environment config)
3. Map dependencies between services to determine recovery order
4. Flag single points of failure — any component with no redundancy that is Tier 1 or Tier 2

---

## STEP 3: Define Backup Strategy

Design a backup approach for each stateful component based on its tier.

### Database Backups

| Method | RPO Achievable | Use For | Command/Config |
|--------|---------------|---------|----------------|
| **Logical dump** (`pg_dump`, `mysqldump`) | Hours | Tier 3, small databases | `pg_dump -Fc -f backup_$(date +%Y%m%d_%H%M).dump $DB_NAME` |
| **WAL archiving / binlog** | Minutes | Tier 1-2, point-in-time recovery | `archive_mode = on` + `archive_command` in `postgresql.conf` |
| **Point-in-time recovery (PITR)** | Minutes | Tier 1, exact-moment restore | Continuous WAL shipping + base backup |
| **Streaming replication** | Seconds | Tier 1, near-zero data loss | Synchronous standby with `synchronous_commit = on` |
| **Managed snapshots** (RDS, Cloud SQL) | Hours | Tier 2-3, managed databases | Automated snapshots with retention policy |

### Backup Schedule by Tier

| Tier | Full Backup | Incremental/WAL | Retention | Off-site Copy |
|------|------------|----------------|-----------|---------------|
| Tier 1 | Daily | Continuous (WAL/binlog) | 30 days full, 7 days WAL | Cross-region, real-time |
| Tier 2 | Daily | Every 1 hour | 14 days full, 3 days incremental | Cross-region, daily |
| Tier 3 | Weekly | Daily | 7 days full | Same region, different AZ |

### File/Object Storage Backups

| Storage Type | Strategy | Configuration |
|-------------|----------|---------------|
| S3 / GCS | Enable versioning + lifecycle rules | `aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled` |
| Local volumes | rsync to remote + periodic snapshots | `rsync -az --delete /data/ backup-host:/backups/data/` |
| NFS / EFS | Snapshot + cross-region replication | Provider-specific snapshot API |

### Secrets Backup

| Secret Store | Backup Method | Frequency |
|-------------|--------------|-----------|
| HashiCorp Vault | `vault operator raft snapshot save` | Daily, encrypted at rest |
| AWS Secrets Manager | Cross-region replication | Real-time (built-in) |
| Kubernetes Secrets | `kubectl get secrets -o yaml` + encrypt with SOPS/sealed-secrets | Daily |
| Environment files | Store encrypted in git (SOPS, age) | On every change |

### Configuration Backup

All configuration MUST be in version control (git). This includes:
- Infrastructure-as-code (Terraform state in remote backend with versioning)
- Application config files
- CI/CD pipeline definitions
- Kubernetes manifests / Helm charts

---

## STEP 4: Create Restore Procedure

Write a step-by-step restore procedure for each stateful component. Each procedure MUST include verification steps.

Each restore procedure MUST follow this sequence:

1. **Stop traffic** — Scale down app, update DNS, or enable maintenance mode. Verify no active connections.
2. **Provision target** — Spin up replacement instance if needed. Verify it is reachable.
3. **Restore data** — Execute the appropriate restore method:
   - From dump: `pg_restore -d $DB_NAME -j 4 backup_file.dump`
   - From PITR: Restore base backup + replay WAL to target timestamp
   - From replica: `pg_ctl promote -D $PGDATA`
   - From S3 versioning: `aws s3api get-object --version-id $VID` or `aws s3 sync`
4. **Validate integrity** — Row counts, latest timestamps, checksum comparisons, application smoke test
5. **Restore traffic** — Scale up, update DNS, disable maintenance mode
6. **Monitor** — Watch error rate, latency, and data consistency for 30 minutes post-restore

Document estimated duration and last-tested date for each procedure.

---

## STEP 5: Design Failover Architecture (If Multi-Region)

Skip this step if the project is single-region. Apply this step when `--multi-region` is specified or when Tier 1 services require sub-hour RTO.

### Failover Patterns

| Pattern | RTO | Cost | Complexity | Best For |
|---------|-----|------|-----------|----------|
| **Active-Active** | Near-zero (seconds) | High (2x infra) | High (data sync, conflict resolution) | Tier 1 services requiring 99.99%+ availability |
| **Active-Passive** | Minutes (DNS failover) | Medium (standby infra) | Medium (replication lag monitoring) | Tier 1-2 services with < 1h RTO |
| **Pilot Light** | 15-30 minutes (scale-up required) | Low (minimal standby) | Low (periodic sync) | Tier 2 services with < 4h RTO |

### Failover Procedure (Active-Passive)

1. **Detect** — Health check fails 3 consecutive times (30s intervals)
2. **Confirm** — Verify genuine failure (provider status page, direct check, team confirmation) to avoid false positives
3. **Failover** — Switch DNS/load balancer to secondary region, promote read-replica to primary
4. **Verify** — Health endpoint returns 200 from secondary, application logs show successful requests
5. **Notify** — Alert stakeholders via on-call channel

**Failback** (after primary recovers): Restore primary infra, replicate data back, verify currency, switch traffic during low-traffic window, demote secondary to read-replica.

---

## STEP 6: Create DR Runbook

Assemble the complete DR runbook combining all procedures into a single operational document.

The runbook MUST include: (1) service inventory with tiers, (2) backup schedule and locations, (3) restore procedures per component, (4) failover procedures if multi-region, (5) communication plan (notify on-call within 5 min, status updates every 15 min, post-incident review within 48h), (6) escalation contacts (incident commander, database lead, infrastructure lead, business stakeholder — each with backup), (7) DR drill history.

Write the runbook to `docs/DR-RUNBOOK.md` (or user-specified location). Include version, owner, and quarterly review cadence.

---

## STEP 7: Schedule DR Drill

Define a DR drill plan to validate the runbook regularly.

### DR Drill Checklist

| Step | Action | Measured Outcome |
|------|--------|-----------------|
| 1 | **Simulate failure** — Take down primary database or service in a non-production environment | Failure detected by monitoring within expected threshold |
| 2 | **Execute runbook** — Follow restore/failover procedures exactly as documented | Each step works without undocumented improvisation |
| 3 | **Measure actual RTO** — Time from failure detection to service restored | Actual RTO <= target RTO for the tier |
| 4 | **Measure actual RPO** — Check data loss between last backup and restore point | Actual RPO <= target RPO for the tier |
| 5 | **Validate data integrity** — Run consistency checks on restored data | Zero corruption, all critical records present |
| 6 | **Test application functionality** — Run smoke tests against restored environment | All critical user flows pass |
| 7 | **Document gaps** — Record any steps that failed, were unclear, or took longer than expected | Gap list for runbook updates |
| 8 | **Update runbook** — Incorporate lessons learned into the runbook | Runbook version incremented, gaps addressed |

### Drill Schedule

| Drill Type | Frequency | Scope | Environment |
|-----------|-----------|-------|-------------|
| **Backup verification** | Monthly | Restore a random backup to a test instance, verify integrity | Non-production |
| **Component failover** | Quarterly | Fail over one Tier 1 component, measure RTO/RPO | Staging |
| **Full DR drill** | Bi-annually | Simulate complete region failure, execute full runbook | Staging or isolated production |
| **Tabletop exercise** | Annually | Walk through runbook with all stakeholders, no actual execution | N/A (discussion-based) |

### Drill Report

After each drill, produce a report containing: date, type, participants, scenario simulated, results table (service, tier, target vs actual RTO/RPO, pass/fail), gaps found with severity, action items with owners and due dates, and runbook updates made.

---

## STEP 7A: Backup Encryption & Key Management

### Encryption at Rest

| Backup Type | Encryption Method | Key Management |
|-------------|------------------|----------------|
| Database dumps | GPG/age encryption before upload | Key stored in separate secret store from backups |
| WAL archives | Server-side encryption (SSE-S3, SSE-KMS) | KMS key with rotation enabled |
| Object storage | Bucket-level SSE with customer-managed keys | KMS key per environment, auto-rotate annually |
| Vault snapshots | Built-in AES-256-GCM | Unseal keys in separate, geographically distributed storage |

### Key Rotation for Backup Encryption

1. Generate new encryption key in KMS/secret store
2. Re-encrypt the latest full backup with the new key — verify decryption succeeds
3. Update backup scripts to use new key ID
4. Retain old key until all backups encrypted with it have expired per retention policy
5. Decommission old key only after zero backups reference it

### Compliance Considerations

| Requirement | Implementation |
|-------------|---------------|
| **GDPR data residency** | Backups MUST reside in the same regulatory region as the primary data. Cross-region DR copies require a Data Processing Agreement with the secondary region's provider |
| **SOC 2 backup verification** | Monthly restore tests with documented evidence (drill reports from Step 7) |
| **HIPAA encryption** | AES-256 at rest, TLS 1.2+ in transit, key management via FIPS 140-2 validated HSM |
| **PCI-DSS** | Cardholder data backups encrypted, access logged, retention per PCI schedule (usually 1 year) |

If compliance requirements are not specified in the PRD, flag this as a question to the user — do not assume no compliance applies.

---

## STEP 7B: Restore Verification Testing

Automated monthly restore verification — ensures backups are not silently corrupted.

### Verification Script Template

```bash
#!/bin/bash
# restore-verify.sh — Run monthly via cron or CI scheduled job
set -euo pipefail

BACKUP_FILE=$(ls -t /backups/full/*.dump | head -1)
TEST_DB="restore_verify_$(date +%Y%m%d)"
REPORT_FILE="docs/dr-reports/restore-verify-$(date +%Y%m%d).md"

echo "## Restore Verification Report" > "$REPORT_FILE"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$REPORT_FILE"
echo "Backup: $BACKUP_FILE" >> "$REPORT_FILE"

# 1. Create isolated test database
createdb "$TEST_DB"
trap "dropdb --if-exists $TEST_DB" EXIT

# 2. Restore backup
START=$(date +%s)
pg_restore -d "$TEST_DB" -j 4 "$BACKUP_FILE" 2>> "$REPORT_FILE"
DURATION=$(( $(date +%s) - START ))
echo "Restore duration: ${DURATION}s" >> "$REPORT_FILE"

# 3. Validate row counts against expected minimums
psql "$TEST_DB" -t -c "
  SELECT tablename, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC
  LIMIT 20;
" >> "$REPORT_FILE"

# 4. Validate schema matches production
pg_dump --schema-only "$TEST_DB" > /tmp/restored_schema.sql
pg_dump --schema-only "$PROD_DB" > /tmp/prod_schema.sql
if diff -q /tmp/restored_schema.sql /tmp/prod_schema.sql > /dev/null; then
  echo "Schema: MATCH" >> "$REPORT_FILE"
else
  echo "Schema: DIVERGED — investigate immediately" >> "$REPORT_FILE"
  diff /tmp/restored_schema.sql /tmp/prod_schema.sql >> "$REPORT_FILE"
fi

# 5. Run application smoke test against restored DB
DATABASE_URL="postgresql://localhost/$TEST_DB" pytest tests/smoke/ -q >> "$REPORT_FILE" 2>&1

echo "Result: PASSED" >> "$REPORT_FILE"
```

### CI Integration

```yaml
# .github/workflows/restore-verify.yml
name: Monthly Restore Verification
on:
  schedule:
    - cron: '0 3 1 * *'  # First day of each month at 3 AM
jobs:
  verify:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - name: Download latest backup
        run: aws s3 cp s3://$BACKUP_BUCKET/latest/full.dump ./backup.dump
      - name: Run restore verification
        run: bash scripts/restore-verify.sh
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: restore-report
          path: docs/dr-reports/restore-verify-*.md
```

---

## MUST DO

- MUST derive RTO/RPO from actual NFR documents or SLAs, not arbitrary defaults
- MUST classify every stateful component into a recovery tier
- MUST include verification steps in every restore procedure — restoring without validating is not restoring
- MUST test backups regularly — an untested backup is not a backup
- MUST store at least one backup copy off-site (different region or provider)
- MUST encrypt backups at rest and in transit
- MUST document the restore procedure so that any team member can execute it, not just the person who wrote it
- MUST version the DR runbook and review it quarterly
- MUST measure actual RTO/RPO during drills and compare against targets

## MUST NOT DO

- MUST NOT assume backups are valid without restore testing — use monthly verification drills instead
- MUST NOT store all backup copies in the same region/AZ as the primary — a regional outage would destroy both
- MUST NOT skip the dependency mapping — restoring services in the wrong order causes cascading failures
- MUST NOT hardcode credentials in runbook procedures — reference the secret store path instead
- MUST NOT create a DR plan and never drill it — an undrilled plan is a guess, not a plan
- MUST NOT set RTO/RPO targets that the architecture cannot actually achieve — if the backup runs hourly, the RPO cannot be 15 minutes
- MUST NOT treat DR planning as a one-time activity — infrastructure changes invalidate existing plans
- MUST NOT rely solely on cloud provider guarantees without verifying them — "11 nines durability" does not protect against accidental deletion or application-level corruption
