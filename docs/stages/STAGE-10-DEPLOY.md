# Stage 10: Deployment & Monitoring — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to deploy reviewed code to production with full observability — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 9 (Review — PR approved, all quality gates passed)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
                    ┌─────────────────────────┐
                    │  Verify Review Approval  │
                    │  (ST9 gate passed)       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Production Readiness    │
                    │  Review (PRR checklist)  │
                    └────────────┬────────────┘
                                 │
                       ┌─────────┴─────────┐
                       │                   │
                   ✅ READY           ❌ NOT READY
                       │                   │
                       │                   ▼
                       │         ┌──────────────────┐
                       │         │ Flag blockers,    │
                       │         │ return to ST9     │
                       │         └──────────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Build & Package           │
          │  ▓ docker-optimize         │
          │  ▓ ci-cd-setup             │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Deploy Infrastructure     │
          │  ▓ iac-deploy (Terraform)  │
          │  ▓ k8s-deploy (manifests)  │
          │  ▓ deploy-strategy         │
          │    (GitOps / canary)       │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Database Migration        │
          │  (expand-contract pattern) │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Deployment Verification   │
          │  ▓ Health checks           │
          │  ▓ Smoke tests             │
          │  ▓ monitoring-setup        │
          │    (Prometheus/Grafana)     │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Output: Deployment URL,   │
          │  CI/CD pipeline, K8s       │
          │  manifests, dashboards,    │
          │  runbooks, SLO defs        │
          └────────────────────────────┘
```

### Diagram B — I/O Artifact Contract

```
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  UPSTREAM INPUTS                                                      ░
 ░                                                                       ░
 ░  ┌───────────────────┐        ┌───────────────────┐                   ░
 ░  │  ST 9: REVIEW     │        │  ALL PRIOR STAGES │                   ░
 ░  │                   │        │                   │                   ░
 ░  │  review report    │        │  source code      │                   ░
 ░  │  (approved)       │        │  test suite       │                   ░
 ░  │  PR URL           │        │  schema/migrations│                   ░
 ░  │  merge strategy   │        │  config files     │                   ░
 ░  └────────┬──────────┘        └────────┬──────────┘                   ░
 ░           │                            │                              ░
 ░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
              │                            │
              ▼                            ▼
 ┌────────────────────────────────────────────────────────────────┐
 │                                                                │
 │              STAGE 10: DEPLOYMENT & MONITORING                 │
 │                                                                │
 │  █ ci-cd-setup  █ docker-optimize  █ k8s-deploy               │
 │  █ iac-deploy  █ deploy-strategy  █ monitoring-setup           │
 │  █ incident-response  █ disaster-recovery                      │
 │                                                                │
 └──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  DOWNSTREAM OUTPUTS                                                   ░
 ░                                                                       ░
 ░  Deployment   .github/       k8s/ or     Grafana     docs/           ░
 ░  URL          workflows/     helm/       dashboards  runbooks/       ░
 ░               ci.yml         manifests   (JSON)      *.md            ░
 ░     │            │              │            │           │            ░
 ░     ▼            ▼              ▼            ▼           ▼            ░
 ░  ┌──────────────────────────────────────────────────────────┐         ░
 ░  │  ST 11: DOCS                                             │         ░
 ░  │  (link in documentation, operational docs, SLO refs,     │         ░
 ░  │   architecture diagrams, handover)                       │         ░
 ░  └──────────────────────────────────────────────────────────┘         ░
 ░                                                                       ░
 ░  SLO definitions ──→ Operations (Prometheus recording rules)          ░
 ░  Incident runbooks ──→ Operations (on-call reference)                 ░
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | CI/CD pipeline (full) | `ci-cd-setup` skill | ✅ Covered | — |
| 2 | Production Docker image | `docker-optimize` skill | ✅ Covered | — |
| 3 | Kubernetes deployment | `k8s-deploy` skill (manifests, probes, HPA, RBAC) | ✅ Covered | — |
| 4 | Infrastructure as Code | `iac-deploy` skill (Terraform/Pulumi) | ✅ Covered | — |
| 5 | Monitoring (Prometheus/Grafana) | `monitoring-setup` skill (golden signals, SLOs) | ✅ Covered | — |
| 6 | Structured logging | `monitoring-setup` skill (Step 6.4) | ✅ Covered | — |
| 7 | Distributed tracing (OpenTelemetry) | `monitoring-setup` skill (Step 6.5) | ✅ Covered | — |
| 8 | Incident runbooks | `incident-response` skill | ✅ Covered | — |
| 9 | SLO definition from NFRs | `monitoring-setup` skill (Step 6.6) | ✅ Covered | **SRE (Google)** |
| 10 | Deployment verification (health + smoke) | Stage 10 prompt (Step 8) | ✅ Covered | — |
| 11 | GitOps workflow | `deploy-strategy` (Step 2: ArgoCD/Flux setup) | ✅ Covered | **GitOps (WeaveWorks)** |
| 12 | Canary / progressive delivery | `deploy-strategy` (Step 3: Flagger/Argo Rollouts) | ✅ Covered | **Progressive Delivery (Flagger/Argo Rollouts)** |
| 13 | Secret rotation strategy | `deploy-strategy` (Step 7: rotation schedule by secret type, vault integration patterns, K8s ESO, zero-downtime dual-read rotation, hygiene checklist) | ✅ Covered | **Secret Management Best Practices** |
| 14 | Disaster recovery plan | `disaster-recovery` skill (RTO/RPO, backup, failover, DR drills) | ✅ Covered | **DR / BCP (ISO 22301)** |
| 15 | Cost estimation / FinOps | `iac-deploy` (Step 13: Infracost integration, CI cost diff on PRs, resource right-sizing, cost tagging, budget alerts, optimization checklist) | ✅ Covered | **FinOps** |
| 16 | Production readiness review (PRR) | `deploy-strategy` (Step 5: PRR checklist) | ✅ Covered | **Google PRR** |
| 17 | Database migration in deployment | `deploy-strategy` (Step 4: expand-contract + migration ordering) | ✅ Covered | **Zero-Downtime Migration** |
| 18 | CDN / edge caching | `deploy-strategy` (Step 8: CDN provider setup, Cache-Control strategy by content type, invalidation patterns, edge functions) | ✅ Covered | **Edge Caching** |
| 19 | Mobile app deployment (Play Store / App Store) | `deploy-strategy` (Step 9: Fastlane + Gradle/Xcode, signing key management, versioning, staged rollout with crash monitoring) | ✅ Covered | **Mobile Release Engineering** |
| 20 | Serverless deployment | `iac-deploy` (Step 14: AWS Lambda, GCP Cloud Functions, API Gateway, Terraform + Pulumi patterns) | ✅ Covered | — |
| 21 | Static site / SSR deployment | `iac-deploy` (Step 14: Vercel, Netlify, Cloudflare Pages, Firebase Hosting, preview deployments) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **GitOps (WeaveWorks)** | Declarative desired state in git, reconciliation loop | ✅ ArgoCD/Flux setup in `deploy-strategy` Step 2, git-as-source-of-truth |
| **Progressive Delivery** | Canary releases with automated metric-based rollback | ✅ Flagger + Argo Rollouts with metric-based rollback in `deploy-strategy` Step 3 |
| **Secret Management** | Rotation schedule, vault integration, no long-lived credentials | ✅ `deploy-strategy` Step 7: rotation schedule by type, vault integration (Vault/AWS SM/GCP SM/Azure KV), K8s ESO, dual-read zero-downtime rotation |
| **ISO 22301 (BCP/DR)** | Recovery Time Objective, Recovery Point Objective, failover procedure | ✅ RTO/RPO targets, backup strategy, failover runbook, DR drills in `disaster-recovery` |
| **Google PRR** | Formal production readiness review template | ✅ PRR checklist (reliability, observability, security, data, ops) in `deploy-strategy` Step 5 |
| **Zero-Downtime Migration** | Run migration before deploy, backward-compatible schema changes | ✅ Expand-contract pattern + migration ordering in `deploy-strategy` Step 4 |
| **FinOps** | Infrastructure cost estimation and optimization | ✅ `iac-deploy` Step 13: Infracost CI integration, resource right-sizing, cost tagging strategy, budget alerts, optimization checklist |
| **SRE (Google)** | SLOs, error budgets, toil reduction | ✅ SLOs defined from NFRs, error budget tracking |

## Gap Proposals

### Gap 10.1: GitOps and progressive delivery (Priority: P1)

**Problem it solves:** CI/CD pushes directly to cluster with rolling update only. No declarative desired-state reconciliation, no canary releases with automated metric-based rollback.

**What to add:**
- ArgoCD or Flux integration for declarative deployment
- Canary releases with Flagger or Argo Rollouts
- Metric-based automated rollback (error rate, latency)

**Existing coverage:** `ci-cd-setup` covers push-based deployment. `k8s-deploy` covers rolling updates.

### Gap 10.2: Zero-downtime database migration strategy (Priority: P1)

**Problem it solves:** Migrations created in Stage 5 but deployment ordering is undefined. Running migrations during deploy can cause downtime or data corruption.

**What to add:**
- Migration ordering: backward-compatible migration → deploy new code → cleanup migration
- Expand-contract pattern for schema changes
- Pre-deploy migration verification step in CI/CD

**Existing coverage:** `fastapi-db-migrate` generates migrations. No deployment ordering strategy.

### Gap 10.3: Disaster recovery plan (Priority: P2)

**Problem it solves:** Rollback tested but no full DR plan. No RTO/RPO targets, no backup schedule, no failover procedure.

**What to add:**
- RTO/RPO targets derived from PRD NFRs
- Backup schedule and restore procedure
- Failover runbook for multi-region (if required)

**Existing coverage:** `incident-response` covers incident handling but not DR planning.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| Deployment URL | Stage 11 (Docs — link in documentation) | URL |
| CI/CD pipeline (full) | Future deploys | `.github/workflows/ci.yml` |
| K8s manifests / Helm chart | Future deploys, operations | `k8s/` or `helm/` |
| Monitoring dashboards | Operations, incident response | Grafana JSON |
| Incident runbooks | Operations | `docs/runbooks/*.md` |
| SLO definitions | Operations, Stage 11 (Docs) | Prometheus recording rules |

## Research Targets

- **GitHub**: `GitOps ArgoCD setup`, `canary deployment Flagger`, `zero-downtime migration`, `production readiness checklist`
- **Reddit**: r/devops — "GitOps vs push-based CI/CD", r/kubernetes — "canary deployment best practices"
- **Twitter/X**: `GitOps production`, `progressive delivery`, `zero-downtime deployment`

## Stack Coverage

| Stack | Deploy Coverage | Notes |
|-------|----------------|-------|
| Web (containerized) | ✅ Docker + K8s + CI/CD | Full pipeline |
| Serverless | ✅ `iac-deploy` Step 14 (Lambda, Cloud Functions, API Gateway) | Terraform + Pulumi patterns |
| Android | ✅ `deploy-strategy` Step 9 (Fastlane + Play Store) | Internal → beta → staged production rollout |
| iOS | ✅ `deploy-strategy` Step 9 (Fastlane + App Store Connect) | TestFlight → App Store Review → production |
| Static sites / SSR | ✅ `iac-deploy` Step 14 (Vercel, Netlify, Cloudflare Pages, Firebase) | Preview deployments per PR |

## Autonomy Verdict

**✅ Can run autonomously.** Exceptional skill coverage: `ci-cd-setup`, `docker-optimize`, `k8s-deploy`, `iac-deploy` (now with FinOps + serverless + static site deployment), `monitoring-setup`, `incident-response`, `deploy-strategy` (now with secret rotation, CDN/edge caching, mobile app deployment), `disaster-recovery`. All 21 capabilities ✅. Full stack coverage: containerized web, serverless, static/SSR, Android (Play Store), iOS (App Store).

---

## Execution Workflow

This section provides step-by-step instructions for the Stage 10 subagent dispatched by the pipeline orchestrator. Follow these steps in order, using the stack-conditional branching to skip inapplicable steps.

### Step 0: Pre-Flight Checks

Before any deployment work, verify the environment has the required tools and credentials.

#### 0.1 Verify Upstream Gate

```bash
# Confirm Stage 9 passed
test -f docs/stages/STAGE-9-REVIEW.md && echo "ST9 artifact exists"
# Check for PR URL in stage 9 output or pipeline state
```

If Stage 9 gate is not PASSED, return `gate: FAILED` with blocker: "Stage 9 not passed."

#### 0.2 Detect Deployment Target

Scan the project to determine which deployment path to follow:

```
IF Dockerfile exists AND (k8s/ OR helm/ OR docker-compose.yml exists)
  → DEPLOY_TARGET = "containerized"

ELSE IF serverless.yml OR sam-template.yml OR (terraform/ AND contains lambda/cloud_function resources)
  → DEPLOY_TARGET = "serverless"

ELSE IF next.config.* OR nuxt.config.* OR astro.config.* OR gatsby-config.* OR (package.json with "build" script AND static output)
  → DEPLOY_TARGET = "static-ssr"

ELSE IF build.gradle.kts with android block OR AndroidManifest.xml
  → DEPLOY_TARGET = "android"

ELSE IF *.xcodeproj OR Package.swift with iOS target
  → DEPLOY_TARGET = "ios"

ELSE IF Dockerfile exists (standalone)
  → DEPLOY_TARGET = "containerized"

ELSE
  → DEPLOY_TARGET = "containerized" (default — generate Dockerfile via docker-optimize)
```

Record `DEPLOY_TARGET` for conditional branching in subsequent steps.

#### 0.3 Verify Required Tools

Check tool availability based on `DEPLOY_TARGET`:

| DEPLOY_TARGET | Required Tools | Check Command |
|---------------|---------------|---------------|
| `containerized` | docker, kubectl, helm (optional), terraform (optional) | `docker --version && kubectl version --client` |
| `serverless` | terraform or pulumi, aws/gcloud CLI | `terraform version` or `pulumi version` |
| `static-ssr` | node/npm, target platform CLI (vercel/netlify/firebase) | `node --version` |
| `android` | java, gradle, bundletool, fastlane (optional) | `java -version && gradle --version` |
| `ios` | xcode, fastlane, cocoapods/spm | `xcodebuild -version && fastlane --version` |

```bash
# Universal checks
git --version || { echo "BLOCKER: git not found"; exit 1; }
gh --version 2>/dev/null || echo "WARN: gh CLI not found — PR operations will fail"
```

If a required tool is missing, return `gate: FAILED` with blocker listing the missing tool(s) and install instructions.

#### 0.4 Verify Credentials & Secrets

Check that required environment variables exist (do NOT log their values):

| DEPLOY_TARGET | Required Env Vars | Purpose |
|---------------|------------------|---------|
| `containerized` | `DOCKER_REGISTRY`, `KUBECONFIG` or `KUBE_CONTEXT` | Container registry push, cluster access |
| `serverless` | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` OR `GOOGLE_APPLICATION_CREDENTIALS` | Cloud provider auth |
| `static-ssr` | `VERCEL_TOKEN` or `NETLIFY_AUTH_TOKEN` or `FIREBASE_TOKEN` | Platform deploy auth |
| `android` | `ANDROID_KEYSTORE_PATH`, `GOOGLE_PLAY_KEY` | APK signing, Play Store upload |
| `ios` | `MATCH_PASSWORD`, `APP_STORE_CONNECT_API_KEY` | Code signing, App Store upload |

```bash
# Example: check containerized credentials exist (not their values)
[ -n "${DOCKER_REGISTRY:-}" ] || echo "WARN: DOCKER_REGISTRY not set"
[ -n "${KUBECONFIG:-}" ] || [ -f "$HOME/.kube/config" ] || echo "WARN: No kubeconfig found"
```

Missing credentials are a WARNING, not a blocker — skills can still generate configs/manifests without deploying. Flag for user to provide before actual deployment.

---

### Step 1: Production Readiness Review (PRR)

Invoke `deploy-strategy` Step 5 PRR checklist against the project:

1. Read the PRD NFRs, test results from Stage 8, and review report from Stage 9
2. Evaluate each PRR category: Reliability, Observability, Security, Data, Operations
3. If any PRR category is RED (critical gap), return `gate: FAILED` with blockers
4. If all categories are GREEN or YELLOW, proceed

**Output:** PRR report appended to deployment documentation.

---

### Step 2: Build & Package

**Skip if:** `DEPLOY_TARGET` is `static-ssr` or `serverless` (no container needed).

#### 2.1 Optimize Docker Image

Invoke `/docker-optimize` on the project's Dockerfile:
- Multi-stage build, minimal base image, non-root user, .dockerignore
- Health check defined in Dockerfile
- Security scan (if trivy/snyk available)

#### 2.2 Set Up CI/CD Pipeline

Invoke `/ci-cd-setup github-actions` (or gitlab-ci based on project):
- Build, test, lint, security scan stages
- Docker build + push to registry
- Deploy stage triggered on main branch merge
- Caching for dependencies and Docker layers

**Output:** `.github/workflows/ci.yml` (or `.gitlab-ci.yml`), optimized `Dockerfile`.

---

### Step 3: Provision Infrastructure

#### Containerized Path

1. Invoke `/iac-deploy write` — Terraform/Pulumi for cloud resources (VPC, cluster, database, secrets)
2. Invoke `/k8s-deploy` — Kubernetes manifests (Deployment, Service, Ingress, ConfigMap, Secrets, HPA, PDB, RBAC)
3. Invoke `/deploy-strategy` — GitOps setup (ArgoCD/Flux) + progressive delivery (canary/blue-green)

#### Serverless Path

1. Invoke `/iac-deploy write` with serverless focus (Step 14) — Lambda/Cloud Functions, API Gateway, IAM roles
2. Skip k8s-deploy and deploy-strategy GitOps steps

#### Static/SSR Path

1. Invoke `/iac-deploy write` with static site focus (Step 14) — Vercel/Netlify/Cloudflare Pages/Firebase config
2. Configure preview deployments per PR
3. Skip k8s-deploy

#### Mobile Path (Android/iOS)

1. Invoke `/deploy-strategy` Step 9 — Fastlane setup, signing config, versioning, staged rollout
2. Skip docker-optimize, k8s-deploy, iac-deploy

**Output:** Infrastructure definitions (`terraform/`, `k8s/`, `helm/`, or platform config).

---

### Step 4: Database Migration Strategy

**Skip if:** No database/migrations detected in project (no `alembic/`, `prisma/`, `migrations/`, `flyway/`).

Invoke `/deploy-strategy` Step 4 (expand-contract pattern):

1. Define migration ordering: pre-deploy migration → deploy new code → post-deploy cleanup
2. Add migration step to CI/CD pipeline (before deployment step)
3. Add pre-deploy migration verification (`/db-migrate-verify`)
4. Document rollback procedure for each migration

**Output:** Migration ordering documented, CI/CD pipeline updated with migration step.

---

### Step 5: Deploy & Verify

#### 5.1 Execute Deployment

Based on `DEPLOY_TARGET`, execute the appropriate deployment:

| Target | Deployment Command | Verification |
|--------|-------------------|--------------|
| `containerized` | `kubectl apply` or ArgoCD sync | `kubectl rollout status` |
| `serverless` | `terraform apply` or `pulumi up` | Invoke function endpoint |
| `static-ssr` | `vercel deploy --prod` or `netlify deploy --prod` | Fetch deployed URL |
| `android` | `fastlane supply` or Gradle Play Publisher | Play Console status |
| `ios` | `fastlane deliver` | App Store Connect status |

#### 5.2 Health Check Verification

```bash
# HTTP health check (containerized, serverless, static)
DEPLOY_URL="${DEPLOY_URL:-http://localhost:8080}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOY_URL/health" || echo "000")

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "Health check: PASSED"
elif [ "$HTTP_STATUS" -eq 000 ]; then
  echo "Health check: UNREACHABLE — deployment may have failed"
else
  echo "Health check: FAILED (HTTP $HTTP_STATUS)"
fi
```

#### 5.3 Smoke Test

Run a minimal set of critical-path tests against the deployed environment:

```bash
# Run smoke tests if they exist
if [ -d "tests/smoke" ]; then
  DEPLOY_URL="$DEPLOY_URL" pytest tests/smoke/ -v --tb=short
elif [ -f "tests/e2e/smoke.spec.ts" ]; then
  BASE_URL="$DEPLOY_URL" npx playwright test tests/e2e/smoke.spec.ts
else
  echo "WARN: No smoke tests found — create tests/smoke/ for post-deploy verification"
fi
```

#### 5.4 Failure Handling & Rollback

```
IF health check FAILS OR smoke tests FAIL:
  1. Capture logs: kubectl logs deployment/<app> --tail=100
  2. Capture events: kubectl get events --sort-by='.lastTimestamp' | tail -20
  3. Execute rollback:
     - Containerized: kubectl rollout undo deployment/<app>
     - Serverless: terraform apply with previous state / pulumi stack export
     - Static: redeploy previous git SHA
     - Mobile: halt staged rollout in Play Console / App Store Connect
  4. Verify rollback succeeded (re-run health check)
  5. Return gate: FAILED with failure details and rollback confirmation
  6. DO NOT retry deployment — return to Stage 9 with diagnostic info
```

---

### Step 6: Set Up Monitoring & Observability

Invoke `/monitoring-setup` for the deployed service:

1. **Golden signals** — Latency, traffic, errors, saturation metrics
2. **SLO definitions** — Derived from PRD NFRs (via `monitoring-setup` Step 6.6)
3. **Alert rules** — Burn-rate alerts for SLO violations
4. **Grafana dashboards** — Service dashboard with golden signals + SLO status
5. **Structured logging** — JSON log format with correlation IDs
6. **Distributed tracing** — OpenTelemetry instrumentation (if multi-service)

**Cross-skill wiring:** Record the Grafana dashboard URL(s) and SLO recording rule file paths — these are needed by Step 7 (runbooks) and Step 8 (DR plan).

**Output:** `monitoring/dashboards/*.json`, `monitoring/slo-rules.yml`, `monitoring/alert-rules.yml`.

---

### Step 7: Generate Incident Runbooks

Invoke `/incident-response runbook` for common failure modes:

1. Generate runbooks for: service down, high error rate, high latency, database connection failure, out of memory, disk full
2. **Cross-skill wiring:** Each runbook MUST include:
   - Link to the Grafana dashboard URL from Step 6
   - Link to the relevant SLO recording rules from Step 6
   - Link to the deployment rollback procedure from Step 5.4
3. Write runbooks to `docs/runbooks/`

**Output:** `docs/runbooks/*.md`

---

### Step 8: Disaster Recovery Plan

Invoke `/disaster-recovery` with the PRD/NFR document:

1. Extract RTO/RPO targets
2. Inventory stateful components
3. Define backup strategy and schedule
4. Create restore procedures with verification
5. **Cross-skill wiring:** Reference monitoring alerts (Step 6) for failure detection, incident runbooks (Step 7) for escalation
6. Write DR runbook to `docs/DR-RUNBOOK.md`

**Output:** `docs/DR-RUNBOOK.md`

---

### Step 9: CDN & Edge Caching (Optional)

**Skip if:** `DEPLOY_TARGET` is `android` or `ios` or project has no static assets / API responses suitable for caching.

Invoke `/deploy-strategy` Step 8:

1. CDN provider selection and setup
2. Cache-Control headers by content type
3. Cache invalidation strategy
4. Edge functions (if applicable)

---

### Step 10: Secret Rotation Strategy

Invoke `/deploy-strategy` Step 7:

1. Inventory all secrets (API keys, DB passwords, JWT signing keys, TLS certs)
2. Define rotation schedule by secret type
3. Configure vault integration (HashiCorp Vault / AWS SM / GCP SM / Azure KV)
4. Set up zero-downtime dual-read rotation pattern

---

### Step 11: Produce Artifacts & Gate Result

#### 11.1 Artifact Checklist

Verify all required artifacts exist on disk:

| Artifact | Path | Required For |
|----------|------|-------------|
| CI/CD pipeline | `.github/workflows/ci.yml` | All targets |
| Deployment URL | (in gate result JSON) | All targets |
| Monitoring dashboards | `monitoring/dashboards/*.json` | All targets |
| SLO definitions | `monitoring/slo-rules.yml` | All targets |
| Alert rules | `monitoring/alert-rules.yml` | All targets |
| Incident runbooks | `docs/runbooks/*.md` | All targets |
| DR runbook | `docs/DR-RUNBOOK.md` | All targets |
| Dockerfile | `Dockerfile` | containerized only |
| K8s manifests | `k8s/` or `helm/` | containerized only |
| IaC definitions | `terraform/` or `pulumi/` | containerized, serverless |
| Platform config | `vercel.json` / `netlify.toml` / `firebase.json` | static-ssr only |
| Fastlane config | `fastlane/Fastfile` | android, ios only |

#### 11.2 Gate Criteria

```
PASSED — ALL of:
  ✓ CI/CD pipeline file exists and is valid YAML
  ✓ Deployment succeeded (health check returned 200) OR deployment configs generated (if no live environment)
  ✓ At least one monitoring dashboard exists
  ✓ At least one incident runbook exists
  ✓ DR runbook exists
  ✓ All required artifacts for DEPLOY_TARGET exist on disk

FAILED — ANY of:
  ✗ PRR has RED category (critical gap)
  ✗ Deployment health check failed AND rollback was executed
  ✗ Smoke tests failed AND rollback was executed
  ✗ Required tool missing (Step 0.3 blocker)
  ✗ CI/CD pipeline file missing or invalid
```

#### 11.3 Return Gate Result

```json
{
  "gate": "PASSED",
  "deploy_target": "containerized",
  "artifacts": {
    "deploy_url": "https://app.example.com",
    "ci_pipeline": ".github/workflows/ci.yml",
    "monitoring_dashboards": "monitoring/dashboards/",
    "slo_definitions": "monitoring/slo-rules.yml",
    "runbooks": "docs/runbooks/",
    "dr_runbook": "docs/DR-RUNBOOK.md"
  },
  "decisions": [
    "Selected ArgoCD for GitOps (team already uses ArgoCD)",
    "Canary deployment with 10% → 50% → 100% traffic shift",
    "RTO: 1h, RPO: 15min (Tier 1) based on PRD SLA 99.9%"
  ],
  "blockers": [],
  "summary": "Deployed to K8s via ArgoCD with canary strategy. Monitoring: 4 golden signal dashboards, 3 SLOs, 6 runbooks, DR plan with quarterly drills."
}
```

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gaps resolved: `deploy-strategy` skill created with GitOps, canary/blue-green, zero-downtime DB migrations, PRR — 4 ❌/⚠️ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `disaster-recovery` skill created with RTO/RPO, backup strategy, failover runbook, DR drills — DR ❌ flipped to ✅ |
| 2026-03-14 | All remaining gaps resolved: #13 secret rotation added to `deploy-strategy` Step 7 (rotation schedule, vault integration, K8s ESO, dual-read pattern) ❌→✅; #15 FinOps added to `iac-deploy` Step 13 (Infracost, right-sizing, tagging, budget alerts) ❌→✅; #18 CDN/caching added to `deploy-strategy` Step 8 (Cache-Control strategy, invalidation, edge functions) ⚠️→✅; Mobile deploy added to `deploy-strategy` Step 9 (Fastlane, Play Store, App Store, staged rollout) ❌→✅; Serverless + static site deploy added to `iac-deploy` Step 14 (Lambda, Vercel, Netlify, Firebase) ⚠️→✅. All 21 capabilities now ✅ |
| 2026-03-14 | Full autonomy overhaul: Added 12-step Execution Workflow (Steps 0-11) with stack-conditional branching (containerized/serverless/static-ssr/android/ios), pre-flight checks (tools + credentials), gate criteria (PASSED/FAILED definitions), failure handling with rollback procedures, cross-skill wiring (monitoring→runbooks→DR), and artifact production checklist. Added `artifacts_in` to orchestrator DAG. Added `triggers:` to ci-cd-setup, docker-optimize, k8s-deploy skills. Enhanced disaster-recovery with backup encryption/key management (Step 7A) and restore verification testing (Step 7B). |
