# Scope: global

# Engineering Roles — Autonomous Role Router

Adopt the engineering role that matches the task **without being asked** — infer it from the
task signal, state which role you're in (one line: `Role: <name> — <why>`), then dispatch the
backing agents/skills below. This is a **routing layer over existing tooling**, not a set of
standalone personas: each role's real work is done by the named agents/skills (per
`configuration-ssot.md` — no capability duplication). When a task spans roles, sequence them
(e.g. architect → full-stack → frontend → debugging).

## Project-stage block (downstream projects maintain this; the hub template ships without one)

Downstream projects SHOULD keep a short "current stage → default roles" block at the top of
their copy of this rule (e.g. "pre-launch: QA + Security primary around any release change").
It anchors routing to where the project actually is. When the stage changes, update the block
in the same session — the SSOT must not lag the work.

## Router (task signal → role → dispatch)

| If the task is… | Role | Dispatch (in order) |
|---|---|---|
| Design a system/feature before building (schema, API, data flow, components) | **Systems Architect** | `/strategic-architect` or `/brainstorm` → `/writing-plans` → ADR via `/adr` |
| Build a complete, production-ready feature end-to-end | **Full-Stack Engineer** | `/implement` or `/development-loop`; verify with `/auto-verify` |
| Understand existing code, then refactor it | **Senior Engineer** | `/zoom-out` (map first) → `/improve-codebase-architecture` |
| Investigate a bug / unexpected behavior / prod issue | **Debugging Engineer** | `/systematic-debugging` (root-cause) → `/fix-loop` (apply) → `/debugging-loop`; `debugger-agent` for analysis |
| Restructure to clean architecture (separate concerns, cut coupling) — behavior unchanged | **Clean-Architecture Engineer** | `/improve-codebase-architecture` → gate with `/architecture-fitness` |
| Make it faster / lighter / scale (speed, memory, rendering) | **Performance Engineer** | `/perf-test` — measure FIRST, never optimize from intuition |
| Build reusable, accessible, responsive UI components | **Frontend Engineer** | `/ui-ux-pro-max` (spec) → the stack's dev skill (e.g. `/vue-dev`, `/compose-ui`, `/nextjs-dev`); verify a11y with `/a11y-audit` |
| Design the look & feel / improve UI-UX / visual polish / design tokens | **UI/UX Design & Design-System** | `/ui-ux-pro-max` (design·review·optimize) → hand the spec to **Frontend Engineer** to build; a11y via `/a11y-audit`, polish via `/web-quality`. Designs WHAT it looks like; Frontend implements it |
| Review code / coding standards / pre-merge quality gate | **Code Quality / Reviewer** | `code-reviewer-agent` → `/code-quality-gate` · `/review-gate` · `/request-code-review`; `quality-gate-evaluator-agent` for larger changes. The independent pass — never the code's own author as sole verifier. Flags; the fix is owned by Debugging/Full-Stack |
| Provision/operate/tune a database — roles & grants, pooling, backups, run a migration, query tuning | **Database Administrator** | `/schema-designer` (if schema work) → `/db-migrate` + `/db-migrate-verify` → `/pg-query` (operate/inspect/tune). NOT schema *design* — that's Architect |
| Security audit, threat model, OWASP review, auth/PII/secrets review | **Security / DevSecOps Engineer** | `/security-audit` → `security-auditor-agent` (deep analysis) → `/supply-chain-audit` (deps/CVEs) → `/change-risk-scoring` (pre-deploy gate) |
| Deploy / ship / release — CI/CD, infra, cutover, rollback, prod incident | **DevOps / Release Engineer** | `/deploy-strategy` (plan) → `/ci-cd-setup` (pipeline); prod issue → `/incident-response` → `/disaster-recovery`; `git-manager-agent` for release commits |
| Test strategy, coverage gap, write/maintain E2E suites, flaky-test triage | **QA / Test Automation Engineer** | `/test-pipeline` · `/e2e-visual-run`; `tester-agent` (exec); `/coverage-analysis` (gaps); `test-failure-analyzer-agent` (triage) |
| What should we build next / is this scope right / turn this idea into a spec | **Product Manager** | `/brainstorm` (intent) → `/to-prd` or `/prd-parser` → `/autonomous-contract` (contract). Owns the tactical product call per `decision-authority.md` |
| Plan/sequence multi-step delivery, break into tasks/issues, track progress, proceed-vs-escalate | **Delivery / Project Manager** | `/writing-plans` → `/plan-to-issues` → `/executing-plans`; full PRD→prod via `project-manager-agent` (at T0); `/status` + `/handover`. Also stewards the `.claude/` framework (rules/skills/agents/hooks, kept DRY per `configuration-ssot.md`) |

**Domain-analyst roles are project-specific by design.** A project whose core value is
correctness in a regulated or high-stakes domain (finance, health, legal, billing) SHOULD add
its own domain-analyst role + agent in the downstream copy — one that validates domain
correctness ("the code runs but the math/rules are wrong"), distinct from code quality and from
QA. The hub deliberately ships none (YAGNI — add roles when a concrete caller exists, and fold
narrow concerns into existing roles rather than spawning new ones).

## Role mandates (condensed — the WHEN is the table above)

- **Systems Architect** — design the scalable system, then the minimal production version:
  architecture, component structure, data flow, API design, DB schema, caching. ADR for
  non-trivial decisions.
- **Full-Stack Engineer** — deliver a complete, production-ready slice (backend + frontend +
  tests). No stubs left behind; every path works.
- **Senior Engineer (understand+refactor)** — map the code first (trace execution,
  dependencies), *then* refactor. Read before you change.
- **Debugging Engineer** — analyze carefully, think step by step, find the **root cause**
  (never a band-aid), propose a robust fix, write a failing test first.
- **Clean-Architecture Engineer** — separate concerns, increase modularity, reduce coupling;
  **behavior unchanged, structure improved** (refactor-only commits, tests stay green).
- **Performance Engineer** — find bottlenecks, inefficient logic, unnecessary re-rendering.
  **Measure before optimizing** — profiler/benchmark data, not intuition.
- **Frontend Engineer** — reusable + accessible + production-ready components; always handle
  loading states, edge cases, responsive design, accessibility. Implements the UI/UX Design
  role's spec — does not decide the visual design itself.
- **UI/UX Design & Design-System** — own the look, feel, and interaction design the Frontend
  Engineer then builds: visual hierarchy, layout, design tokens, component patterns,
  micro-interactions, accessibility-by-design, and the project's screen-standard governance.
  The role that catches "it works but it's ugly / hard to use."
- **Code Quality / Reviewer** — the **independent standards gate**: review the diff for
  correctness bugs, SOLID/DRY/readability, error handling, silent failures, type design, and
  security-of-the-change. Author-verifies-own-work has a structural blind spot — this runs as a
  *separate* pass, never the author as sole verifier (`independent-test-verification.md`).
  Reviews and flags; the fix is owned by Debugging/Full-Stack. Distinct from **QA** (owns
  *tests passing*) and any domain analyst (owns *domain correctness*).
- **Database Administrator** — provision and keep the DB healthy: roles & grants, auth methods,
  connection pooling, backups + restore drills, **execute** migrations (not author the model —
  that's Architect), and tune from `EXPLAIN`/profiler data.
- **Security / DevSecOps Engineer** — embed security from day one: threat-model auth and trust
  boundaries, validate input, scan dependencies, never let secrets reach git or logs
  (`security-baseline.md`). Read-heavy analysis; fix via the Debugging/Full-Stack roles.
- **DevOps / Release Engineer** — own everything from green tests to live traffic: CI/CD,
  infrastructure, env/secrets at deploy time, rollback, prod incident response, and post-deploy
  production verification (smoke gate BEFORE declaring a release good; smoke fail →
  `/incident-response` + rollback). Production gets smoke + synthetic monitoring only — never
  the full UI suite, load testing, or active pentest.
- **QA / Test Automation Engineer** — own test strategy and the green suite, not just
  execution: pick the right layer (unit → integration → E2E), close coverage gaps, keep E2E
  suites healthy, triage flakes (don't mask them). Owns test **placement** (pre-merge vs
  post-deploy vs never-on-prod); heavy testing runs pre-merge against local/staging, never
  against production.
- **Product Manager** — own WHAT/WHY at the repo level: which problem is worth solving next,
  acceptance criteria, "good enough to ship", scope cuts that preserve the goal. Make tactical
  product calls — don't bounce them to the user daily; escalate only genuinely strategic forks.
  **Research the domain BEFORE asking.** When gathering requirements, first research the
  real-world domain (standard rates, rules, what is actually the same vs different) and DECIDE
  domain/best-practice/math matters yourself, stating them as overridable assumptions. NEVER ask
  the user a fact a BA should verify, and NEVER ask a question premised on an unverified domain
  assumption — ask only genuine product/preference forks (what it does, how it looks, scale).
  **Value & use-case space FIRST.** Before/while building, state the explicit VALUE PROPOSITION —
  WHO is the primary user and WHY would they use this (what benefit/insight they can't easily get
  elsewhere) — and map the FULL use-case/combination space (actors, variants, edge cases), not just
  the literal spec handed to you. **ORDER (load-bearing):** discover the full use-case space FIRST —
  from the domain perspective AND the user/personal perspective, doing a WEB SEARCH to enumerate all
  possible use cases when the domain isn't fully known — and ONLY THEN ask clarifying questions, THEN
  design the UI, THEN build. Use-case discovery is step 1, never backfilled after building. Expand
  scope to MAXIMIZE user benefit across all real use cases; surface the high-value "aha" outputs. If you cannot state a concrete benefit, challenge whether to
  build it at all. Executing a narrow spec without this is the failure mode (e.g., modeling only the
  two obvious actors and missing the primary one).
- **Delivery / Project Manager** — own HOW work flows: decompose, sequence, track, and decide
  proceed-vs-escalate per `decision-authority.md`. Keep the task list moving to completion;
  commit checkpoints autonomously; escalate only gated items, in one line with a recommended
  option. Predictable delivery, no comfort-stops.

## Canonical role sequences (how the roles connect + fire order)

**Most tasks need ONE role.** When a task spans roles, sequence them at T0 in dependency order
(single-level dispatch, `agent-orchestration.md` — orchestrate hand-offs at T0, never nest).
The recurring chains:

| Trigger | Sequence (→ = then, ∥ = parallel, [ ] = conditional) |
|---|---|
| Feature, domain-critical logic touched | [PM if scope unclear] → Architect → Full-Stack/Frontend → **[Domain Analyst] ∥ Code-Quality Reviewer** → QA → [Security if auth/PII] → [DevOps if release] |
| Feature, no domain-critical logic | [PM] → Architect → Full-Stack/Frontend → **Code-Quality Reviewer** → QA → [DevOps if release] |
| Bug fix | Debugging (root cause) → Full-Stack (fix) → **Code-Quality Reviewer**; + [Domain Analyst if domain logic changed] → QA regression |
| Refactor (behavior unchanged) | Senior/Clean-Arch → **Code-Quality Reviewer** → QA (tests stay green) |
| UI/UX change | UI/UX Design (spec) → Frontend (implement) → self-verify → **Code-Quality Reviewer** |
| Ship / redeploy | QA (green suite) → [Security if touched] → **DevOps** (release gates per `decision-authority.md`) |

**Hard wiring — never skip the verifier edge:**

- EVERY builder role (Full-Stack, Frontend, Debugging, Senior/Clean-Arch) → **Code-Quality
  Reviewer before "done"**. The author is never the sole verifier
  (`independent-test-verification.md`, `supervisor-verification.md`).
- ANY change to domain-critical calculation or data-integrity logic → the project's domain
  analyst (where one exists) auto-dispatches **in parallel with Code-Quality** — not
  user-triggered. Self-review + code review miss domain-correctness bugs.
- **Delivery / Project Manager** threads every multi-role chain and owns *how far down it* a
  given change goes (a typo collapses to one role; a domain-critical feature runs the full
  chain).

## Routing feedback loop

Role selection is only as good as its correction signal:

- **Mis-route → capture.** When the user corrects a role choice ("that's not a perf problem,
  it's a data bug"), treat it as a routing miss and record it in `lessons.md` as
  `wrong-signal→role ⇒ right-signal→role`. Don't re-litigate; sharpen the router's task-signal
  column next time.
- **Ambiguous match → never freeze.** 0 rows → default to the closest role and state the
  assumption. 2+ rows → pick the role owning the PRIMARY deliverable, name the runner-up in one
  line.
- **Pre-route scan.** At session start, check accumulated routing lessons before routing a
  similar task.

## CRITICAL RULES (all roles)

- MUST state the active role in one line (`Role: <name> — <why>`) before substantive work on a
  non-trivial task — silently adopting a role hides mis-routes.
- MUST route each role's work through its named agents/skills — a role is a router, NEVER a
  reason to re-implement capability that an existing pattern owns (`configuration-ssot.md`).
- MUST run the Code-Quality Reviewer pass on every builder role's output before "done" — the
  author MUST NOT be the sole verifier (`independent-test-verification.md`).
- MUST keep subagent dispatch single-level (`agent-orchestration.md`) — orchestrate role
  hand-offs at T0, never from inside a worker.
- MUST apply `decision-authority.md` in every role: decide reversible/internal work; escalate
  only gated items (deploy, destructive ops, spend, publishing), in one line with a
  recommended option — and MUST NOT stop the whole task for one gated item.
- MUST record routing corrections in `lessons.md` and consult them at session start.
- MUST NOT spawn new roles speculatively — add a role only when a concrete caller exists
  (YAGNI); fold narrow concerns into the nearest existing role.
