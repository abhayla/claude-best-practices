# Plan: Promote firekaro-planner patterns into the hub

**Owner:** hub architect pass · **Started:** 2026-06-09 · **Source:** `D:/Abhay/VibeCoding/firekaro-planner`

Manual curation pass (firekaro `allow_hub_sharing: false`, so the automated
flywheel is off). Goal: generalize firekaro-originated patterns into
`core/.claude/` so all downstream projects benefit. Strict bar: portable
(no firekaro/finance/INR/persona refs), evidence-backed, no duplication,
registry+changelog+validators per `core/.claude/rules/rule-curation.md`.

Each tier ships as its **own branch + PR** (per standing preference).

## Tier 1 — 8 universal verification/governance rules  ← IN PROGRESS
Branch: `feat/promote-firekaro-verification-rules`. Pure-additive, no script changes.

| New hub rule | From firekaro | Scope |
|---|---|---|
| `output-plausibility-verification.md` | `output-plausibility-verification.md` | global |
| `independent-test-verification.md` | `independent-test-verification.md` | global |
| `supervisor-verification.md` | `orchestrator-output-validation.md` | global |
| `decision-authority.md` | `decision-authority.md` (kernel only; git → git-collaboration) | global |
| `bug-triage-discipline.md` | `bug-filing-and-sibling-audit.md` | global |
| `environment-validation.md` | `environment-validation.md` | global |
| `e2e-readiness-signal.md` | `e2e-hydration-signal.md` | globs: E2E |
| `e2e-persistence-verification.md` | `e2e-multi-row-verification.md` | globs: E2E |

De-firekaro checklist: strip FIRE/tax/INR/persona, firekaro.com/VPS, `src/lib`,
agent names (FinTech Domain Analyst, git-manager-agent), hook filenames,
firekaro rule numbers, GitHub repo URLs, dates, "Abhay". Fix the
`non-blocking-side-effects` `console.error` inconsistency if that idea is carried.

## Tier 2 — merges into existing hub patterns
Branch: `feat/promote-firekaro-quickwins` (later).
- DoD-verbs-are-load-bearing → small rule + fold into `writing-plans`/`brainstorm`
- Zero-open-questions grep gate → `writing-plans`
- GENERIC-vs-PRODUCT-SPECIFIC learnings routing → rule or `self-improve`
- Numeric safety (NaN/Inf/÷0) + fire-and-forget `.catch()` → `error-handling.md`
- Structured-logging choke point + message-interpolation trap → `security-baseline.md`
- API-as-oracle calc verification + never-full-regression-on-prod matrix → `e2e-best-practices`
- Background-run worktree lock → `git-worktrees`

## Tier 3 — new backend stack rule sets (needs bootstrap.py/recommend.py stack detection)
Branch(es): `feat/hub-hono-stack`, `feat/hub-prisma-stack` (later).
- New `hono-*`: `hono-route-conventions` + `api-envelope-pattern` (+ pagination, rate-limit note)
- New `prisma-*`: `prisma-conventions`
- Vuetify+Playwright E2E: `e2e-vuetify-timing` + `e2e-vee-validate-forms`
- Merge into `vue.md`: pinia ref()-over-reactive(), url-query-sync, form-validation, api-response-unwrapping
- Requires: `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS`+`DEP_PATTERN_MAP` (recommend.py) + tests

## Tier 4 — `autonomous-contract` authoring skill (from goal-creator)
Branch: `feat/hub-autonomous-contract-skill` (later). `/brainstorm` first.
- New genre: interview → zero-input self-contained contract → hand to an autonomous executor
- Port: zero-open-questions gate, idempotency/ledger preflight, worktree+lock isolation,
  cross-session progress log, DONE/PENDING/BLOCKED/NEXT summary, DoD-verbs, env-provisioning
- De-firekaro the `/goal` executor coupling; needs `/skill-evaluator` before merge

## SKIP (verified project-specific / duplicate)
plan-before-coding (=rule 1), documentation-management (=design-ssot), commit-convention
(=git-collaboration), session-management (=session skills), engineering-roles,
must-have-only-focus (=YAGNI), type-organization, all finance-domain rules,
ui-verification / e2e-test-runner / e2e-auto-fixer / verify-ui skills,
fintech-domain-analyst agent, wati-* skills.
