# Stage 10: Deployment & Monitoring — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to deploy reviewed code to production with full observability — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 9 (Review — PR approved, all quality gates passed)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

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
| 13 | Secret rotation strategy | None — secrets created but no rotation schedule or automation | ❌ Missing | **Secret Management Best Practices** |
| 14 | Disaster recovery plan | `disaster-recovery` skill (RTO/RPO, backup, failover, DR drills) | ✅ Covered | **DR / BCP (ISO 22301)** |
| 15 | Cost estimation / FinOps | None | ❌ Missing | **FinOps** |
| 16 | Production readiness review (PRR) | `deploy-strategy` (Step 5: PRR checklist) | ✅ Covered | **Google PRR** |
| 17 | Database migration in deployment | `deploy-strategy` (Step 4: expand-contract + migration ordering) | ✅ Covered | **Zero-Downtime Migration** |
| 18 | CDN / edge caching | None | ⚠️ Partial — IaC mentions CDN but no caching strategy | **Edge Caching** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **GitOps (WeaveWorks)** | Declarative desired state in git, reconciliation loop | ✅ ArgoCD/Flux setup in `deploy-strategy` Step 2, git-as-source-of-truth |
| **Progressive Delivery** | Canary releases with automated metric-based rollback | ✅ Flagger + Argo Rollouts with metric-based rollback in `deploy-strategy` Step 3 |
| **Secret Management** | Rotation schedule, vault integration, no long-lived credentials | ⚠️ SealedSecrets/ESO mentioned but no rotation strategy |
| **ISO 22301 (BCP/DR)** | Recovery Time Objective, Recovery Point Objective, failover procedure | ✅ RTO/RPO targets, backup strategy, failover runbook, DR drills in `disaster-recovery` |
| **Google PRR** | Formal production readiness review template | ✅ PRR checklist (reliability, observability, security, data, ops) in `deploy-strategy` Step 5 |
| **Zero-Downtime Migration** | Run migration before deploy, backward-compatible schema changes | ✅ Expand-contract pattern + migration ordering in `deploy-strategy` Step 4 |
| **FinOps** | Infrastructure cost estimation and optimization | ❌ No cost awareness |
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
| Serverless | ⚠️ `iac-deploy` covers AWS Lambda/GCF but no dedicated workflow | Limited |
| Android | ❌ | No Play Store deployment, no Fastlane |
| iOS | ❌ | No App Store deployment |
| Static sites | ⚠️ IaC mentions CDN but no Vercel/Netlify/Cloudflare Pages | Limited |

## Autonomy Verdict

**✅ Can run autonomously.** Exceptional skill coverage: `ci-cd-setup`, `docker-optimize`, `k8s-deploy`, `iac-deploy`, `monitoring-setup`, `incident-response`, `deploy-strategy`, `disaster-recovery`. This stage has 8 dedicated skills covering the full deployment spectrum. Remaining minor gaps: secret rotation strategy, FinOps, CDN caching strategy.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gaps resolved: `deploy-strategy` skill created with GitOps, canary/blue-green, zero-downtime DB migrations, PRR — 4 ❌/⚠️ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `disaster-recovery` skill created with RTO/RPO, backup strategy, failover runbook, DR drills — DR ❌ flipped to ✅ |
