# Skill Backlog — PRD-to-Production Pipeline

> Central prioritized backlog of all proposed skills identified during pipeline audit.
> Each entry links to the stage that identified the gap.

## Status Legend
- `proposed` — Identified during audit, not yet created
- `in-progress` — Skill is being written
- `complete` — Skill merged into `core/.claude/skills/`
- `rejected` — Evaluated and deemed unnecessary (with reason)

---

## Backlog

| # | Skill Name | Priority | Source Stage | Status | Problem It Solves |
|---|-----------|----------|-------------|--------|-------------------|
| 1 | `pipeline-orchestrator` | P0 | Stage 0 | **complete** | DAG-based multi-stage pipeline coordination with typed contracts, state persistence, conditional branching, rollback, and observability |
| 2 | `brainstorm` enhancement | P1 | Stage 1 | **complete** | Add IEEE 830 sections, full ISO 25010 NFRs, risk scoring, RACI, traceability matrix to PRD mode |
| 3 | `prd-parser` | P2 | Stage 1 | **complete** | Parse/normalize existing PRDs from various formats (markdown, Notion, Jira) with IEEE 830 validation |
| 4 | `writing-plans` enhancement | P1 | Stage 2 | **complete** | Add WBS hierarchy, PERT estimation (optimistic/expected/pessimistic), buffer allocation, rollback notes per task |
| 5 | Risk mitigation task generation | P1 | Stage 2 | **complete** | Auto-generate mitigation tasks from PRD risk register entries |
| 6 | `project-scaffold` | P1 | Stage 3 | **complete** | Multi-stack project initialization with 12-factor compliance, commitlint, semantic-release, .editorconfig, health endpoint |
| 7 | Security baseline in scaffold | P1 | Stage 3 | **complete** | Dependency audit, Dependabot/Renovate config, .gitignore audit, SAST baseline (Semgrep) from day 0 (merged into `project-scaffold`) |
| 8 | `html-prototype` | P2 | Stage 4 | **complete** | Reusable single-file HTML prototype generation with design tokens, Nielsen's heuristics, PRD traceability annotations |
| 9 | Automated a11y audit in demo | P2 | Stage 4 | **complete** | axe-core/Lighthouse integration for automated WCAG compliance checking in prototype gate (as `a11y-audit` skill) |
| 10 | `schema-designer` | P1 | Stage 5 | **complete** | Holistic DB schema design: evolutionary strategy, query plan analysis, PII identification, API contract alignment, multi-DB support |
| 11 | Stack-neutral `db-migrate` | P2 | Stage 5 | **complete** | Generic migration skill supporting Prisma, Knex, Django, TypeORM, Drizzle (not just Alembic) |
| 12 | `test-generator` | P1 | Stage 6 | **complete** | Auto-generate test stubs from PRD/schema, BDD/Gherkin, coverage thresholds, property-based testing, mutation testing setup |
| 13 | `contract-test` | P2 | Stage 6 | **complete** | Consumer-driven contract testing with Pact, provider verification, contract broker integration |
| 14 | Code quality gate enhancement | P1 | Stage 7 | **complete** | Cyclomatic complexity, duplication detection, SOLID checklist, TDD refactor phase, structured logging enforcement (as `code-quality-gate` skill) |
| 15 | `api-docs-generator` | P2 | Stage 7 | **complete** | Auto-generate OpenAPI/Swagger docs from code annotations (FastAPI, Express JSDoc) — resolved by P1 #26 |
| 16 | Feature flag guidance | P2 | Stage 7 | **complete** | Feature toggle patterns (LaunchDarkly, Unleash, env-var flags) with cleanup checklist (as `feature-flag` skill) |
| 17 | DAST integration | P1 | Stage 8 | **complete** | OWASP ZAP / Nuclei runtime scanning, header security checks, session management testing (as `dast-scan` skill) |
| 18 | Chaos / resilience testing | P2 | Stage 8 | **complete** | Failure injection (DB kill, network timeout, OOM), graceful degradation verification (as `chaos-resilience` skill) |
| 19 | `perf-test` | P2 | Stage 8 | **complete** | Dedicated perf testing skill: k6 + Lighthouse + bundle analysis, baseline comparison, NFR threshold extraction |
| 20 | Architecture fitness functions | P1 | Stage 9 | **complete** | Dependency direction checks, circular dependency detection, coupling metrics as review gate (as `architecture-fitness` skill) |
| 21 | Change risk scoring | P2 | Stage 9 | **complete** | Quantified risk score (files × complexity × inverse coverage) for deploy go/no-go (as `change-risk-scoring` skill) |
| 22 | Merge strategy + post-merge plan | P2 | Stage 9 | **complete** | Squash/merge/rebase guidance by branch type, post-merge smoke test on main (as `merge-strategy` skill) |
| 23 | GitOps + progressive delivery | P1 | Stage 10 | **complete** | ArgoCD/Flux integration, canary releases with Flagger/Argo Rollouts, metric-based rollback (as `deploy-strategy` skill) |
| 24 | Zero-downtime DB migration strategy | P1 | Stage 10 | **complete** | Migration ordering (expand-contract), pre-deploy verification, backward-compatible changes (merged into `deploy-strategy` skill) |
| 25 | Disaster recovery plan | P2 | Stage 10 | **complete** | RTO/RPO targets from NFRs, backup schedule, restore procedure, failover runbook (as `disaster-recovery` skill) |
| 26 | `api-docs-generator` | P1 | Stage 11 | **complete** | Auto-generate OpenAPI from code, validate against API tests, Redoc/Swagger UI (shared with Stage 7) |
| 27 | CHANGELOG + CONTRIBUTING generation | P2 | Stage 11 | **complete** | Auto-generate CHANGELOG from conventional commits, CONTRIBUTING.md with project guidelines (as `changelog-contributing` skill) |
| 28 | Diátaxis doc structure | P2 | Stage 11 | **complete** | Organize docs into tutorials/how-to/reference/explanation with templates per category (as `diataxis-docs` skill) |

---

## Priority Definitions

- **P0** — Blocks autonomous operation of the pipeline entirely
- **P1** — Significantly reduces autonomy or quality of a stage
- **P2** — Nice-to-have improvement, stage can function without it

---

## Completion Summary

All 28 backlog items are **complete** (1 P0 + 12 P1 + 15 P2). The PRD-to-Production pipeline has full skill coverage across all 12 stages.
