# Gap Analysis: PRD → Production Autonomous Pipeline

> **Date:** 2026-03-13
> **Scope:** Comprehensive audit of `core/.claude/` tooling (76 skills, 16 agents, 14 rules) to determine readiness for fully autonomous PRD-to-production delivery.
> **Architecture:** 12-stage pipeline (Stage 0–11) with parallel execution across dedicated Claude Code context windows.

---

## Pipeline Architecture (12 Stages)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      STAGE 0: MASTER ORCHESTRATOR                           │
│              Spawns all stages, monitors gates, manages state               │
└──┬──────┬──────┬──────────────────────────────────────────────────────────┬──┘
   │      │      │                                                          │
   ▼      │      │                                                          │
┌──────┐  │      │     WAVE 1 (immediate — no deps)                        │
│ ST 1 │  │      │                                                          │
│ PRD  │  │      │                                                          │
└──┬───┘  │      │                                                          │
   │      ▼      ▼                                                          │
   │  ┌──────┐ ┌──────┐  WAVE 2 (after Stage 1)                            │
   ├─→│ ST 2 │ │ ST 3 │  Plan + Scaffold run in parallel                   │
   │  │ PLAN │ │SCAFF │                                                     │
   │  └──┬───┘ └──┬───┘                                                    │
   │     │        │                                                         │
   │     │     ┌──▼───┐   WAVE 3 (after Stage 1 + 3)                       │
   │     │     │ ST 4 │   Demo uses PRD + scaffolded project                │
   │     │     │ DEMO │                                                     │
   │     │     └──────┘                                                     │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 4 (after Stage 2 + 3)                       │
   │  │ ST 5 │            Schema needs plan + scaffolded project            │
   │  │SCHEMA│                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 5 (after Stage 2 + 5)                       │
   │  │ ST 6 │            Pre-impl tests need plan + schema                 │
   │  │TESTS │                                                              │
   │  │(pre) │                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 6 (after Stage 6)                           │
   │  │ ST 7 │            Implement against failing tests                   │
   │  │ IMPL │                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 7 (after Stage 7)                           │
   │  │ ST 8 │            Post-impl tests need running code                 │
   │  │TESTS │                                                              │
   │  │(post)│                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 8 (after Stage 8)                           │
   │  │ ST 9 │            Review the complete, tested code                  │
   │  │REVIEW│                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 9 (after Stage 9)                           │
   │  │ST 10 │            Deploy reviewed code                              │
   │  │DEPLOY│                                                              │
   │  └──┬───┘                                                              │
   │     ▼                                                                  │
   │  ┌──────┐            WAVE 10 (after Stage 10)                         │
   └─→│ST 11 │            Final docs + handover                             │
      │ DOCS │                                                              │
      └──────┘                                                              │
```

### Stage Summary Table

| Stage | Name | Purpose | Depends On | Key Skills/Agents | Doc |
|-------|------|---------|------------|-------------------|-----|
| 0 | Master Orchestrator | Spawn, gate-check, coordinate all stages | — | `subagent-driven-dev`, `skill-master` | `STAGE-0-MASTER-ORCHESTRATOR.md` |
| 1 | PRD | Generate or parse requirements document | — | `brainstorm`, `/github`, `/reddit`, `/twitter-x` | `STAGE-1-PRD.md` |
| 2 | Plan | Decompose PRD into tasks + ADRs | Stage 1 | `writing-plans`, `plan-to-issues`, `planner-researcher` | `STAGE-2-PLAN.md` |
| 3 | Scaffolding | Repo setup, CI skeleton, dev env, linters | Stage 1 | `ci-cd-setup`, `/github` (inspect scaffolds) | `STAGE-3-SCAFFOLDING.md` |
| 4 | HTML Demo | Interactive prototype with sample data | Stages 1, 3 | `ui-ux-pro-max`, `d3-viz`, `/github` | `STAGE-4-HTML-DEMO.md` |
| 5 | Schema & Data | DB design, migrations, seed data | Stages 2, 3 | `fastapi-db-migrate`, `pg-query`, `/github` | `STAGE-5-SCHEMA.md` |
| 6 | Pre-Impl Tests | TDD red phase: unit + contract + API stubs | Stages 2, 5 | `tdd`, `playwright` (stubs), `security-audit` | `STAGE-6-PRE-IMPL-TESTS.md` |
| 7 | Implementation | Code against failing tests | Stage 6 | `implement`, `executing-plans`, `subagent-driven-dev`, `fix-loop` | `STAGE-7-IMPLEMENTATION.md` |
| 8 | Post-Impl Tests | E2E, visual, perf, load, security | Stage 7 | `playwright`, `verify-screenshots`, `web-quality`, `security-audit` | `STAGE-8-POST-IMPL-TESTS.md` |
| 9 | Review | Code review, quality gates, PR | Stage 8 | `adversarial-review`, `code-reviewer`, `request-code-review`, `pr-standards` | `STAGE-9-REVIEW.md` |
| 10 | Deploy & Monitor | CI/CD, Docker, K8s, observability | Stage 9 | `ci-cd-setup`, `docker-optimize`, `k8s-deploy`, `iac-deploy`, `monitoring-setup` | `STAGE-10-DEPLOY.md` |
| 11 | Docs & Handover | API docs, user guide, runbooks, handover | Stage 10 | `handover`, `incident-response` (runbooks), `learn-n-improve` | `STAGE-11-DOCS.md` |

### Parallelism Opportunities

| Parallel Group | Stages | Condition |
|----------------|--------|-----------|
| Group A | 2 (Plan) + 3 (Scaffold) | Both need only Stage 1 |
| Group B | 4 (Demo) can overlap with 2, 3 | Needs Stage 1; updates when 3 completes |
| Group C | 4 (Demo) + 5 (Schema) | After Plan + Scaffold done |
| Group D | 11 (Docs) starts partial work | API docs can begin after Stage 7 |

---

## 1. Coverage Matrix (Revised 12-Stage)

| # | Capability | Status | Evidence |
|---|-----------|--------|----------|
| **STAGE 0: Master Orchestrator** |||
| 0.1 | Pipeline state management | ❌ Missing | No `.pipeline/state.json` tracker exists |
| 0.2 | Gate checking between stages | ❌ Missing | No automated gate protocol |
| 0.3 | Parallel stage dispatch | ⚠️ Partial | `subagent-driven-dev` handles parallel tasks but not pipeline stages |
| **STAGE 1: PRD** |||
| 1.1 | Generate formal PRD | ✅ Full | `brainstorm` PRD mode with user stories, tiers, NFRs |
| 1.2 | Parse existing external PRD | ❌ Missing | Cannot consume external documents |
| 1.3 | Tier requirements | ✅ Full | Must / Nice / Out of Scope |
| **STAGE 2: Plan** |||
| 2.1 | Task decomposition with dependencies | ✅ Full | `writing-plans` with dependency graph + waves |
| 2.2 | GitHub Issues with epics | ⚠️ Partial | `plan-to-issues` capped at 20/invocation |
| 2.3 | ADRs | ⚠️ Partial | `planner-researcher` agent only; not `strategic-architect` |
| **STAGE 3: Scaffolding** |||
| 3.1 | Project initialization (package.json, pyproject.toml, etc.) | ❌ Missing | No dedicated scaffolding skill |
| 3.2 | Linter/formatter setup | ❌ Missing | Rules mention linters but no setup skill |
| 3.3 | CI skeleton | ✅ Full | `ci-cd-setup` covers GitHub Actions + GitLab CI |
| 3.4 | Dev environment (Docker Compose, env files) | ⚠️ Partial | `docker-optimize` covers Docker but not full dev env |
| 3.5 | Folder structure creation | ❌ Missing | No skill creates standard project layouts |
| **STAGE 4: HTML Demo** |||
| 4.1 | Standalone HTML prototype | ❌ Missing | No skill generates complete pages |
| 4.2 | Design system guidance | ✅ Full | `ui-ux-pro-max` |
| 4.3 | Data visualization | ⚠️ Partial | `d3-viz` for charts only |
| **STAGE 5: Schema & Data** |||
| 5.1 | Database schema design | ⚠️ Partial | `pg-query` reads schemas; no design skill |
| 5.2 | Migrations | ⚠️ Partial | `fastapi-db-migrate` Alembic-only |
| 5.3 | Seed data | ⚠️ Partial | `fastapi-deploy` seeds but FastAPI-only |
| **STAGE 6: Pre-Impl Tests** |||
| 6.1 | Unit test stubs (TDD red) | ✅ Full | `tdd` red-green-refactor |
| 6.2 | API contract test stubs | ❌ Missing | No contract testing skill |
| 6.3 | E2E test stubs (Playwright) | ✅ Full | `playwright` POM + cross-browser |
| 6.4 | Batch test generation from specs | ❌ Missing | No bulk generation from acceptance criteria |
| **STAGE 7: Implementation** |||
| 7.1 | Test-first implementation | ✅ Full | `implement` 7-step workflow |
| 7.2 | Plan execution | ✅ Full | `executing-plans` with resume |
| 7.3 | Parallel agent orchestration | ✅ Full | `subagent-driven-dev` |
| 7.4 | Iterative failure fixing | ✅ Full | `fix-loop` max 5 iterations |
| **STAGE 8: Post-Impl Tests** |||
| 8.1 | E2E tests (full) | ✅ Full | `playwright` cross-browser |
| 8.2 | Visual regression | ✅ Full | `verify-screenshots` baselines + CI |
| 8.3 | Performance/load tests | ❌ Missing | No k6/Locust/Artillery skill |
| 8.4 | Security SAST | ✅ Full | `security-audit` CodeQL + Semgrep |
| 8.5 | Web quality (CWV, a11y) | ✅ Full | `web-quality` |
| 8.6 | API tests (generic) | ❌ Missing | FastAPI-only |
| **STAGE 9: Review** |||
| 9.1 | Adversarial code review | ✅ Full | `adversarial-review` |
| 9.2 | PR creation | ✅ Full | `request-code-review` |
| 9.3 | Standards enforcement | ✅ Full | `pr-standards` |
| 9.4 | STRIDE threat model | ✅ Full | `security-auditor` agent |
| **STAGE 10: Deploy & Monitor** |||
| 10.1 | CI/CD pipeline | ✅ Full | `ci-cd-setup` |
| 10.2 | Docker production images | ✅ Full | `docker-optimize` |
| 10.3 | Kubernetes deployment | ✅ Full | `k8s-deploy` Helm + RBAC + HPA |
| 10.4 | IaC (Terraform/Pulumi) | ✅ Full | `iac-deploy` |
| 10.5 | Monitoring & observability | ✅ Full | `monitoring-setup` Prometheus + Grafana + OTel |
| 10.6 | Incident runbooks | ✅ Full | `incident-response` |
| **STAGE 11: Docs & Handover** |||
| 11.1 | API documentation | ❌ Missing | No OpenAPI doc generation skill |
| 11.2 | User guide / README | ⚠️ Partial | No dedicated skill; can be done manually |
| 11.3 | Session handover | ✅ Full | `handover` 11-step structured doc |
| 11.4 | Runbook generation | ✅ Full | `incident-response` Phase 6 |
| 11.5 | Learning capture | ✅ Full | `learn-n-improve` |

---

## 2. Gap List (Ranked by Impact — Revised)

| Rank | Gap | Impact | Stage | Why Critical |
|------|-----|--------|-------|-------------|
| **1** | No master pipeline orchestrator | 🔴 Critical | 0 | Every stage requires manual invocation |
| **2** | No project scaffolding skill | 🔴 Critical | 3 | Can't initialize repos, install deps, set up linters — blocks ALL downstream |
| **3** | No HTML UI prototype generator | 🔴 Critical | 4 | Can't demo to stakeholders before coding |
| **4** | No external PRD parser | 🟠 High | 1 | Teams with existing PRDs can't feed them in |
| **5** | No generic API test skill | 🟠 High | 6, 8 | REST/GraphQL ubiquitous; only FastAPI exists |
| **6** | No performance/load testing | 🟠 High | 8 | Can't verify system handles load |
| **7** | No generic DB migration skill | 🟠 High | 5 | Only Alembic; no Prisma, Knex, Flyway |
| **8** | No batch test generation | 🟡 Medium | 6 | TDD one-at-a-time; bulk from specs faster |
| **9** | No contract/schema testing | 🟡 Medium | 6, 8 | OpenAPI validation absent |
| **10** | No API documentation generator | 🟡 Medium | 11 | No OpenAPI doc / Swagger UI generation |
| **11** | Placeholder stacks (React, Firebase, Go) | 🟡 Medium | all | Minimal guidance for these stacks |
| **12** | plan-to-issues capped at 20 | 🟢 Low | 2 | Large PRDs need multiple invocations |

---

## 3. Chain Analysis (Revised 12-Stage)

```
STAGE 0:  MASTER ORCHESTRATOR
          (spawns all stages, monitors gates, manages .pipeline/state.json)
              │
STAGE 1:  brainstorm ─→ [NEW: prd-parser]
          (PRD generation)  (external PRD ingestion)
              │
         ┌────┴────┐
         ▼         ▼
STAGE 2:          STAGE 3:
writing-plans     [NEW: project-scaffold]
plan-to-issues    ci-cd-setup (skeleton)
planner-researcher  docker-optimize (dev compose)
         │         │
         │    ┌────┘
         │    ▼
         │  STAGE 4:
         │  [NEW: html-prototype] ←── ui-ux-pro-max + d3-viz
         │    │
         ▼    │
STAGE 5:      │
[NEW: schema-designer]
fastapi-db-migrate / [NEW: generic-migrate]
pg-query (schema exploration)
         │
         ▼
STAGE 6:
tdd (red phase — failing unit tests)
[NEW: api-test-suite] (contract stubs)
[NEW: test-generator] (batch from acceptance criteria)
playwright (E2E stubs)
         │
         ▼
STAGE 7:
implement ─→ executing-plans ─→ subagent-driven-dev
fix-loop ─→ auto-verify
batch (codebase-wide refactors)
         │
         ▼
STAGE 8:
playwright (full E2E run)
verify-screenshots (visual regression)
[NEW: perf-test] (k6 load testing)
security-audit (CodeQL + Semgrep)
web-quality (CWV, a11y, SEO)
supply-chain-audit
         │
         ▼
STAGE 9:
adversarial-review ─→ request-code-review
code-reviewer agent
security-auditor agent (STRIDE)
pr-standards ─→ receive-code-review
         │
         ▼
STAGE 10:
ci-cd-setup (full pipeline) ─→ docker-optimize ─→ k8s-deploy
iac-deploy (Terraform/Pulumi)
monitoring-setup (Prometheus/Grafana/OTel)
incident-response (runbooks)
         │
         ▼
STAGE 11:
[NEW: api-docs-generator]
handover (session handover)
incident-response (runbooks)
learn-n-improve (session learnings)
skill-factory (promote patterns to skills)
```

---

## 4. Proposed New Skills/Agents (Revised)

### 4.1 `pipeline-orchestrator` — Priority: Critical (Stage 0)
- **Trigger:** `/pipeline` or `/prd-to-prod`
- **What:** Master orchestrator — spawns 11 stages in parallel waves, manages `.pipeline/state.json`, enforces gate checks, handles failures with 3 retries
- **Integrates:** All stages; `subagent-driven-dev` for dispatch; `learn-n-improve` at completion

### 4.2 `project-scaffold` — Priority: Critical (Stage 3)
- **Trigger:** `/scaffold`
- **What:** Initializes project structure — `package.json`/`pyproject.toml`, folder layout, linter config (ESLint/Ruff/Prettier), formatter, Git hooks (husky/pre-commit), CI skeleton, Docker Compose dev, `.env.example`, test framework setup
- **Integrates:** `ci-cd-setup` (CI skeleton), `docker-optimize` (dev compose), `/github` (inspect scaffolds from top repos)

### 4.3 `html-prototype` — Priority: Critical (Stage 4)
- **Trigger:** `/prototype` or `/html-demo`
- **What:** Single self-contained HTML with Tailwind CDN + Alpine.js + Chart.js, realistic sample data, all CRUD simulated, responsive, accessible
- **Integrates:** `ui-ux-pro-max` (design), `d3-viz` (charts), `brainstorm` (PRD input)

### 4.4 `prd-parser` — Priority: High (Stage 1)
- **Trigger:** `/parse-prd`
- **What:** Ingests external PRD (markdown, PDF, Notion export), extracts user stories + acceptance criteria + NFRs + tiers, outputs structured format for `writing-plans`
- **Integrates:** `writing-plans`, `plan-to-issues`, `pipeline-orchestrator`

### 4.5 `api-test-suite` — Priority: High (Stages 6, 8)
- **Trigger:** `/api-test`
- **What:** Framework-agnostic REST/GraphQL testing — endpoint discovery, contract validation, happy/error/edge cases, OpenAPI schema validation
- **Integrates:** `tdd`, `auto-verify`, `security-audit`

### 4.6 `perf-test` — Priority: High (Stage 8)
- **Trigger:** `/perf-test` or `/load-test`
- **What:** k6/Locust/Artillery — load profiles (smoke/average/stress/spike/soak), performance budgets, CI regression detection
- **Integrates:** `ci-cd-setup`, `monitoring-setup`, `web-quality`

### 4.7 `schema-designer` — Priority: High (Stage 5)
- **Trigger:** `/schema`
- **What:** Database schema design from PRD data models — generates migration files (Alembic/Prisma/Knex/Flyway), seed data scripts, ERD diagrams
- **Integrates:** `fastapi-db-migrate`, `pg-query`, `writing-plans`

### 4.8 `test-generator` — Priority: Medium (Stage 6)
- **Trigger:** `/generate-tests`
- **What:** Batch-generates test files from acceptance criteria — maps each AC to test cases across types (unit/integration/E2E), outputs all files at once
- **Integrates:** `tdd`, `playwright`, `implement`, `writing-plans`

### 4.9 `contract-test` — Priority: Medium (Stages 6, 8)
- **Trigger:** `/contract-test`
- **What:** OpenAPI/AsyncAPI schema validation, breaking change detection, Pact-style consumer-driven contracts
- **Integrates:** `api-test-suite`, `ci-cd-setup`

### 4.10 `api-docs-generator` — Priority: Medium (Stage 11)
- **Trigger:** `/api-docs`
- **What:** Generates OpenAPI spec from code, Swagger UI page, markdown API reference, changelog
- **Integrates:** `handover`, `ci-cd-setup`

---

## 5. Autonomy Assessment (Revised)

**Current autonomous coverage: ~55%**

| Stage | Autonomy | Blocker |
|-------|----------|---------|
| 0. Orchestrator | 0% | Does not exist |
| 1. PRD | 85% | Can't ingest existing PRDs |
| 2. Plan | 90% | 20-issue cap |
| 3. Scaffolding | 20% | No scaffolding skill; CI skeleton exists |
| 4. HTML Demo | 10% | No prototype skill |
| 5. Schema & Data | 40% | Alembic-only; no generic migrations |
| 6. Pre-Impl Tests | 55% | No API/contract tests; no batch generation |
| 7. Implementation | 95% | Excellent |
| 8. Post-Impl Tests | 60% | No perf/load; no generic API tests |
| 9. Review | 95% | Excellent |
| 10. Deploy & Monitor | 90% | Excellent (minor: FastAPI-only deploy) |
| 11. Docs & Handover | 50% | No API doc generator; handover exists |
| **Cross-cutting** | 25% | No master orchestrator |

### Path to ~95% Autonomy

| Priority | New Skill | Autonomy Gain | Stages Unblocked |
|----------|-----------|---------------|------------------|
| 1 | `pipeline-orchestrator` | +25% | 0 (all stages) |
| 2 | `project-scaffold` | +10% | 3 (unblocks 4, 5, 6, 7) |
| 3 | `html-prototype` | +5% | 4 |
| 4 | `schema-designer` | +5% | 5 (unblocks 6, 7) |
| 5 | `api-test-suite` + `perf-test` | +5% | 6, 8 |
| 6 | `prd-parser` | +3% | 1 |
| 7 | `test-generator` + `contract-test` | +2% | 6 |
| 8 | `api-docs-generator` | +1% | 11 |

### Verdict

The pipeline has **strong middle and late stages** (Implementation at 95%, Review at 95%, Deploy at 90%) but **weak early stages** (Scaffolding 20%, Demo 10%, Schema 40%) and **no orchestration** (0%). The critical path to full autonomy is: `pipeline-orchestrator` → `project-scaffold` → `schema-designer` → `html-prototype`. These 4 skills would lift overall autonomy from ~55% to ~85%.

---

## Stage Doc Index

All stage prompts are maintained in `docs/stages/`:

| File | Stage | Status |
|------|-------|--------|
| [`STAGE-0-MASTER-ORCHESTRATOR.md`](stages/STAGE-0-MASTER-ORCHESTRATOR.md) | Master Orchestrator | Prompt designed |
| [`STAGE-1-PRD.md`](stages/STAGE-1-PRD.md) | PRD | Prompt designed |
| [`STAGE-2-PLAN.md`](stages/STAGE-2-PLAN.md) | Plan | Prompt designed |
| [`STAGE-3-SCAFFOLDING.md`](stages/STAGE-3-SCAFFOLDING.md) | Scaffolding | Prompt designed |
| [`STAGE-4-HTML-DEMO.md`](stages/STAGE-4-HTML-DEMO.md) | HTML Demo | Prompt designed |
| [`STAGE-5-SCHEMA.md`](stages/STAGE-5-SCHEMA.md) | Schema & Data | Prompt designed |
| [`STAGE-6-PRE-IMPL-TESTS.md`](stages/STAGE-6-PRE-IMPL-TESTS.md) | Pre-Impl Tests | Prompt designed |
| [`STAGE-7-IMPLEMENTATION.md`](stages/STAGE-7-IMPLEMENTATION.md) | Implementation | Prompt designed |
| [`STAGE-8-POST-IMPL-TESTS.md`](stages/STAGE-8-POST-IMPL-TESTS.md) | Post-Impl Tests | Prompt designed |
| [`STAGE-9-REVIEW.md`](stages/STAGE-9-REVIEW.md) | Review | Prompt designed |
| [`STAGE-10-DEPLOY.md`](stages/STAGE-10-DEPLOY.md) | Deploy & Monitor | Prompt designed |
| [`STAGE-11-DOCS.md`](stages/STAGE-11-DOCS.md) | Docs & Handover | Prompt designed |
