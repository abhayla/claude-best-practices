# Plan — Idea → Production-Deployed Readiness (Goal #3)

**Status:** active · **Created:** 2026-06-17 · **Owner:** Abhay
**Anchors:** README goal #3 (idea → production-deployed, role-per-stage) ·
`engineering-roles.md` · `decision-authority.md` · audit 2026-06-17 (4 parallel stage agents)

## Why

README goal #3 commits the hub to taking an idea all the way to a **deployed** app, with
the right role owning each stage. A 2026-06-17 audit found the build→test→verify core is
production-grade, but **three gaps break the full chain**. This plan closes them generically
in `core/` so any downstream project inherits the capability.

## Decisions (locked 2026-06-17)

- **Operating model (dogfood loop):** Claude conceives its OWN app idea and drives it
  idea→production-deployed THROUGH this pipeline. Every gap hit during the real build is closed
  in the hub *then*, justified by a concrete caller (no speculative YAGNI), and the app keeps
  moving. Build the app and upgrade the hub interleaved — the app is the forcing function, the
  hub upgrades are the durable output. (Abhay's reframing, 2026-06-17.)
- **Deploy target:** Hostinger **VPS** — executor is SSH + Docker (portable, not MCP-session-bound).
- **Scope:** hub upgrades land generically in `core/.claude/`; the app lives in its own repo/dir.
  The app exists to *exercise and prove* the chain, not as the deliverable — the hardened hub is.
- **Domain BA:** a generic BA becomes domain-deep by **researching the domain at runtime**
  (wire existing research primitives into the requirements stage) — NOT by pre-shipping N
  static per-domain modules (that stays YAGNI-rejected). This is Abhay's reframing.
- **Human-in-the-loop:** explicit user-approval pauses are REQUIRED at (a) UI mockup before
  build and (b) before production deploy; plus a feature sign-off after verification.

## Units (sequence)

### Unit 1 — Human-approval gates (SSOT spine) · low risk · DO FIRST
- **New rule** `core/.claude/rules/human-approval-gates.md` (`# Scope: global`): defines the
  mandatory human checkpoints in the idea→deploy pipeline — UI/design-mockup approval before
  implementation, feature acceptance after verification, production-deploy approval (the last
  one points to `decision-authority.md`, which already gates deploy — no duplication).
- Registry: add entry + bump `_meta.total_patterns` + `last_updated`; run
  `pytest scripts/tests/` (esp. `test_registry_integrity.py`), the 2 validators, `generate_docs.py`.
- Verification: validators green + full pytest green.

### Unit 2 — Domain-research BA step · medium risk
- Enhance `core/.claude/skills/brainstorm` requirements stage + the Product Manager role
  routing in `engineering-roles.md` to dispatch domain research (`/research-mode`,
  `/deep-research`, `web-research-specialist-agent`, `/grill-with-docs`) BEFORE asking
  clarification, then write domain-specific acceptance criteria.
- Verification: a brainstorm run on a regulated-domain idea surfaces domain-specific questions
  + ACs that a generic run would miss.

### Unit 3 — VPS deploy-executor · high risk · BUILD DURING FIRST REAL APP
- **New skill** `core/.claude/skills/vps-deploy` (`type: workflow`): SSH + `docker compose`
  deploy to a Hostinger VPS, env/secret injection at deploy time, post-deploy smoke against
  the live URL, rollback on smoke-fail; wire into the DevOps/Release role.
- Deferred deliberately: building a VPS deployer before the real app's stack + live server is
  speculative. Needs Abhay's host + credentials at deploy time (escalate then).
- Verification: deploy a throwaway container to the VPS, confirm live-URL smoke + rollback.

### Unit 4 — Pipeline integration · medium risk
- Wire Units 1–3 into `project-manager-agent` + `config/pipeline-stages.yaml`: insert the
  approval-gate pauses, the domain-research step, and the deploy-executor stage; update
  `docs/stages/STAGE-4-HTML-DEMO.md` (remove "runs autonomously" where a gate now pauses) and
  STAGE-10-DEPLOY.
- Verification: smoke-test the pipeline DAG; `test_workflow_closure_consistency.py` green.

## Self-improvement loop (runs at EVERY stage — Abhay's standing directive 2026-06-17)

While building the app, after each stage AND on every mistake/correction/friction, run a
self-improve micro-cycle (do NOT defer it to the end):

1. **Detect** — did I hit a mistake, friction, a routing miss, or a hub capability gap this stage?
2. **Type it** (`learnings-routing.md`): GENERIC craft/process/tooling vs PRODUCT-SPECIFIC (this app's domain).
3. **Route + act**:
   - GENERIC craft/process → append to `.claude/tasks/lessons.md` (+ memory); propose a rule change (approval-gated) if it's a constraint.
   - HUB CAPABILITY GAP (a Unit hit by a real caller) → close it in `core/` NOW + land via PR, then continue the build (concrete caller = no speculative YAGNI).
   - PRODUCT-SPECIFIC → the app's own docs, never a hub pattern.
4. **Prefer a deterministic gate** (hook/test/validator) over prose when mechanically enforceable.
5. **Capture** via `/learn-n-improve` after any fix (per `claude-behavior.md` rule 15); dedup before filing.
6. **Continue** the build — the app keeps moving; the hub upgrades + lessons are the durable byproduct.

The hardened hub + the accumulated lessons are the real deliverable of the run; the app proves them.

**Execution engine.** The build does not run the self-improve cycle as a side-discipline — it runs
*under* `/loop-engineering` (v1.1.0), whose DISCOVER→PLAN→EXECUTE(maker)→VERIFY(checker, maker≠checker)
→GATE→(SHIP|FEEDBACK self-heal)→LEARN cycle IS the iterative self-feedback loop, bounded by
`--max-cycles` + retry budget. Cross-run compounding rides `/learning-self-improvement` (capture →
3+-evidence pattern detection → staged skill/rule proposals → staleness prune).

**Honest gap — Unit 5 (measured self-feedback).** Loops 1–2 self-heal and capture lessons well, but the
*measured* fitness signal (am I provably improving task-over-task — first-pass success rate up, heals/cycle
down?) is thin: it depends on `aggregate_telemetry.py`'s effectiveness data, which is nascent (audit gap B).
This closes as the dogfood run accumulates cycles — surface per-run metrics (cycles, heals, escalations,
first-pass-pass) and trend them so "improving" is evidenced, not asserted. Build when enough runs exist.

## Where the app lives + how feedback returns (no silent loophole)

The app is built in its **own repo** (the hub is the framework — building an app inside it would
pollute the template), synthesized via `/synthesize-project --repo <app>`. Feedback returns to the
hub by 4 paths: in-session hub PR (immediate, when a gap is hit — primary), `/contribute-practice`
(on-demand pattern push), `collate.py`/scan-projects (weekly), `aggregate_telemetry.py` (weekly,
reads committed `.claude/learnings.json`). `/synthesize-hub` generalizes shared patterns.

### Dogfood-bootstrap checklist — MUST run at app-project creation, BEFORE the first code line

These are preconditions the feedback flows assume; if unset, the app improves locally but nothing
reaches the hub (the silent loophole). Wiring them at birth is non-negotiable:

1. **GitHub remote** — create + push the app repo (aggregators read via GitHub API; local-only = invisible).
2. **Enroll** the repo in the hub's `config/repos.yml` (else collate + telemetry never scan it).
3. **Commit `.claude/learnings.json`** — MUST NOT be gitignored (hub reads the committed file; gitignored = zero signal — loop-engineering's #1 silent failure).
4. **`allow_hub_sharing: true`** in the app's `.claude/synthesis-config.yml` (enables `/synthesize-hub`).
5. **Routing discipline** (`learnings-routing.md`) — generic learnings flow hub-ward; product-specific stay in the app. The loop-engineering signals carry `hub_pattern_link` so the aggregator matches them.

Build this as a real `/bootstrap-dogfood-project` step (or fold into `/synthesize-project`) when the
project-creation stage is hit — until then this checklist is the contract. A run is NOT "set up"
until all 5 are verified green.

## Done = README goal #3 is truthfully met: an idea runs idea→clarify(domain-deep)→UI+approve
→build→test→verify→sign-off→deploy-to-VPS, with the right role at each stage — AND the
self-improvement loop above ran at every stage (lessons captured, gaps closed in the hub).
