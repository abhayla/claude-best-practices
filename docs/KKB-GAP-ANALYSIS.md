# KKB (RasoiAI) — Claude Resources Gap Analysis

**Date:** 2026-03-12
**Repo:** https://github.com/abhayla/KKB
**Registered stacks:** `android-compose`, `fastapi-python`, `ai-gemini`, `firebase-auth`

## Current State

| Resource | KKB has | Hub has (eligible) | Gap |
|----------|---------|-------------------|-----|
| **Agents** | 14 | 14 (11 universal + 3 stack) | 1 missing (`security-auditor-agent`) |
| **Skills** | 25 | ~55 (45 universal + 10 stack) | ~18 recommended |
| **Rules** | 6 | 10 (5 universal + 5 stack) | 2 missing |
| **Hooks** | 8 | 7 | 2 missing safety hooks |

## Name Mapping (KKB ↔ Hub)

KKB uses shorter names for some resources that correspond to hub stack-prefixed names:

| KKB name | Hub name | Match |
|----------|----------|-------|
| `adb-test` | `android-adb-test` | Same skill |
| `run-android-tests` | `android-run-tests` | Same skill |
| `run-e2e` | `android-run-e2e` | Same skill |
| `run-backend-tests` | `fastapi-run-backend-tests` | Same skill |
| `db-migrate` | `fastapi-db-migrate` | Same skill |
| `deploy` | `fastapi-deploy` | Same skill |
| `gemini-api` | `ai-gemini-api` | Same skill |
| `api-tester` (agent) | `fastapi-api-tester-agent` (agent) | Same agent |
| `database-admin` (agent) | `fastapi-database-admin` (agent) | Same agent |

---

## MUST-HAVE — High impact for daily workflow

### Skills (12)

| # | Hub Skill | Why |
|---|-----------|-----|
| 1 | **`skill-master`** | KKB has 25 skills growing to 35+. This is the universal entry point — dynamic runtime router that scans `.claude/skills/`, matches user intent to the right skill, suggests multi-skill workflows, and chains skills in sequence. Without it, developers must memorize all slash commands. |
| 2 | **`systematic-debugging`** | KKB has `fix-loop` for iterative test-fix but no structured root-cause-analysis skill. With 2000+ tests and async AI integrations (Claude + Gemini), debugging needs a methodical workflow: reproduce → isolate → hypothesize → gather evidence → fix → verify → prevent recurrence. |
| 3 | **`pg-query`** | KKB uses PostgreSQL as backend source of truth with 14 SQLAlchemy models. Read-only query assistant with EXPLAIN ANALYZE, schema exploration, and index statistics helps debug performance issues (meal generation ~35s, recipe search across 3,580 records). |
| 4 | **`tdd`** | KKB's workflow rule mandates "write tests first" (Step 2) but there's no dedicated skill enforcing strict red-green-refactor. This formalizes what KKB already aspires to — every line of production code justified by a failing test. |
| 5 | **`firebase-dev`** | KKB uses Firebase Phone OTP auth (both Android `com.google.firebase:firebase-auth` and backend `firebase-admin` SDK). This skill covers auth providers, security rules, CLI setup, and Firestore patterns. |
| 6 | **`firebase-ai`** | KKB uses Gemini via `google-genai` SDK for meal generation (structured JSON output with `response_json_schema`) and food photo analysis (Vision). This skill covers Firebase AI Logic integration including structured output, multimodal input, and streaming. |
| 7 | **`android-arch`** | KKB has a 4-layer Android architecture (app/domain/data/core) with Hilt DI, ViewModel + StateFlow, Room + Retrofit repositories. This skill provides Clean Architecture patterns with exactly these technologies. |
| 8 | **`android-gradle`** | KKB uses AGP 9.0.1, version catalogs (`libs.versions.toml`), KSP 2.3.2, Compose compiler plugins, and multiple Gradle modules. Build optimization and convention plugin patterns are directly relevant. |
| 9 | **`compose-ui`** | KKB has 18+ Compose screens with a design system (documented in `docs/design/RasoiAI Design System.md`). This skill covers Jetpack Compose UI development patterns — complements the existing `android-compose` agent. |
| 10 | **`pr-standards`** | KKB has `claude-code-review.yml` for automatic PR review but no skill enforcing team standards against PR diffs before submission. Shifts quality left. |
| 11 | **`request-code-review`** | Creates review-optimized PRs with risk analysis, test evidence, and focused review questions. Pairs with KKB's existing `claude-code-review.yml` workflow. |
| 12 | **`receive-code-review`** | Skill for systematically acting on code review feedback — parsing comments, categorizing must-fix vs nice-to-have, applying changes, requesting re-review. Completes the review lifecycle. |

### Hooks (2)

| # | Hub Hook | Why |
|---|----------|-----|
| 1 | **`dangerous-command-blocker.sh`** | PreToolUse on `Bash`. Blocks `rm -rf /`, `DROP DATABASE`, force pushes to main, protects `.git/`, `.claude/`, `.env`. KKB has a PostgreSQL production database and Firebase service account credentials — accidental destructive commands are a real risk. KKB's existing hooks enforce workflow process; this enforces safety. |
| 2 | **`secret-scanner.sh`** | PreToolUse on `Write|Edit`. Scans for AWS keys, API tokens, PEM keys, JWT secrets, hardcoded passwords. KKB uses `ANTHROPIC_API_KEY`, `GOOGLE_AI_API_KEY`, `JWT_SECRET_KEY`, and Firebase service account JSON. High risk of accidental secret leakage into committed code. |

### Agent (1)

| # | Hub Agent | Why |
|---|-----------|-----|
| 1 | **`security-auditor-agent`** | KKB handles auth (Firebase Phone OTP), JWT token rotation, encrypted storage (AES256-GCM), rate limiting, and GDPR compliance. A dedicated security auditor agent pairs with the `security-audit` skill for periodic vulnerability assessment. |

### Rules (2)

| # | Hub Rule | Why |
|---|----------|-----|
| 1 | **`context-management.md`** | KKB's CLAUDE.md is 25KB+ and sessions involve cross-layer work (Android ↔ backend). This rule enforces progressive disclosure, minimized context imports, scratchpad usage, subagent delegation for bulk reads, and compaction survival — all critical for long KKB sessions. |
| 2 | **`rule-writing-meta.md`** | KKB has 6 custom rules and will grow. This meta-rule teaches how to write effective rules: directive language, instruction budgets, when to use hooks vs rules vs skills. Prevents rule bloat. |

---

## NICE-TO-HAVE — Valuable but not blocking

### Skills (13)

| # | Hub Skill | Why / Why lower tier |
|---|-----------|---------------------|
| 1 | **`security-audit`** | Full security audit workflow (CodeQL, Semgrep, SARIF triage). KKB handles auth, JWT, encryption. Valuable but periodic, not daily. |
| 2 | **`adversarial-review`** | Structured adversarial review of security-sensitive code. Useful pre-release for auth/token rotation code. |
| 3 | **`branching`** | Full branch lifecycle management. KKB has `git-manager-agent` covering basics; this adds structured creation/cleanup. |
| 4 | **`git-worktrees`** | Isolated parallel development — useful for working on Android + backend simultaneously. Nice workflow improvement. |
| 5 | **`brainstorm`** | Socratic questioning before planning. KKB already has `strategic-architect` and `planner-researcher-agent`. Additive. |
| 6 | **`writing-plans`** | Structured plan generation. KKB has `plan-executor-agent` and `docs/plans/`. This adds the generation side. |
| 7 | **`executing-plans`** | Execute pre-written plans step by step. Complements `plan-executor-agent`; some overlap. |
| 8 | **`subagent-driven-dev`** | Orchestrate tasks across subagents. KKB's CLAUDE.md already uses subagent patterns; this formalizes orchestration. |
| 9 | **`batch`** | Bulk operations across KKB's 416 Kotlin + 98 Python files (e.g., rename, migrate patterns). |
| 10 | **`handover`** | Structured handover documents. KKB has `session-summarizer-agent` and `docs/CONTINUE_PROMPT.md`; this is a more structured version. |
| 11 | **`supply-chain-audit`** | KKB has many dependencies (gradle version catalog, requirements.txt). Periodic supply chain security checks. |
| 12 | **`learn-n-improve`** | Formalized learning system. KKB has a `reflect` skill; this adds analysis and self-modification. |
| 13 | **`firebase-data-connect`** | Firebase Data Connect (PostgreSQL + GraphQL). KKB uses PostgreSQL but not GraphQL — partially relevant if KKB ever adds a GraphQL layer. |

---

## SKIP — Not applicable to KKB

| Hub Resource | Reason |
|-------------|--------|
| `k8s-deploy` | KKB deploys to VPS with PM2 + Nginx. No Kubernetes. |
| `docker-optimize` | No Docker in deployment stack. |
| `iac-deploy` | No Terraform/Pulumi — VPS is manually managed. |
| `ci-cd-setup` | KKB already has 4 GitHub Actions workflows configured. |
| `monitoring-setup` | KKB already uses Sentry + structured JSON logging. |
| `incident-response` | Pre-launch product — no production incidents. |
| `semgrep-rules` | Custom Semgrep rule authoring is niche. `security-audit` covers Semgrep usage. |
| `xml-to-compose` | KKB is Compose-native — no XML layouts to convert. |
| `update-practices` / `contribute-practice` | Meta hub sync skills — handled by `collate.py` and `sync_to_projects.py`. |
| `writing-skills` | Skill authoring guide — KKB already has `skill-factory`. |
| `d3-viz` | Data visualization — outside KKB's domain. |
| `obsidian` | Vault management — not used by KKB. |
| `solidity-audit` | Blockchain — not applicable. |
| `playwright` | Browser E2E — KKB is Android native. |
| `remotion-video` | Programmatic video — not applicable. |
| `web-quality` | Web audit — KKB has no web frontend. |
| `vue-dev` / `nuxt-dev` / `expo-dev` / `flutter-dev` / `flutter-e2e-test` / `react-native-dev` | Wrong framework/stack. |
| `redis-patterns` | KKB's VPS has Redis but the app uses in-memory `cachetools`. Not currently applicable. |
| `twitter-x` / `reddit` / `github` | Social media / discovery skills — not development workflow. |
| `mcp-server-builder` | No MCP server building needed. |

---

## Summary: Recommended Additions

| Type | Must-Have | Nice-to-Have |
|------|-----------|-------------|
| Skills | 12 | 13 |
| Hooks | 2 | 0 |
| Agents | 1 | 0 |
| Rules | 2 | 0 |
| **Total** | **17** | **13** |

### Implementation Priority

1. **Safety first**: Add `dangerous-command-blocker.sh` and `secret-scanner.sh` hooks
2. **Routing**: Add `skill-master` so all 35+ skills become discoverable
3. **Stack-specific**: Add `android-arch`, `android-gradle`, `compose-ui`, `firebase-dev`, `firebase-ai`, `pg-query`
4. **Workflow**: Add `systematic-debugging`, `tdd`, `pr-standards`, `request-code-review`, `receive-code-review`
5. **Rules + agent**: Add `context-management.md`, `rule-writing-meta.md`, `security-auditor-agent`
