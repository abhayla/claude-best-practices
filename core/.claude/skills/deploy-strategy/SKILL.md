---
name: deploy-strategy
description: >
  Advanced deployment strategies: GitOps (ArgoCD/Flux), progressive delivery
  (canary/blue-green with Flagger/Argo Rollouts), zero-downtime DB migrations
  (expand-contract), and production readiness review. Use before first production deploy.
triggers:
  - deploy strategy
  - gitops
  - canary deploy
  - progressive delivery
  - blue green
  - zero downtime
  - db migration deploy
  - production readiness
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<deployment target description, or 'review current strategy'>"
---

# Deploy Strategy — GitOps, Progressive Delivery & Zero-Downtime Migrations

Configure advanced deployment strategies for production-grade releases.

**Input:** $ARGUMENTS

---

## STEP 1: Assess Current State

Determine what deployment infrastructure already exists:

```bash
# Check for existing deployment configs
ls -la .github/workflows/deploy* k8s/ helm/ argocd/ flux/ 2>/dev/null

# Check for database migration setup
ls -la migrations/ alembic/ prisma/ 2>/dev/null

# Check current deployment method
grep -l "deploy\|release\|publish" .github/workflows/*.yml 2>/dev/null
```

Present the current state and recommended strategy:

```markdown
## Current Deployment State

| Component | Status | Tool |
|-----------|--------|------|
| CI pipeline | ✅ | GitHub Actions |
| Container build | ✅ | Docker multi-stage |
| K8s manifests | ✅ | Raw YAML / Helm |
| GitOps reconciliation | ❌ | None |
| Progressive delivery | ❌ | Rolling update only |
| DB migration ordering | ❌ | No deploy-time strategy |
| Production readiness | ❌ | No PRR checklist |
```

---

## STEP 2: GitOps Setup

### 2.1 Choose GitOps Tool

| Tool | Best For | Complexity |
|------|---------|-----------|
| ArgoCD | Teams wanting a UI, multi-cluster | Medium |
| Flux | GitOps-purist, lightweight | Low |
| Neither | Simple apps, not on K8s | — |

### 2.2 ArgoCD Configuration

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: <git-repo-url>
    targetRevision: main
    path: k8s/overlays/production  # or helm/
  destination:
    server: https://kubernetes.default.svc
    namespace: <app-namespace>
  syncPolicy:
    automated:
      prune: true        # Remove resources deleted from git
      selfHeal: true      # Revert manual cluster changes
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 2.3 Flux Configuration

```yaml
# flux/kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: <app-name>
  namespace: flux-system
spec:
  interval: 5m
  path: ./k8s/overlays/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: <app-name>
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: <app-name>
      namespace: <app-namespace>
  timeout: 3m
```

### 2.4 GitOps Workflow

```
Developer → PR → Review → Merge to main
                                  ↓
                        ArgoCD/Flux detects change
                                  ↓
                        Sync cluster to desired state
                                  ↓
                        Health check passes → Done
                        Health check fails → Alert + auto-rollback
```

Key principle: **Git is the source of truth.** No `kubectl apply` or `helm install` outside of GitOps.

---

## STEP 3: Progressive Delivery

### 3.1 Strategy Selection

| Strategy | Risk | Complexity | Best For |
|----------|------|-----------|----------|
| Rolling Update | Medium | Low | Simple apps, no traffic splitting |
| Blue/Green | Low | Medium | Instant rollback needed |
| Canary | Very Low | High | High-traffic, metric-driven releases |
| A/B Testing | Feature-dependent | High | UX experiments |

### 3.2 Canary with Flagger (Istio/Nginx)

```yaml
# flagger/canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: <app-name>
  namespace: <namespace>
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <app-name>
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s           # Check every 30s
    threshold: 5             # Max failed checks before rollback
    maxWeight: 50            # Max traffic to canary (%)
    stepWeight: 10           # Increase canary traffic by 10% each step
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99            # Rollback if success rate < 99%
        interval: 30s
      - name: request-duration
        thresholdRange:
          max: 500           # Rollback if p99 latency > 500ms
        interval: 30s
    webhooks:
      - name: smoke-test
        type: pre-rollout
        url: http://flagger-loadtester/
        metadata:
          cmd: "curl -s http://<app-name>-canary/health"
```

### 3.3 Canary with Argo Rollouts

```yaml
# k8s/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: <app-name>
spec:
  replicas: 3
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 2m}     # Observe metrics
        - setWeight: 30
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
      canaryMetadata:
        labels:
          role: canary
      stableMetadata:
        labels:
          role: stable
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2
        args:
          - name: service-name
            value: <app-name>
  revisionHistoryLimit: 3
```

### 3.4 Blue/Green Deployment

```yaml
# k8s/rollout-bluegreen.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: <app-name>
spec:
  strategy:
    blueGreen:
      activeService: <app-name>-active
      previewService: <app-name>-preview
      autoPromotionEnabled: false   # Manual promotion after verification
      prePromotionAnalysis:
        templates:
          - templateName: smoke-test
      postPromotionAnalysis:
        templates:
          - templateName: success-rate
```

---

## STEP 4: Zero-Downtime Database Migrations

### 4.1 The Expand-Contract Pattern

Every schema change follows three phases:

```
Phase 1: EXPAND (pre-deploy migration)
  ┌─────────────────────────────────────┐
  │ Add new column/table (nullable)     │
  │ No constraints yet                  │
  │ Old code continues to work          │
  └─────────────────────────────────────┘
                    ↓
Phase 2: DEPLOY (new code)
  ┌─────────────────────────────────────┐
  │ Deploy code that writes to BOTH     │
  │ old and new columns                 │
  │ Reads from new column with fallback │
  └─────────────────────────────────────┘
                    ↓
Phase 3: CONTRACT (post-deploy migration)
  ┌─────────────────────────────────────┐
  │ Backfill data from old to new       │
  │ Add NOT NULL constraints            │
  │ Drop old column (separate deploy)   │
  └─────────────────────────────────────┘
```

### 4.2 Migration Deployment Ordering

```yaml
# CI/CD pipeline migration step
jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - name: Run pre-deploy migrations
        run: |
          # Only EXPAND migrations (additive, backward-compatible)
          alembic upgrade head
          # Verify: old code still works with new schema
          curl -f http://staging/health

  deploy:
    needs: migrate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy new code
        run: <deploy command>

  post-migrate:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Run post-deploy migrations
        run: |
          # CONTRACT migrations (cleanup, add constraints)
          alembic upgrade head
```

### 4.3 Migration Safety Rules

| Rule | Why |
|------|-----|
| Never rename a column in one step | Old code references old name → crash |
| Never change a column type in one step | Old code expects old type → error |
| Never add NOT NULL without a default | Old code inserts without the column → crash |
| Never drop a column that's still read | Old instances read the column → error |
| Always separate DDL and DML migrations | Large data migrations lock tables |
| Always test migrations on a production-size dataset | Migrations that take seconds on dev take hours on prod |

### 4.4 Rollback Strategy

```markdown
### Migration Rollback Plan

| Migration | Rollback Command | Data Loss? |
|-----------|-----------------|-----------|
| 001_add_column | `alembic downgrade -1` | No |
| 002_backfill_data | Manual: restore from backup | Yes — backfill is one-way |
| 003_add_constraint | `alembic downgrade -1` | No |
| 004_drop_old_column | ❌ IRREVERSIBLE | Yes — data lost |
```

**Rule:** Mark any migration that drops data as IRREVERSIBLE and require explicit approval.

---

## STEP 5: Production Readiness Review (PRR)

Before the first production deploy, complete this checklist:

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
## Production Readiness Review

**Service:** <name>
**Date:** <date>
**Reviewer:** Claude Code

| Category | Score | Status |
|----------|-------|--------|
| Reliability | 7/7 | ✅ Ready |
| Observability | 8/8 | ✅ Ready |
| Security | 6/6 | ✅ Ready |
| Data | 4/5 | ⚠️ PII doc missing |
| Operations | 5/5 | ✅ Ready |

**Verdict:** READY for production (1 minor item)
```

---

## STEP 6: Deployment Runbook

Generate a deployment runbook:

```markdown
## Deployment Runbook: <service>

### Pre-deploy
1. Verify all tests pass on main
2. Run pre-deploy migrations against staging
3. Smoke test staging with new schema + old code
4. Create release tag: `git tag v<version>`

### Deploy
1. Push tag → triggers deploy pipeline
2. ArgoCD/Flux syncs new manifests
3. Canary starts at 10% traffic
4. Monitor error rate and latency for 5 minutes
5. If metrics healthy → auto-promote to 50%, then 100%
6. If metrics degrade → auto-rollback to previous version

### Post-deploy
1. Run post-deploy migrations (contract phase)
2. Verify health endpoint on all pods
3. Check Grafana dashboard for anomalies
4. Run smoke tests against production
5. Notify team in Slack: "v<version> deployed successfully"

### Rollback
1. `kubectl argo rollouts undo <app-name>` (Argo Rollouts)
2. Or: revert git commit → ArgoCD auto-syncs old version
3. Run `alembic downgrade -1` if migration rollback needed
4. Verify health endpoint returns 200
5. Create incident ticket if rollback was due to a bug
```

---

## MUST DO

- Always assess current deployment state before recommending changes
- Always use the expand-contract pattern for schema changes
- Always separate pre-deploy and post-deploy migrations
- Always configure metric-based rollback for canary deployments
- Always complete the PRR checklist before first production deploy
- Always generate a deployment runbook

## MUST NOT DO

- MUST NOT run migrations and deploy code in a single atomic step — they must be separate
- MUST NOT skip the PRR for "simple" services — every production service needs it
- MUST NOT recommend GitOps for non-Kubernetes deployments — use push-based CI/CD instead
- MUST NOT mark irreversible migrations as "rollback safe"
- MUST NOT deploy canary without automated rollback metrics
- MUST NOT duplicate CI/CD setup that `ci-cd-setup` already handles — this skill adds GitOps and progressive delivery on top
