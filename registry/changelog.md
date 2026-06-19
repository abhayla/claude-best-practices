# Changelog

All notable pattern additions, updates, and removals.

## [Unreleased]

### 2026-06-19 — Add cross-project context-capture rule (category: core, tier: must-have)

- **added** rule `cross-project-context-capture` (`core/.claude/rules/cross-project-context-capture.md`, global scope) — capture-on-sight of facts bigger than one repo (shared accounts, registrations, contacts, vendors, compliance text, cross-cutting prefs) to the workspace-level global files, in the SAME session they surface; route by sensitivity (secret/credential → the global secrets file per `security-baseline.md`; non-secret fact/preference → the global context file); reference by PATH only, never copy contents into a repo (PII/leak + stale-copy risk). The cross-PROJECT analog of `learnings-routing` (one home WITHIN a project) and `configuration-ssot` (one canonical layer per fact). Portable by design — no hardcoded paths; a no-op when the workspace keeps no such files (YAGNI). Distributable to downstream projects. `_meta.total_patterns` 267 → 268.

### 2026-06-19 — idea-to-deploy-readiness Unit 4 COMPLETE: human-approval gates + domain-research step wired into the pipeline

- **updated** agent `project-manager-agent` (1.0.0 → 1.1.0, MINOR) — responsibility #2 now MUST HALT for the human-approval gates G1 (after `stage_4_demo`), G2 (after `stage_9_review`), G3 (before `stage_10_deploy`) per `human-approval-gates.md` — present the artifact + STOP, never infer approval from silence. Folded into the existing responsibility (count stays 4 — rule-8 cap respected); hash resynced.
- **updated** `config/pipeline-stages.yaml` — `stage_1_prd` documents the domain-research-first step (Unit 2 → `/brainstorm` STEP 1.0); `stage_4_demo` documents the G1 pause; `stage_9_review` documents the G2 pause (G3 already on `stage_10_deploy`).
- **updated** `docs/stages/STAGE-4-HTML-DEMO.md` — G1 human-approval PAUSE banner (demo generation autonomous, then STOP for "build THIS" before implementation).
- Completes idea-to-deploy-readiness Unit 4 (pipeline integration). Verified: pipeline-stages.yaml parses, PM-agent responsibility count = 4 (≤ rule-8 cap), full CI green.

### 2026-06-19 — idea-to-deploy-readiness: Unit 2 (domain-research BA) + Unit 4 deploy-executor wiring

Closes the two autonomous gaps the migration's sibling plan (goal #3) still had after `vps-deploy` shipped.

- **updated** skill `brainstorm` (1.1.0 → 1.2.0, MINOR; also fixed a prior 1.0.0/1.1.0 registry drift) — STEP 1 now opens with **STEP 1.0 Domain research FIRST**: for regulated/specialized domains, dispatch `/research-mode` / `/deep-research` BEFORE clarifying questions (never ask a fact a BA should verify), make the questions domain-informed, and write domain-specific ACs. Closes Unit 2's `/brainstorm`-body gap. Hash resynced.
- **wired `/vps-deploy` into the pipeline (Unit 4 deploy-executor)** — `docs/stages/STAGE-10-DEPLOY.md` Step 3 gained a Self-Managed VPS Path (SSH+nginx/PM2, live-URL smoke + rollback = the gate); `config/pipeline-stages.yaml` `stage_10_deploy` documents the executor-by-target map + the G3 human-approval gate. (Docs/config — not registered patterns.)
- Unit 4's remaining DAG gate-pauses + STAGE-4 edit are deferred to a focused pass (load-bearing `project-manager-agent`/DAG; context-rot discipline) — autonomous, not owner-blocked.

### 2026-06-19 — Phase 4.2-C5: empirical nested-dispatch pilot → evidence-based decision

Ran the C5 pilot the honest way — **a live probe instead of an assertion**: a dispatched worker subagent successfully spawned its own sub-worker and returned its result, confirming nested dispatch works **in-environment** (≤5 levels), not just per the docs. Evidence-based decision: nesting is now a **tested, ready option**; the hub keeps single-level by **default** because a workflow audit (test-pipeline, development-loop, code-review-workflow, loop-engineering, project-manager-agent) found no current 2-level decomposition need (the one near-candidate, loop-engineering's MAKER→CHECKER, saves only one T0 round-trip vs depth-2 complexity). No production workflow nested — by evidence, not assumption.

- **updated** rule `agent-orchestration` (1.2.0 → 1.3.0, MINOR) — top note records the empirical verification + the evidence-based keep-single-level decision + a **dual-mode adoption recipe** (mark the worker `dispatched_from: dual-mode` + add `Agent`; validator-sanctioned, no code change) for when a concrete multi-level need arrives. Hash resynced.
- No validator/pattern churn (dual-mode was already sanctioned by `pattern-structure.md`); convention assertions unchanged.

### 2026-06-19 — Phase 3.2: governance prose → harness (deterministic `permissions.deny` rules)

Encodes the git-gate-bypass slice of `decision-authority.md`'s irreversible-action escalation list as **deterministic deny rules** (they apply in EVERY permission mode), so a forgotten prose rule is *blocked*, not just discouraged. Owner-approved 2026-06-19. Scoped to unambiguous always-wrong invocations (no `reset --hard`/`rm -rf` — too false-positive-prone; no deploy/DNS matchers — Auto mode already hard-denies prod deploy + push-to-main natively).

- **updated** `core/.claude/settings.json` + `.claude/settings.json` (hub dogfoods it) — `permissions.deny` now blocks `git push --force` / `-f`, `git push --no-verify`, `git commit --no-verify` / `-n` (maps to `git-collaboration.md` MUST-NOTs).
- **updated** rule `decision-authority` (1.0.0 → 1.1.0, MINOR) — new "Harness enforcement (prose → deterministic deny rules)" section documenting the two harness layers (native Auto mode + these deny rules); hash resynced.
- **added** test `test_governance_deny_rules.py` — pins the required deny set in both settings files + the decision-authority harness doc.

### 2026-06-19 — Add `vps-deploy` skill (Platform Migration 2.3 / idea-to-deploy-readiness Unit 3 — the deploy=finish-line gap)

Closes the deploy gap with the reusable, env-var-driven deploy capability the readiness plan deferred until a real target existed. Owner-approved 2026-06-19; grounded in a verified self-managed Linux VPS stack (nginx + static webroots + PM2; NO Docker — so SSH+rsync+nginx, not docker-compose). `total_patterns` 266→267.

- **added** skill `vps-deploy` (v1.0.0, nice-to-have) — SSH+rsync deploy of a built artifact to a self-managed Linux VPS: backup prior release → rsync to webroot → **`nginx -t`-gated reload** (or PM2 reload) → **live-URL smoke** (verifies NEW-release substance, not just HTTP 200) → **auto-rollback on smoke-fail**. Portable: reads `DEPLOY_HOST/USER/SSH_KEY/WEBROOT/URL` from env (never hardcodes host/keys; keys stay in `~/.ssh/`). Treats prod deploy as a G3 human-approval gate; deps deploy-strategy/pm2-deploy/incident-response/disaster-recovery.
- **updated** rule `engineering-roles` (1.5.0 → 1.6.0, MINOR) — DevOps/Release row points to `/vps-deploy`.

### 2026-06-19 — Adopt native `/code-review ultra` + `/autofix-pr` by pointer (Platform Migration 2.1/2.2); decline crons→Routines (3.1)

Migration goal "thin layer on top of the platform": adopt two GA native Claude Code features as **additive pointers** in the distributable patterns — NOT replacements. Both are cloud / billed / Claude-GitHub-App, opt-in, and **never auto-invoked** by hub patterns; the free local hand-rolled skills (`/review-gate`, `/fix-loop`, etc.) stay the default. Verified before effort (3 Explore agents + web check): `/autofix-pr` is real ([web docs](https://code.claude.com/docs/en/claude-code-on-the-web)); `/code-review ultra` is user-triggered + billed.

- **updated** skill `code-review-workflow` (2.1.1 → 2.2.0, MINOR) — DEEP_AUDIT step now recommends native `/code-review ultra` as an opt-in cloud deep pass alongside the local agent dispatch.
- **updated** skill `review-gate` (registry 2.0.0 → 2.4.0; also fixes a prior file/registry version drift) — added a "native cloud alternative" note pointing to `/code-review ultra`; the local gate stays the free default.
- **updated** skill `fix-loop` (1.4.0 → 1.5.0, MINOR) — documents `/autofix-pr` (cloud PR-watcher) vs `/fix-loop` (local iterative) boundary.
- **updated** skills `pipeline-fix-pr` (1.0.0 → 1.1.0) + `debugging-loop` (2.1.2 → 2.2.0) — one-line `/autofix-pr` pointers for the open-PR case.
- **updated** rule `engineering-roles` (1.4.2 → 1.5.0, MINOR) — Code-Quality/Reviewer row points to `/code-review ultra`; DevOps/Release row points to `/autofix-pr`.
- All 6 registry hashes resynced; no pattern deleted/replaced (additive only).
- **Phase 3.1 (crons→Routines): DECLINED** (no code change) — recorded in `plans/platform-migration-2026H2.md` as KEEP-as-GH-Actions. The 5 scheduled workflows are deterministic Python+git pipelines (not agentic); Routines are scheduled cloud agents → negative ROI. Mirrors the Phase 1.3 KEEP precedent.

### 2026-06-19 — RETIRE 6 deprecated test-pipeline patterns (Platform Migration 2026 H2, Phase 0 ledger)

Removes 6 patterns that were `deprecated`/`deprecated: true` since 2026-04-24, fully superseded by the active `/test-pipeline` skill-at-T0 (its flat workers) and `/fix-github-issue`. Owner-approved deletion 2026-06-19. `total_patterns` 272 → 266. Test surgery removed ONLY the dead-agent contract assertions; every live `/test-pipeline` worker guard (tester-agent, test-scout-agent, visual-inspector-agent, test-failure-analyzer-agent, github-issue-manager-agent, test-healer-agent) is preserved. The canonical spec `docs/specs/test-pipeline-three-lane-spec-v2.md` is annotated HISTORICAL (functional contract preserved in `/test-pipeline`), not deleted.

- **removed** agent `e2e-conductor-agent` → `/test-pipeline` (+ `/e2e-visual-run`)
- **removed** agent `test-pipeline-agent` → `/test-pipeline`
- **removed** agent `failure-triage-agent` → `/test-pipeline` (+ its `evals/` scenarios)
- **removed** agent `testing-pipeline-master-agent` → `/test-pipeline`
- **removed** skill `testing-pipeline-workflow` → `/test-pipeline`
- **removed** skill `fix-issue` (deprecation stub) → `/fix-github-issue`
- **updated** `registry/patterns.json` — 6 entries removed; `_meta.total_patterns` 272→266; stale `description`s of live `test-pipeline` ("dispatching test-pipeline-agent") and `github-issue-manager-agent` ("Spawned by failure-triage-agent") repointed to `/test-pipeline`.
- **updated** config `orchestrator-responsibility-allowlist` — sole entry (failure-triage-agent) removed → `allowlist: []`; hash resynced.
- **updated** `config/workflow-groups.yml` (dropped 6 seeds), `scripts/recommend.py` (`MUST_HAVE_AGENTS` − test-pipeline-agent), `CLAUDE.md` (legacy master-agents 8→7; workflow map row repointed to `test-pipeline`).
- **removed/edited** ~11 coupled test files — dead-agent assertions/cases/parametrize entries dropped; `test_tier_dispatch_consistency.py` deleted (its DISPATCH_CHAIN keyed only deleted orchestrators).

### 2026-06-19 — orchestration doctrine: single-level is a CONVENTION, not a platform limit (Phase 4.2 C2–C4)

Reframes the hub's single-level subagent-dispatch doctrine from "platform-forced" to "deliberate KISS/YAGNI convention." Nested subagent dispatch went GA in Claude Code (v2.1.172, ≤5 levels), so the old rationale ("Claude Code does not forward `Agent` to subagents" / "runtime strips it") is factually stale. Prose-only reframe — **all validator assertions and existing patterns are unchanged and stay green** (workers still don't declare `Agent`, now by convention rather than platform limit). Also corrects one now-false mechanism claim: the runtime *would* expose `Agent` to a worker below the 5-level cap; only the depth-5 cap genuinely withholds it. No master-agent / workflow / `project-manager-agent` changed (per `plans/skill-at-t0-doctrine-relaxation.md` C4 decision). C5 pilot deferred (YAGNI).

- **updated** rule `agent-orchestration` (v1.1.0 → v1.2.0, MINOR) — §1–§3/§10 + §6 reframed to convention; the dated dual-banner collapsed into one settled note.
- **updated** rule `pattern-structure` (v1.1.0 → v1.2.0, MINOR) — "Tool Grants (Platform-Constrained)" → "(Single-Level Convention)"; tables corrected from "`Agent` stripped at runtime" to "flat by convention"; stale planned-probe paragraph trimmed.
- **updated** rule `independent-test-verification` (v1.0.0 → v1.1.0, MINOR) — coherence sibling: "Subagents cannot spawn subagents" → "hub workers stay flat by convention" (operational conclusion unchanged).
- **updated** rule `supervisor-verification` (v1.0.0 → v1.1.0, MINOR) — coherence sibling: "The platform allows a single dispatch level" → "the hub uses a single dispatch level by convention."
- **updated** `scripts/tests/test_orchestrator_tool_grants.py` (C2) — module docstring + assertion-message rationale reframed to convention; **assertions untouched** (118 passed / 77 skipped, unchanged).
- **updated** `CLAUDE.md` (C4) — "Workflow Orchestration (skill-at-T0)" rationale reframed from platform-constraint to deliberate convention.

### 2026-06-17 — loop-engineering: hub-ward monitoring (v1.1.0)

Closes the downstream-observability gap: the loop now emits a hub-linked learning on every terminal outcome, so the existing weekly telemetry cron monitors it automatically — no new pipeline, no outward call from the project.

- **updated** skill `loop-engineering` (v1.0.0 → v1.1.0, MINOR) — STEP 1.5 / STEP 6 / STEP 7 now append a `.claude/learnings.json` entry with `hub_pattern_link: "loop-engineering"` + a typed `signal` (`preflight_blocked` / `escalated` / `healed` / `shipped`) and a stable `tags` defect-class signature. `aggregate_telemetry.compute_error_prevention_rate` already keys on `hub_pattern_link` + `tags`, so escalations and PREFLIGHT blocks surface as per-pattern effectiveness in `registry/patterns.json` on the Friday cron over enrolled repos. Spec §5.1.
- **fixed** `aggregate_telemetry.py` (B1, caught by independent review) — `aggregate_project_telemetry` + `aggregate_remote` only computed effectiveness for patterns in the sync-manifest adoption set, so a `hub_pattern_link` learning was silently dropped unless the pattern was also manifest-adopted (false in copy-all / synthesis adoptions). Now seeds the pattern set with the union of manifest-adopted names ∪ every `hub_pattern_link` across learnings (`_linked_pattern_names`); learnings-only patterns get `error_prevention_rate` with `adoption`/`retention` = None (omitted on write).
- **added** regression tests — `test_loop_engineering_emits_hub_linked_telemetry` + `test_loop_engineering_telemetry_link_matches_aggregator_key` (skill-level) and `test_learnings_only_pattern_is_aggregated` (aggregator end-to-end — the guard that would have caught B1).

### 2026-06-16 — loop-engineering: autonomous self-* meta-loop (skill + contract)

Promoted the *Loop Engineering* pattern (Addy Osmani; Anthropic agent-loop docs) into a distributable hub workflow. Owner directive 2026-06-16; goal-anchored to the hub's reusable-patterns mission. Composes existing self-* assets — no new engine — per `rule-curation.md` (reactive-not-speculative) + KISS/DRY. Net new pattern: **1**. `total_patterns` 263 → 264.

- **added** skill `loop-engineering` (v1.0.0, must-have) — skill-at-T0 orchestrator for the autonomous DISCOVER→PLAN→EXECUTE(maker)→VERIFY(checker)→SHIP|FEEDBACK loop. **Self-verifying** (maker `plan-executor-agent` ≠ checker `code-reviewer-agent`, per `independent-test-verification.md` + `supervisor-verification.md`), **self-healing** (`/fix-loop`, `/debugging-loop`), **self-learning** (`/learn-n-improve` each cycle), **self-feedback** (`/escalation-report` + triage inbox on budget exhaustion). Bounded by `global_retry_budget` + `--max-cycles`; STEP 1.5 PREFLIGHT BLOCKs downstream when the worker closure is missing or maker==checker. Spec: `docs/specs/loop-engineering-spec.md`.
- **added** workflow contract `loop-engineering` to `config/workflow-contracts.yaml` (+ identical distributable copy in `core/.claude/config/`) — 7-step DAG with distinct maker/checker dispatches.
- **added** tests — closure-coverage assertion + `test_loop_engineering_maker_differs_from_checker_in_contract` + `test_loop_engineering_skill_dispatches_two_distinct_agents` (regression guard so maker/checker can never silently collapse).
- **added** `loop-engineering` workflow group seed in `config/workflow-groups.yml`; docs regenerated.

### 2026-06-12 — notifier-hub-pattern learnings fold-back (pattern-portability + autonomous-contract)

Folding back the two LEARNINGS-TO-FOLD-BACK proposals from the notifier-hub-pattern goal run (user-approved).

- **updated** rule `pattern-portability` (v1.0.0 → v1.1.0) — new "Templates with Wire Contracts" section: distributed code templates that POST to a service MUST be checked against the receiver's validator semantics (null-vs-absent serialization — `JSON.stringify` drops `undefined`, Python serializes `None` as `null`; enum/optionality verification from the receiver's real types; cross-language payload equivalence; independent fresh-context review as the mandatory catching layer, since no hub validator type-checks template code). Source: Rule-29 HIGH finding on `owner_notify.py`.
- **updated** skill `autonomous-contract` (v1.0.0 → v1.1.0) — Self-contained principle now requires verifying every cited reference file exists at drafting time, or stating an explicit fallback. Source: the goal contract cited `structured-logging.md` as the house-style reference, which does not exist in the hub.

### 2026-06-12 — notifier-integration: owner-alert + heartbeat standard (rule + templates)

Promoted FireKaro's proven owner-alert integration (`server/src/lib/owner-notify.ts`) into a distributable hub pattern. Source: `project:firekaro-planner` via goal contract `docs/goals/2026-06-12-notifier-hub-pattern.md`.

- **added** rule `notifier-integration` (v1.0.0) — owner alerts AND uptime heartbeats via the Notifier gateway: `NOTIFIER_URL`/`NOTIFIER_KEY`, fail-open `notifyOwner()` contract (no-op unset env, 2s timeout, fire-and-forget, never throws), canonical detector set (signup / unhandled-5xx / DB-down / boot-env), heartbeat directive, explicit healthchecks.io/UptimeRobot/cron-ping.me retirement, no end-user PII. Ships with `templates/owner-notify.ts` + `templates/owner_notify.py` (notifyOwner + heartbeat companions) and `templates/claude-md-production-monitoring-block.md` (v1.0.0) — templates ride along via provisioning's full `core/.claude/` copy (not registry-tracked, per `templates/` precedent).

### 2026-06-12 — Tier 5c: prompt-auto-enhance v3.6.0 from firekaro-planner (skill + rule + reminder hook)

Final PR of the Tier-5 session-governance promotion. Source: `project:firekaro-planner`, where v3.3→v3.6 were hardened across four 5-prompt verification campaigns with documented defects and fixes. Hub-operational `.claude/` copies (skill, rule, hooks, settings wiring) updated in lockstep with `core/.claude/`.

- **updated** skill `prompt-auto-enhance` (v3.2.0 → v3.6.0) — STEP 0-pre transcription normalization (voice fillers/stutters stripped; phonetic mishears rendered as auditable `heard → read as` mappings; load-bearing mishears route to the Clarification Gate); evidence-override lane (a quoted concrete flaw in a ≥7 dimension may be fixed, cap-counted, labeled); cap-exempt grade-independent MISSING_ROLE fix (applies even at Grade A); half-open grade bands (no unmapped scores); role tie-break rule (primary deliverable wins; co-primary = OVER_SCOPED); STEP 3.6 post-rewrite re-grade with proof-of-lift gate (`Overall before → after`, no-lift → re-map, max 2 retries); blind re-grade audit (context-blind agent re-scores both prompts on deterministic triggers; divergence >1.5 logs `regrade-divergence` and the blind score wins); R1≠R2 clarification; STEP 4.7 role routing (`engineering-roles`), STEP 5 execute-under-`decision-authority`, STEP 6 conditional git via `git-manager-agent`.
- **updated** rule `prompt-auto-enhance-rule` — new **MANDATORY OUTPUT (format A)** section: every non-trivial turn renders the compact "What changed / Final prompt executed" block (one-liner on trivial turns); the unified 0→6 pipeline table (strengthen → role → plan → execute → verify → git) with pointer-pattern SSOT references; output-side unconditional-indicator clause (banner fires on output blast radius even when the prompt hook stayed silent); tiered Clarification & Confidence Gate (small gaps → one question; consequential fork <~95% → `/grill-me`/`/grill-with-docs`; pre-authorized → waived); format-A-default verbosity.
- **updated** hook `prompt-enhance-reminder` (v2.0.0 → v2.1.0) — reminder lines for the governance tail (role / gate / decision-authority / git), ALWAYS-SHOW-THE-ENHANCED-PROMPT (format A), PLAN BEFORE CODING, DECIDE-DON'T-ASK, GRILL-WHEN-UNSURE (with the `*Sync-check:*` marker contract), DON'T-NARRATE-AND-STOP; resets `.claude/.keepgoing-count` per user prompt (bounding the Tier 5b Stop-hook auto-continue cap per turn).
- **updated** `references/grading-rubric.md` — scoring anchors aligned to the half-open grade bands.
- **changed** hub-operational `.claude/` — mirrored the updated skill/rule/reminder hook; adopted `no-overask-guard.sh` (Stop) + `session-governance-status.sh` (SessionStart) from Tier 5b with `settings.json` wiring, so the hub itself runs the full governance loop.

### 2026-06-12 — Tier 5b: session-governance hooks from firekaro-planner

Second of three PRs promoting firekaro's session-governance layer. Source: `project:firekaro-planner`. Wires two new hook events into the distributable `core/.claude/settings.json` template (`Stop` + `SessionStart`).

- **added** hook `no-overask-guard` (Stop, tier: must-have) — deterministic stop-discipline guard: BLOCKS over-ask (trailing offer / multiple-choice / recommendation+question) and narrate-and-stop endings on reversible work, re-injecting the `decision-authority` rule to force continuation; exempts genuine blockers and `*Sync-check:*` intent grills; logs enhance-banner/block/role misses to `.claude/.enhance-misses.log` as non-blocking telemetry; caps auto-continues at 12 per user turn via `.claude/.keepgoing-count` (reset by `prompt-enhance-reminder`). Carries the per-turn text-aggregation fix (analyze ALL assistant text since the last real user prompt, not the last block) that eliminated 58/59 false-positive banner misses in firekaro's 7-day log.
- **added** hook `session-governance-status` (SessionStart, tier: must-have) — machine-readable governance status block at session boot: supervisor-duty pointer (`supervisor-verification`), git branch + uncommitted count, role-router pointer (`engineering-roles`), and a 7-day enhance-misses summary with an explicit-zero line (so "clean" is distinguishable from "summary not wired") plus a >5/week alert.
- **changed** `core/.claude/settings.json` — added `SessionStart` → `session-governance-status.sh` and `Stop` → `no-overask-guard.sh` hook wiring alongside the existing `UserPromptSubmit` → `prompt-enhance-reminder.sh`.

### 2026-06-12 — Tier 5a: supporting governance rules from firekaro-planner (user-approved override of the Tier-plan SKIP verdict)

First of three PRs promoting firekaro's session-governance layer (rules → hooks → prompt-auto-enhance v3.6.0). Source: `project:firekaro-planner`. These two were originally marked SKIP in `plans/hub-promotion-firekaro.md`; promoted on explicit user direction because the v3.6.0 prompt-auto-enhance governance tail (Tier 5c) cross-references them.

- **added** rule `plan-before-coding` (global, tier: must-have) — SSOT for the plan-first discipline: visible plan (plan mode / `/autonomous-contract` / inline plan block) BEFORE the first code edit on any non-trivial change, with approach+WHY, concrete file list, build sequence, verification, and risks. Folds in the root-cause + full consumer/surface map as part of the plan (never a one-symptom patch), and propagates both mandates to every dispatched code-changing worker (`supervisor-verification`). Generalized: domain-critical-logic trigger replaces firekaro's financial-math paths; goal-contract surface retargeted to `/autonomous-contract`.
- **added** rule `engineering-roles` (global, tier: nice-to-have) — autonomous role router: infer the role from the task signal, state `Role: <name> — <why>`, dispatch the role's named agents/skills (routing layer over existing tooling, `configuration-ssot`). Router table + condensed mandates for 15 generic roles, canonical multi-role sequences with a mandatory independent-reviewer edge (`independent-test-verification`), and a mis-route→`lessons.md` feedback loop. Generalized: project-stage block templated for downstream copies; domain-analyst roles documented as project-specific additions (hub ships none, YAGNI); all dispatch targets retargeted to existing hub patterns.

### 2026-06-10 — Tier 4: `autonomous-contract` skill from firekaro-planner goal-creator

Tier 4 (final) of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). Source: `project:firekaro-planner`. Brainstorm spec: `docs/specs/autonomous-contract-skill-spec.md`.

- **added** skill `autonomous-contract` (workflow, category: core, tier: nice-to-have) — authors a dense, zero-open-questions contract to hand to an autonomous executor (Claude Code's built-in `/goal`, or `/loop` / routines / headless) that runs unattended until a Definition of Done. Generalized + executor-anchored-on-`/goal` from firekaro's `goal-creator`. Full apparatus: interview-first Clarification Gate (scoped by `decision-authority`), idempotency preflight, worktree+lock+commit-gate isolation (points to `git-worktrees`), cross-session progress log, DONE/PENDING/BLOCKED/NEXT summary, DoD-verb precision (`dod-verbs`), and blast-radius verification gates that **point to** the Tier 1–3 hub rules (`supervisor-verification`, `independent-test-verification`, `output-plausibility-verification`, `e2e-persistence-verification`, `bug-triage-discipline`) rather than inlining them (`configuration-ssot`). References: `contract-template.md`, `baked-in-rules.md`, `example-contract.md`. Authors and stops — never runs the executor, never commits; Mode B folds run learnings back (PROPOSE-only, per `learnings-routing`).

### 2026-06-10 — Tier 3: new Hono + Prisma + Vuetify-E2E stack rules from firekaro-planner

Tier 3 of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). New dependency-gated stack rules + a `vue.md` enrichment. Source: `project:firekaro-planner`. Wiring: `recommend.py` `DEP_PATTERN_MAP` (hono→hono-conventions, prisma→prisma-conventions, vuetify→vue-e2e) + `RESOURCE_STACK_REQUIREMENTS` empty-set gates (mirroring `bun-elysia`). No `bootstrap.py` `STACK_PREFIXES` change needed — these detect via project dependencies, not stack prefixes.

- **added** rule `hono-conventions` (globs: server/api TS) — `new Hono()` + global auth + `export default`; inline Zod (`.partial()` updates); `findFirst` ownership; POST for state-changing actions; discriminated `{success,data}` response envelope; opt-in pagination on `?page=`; rate-limit middleware factory. Seeds a `hono-*` rule set (hub previously had none).
- **added** rule `prisma-conventions` (globs: schema.prisma + prisma TS) — cuid PKs + timestamps; `onDelete: Cascade` + `@@index`; `findFirst` (not `findUnique`) for ownership; `upsert` singletons; `Promise.all` parallel reads; dev-mode `globalThis` client singleton. Seeds a `prisma-*` rule set.
- **added** rule `vue-e2e` (globs: E2E) — Vuetify + Playwright: `networkidle` navigation, component animation timing, `workers:1` for data-dependent suites, and the vee-validate `fill()` gotcha (`pressSequentially` + `blur`).
- **updated** rule `vue` (v1.1.0) — + `ref()`-over-`reactive()` & Pinia-vs-Vue-Query lifetime split, URL↔query-param sync, two-tier form validation, API response unwrapping (pairs with `hono-conventions` envelope).
- **changed** `recommend.py` — `DEP_PATTERN_MAP`: `prisma`/`@prisma/client` → +`prisma-conventions`, `hono` → +`hono-conventions`, new `vuetify` → `{vue, vue-e2e}`; `RESOURCE_STACK_REQUIREMENTS`: added empty-set gates for the 3 new rules.

### 2026-06-10 — Tier 2: merge firekaro-planner quick-wins into existing patterns + 2 new meta-rules

Tier 2 of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). Generalized merges into existing hub patterns + 2 new global rules. Source: `project:firekaro-planner`.

- **updated** rule `error-handling` (v1.1.0) — added "Numeric & Derived-Value Safety" (NaN/Infinity/division-by-zero guards on derived values) and "Fire-and-Forget Side Effects" (logged `.catch()` mandate, no bare-`void` discard). Fixed the firekaro `console.error`-in-catch inconsistency: routes logging through the project logger per `security-baseline`.
- **updated** rule `security-baseline` (v1.1.0) — added "Structured Logging as a Redaction Choke Point" (single logger, field-level redaction, never interpolate secrets into the message string — redaction covers fields, not the formatted message).
- **updated** skill `writing-plans` (v1.3.0) — added a mechanical zero-open-questions grep gate (STEP 4.1) + a DoD-verbs checklist item. (Also corrected a pre-existing registry/frontmatter version drift.)
- **updated** skill `e2e-best-practices` (v1.1.0) — added "Production: What NEVER Runs There, and What MUST Run After Every Deploy" + "Calculation Verification — use the API as the oracle" (tolerance compare, validate empty states, never `test.skip()`).
- **updated** skill `git-worktrees` (v1.1.0) — added "Background Autonomous-Run Isolation" (dedicated worktree + lock file + pre-commit run-token gate + cross-session progress log).
- **added** rule `dod-verbs` (global) — definition-of-done verbs are load-bearing: every acceptance criterion states an ACTION + COMPLETENESS BAR; elastic verbs get satisfied at the weakest reading.
- **added** rule `learnings-routing` (global) — type each learning GENERIC vs PRODUCT-SPECIFIC, route to one canonical home, prefer a deterministic gate over prose, dedup, rule-changes are PROPOSE-only.

### 2026-06-10 — Promote 8 verification/governance rules from firekaro-planner (category: core, tier: must-have)

Generalized (de-project-specific) and promoted from the firekaro-planner downstream project. Source: `project:firekaro-planner`. Tier 1 of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`).

- **added** rule `output-plausibility-verification` (global) — verify user-facing computed values are domain-SANE, not just that they render/persist/pass; default-path verification, plausibility bounds, shape-locks-are-not-correctness-proofs.
- **added** rule `independent-test-verification` (global) — every non-trivial test verdict re-checked by a separate, context-blind agent given the same inputs + raw evidence (doer/checker separation, IEEE-1012); single-level two-wave dispatch.
- **added** rule `supervisor-verification` (global) — the T0 orchestrator must reproduce a worker's claimed gate and inspect output substance before accepting; includes a drive-the-UI loop for rendered changes. Extends `agent-orchestration.md` §2.
- **added** rule `decision-authority` (global) — decide-vs-escalate taxonomy (DECIDE / DECIDE+INFORM / ESCALATE) + confidence-gate-on-intent + anti-over-ask (no trailing offer, no narrate-and-stop). Complements `claude-behavior.md` rule 23; defers git authority to `git-collaboration.md`.
- **added** rule `bug-triage-discipline` (global) — every bug fix answers "why was this missed?" and runs a repo-wide sibling-class audit before closing; one canonical tracker is SSOT; shape-vs-substance is a named miss class.
- **added** rule `environment-validation` (global) — validate required env vars at boot in one validator before binding a listener; reject placeholder secrets in production; log only the variable name. Extends `error-handling.md` (fail-fast) + `security-baseline.md`.
- **added** rule `e2e-readiness-signal` (globs: E2E) — wait on an explicit app-emitted readiness signal after navigation, never a fixed delay; the positive pattern behind the no-sleep prohibition. Framework-agnostic.
- **added** rule `e2e-persistence-verification` (globs: E2E) — E2E creates must verify actual persistence (per iteration in loops) + final reloaded UI; never trust a closed dialog or end-of-loop count as success.

### 2026-05-30 — Add design/scope SSOT rule (category: core, tier: must-have)

- **added** rule `design-ssot` (`core/.claude/rules/design-ssot.md`, global scope) — every design decision, screen/feature pattern, and unit of agreed scope MUST have exactly one canonical doc, captured at decision time (including discussion-only sessions), propagated to all references on change, with a goal contract pinned before finalized scope is implemented. Distinct from `configuration-ssot` (Claude Code config layering) and `design-principles` DRY (code-level knowledge duplication).

### 2026-05-28 — Port 4 skills from mattpocock/skills (category: core, tier: must-have)

- **added** skill `improve-codebase-architecture` — Ousterhout deep-modules lens: surface architectural friction, propose deepening opportunities, produce an HTML report with before/after Mermaid diagrams, then drop into a grilling loop. References: `LANGUAGE.md`, `HTML-REPORT.md`, `DEEPENING.md`, `INTERFACE-DESIGN.md`. Adapted from upstream (no auto-open, Agent-tool dispatch at T0, references/ layout).
- **added** skill `grill-with-docs` — docs-aware grilling session: one question at a time, challenges plan against `CONTEXT.md` glossary + `docs/adr/`, updates docs inline. Required companion to `improve-codebase-architecture`. References: `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`.
- **added** skill `zoom-out` — 3-step "go up a layer, name the surrounding modules in domain vocabulary" map. Tiny, high-value habit nudge.
- **added** skill `to-prd` — synthesize a PRD from current conversation + codebase understanding (no interview). Inverse direction of existing `/prd-parser`. Looks for deep-module opportunities during module sketching.

Source: <https://github.com/mattpocock/skills/tree/main/skills/engineering>.
