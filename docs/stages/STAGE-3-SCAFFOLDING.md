# Stage 3: Project Scaffolding & Dev Environment — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to initialize a fully configured, buildable, lintable, testable project skeleton — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 1 (PRD — to know the tech stack)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
 ┌─────────────────────────────────────────────────────────────────┐
 │              STAGE 3: PROJECT SCAFFOLDING                        │
 └─────────────────────────────────────────────────────────────────┘

        ┌───────────────────────┐
        │  Read PRD from ST1    │
        │  (detect tech stack)  │
        └───────────┬───────────┘
                    │
                    ▼
  ┌──────────────────────────────┐
  │  Stack Detection             │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  Python? Node? Android?      │
  │  Go? Rust? React?            │
  └──────────────┬───────────────┘
                 │
        ┌────────┼────────┬────────┐
        │        │        │        │
        ▼        ▼        ▼        ▼
   ┌────────┐┌────────┐┌────────┐┌────────┐
   │Python  ││Node/TS ││Android ││Go/Rust │
   │pyproj  ││pkg.json││Gradle  ││go.mod/ │
   │toml    ││        ││        ││Cargo   │
   └───┬────┘└───┬────┘└───┬────┘└───┬────┘
       └─────┬───┘────┬────┘─────────┘
             │        │
             ▼        │
  ┌──────────────────────────────┐
  │  Project Initialization      │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  project-scaffold skill      │
  │  • Package manifests         │
  │  • Clean Architecture dirs   │
  │  • .editorconfig             │
  │  • License file              │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Tooling Setup               │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  • Linter + formatter        │
  │  • Commitlint (conventional) │
  │  • Semantic-release / SemVer │
  │  • Pre-commit hooks          │
  │  • Test framework config     │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Infrastructure Setup        │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Docker Compose dev env    │
  │  • CI skeleton (ci-cd-setup) │
  │  • .env.example              │
  │  • Health check endpoint     │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Security Baseline           │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Dependabot / Renovate     │
  │  • SAST (Semgrep) in CI      │
  │  • .gitignore audit          │
  │  • Dependency audit          │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  12-Factor Audit Gate        │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  All 12 factors verified     │
  │  Lockfile exists? Build OK?  │
  └──────────────┬───────────────┘
                 │
            PASS │ / FAIL → retry
                 ▼
       ┌──────────────────┐
       │  Scaffold Output  │
       │  ████████████████ │
       └──────────────────┘
```

### Diagram B — I/O Artifact Contract

```
                          INPUTS
 ┌──────────────────────────────────────────────┐
 │                                              │
 │  ┌───────────────────────────────────────┐   │
 │  │ From ST1: prd.md                      │   │
 │  │   • Tech stack requirements           │   │
 │  │   • NFRs (performance, security)      │   │
 │  └───────────────────────────────────────┘   │
 │                                              │
 └──────────────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │                               │
        │  ███ STAGE 3: SCAFFOLDING ███ │
        │                               │
        │  project-scaffold             │
        │  ci-cd-setup                  │
        │                               │
        └──────────────┬────────────────┘
                       │
         ┌─────────────┼──────────┬──────────────┐
         │             │          │              │
         ▼             ▼          ▼              ▼
 ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
 │ Project    │ │ ci.yml    │ │ docker-  │ │ .env     │
 │ skeleton   │ │ (CI       │ │ compose  │ │ .example │
 │ (dirs,     │ │  skeleton)│ │ .yml     │ │ smoke    │
 │  manifests,│ │           │ │          │ │ test     │
 │  configs)  │ │           │ │          │ │          │
 └─────┬──────┘ └─────┬─────┘ └────┬─────┘ └────┬─────┘
       │              │            │             │
       ▼              ▼            ▼             ▼
 ┌──────────┐  ┌──────────┐ ┌──────────┐  ┌──────────┐
 │ ST4 Demo │  │ ST10     │ │ ST7 Impl │  │ ST6 Tests│
 │ ST5 Schma│  │ Deploy   │ │ ST8 Post │  │ ST7 Impl │
 │ ST6 Tests│  │ (extends)│ │          │  │ ST10 Depl│
 │ ST7 Impl │  │          │ │          │  │          │
 └──────────┘  └──────────┘ └──────────┘  └──────────┘
                   OUTPUTS
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Project initialization (package manifests) | Stage 3 prompt (Step 2) | ✅ Covered | — |
| 2 | Folder structure creation | Stage 3 prompt (Step 3) | ✅ Covered | — |
| 3 | Linter & formatter setup | Stage 3 prompt (Step 4) | ✅ Covered | — |
| 4 | Git hooks (pre-commit) | Stage 3 prompt (Step 5) | ✅ Covered | — |
| 5 | Test framework configuration | Stage 3 prompt (Step 6) | ✅ Covered | — |
| 6 | CI skeleton | `ci-cd-setup` skill | ✅ Covered | — |
| 7 | Docker Compose dev environment | Stage 3 prompt (Step 8) | ✅ Covered | — |
| 8 | .env.example with variable documentation | Stage 3 prompt (Step 8) | ✅ Covered | — |
| 9 | 12-factor app compliance | `project-scaffold` (Step 9: 12-factor audit) | ✅ Covered | **12-Factor App (Heroku)** |
| 10 | Commitlint / conventional commits | `project-scaffold` (Step 4: commitlint + commit-msg hook) | ✅ Covered | **Conventional Commits** |
| 11 | Semantic versioning setup | `project-scaffold` (Step 4.3: semantic-release) | ✅ Covered | **SemVer / semantic-release** |
| 12 | Security baseline from day 0 | `project-scaffold` (Step 6: Dependabot, SAST, audit) | ✅ Covered | **OWASP Secure SDLC** |
| 13 | Editorconfig / shared IDE settings | `project-scaffold` (Step 2.2: .editorconfig) | ✅ Covered | **EditorConfig standard** |
| 14 | License file | `project-scaffold` (Step 10.1: license selection) | ✅ Covered | **OSS Compliance** |
| 15 | Health check endpoint | `project-scaffold` (Step 8: health endpoint per stack) | ✅ Covered | **12-Factor: Admin Processes** |
| 16 | Dependency lockfile generation | `project-scaffold` (Step 9: Factor II + Step 11 gate) | ✅ Covered | **Reproducible Builds** |
| 17 | Multi-stack scaffolding (Android, React, etc.) | `project-scaffold` (Step 2.1: Python, Node, Android, Go, Rust) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **12-Factor App** | Config in env vars, port binding, dev/prod parity, backing services | ✅ Full 12-factor audit in `project-scaffold` Step 9 (all 12 factors checked) |
| **Conventional Commits** | Structured commit messages for changelog generation | ✅ Commitlint + commit-msg hook in `project-scaffold` Step 4 |
| **SemVer** | Version management with semantic-release or equivalent | ✅ Semantic-release setup in `project-scaffold` Step 4.3 |
| **OWASP Secure SDLC** | Security from project inception: dependency audit, .gitignore for secrets, SAST baseline | ✅ Dependency audit + Semgrep SAST + Dependabot in `project-scaffold` Steps 5-6 |
| **EditorConfig** | Consistent editor settings across team | ✅ .editorconfig template in `project-scaffold` Step 2.2 |
| **Reproducible Builds** | Lockfiles, pinned versions, deterministic builds | ✅ Lockfile verification in `project-scaffold` gate check (Step 11) |
| **Clean Architecture** | Separation of concerns in folder structure | ✅ Domain/application/infrastructure/presentation layers in `project-scaffold` Step 2.1 |

## Gap Proposals

### Gap 3.1: `project-scaffold` skill (Priority: P1)

**Problem it solves:** Scaffolding logic lives only in the Stage 3 prompt — not reusable outside the pipeline. No dedicated skill handles multi-stack project initialization with 12-factor compliance, commitlint, semantic-release, security baseline, and .editorconfig.

**What it needs:**
- Multi-stack support: Python, Node, Android, React, Go, Rust
- 12-factor compliance checklist (all 12 factors verified)
- .editorconfig generation
- Commitlint + conventional commits setup
- Semantic-release / version management
- Dependency audit in CI (`npm audit` / `pip audit`)
- Lockfile verification in gate check
- Health endpoint template per stack

**Existing coverage:** Stage 3 prompt covers Python/Node scaffolding inline. `ci-cd-setup` covers CI. Neither is a reusable scaffold skill.

### Gap 3.2: Security baseline in scaffold (Priority: P1)

**Problem it solves:** No security tooling from day 0. Dependency vulnerabilities and secret leaks are only caught later (Stage 9 Review) instead of being prevented at scaffold time.

**What to add:**
- `npm audit` / `pip audit` / `safety check` in CI skeleton
- Dependabot config or Renovate for automated dependency updates
- `.gitignore` audit: verify all secret patterns covered
- SAST baseline (Semgrep with default ruleset) in CI

**Existing coverage:** `security-audit` skill exists but targets code review (Stage 9), not scaffold-time baseline.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| Project skeleton (all files) | Stage 4 (Demo), Stage 5 (Schema), Stage 6 (Tests), Stage 7 (Impl) | Files on disk |
| `.github/workflows/ci.yml` | Stage 10 (Deploy) — extends this | YAML |
| `docker-compose.yml` | Stage 7 (Impl), Stage 8 (Tests) | YAML |
| `.env.example` | Stage 7 (Impl), Stage 10 (Deploy) | dotenv |
| Smoke test | Stage 6 (Pre-Tests) — extends this | Test file |

## Research Targets

- **GitHub**: `<framework> starter template` >5000 stars, `12-factor app template`, `commitlint conventional commits setup`
- **Reddit**: r/webdev — "project structure 2025", r/devops — "CI scaffold best practices"
- **Twitter/X**: `project scaffolding AI agent`, `12-factor app setup automation`

## Stack Coverage

| Stack | Covered in `project-scaffold` | Notes |
|-------|------------------------------|-------|
| Python (FastAPI/Django) | ✅ | pyproject.toml, ruff, pytest, mypy, health endpoint |
| Node/TypeScript | ✅ | package.json, ESLint/Biome, Vitest/Jest, health endpoint |
| Android (Compose) | ✅ | build.gradle.kts, settings.gradle.kts, AndroidManifest.xml, Clean Architecture dirs, health check |
| Go | ✅ | go.mod, .golangci.yml, health endpoint |
| Rust | ✅ | Cargo.toml, clippy.toml, Clean Architecture dirs, health endpoint (Actix Web) |
| React (Next.js) | ✅ | next.config.ts, App Router structure, Playwright E2E, Tailwind config, health API route |

## Autonomy Verdict

**✅ Can run autonomously.** `project-scaffold` skill covers: multi-stack initialization (Python, Node/TS, React/Next.js, Android, Go, Rust), Clean Architecture folder structure, 12-factor compliance audit (all 12 factors), commitlint + semantic versioning, security baseline (dependency audit, SAST, Dependabot), .editorconfig, health endpoints (all 6 stacks), Docker dev environment, stack-specific gate commands, and gate verification. All 17 capabilities ✅ with full stack coverage.

---

## Orchestration Dispatch

When the pipeline-orchestrator dispatches this stage, the stage agent executes:

```
# 1. Read upstream PRD to detect tech stack
# Read: docs/plans/<feature>-prd.md (from Stage 1)

# 2. Initialize project skeleton with detected stacks
Skill("project-scaffold", args="<detected_stacks>")

# 3. Set up CI/CD pipeline skeleton
Skill("ci-cd-setup", args="<detected_stacks>")
```

**Artifact validation:** Verify project skeleton exists (package manifests, folder structure, linter config, test framework config). Verify `.github/workflows/ci.yml` exists. Run `<stack_build_command>` to verify the skeleton compiles.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gaps resolved: `project-scaffold` skill created with multi-stack init, 12-factor audit, security baseline, commitlint, SemVer, .editorconfig, health endpoint — all 9 ❌/⚠️ items flipped to ✅ |
| 2026-03-14 | Comprehensive review: Fixed stale Stack Coverage table — Android, Go, Rust flipped ❌→✅ (actually covered in `project-scaffold`). Identified 3 gaps |
| 2026-03-14 | Gaps fixed in `project-scaffold`: (1) Added health endpoints for Android (ContentProvider/Ktor) and Rust (Actix Web), (2) Added dedicated React/Next.js template with App Router, Playwright, Tailwind — ⚠️→✅, (3) Added stack-specific gate commands table (build/lint/test/lockfile/health per stack). All 6 stacks now fully covered |
