# Stage 11: Documentation & Handover — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to generate all project documentation and produce a maintainable handover — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 10 (Deploy — production running with monitoring)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
                    ┌─────────────────────────┐
                    │  Verify Deployment       │
                    │  (ST10 complete, prod    │
                    │   running with monitors) │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Generate README         │
                    │  (setup, usage, badges,  │
                    │   architecture overview) │
                    └────────────┬────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  Generate Architecture Docs       │
               │                                   │
               │  ▓ Mermaid diagrams               │
               │  ▓ ADR index (docs/adr/)          │
               │  ▓ diataxis-docs (4 quadrants)    │
               └────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  Generate API Documentation       │
               │                                   │
               │  ▓ api-docs-generator             │
               │    (OpenAPI auto-gen + Redoc)     │
               └────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  Generate Operational Docs        │
               │                                   │
               │  ▓ changelog-contributing          │
               │    (CHANGELOG.md + CONTRIBUTING)  │
               │  ▓ Monitoring/deploy/rollback     │
               └────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  Pipeline Summary & Handover      │
               │                                   │
               │  ▓ handover skill                 │
               │  ▓ learn-n-improve                │
               │  ▓ Pipeline summary report        │
               └────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  Output: All documentation        │
               │  committed + learnings captured   │
               └──────────────────────────────────┘
```

### Diagram B — I/O Artifact Contract

```
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  UPSTREAM INPUTS                                                      ░
 ░                                                                       ░
 ░  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────┐   ░
 ░  │  ST 10: DEPLOY    │  │  ST 9: REVIEW     │  │  ST 1: PRD       │   ░
 ░  │                   │  │                   │  │                  │   ░
 ░  │  deployment URL   │  │  review report    │  │  prd.md          │   ░
 ░  │  CI/CD pipeline   │  │  ADR statuses     │  │  requirements    │   ░
 ░  │  K8s manifests    │  │  PR URL           │  │  .json           │   ░
 ░  │  dashboards       │  │                   │  │                  │   ░
 ░  │  runbooks         │  │                   │  │                  │   ░
 ░  │  SLO defs         │  │                   │  │                  │   ░
 ░  └────────┬──────────┘  └────────┬──────────┘  └────────┬─────────┘   ░
 ░           │                      │                      │             ░
 ░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░
              │                      │                      │
              ▼                      ▼                      ▼
 ┌────────────────────────────────────────────────────────────────┐
 │                                                                │
 │              STAGE 11: DOCUMENTATION & HANDOVER                │
 │                                                                │
 │  █ handover  █ learn-n-improve  █ api-docs-generator           │
 │  █ changelog-contributing  █ diataxis-docs                     │
 │                                                                │
 └──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  FINAL OUTPUTS (no downstream stage)                                  ░
 ░                                                                       ░
 ░  README.md        docs/             docs/         docs/stages/        ░
 ░                   ARCHITECTURE.md   API.md        PIPELINE-           ░
 ░                   (+ Mermaid)       (OpenAPI)     SUMMARY.md          ░
 ░                                                                       ░
 ░  docs/            CHANGELOG.md      CONTRIBUTING  .claude/            ░
 ░  HANDOVER.md                        .md           learnings.json      ░
 ░                                                                       ░
 ░  ┌──────────────────────────────────────────────────────────┐         ░
 ░  │  CONSUMERS                                               │         ░
 ░  │                                                          │         ░
 ░  │  ▓ Developers (README, ARCHITECTURE, onboarding)         │         ░
 ░  │  ▓ API consumers (API.md, OpenAPI spec)                  │         ░
 ░  │  ▓ Operations (runbooks, dashboards, SLOs)               │         ░
 ░  │  ▓ Stakeholders (PIPELINE-SUMMARY, CHANGELOG)            │         ░
 ░  │  ▓ Future Claude Code sessions (HANDOVER, learnings)     │         ░
 ░  └──────────────────────────────────────────────────────────┘         ░
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Session handover document | `handover` skill | ✅ Covered | — |
| 2 | Learning capture | `learn-n-improve` skill | ✅ Covered | — |
| 3 | README generation | Stage 11 prompt (Step 2) | ✅ Covered | — |
| 4 | Architecture documentation (Mermaid) | Stage 11 prompt (Step 3) | ✅ Covered | — |
| 5 | ADR index | Stage 11 prompt (Step 3.5) | ✅ Covered | **ADR (Nygard)** |
| 6 | API documentation (manual) | Stage 11 prompt (Step 4) | ✅ Covered | — |
| 7 | Operational docs (monitoring, deploy, rollback) | Stage 11 prompt (Step 5) | ✅ Covered | — |
| 8 | Pipeline summary report | Stage 11 prompt (Step 6.3) | ✅ Covered | — |
| 9 | Auto-generated API docs (OpenAPI) | `api-docs-generator` skill (multi-framework OpenAPI gen + validation) | ✅ Covered | **OpenAPI 3.0** |
| 10 | CONTRIBUTING.md | `changelog-contributing` skill (branch naming, test reqs, PR template) | ✅ Covered | **OSS Best Practices** |
| 11 | CHANGELOG generation | `changelog-contributing` skill (conventional commits → CHANGELOG.md) | ✅ Covered | **Keep a Changelog** |
| 12 | Code-level documentation (docstrings) | None — rule 7 says "no redundant comments" but no guidance on when docstrings ARE needed | ⚠️ Partial | **Documentation Best Practices** |
| 13 | Onboarding guide (new developer) | None — README has setup but no conceptual onboarding | ❌ Missing | **Developer Experience** |
| 14 | API versioning documentation | None | ❌ Missing | **API Versioning** |
| 15 | Deprecation policy | None | ❌ Missing | **API Lifecycle Management** |
| 16 | Diátaxis documentation framework | `diataxis-docs` skill (tutorials, how-to, reference, explanation) | ✅ Covered | **Diátaxis (Procida)** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **OpenAPI 3.0** | Machine-readable API specification auto-generated from code | ✅ Multi-framework auto-gen + spectral validation + test alignment in `api-docs-generator` |
| **Keep a Changelog** | Structured changelog from commit history | ✅ Conventional commit parsing + Keep a Changelog format in `changelog-contributing` |
| **Diátaxis Framework** | 4 doc types: tutorials, how-to guides, reference, explanation | ✅ 4-quadrant organization with templates in `diataxis-docs` |
| **OSS Best Practices** | CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR templates | ✅ CONTRIBUTING.md generation with project-specific guidelines in `changelog-contributing` |
| **Developer Experience** | Onboarding guide, conceptual overview, glossary | ❌ Setup exists but no conceptual onboarding |
| **API Lifecycle** | Versioning strategy, deprecation policy, migration guides | ❌ No versioning or deprecation guidance |
| **C4 Model (Simon Brown)** | Context, Container, Component, Code diagrams | ⚠️ Mermaid diagram exists but no structured C4 levels |

## Gap Proposals

### Gap 11.1: `api-docs-generator` skill (Priority: P1)

**Problem it solves:** API documentation is manual-only — error-prone and quickly outdated. No auto-generation from code annotations, no validation against API tests.

**What it needs:**
- Auto-generate OpenAPI spec from FastAPI annotations / Express JSDoc / NestJS decorators
- Validate spec against Stage 6 API tests (contract consistency)
- Generate human-readable docs from spec (Redoc / Swagger UI)

**Existing coverage:** Stage 11 prompt writes manual API.md. Also identified in Stage 7 (Gap 7.2) — same skill shared between stages.

### Gap 11.2: CHANGELOG and CONTRIBUTING generation (Priority: P2)

**Problem it solves:** No automated changelog from conventional commits. No CONTRIBUTING.md with project-specific guidelines.

**What to add:**
- Auto-generate CHANGELOG.md from conventional commits (depends on Stage 3 commitlint)
- Generate CONTRIBUTING.md with branch naming, test requirements, PR template

**Existing coverage:** Neither generated.

### Gap 11.3: Diátaxis documentation structure (Priority: P2)

**Problem it solves:** Docs are monolithic files mixing tutorials, references, and explanations. Hard to navigate for different audiences (new dev vs operator vs API consumer).

**What to add:**
- Organize docs into 4 Diátaxis categories: tutorials, how-to, reference, explanation
- Template for each category

**Existing coverage:** None — docs are ad-hoc.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `README.md` | Developers, GitHub display | Markdown |
| `docs/ARCHITECTURE.md` | Developers, onboarding | Markdown + Mermaid |
| `docs/API.md` | API consumers | Markdown (or OpenAPI spec) |
| `docs/HANDOVER.md` | Next Claude Code session | Markdown |
| `docs/stages/PIPELINE-SUMMARY.md` | Stakeholders, retrospective | Markdown |
| `.claude/learnings.json` | Future pipeline runs (`learn-n-improve`) | JSON |

## Research Targets

- **GitHub**: `README template` >5000 stars, `documentation best practices`, `Diátaxis framework`, `API documentation tools`
- **Reddit**: r/technicalwriting — "project documentation templates", r/programming — "developer onboarding docs"
- **Twitter/X**: `documentation developer experience`, `Diátaxis documentation`, `README best practices`

## Stack Coverage

Universal — documentation is stack-agnostic. API docs format varies by stack (FastAPI auto-generates OpenAPI, Express needs JSDoc, Android needs KDoc) but the documentation structure is universal.

## Autonomy Verdict

**✅ Can run autonomously.** Strong skill coverage: `handover`, `learn-n-improve`, `api-docs-generator`, `changelog-contributing`, `diataxis-docs`, plus detailed prompt for README/ARCHITECTURE docs. All P1 and P2 gaps resolved. Remaining minor gaps: code-level docstring guidance, onboarding guide, API versioning docs, deprecation policy.

---

## Orchestration Dispatch

When the pipeline-orchestrator dispatches this stage, the stage agent executes:

```
# 1. Read upstream artifacts
# Read: deployment URL (from Stage 10)
# Read: review report (from Stage 9)
# Read: docs/plans/<feature>-prd.md (from Stage 1)
# Read: all docs/adr/ADR-*.md (from Stage 2)

# 2. Generate documentation using Diátaxis framework
Skill("diataxis-docs", args="<project_root>")

# 3. Generate CHANGELOG.md and CONTRIBUTING.md
Skill("changelog-contributing", args="<project_root>")

# 4. Generate session handover document
Skill("handover", args="<project_root>")

# 5. Capture learnings for future pipeline runs
Skill("learn-n-improve", args="session")
```

**Artifact validation:** Verify `README.md`, `docs/ARCHITECTURE.md`, `docs/HANDOVER.md`, `CHANGELOG.md`, `CONTRIBUTING.md` exist. Verify `docs/stages/PIPELINE-SUMMARY.md` is generated with all stage results consolidated.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `api-docs-generator` skill created with multi-framework OpenAPI gen, spectral validation, test alignment, Redoc/Swagger UI, CI integration — API docs ❌ flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `changelog-contributing` skill (CHANGELOG + CONTRIBUTING.md) and `diataxis-docs` skill (4-quadrant documentation framework) — 3 ❌ items flipped to ✅ |
