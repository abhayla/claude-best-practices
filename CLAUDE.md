# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- Audit trail (full-audit dates; scoped addenda in git history): 2026-06-19 full audit; 2026-06-20 trust-score addendum (PR #163); 2026-06-22 G6 refresh (PR #195); 2026-06-29 branch-choice addendum (PRs #217/#218/#227); 2026-07-14 /init audit (CI gates, config list, rule list — PR #396); 2026-07-14 owner-approved compression of the G6 + hooks narratives (history detail → changelog/graduation docs); 2026-07-24 /init audit (added missing global rule verify-before-suggest-do-before-delegate.md to rule list; then added missing Key Script check_fleet_script_health.py; plugins/config/CI/workflow-map/skills/agents/sampled-paths all verified in sync); 2026-07-26 /init audit (added 3 wired-but-undocumented hooks — atlas-session-start/atlas-post-edit/session-concurrency-guard — plus the unwired session-git-landing helper; everything else verified in sync); 2026-08-13 /init audit (added missing Key Script check_prereq_contract.py; recommend.yml prose corrected weekly-cron→workflow_dispatch-only; plugins/rules/config/CI/hooks/workflow-map/paths all verified in sync); 2026-08-26 /init audit (CI prose corrected 6→7 checks / two→three blocking gates — root-marketplace mirror gate was undocumented in both places; added `config/dual-home-resources.yml` to Key Config Files; noted recommend.py's import-only library modules so audits stop re-flagging them; plugins/rules/hooks/agents/workflow-map/paths all verified in sync). How to audit this file: see "Maintaining This File" at the bottom. NOTE: live pattern count is whatever `registry/patterns.json` holds (one top-level key per pattern, minus `_meta`) — that file is the SSOT; do not pin a number here. -->

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template for downstream projects. NEVER put hub-only config here. NEVER use patterns from this directory (skills, agents, rules, hooks) when working on this hub repo — they are for downstream projects only.
- **`.claude/`** (repo root) — Hub-only operational config (scan skills, `synthesize-hub`, hub agents, hooks). This is what THIS repo uses. NEVER distribute this.
- **Exception — governance SSOT reads**: the auto-loaded `.claude/rules/prompt-auto-enhance.md` pipeline cites SSOT detail files (`engineering-roles.md`, `decision-authority.md`, `supervisor-verification.md`, `configuration-ssot.md`, `plan-before-coding.md`, `independent-test-verification.md`, `git-collaboration.md`) that live only in `core/.claude/rules/`. The same applies to the BA-gate SSOTs the PM mandate + the `ba-usecase-discovery-reminder.sh` hook point to (`ba-discovery-checklist.md`, `full-space-first.md`, `human-approval-gates.md`). READING those files when the pipeline or the BA-gate hook points to them is correct and expected — the prohibition above is about dispatching core skills/agents/hooks as if they were hub config, not about reading rule documentation.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`
- **Windows (PowerShell)**: prefix commands with `$env:PYTHONPATH = "."` and a semicolon (e.g., `$env:PYTHONPATH = "."; python -m pytest scripts/tests/ -v`). For cmd.exe use `set PYTHONPATH=. &&`. Git Bash works with the Unix syntax shown below. When writing **ad-hoc Python one-liners** to inspect `registry/patterns.json` or other config files, set `$env:PYTHONUTF8 = "1"` (or pass `encoding="utf-8"` to `open()`) — these files contain non-ASCII bytes and Python's default Windows codec (cp1252) raises `UnicodeDecodeError`. The repo's own scripts already pass `encoding="utf-8"`; this only bites improvised commands.
- **New here?** For downstream provisioning options (copy-all, smart, full synthesis), see `README.md`; for deeper setup walkthroughs, see `docs/GETTING-STARTED.md`.
- **`CLAUDE.local.md`** (repo root, gitignored) — per-developer overrides and local notes (e.g., local paths, secrets-free environment tweaks, in-progress scratch notes that shouldn't ship). Distinct from: auto-memory (cross-session user prefs) and `.claude/tasks/lessons.md` (correction patterns across sessions). Safe to read/update; never commit.

## Commands

```bash
# Run all tests (PYTHONPATH=. required for cross-module imports)
PYTHONPATH=. python -m pytest scripts/tests/ -v

# Run a single test
PYTHONPATH=. python -m pytest scripts/tests/test_bootstrap.py::TestCopyClaudeDir::test_copies_core_files -v

# Provision a project
PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

# Full local CI replication (run before opening a PR — mirrors validate-pr.yml's 7 checks)
PYTHONPATH=. python scripts/dedup_check.py --validate-all
PYTHONPATH=. python scripts/dedup_check.py --secret-scan
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
PYTHONPATH=. python -m pytest scripts/tests/ -v
PYTHONPATH=. python scripts/check_eval_coverage.py --enforce --base origin/main   # skip if no skills changed
PYTHONPATH=. python scripts/check_plugin_version_bump.py --base origin/main      # skip if plugins/ untouched
PYTHONPATH=. python scripts/generate_root_marketplace.py --check                  # skip if plugins/ untouched

# Regenerate docs after registry changes
python scripts/generate_docs.py

# Regenerate workflow docs after pattern cross-reference changes
PYTHONPATH=. python scripts/generate_workflow_docs.py
```

## Architecture

A curated hub of Claude Code patterns (agents, skills, rules, hooks) organized by stack — for the live count, see `registry/patterns.json` (one top-level key per pattern, excluding `_meta`); `registry/changelog.md` has human-readable history of pattern additions/removals. Three provisioning modes: (1) copy all from `core/.claude/` and prune, (2) smart provision via `recommend.py --provision` (auto-detects stacks), (3) full synthesis via `/synthesize-project`.

The hub has two delivery tiers: **atomic patterns** (above) and **reusable workflows** — the 9 orchestrated multi-step processes the hub creates, updates, and maintains for downstream projects to adopt for productivity (the original 8, plus `loop-engineering`; see "Workflow Orchestration (skill-at-T0)" below).

For sync direction semantics (hub↔projects, hub↔internet, aggregation flows), read `docs/SYNC-ARCHITECTURE.md` before modifying any sync script.

### Pattern Types

- **Agents** (`core/.claude/agents/*.md`) — sub-agents with isolated context, dispatched via `Agent()`. YAML frontmatter declares allowed tools.
- **Skills** (`core/.claude/skills/<name>/SKILL.md`) — slash-command workflows. Frontmatter: `name`, `description`, optional `triggers`. Body is the procedure.
- **Rules** (`core/.claude/rules/*.md`) — auto-loaded directives. `# Scope: global` loads always; `paths:` frontmatter scopes to matching paths.
- **Hooks** (`core/.claude/hooks/*.sh`) — shell scripts wired into `settings.json` events (pre/post-tool, prompt-submit, etc.).

### Synthesize Flywheel

Projects can opt in to share back synthesized patterns by setting `allow_hub_sharing: true` in their `.claude/synthesis-config.yml`. `/synthesize-hub` then collates `synthesized: true` patterns from enrolled repos in `config/repos.yml`, dedups via 3-level matching (hash/structural/semantic), and drafts generalized hub PRs. Default is local-only — sharing is bilateral and opt-in. See `docs/synthesize-flywheel.md`.

### Goal Vocabulary (`goals.yml`)

`goals.yml` (repo root) is the **host-owned goal SSOT** — the vocabulary the hub steers by. It defines G0–G6 (G0 infra; G1 distribute patterns; G2 maintain workflows; G3 idea→deployed; G4 thin-layer-on-platform; G5 north-star: an autonomous self-improving machine; G6 package capabilities as installable plugins). Each goal carries a `dod:` (definition-of-done) of machine-checkable proxies — mostly `file`-exists checks, except G5 which additionally gates on the REAL bar (trust-score graduated over 30 runs) so the % stays honest. The SessionStart "Atlas Goal Pulse" banner and the `core/.claude/rules/goal-anchored-decisions.md` rule both read this file; edit goal definitions/DoDs here, never hardcode them.

**G6 architecture** (live %: the Atlas Goal Pulse banner / `goals.yml` — never a number pinned here; PR/date trail: `registry/changelog.md`): plugins are built **one at a time, owner-approved** (strategic builds need explicit approval *before* building) under the in-tree monorepo marketplace (`plugins/.claude-plugin/marketplace.json`) — see the `plugins/` entry under Key Directories for what each is. TWO-TIER validation vocabulary (owner-delegated 2026-07-10): **G6-validated** = the formal second-project `/plugin install` + maker≠checker graduation bar; **serve-validated** = the automated clean-room pipeline `scripts/validate_plugin_cleanroom.py` (`docs/plugin-validation-pipeline.md`) — a cheaper PREREQUISITE gate proving install-serving, necessary but never sufficient alone. Status: ALL plugins are serve-validated AND G6-validated; the DoD's ≥9 count bar was MET 2026-07-12 (graduation evidence: `docs/g6-graduation-2026-07-10.md`, `docs/g6-graduation-2026-07-12.md`), so the % now gates on building more plugins, not re-proving these. `prompt-auto-enhance` is the first capability to graduate from a copied `core/` template to **plugin-as-SSOT** (its core skill is a thin `/plugin install` pointer; classified `divergent` in `config/dual-home-resources.yml`; retirement plan `plans/prompt-auto-enhance-core-retirement.md`). Deferred follow-up: the hub consuming its own plugin (full dogfood).

### Trust Score & Walk-Phase (autonomous-factory MVP)

The hub's trust-score subsystem is the gate that decides whether an autonomous-factory pipeline run is trustworthy enough to auto-land vs. must escalate to a human. **Motto: don't build for autonomy — prove the trust score first.** It runs in **shadow mode** (the engine only ever *recommends* — a human still acts — until calibration data proves the score), and is governed by **hard gates** (per-signal safety floors that a good weighted average can never out-vote) plus **per-stage graduation** (a reversible stage can earn autonomy before an irreversible one).

- **`config/trust-score.yml`** — the rulebook: 6 weighted verification signals (`tests_pass`, `independent_verification`, `coverage`, `regression_clean`, `secret_scan_clean`, `production_health`; weights sum to 1.0), the `threshold` to be RECOMMENDED, and `hard_gates` floors. Edit this, never hard-code thresholds. **Unmeasurable-signal rule (T-144):** a signal recorded as `null` is EXCLUDED from the weighted sum and the surviving weights renormalized — recording "no evidence" as `0.0` subtracts a fixed penalty from every run and flatlines the gauge (the live defect: all 133 ATLAS runs scored an identical 60 because `record_merged_prs.py` passed `coverage=0.0`). `hard_gates` are the deliberate exception and FAIL CLOSED on `null` — absence of evidence is not evidence of safety.
- **`scripts/trust_score.py`** — the engine: signals (0.0–1.0) → weighted 0–100 score → hard-gate veto → `graduation_status()` per stage. `config/trust-score.yml` is mirrored as the importable default.
- **`scripts/collect_signals.py`** — the *real-signal* adapter: assembles signals from actual evidence (test counts, coverage, a live secret-scan) and records a run to `trust-score/calibration-ledger.jsonl` so honesty data accrues automatically as real tasks finish. Supports `--secret-scan-clean` to override for accurate per-project scoring.
- **`scripts/simulate_walk_phase.py`** — a **sandbox** that fabricates realistic runs to stress-test the controller; writes ONLY to `trust-score/sim-ledger.jsonl` so fabricated data can never contaminate real calibration. Real graduation still requires real runs.
- **`scripts/generate_trust_dashboard.py`** → `trust-score/dashboard.html` (self-contained, auto-refreshing) from `trust-score/build-state.json` (build sections) + the live per-project calibration ledger `trust-score/ledgers/atlas.jsonl` (real runs accrued / 30 + false-confidence — sourced live, never hand-typed).
- **`trust-score/`** — runtime ledgers and state: `build-state.json`, `calibration-ledger.jsonl` (real), `sim-ledger.jsonl` (sandbox), `ledgers/` (per-project), `dashboard.html`. Tests: `test_trust_score.py`, `test_walk_phase.py`, `test_collect_signals.py`.

### Autonomous Branch Lifecycle

The hub manages its own git branches end-to-end so the user never touches git. The flow: edit → auto-commit → auto-push → auto-PR → merge-on-green → auto-prune, leaving only CI-red or genuinely-strategic PRs open for a human. The pieces (hooks + skills + GitHub config):

- **`.claude/hooks/auto-git.sh`** (SessionStart + Stop) — commits + pushes each turn's work to a task branch; keeps `main` clean (branches off it); guardrail 1b refuses to stack new work onto an already-merged branch. Secret-scan-gated, fail-open.
- **`.claude/hooks/auto-pr.sh`** (SessionEnd) — opens the PR, arms native CI-gated auto-merge (squash), prunes local branches `gh` confirms MERGED. Arms on session close (NOT per-turn) so work never merges mid-session. Off-switches `AUTO_PR_DISABLE=1` / `AUTO_MERGE=0`.
- **`.claude/hooks/auto-pr-reconcile.sh`** (SessionStart) — the **self-healing catch-up** that fixes "CLEAN PR left open with no action". `auto-pr.sh` only fires at the *unreliable* SessionEnd and only for the current branch; when SessionEnd is missed (killed/crashed/abruptly-closed session, sleep/shutdown), that PR is never armed or pruned. This hook runs at the reliably-firing SessionStart and sweeps **all** open PRs — prunes merged branches and arms auto-merge on every open, non-draft, not-already-armed PR **except the current HEAD branch** (active work is never merged out). Same `AUTO_PR_DISABLE`/`AUTO_MERGE` off-switches; fail-safe (exit 0); still 100% CI-gated. Hub-only for now (promote to `core/` once proven across a session boundary). Test: `scripts/tests/test_auto_pr_reconcile.py`.
- **`/git-branch-lifecycle`** skill (v1.1.0, model-driven layer) — `status`; `work <name>` (worktree for true parallel isolation); `finish` (agent code-review before merge); `cleanup` (reconcile EVERY branch — merged→prune, unmerged→auto-PR+merge-on-green, escalate only CI-red/strategic via open-PR veto, never a blocking land-or-delete question).
- **`/branch-choice` skill + `branch-choice-gate.sh` (PreToolUse) + `stale-branch-reaper.sh` (SessionStart)** — the **owner-driven front door** to the lifecycle (PRs #217/#218/#227). The gate presents a once-per-session branch menu (new-from-main / keep / switch / merge-then-new / stash) before the FIRST file edit — skipped when a session-scoped `.claude/.branch-choice-active.<session_id>` marker exists — replacing silent auto-rotation. The reaper flags branches older than 24h at SessionStart for owner-approved, CI-gated landing (merge one at a time). Both emit a SessionStart banner (`BRANCH-CHOICE:` / `stale-branch-reaper:`). Promoted to `core/` (#227), so downstream projects get the same gate.
- **Hold marker** (T-118, 2026-08-13) — every `gh pr merge` call site in `.claude/hooks/session-git-landing.sh` (the shared landing SSOT all the hooks above delegate to) skips a PR that carries the `hold` label or whose body matches "owner review required" (case-insensitive, fails closed on a `gh` query error) — the mechanism to hold a green PR for owner review across a session boundary.
- **GitHub config** — `main` protected on required check `validate` (the universal gate that runs the full suite on every PR; `enforce_admins=false` escape hatch); repo-level auto-merge + delete-branch-on-merge enabled. A PR squash-merges itself the moment CI is green, then its branch auto-deletes. NOTE: `.claude/` is gitignored, so new hooks/skills need `git add -f` to commit (auto-git's `git add -A` skips them).
- **Distributable** — the skills + hooks above also ship in `core/.claude/` (genericized: pluggable `SECRET_SCAN_CMD`→gitleaks secret-scan, `AUTO_MERGE=0` opt-out, branch-protection setup as a per-repo prerequisite). The hub keeps its own operational copy in `.claude/` (uses `dedup_check.py`); downstream projects opt in by provisioning. Registered as `auto-git`, `auto-pr`, `git-branch-lifecycle`, `branch-choice`, `branch-choice-gate`, `stale-branch-reaper` (nice-to-have). `auto-pr-reconcile.sh` stays **hub-only** until proven across a session boundary.

### Key Directories

- **`core/.claude/`** — All **distributable** patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, `config/`, templates. These ship to downstream projects — never run them against this hub repo (see "Two `.claude/` Directories" above). The full pattern list lives in the registry (not enumerated here, by budget design); one architectural call-out worth knowing: `karpathy-advisor` (+ `karpathy-advisor-agent`, dual-mode) is the hub's **expert-persona decision lens** — a "what would Karpathy do?" lens for AI/ML / agents / build-vs-buy / learning forks, grounded strictly in his documented heuristics (never fabricated). It is surfaced via the `engineering-roles` **Decision Advisor** router row alongside `/five-advisors` (on-demand, never auto-injected), and is the first instance of a generalizable expert-advisor pattern class (PRs #154/#157; future work #156). A second call-out: `web-deploy-readiness.md` (registered distributable rule, PRs #204/#205) is the **ship-readiness DoD for web apps** — four reactive gates (visual responsive verification at 390/768/1280 breakpoints, static-host cache headers, auth-provider authorized-domains, shared-host config-validity gate) that compose with (never duplicate) the `supervisor-verification`/`independent-test-verification`/`e2e-persistence-verification` rules and the `/vps-deploy` skill
- **`.claude/agents/`** — Hub-only **operational** agents (NOT distributed): `planner-researcher-agent`, `code-reviewer-agent`, `quality-gate-evaluator-agent`, `skill-author-agent`, `web-research-specialist-agent`, `anthropic-multi-agent-reviewer-agent`, `pre-git-merge-checker-agent` (runs the full local gate — dedup-validate + secret-scan + quality-gate + pytest — in isolation and returns a PASS/FAIL verdict, keeping the suite's output out of the main context; paired with the `/promote-to-core` skill). Distinct from `core/.claude/agents/` (the downstream template). Dispatch these when doing hub work
- **`.claude/skills/`** — Hub-only operational skills (NOT distributed), grouped by purpose: scan/discovery (`scan-repo`, `scan-url`, `scan-discovery-report`, `self-improve`), synthesis/provisioning (`synthesize-hub`, `synthesize-project`, `apply-selections`, `provision-report`), governance/authoring (`pattern-quality`, `claude-guardian`, `ssot-workflow-audit`, `writing-skills`, `skill-evaluator`, `skill-master`, `workflow-doc-reviewer`, `promote-to-core` — codifies the hub-only→distributable `core/` promotion recipe: frontmatter standard, registry entry+hash+tier, dual-home classification, docs regen, CI gate via `pre-git-merge-checker-agent`, land; `plugin-lifecycle` — create & maintain `plugins/` monorepo plugins, see the `plugins/` entry below), git lifecycle (`git-branch-lifecycle` — model-driven layer over the auto-git/auto-pr hooks; see "Autonomous Branch Lifecycle" above), prompt/decision support (`prompt-auto-enhance`, `brainstorm`, `grill-me`, `five-advisors`, `writing-plans`, `executing-plans`), session continuity (`continue`, `end-session`, `start-session`), fleet dispatch (`get-work-done` — the central work dispatcher; see its SKILL.md), and external research (`github`, `reddit`, `twitter-x`, `bootstrap-dogfood-project`, `anthropic-multi-agent-research-system-skill`). This grouping is representative, not exhaustive — `ls .claude/skills/` is the source of truth. New hub-only skills go HERE, never in `core/.claude/skills/`
- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`paths:` frontmatter) load only when working with matching files
- **`.claude/hooks/`** — Hub-only governance/telemetry hooks wired into `.claude/settings.json`. Git lifecycle: `auto-git.sh` (per-turn commit/push; force-added past the `.claude/` ignore), `auto-pr.sh` (SessionEnd), `auto-pr-reconcile.sh` (SessionStart) — see "Autonomous Branch Lifecycle" above. Governance gates: `session-governance-status.sh` (start banner), `prompt-enhance-reminder.sh` + `turn-origin.sh` (enhance triggering + turn-origin SSOT), `no-overask-guard.sh` (Stop; missed enhance banners), `ba-usecase-discovery-reminder.sh` (UserPromptSubmit BA offer), `verifier-edge-guard.sh` (Stop; done-claims without verifier evidence), `subagent-governance-inject.sh` (SubagentStart; injects plan-first + root-cause + structured-return mandates into every worker), `config-change-crud-guard.sh` (ConfigChange telemetry), `compaction-handoff.sh` (PreCompact breadcrumb), plus `prompt-logger.sh`, `auto-learn-trigger.sh`, `pattern-quality-gate.sh`, `post-failure-capture.sh`. Goal pulse + session safety: `atlas-session-start.sh` (SessionStart; the Atlas Goal Pulse banner off `goals.yml`), `atlas-post-edit.sh`, `session-concurrency-guard.sh`. Helper scripts on disk but not event-wired (invoked by the reaper/skills): `session-git-landing.sh`. Runtime state files (`.claude/.*-misses.log` etc.) are gitignored. Platform-event status (CC v2.1.183): `SubagentStart` + `ConfigChange` verified firing live; `PreCompact` wired but unverified; `subagent-verifier-edge.sh` (SubagentStop) stays on disk UNWIRED — its `additionalContext` never reaches the T0 parent (#144), re-wire when the platform surfaces it. No governance gap: the T0 `verifier-edge-guard.sh` covers the done-claim boundary
- **`config/`** — `settings.yml`, `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow docs), `pipeline-stages.yaml` (DAG config), `workflow-contracts.yaml` (step DAGs + artifact contracts)
- **`docs/specs/`** — Canonical workflow/feature specs (e.g., `test-pipeline-three-lane-spec-v2.md`). Reference these — do not duplicate spec content elsewhere
- **`docs/workflows/`** — Auto-generated workflow docs. Do not edit manually — regenerate after pattern changes
- **`docs/WORKFLOW-DIAGRAM.md`** — Visual reference for the skill-at-T0 workflow orchestration model. Read alongside the "Workflow Orchestration (skill-at-T0)" section below
- **`internet-sources/`** — Pending and archived sources for `scan_web.py` (`pending/`, `archived/`)
- **`docs/process-improvement/`** — Durable capture store for external content worth keeping (X/Twitter articles, web posts, research notes): full captures go in `sources/`, each registered in its `INBOX.md` for later processing. Capture with the `twitter-x` skill (ADHX → Jina Reader ladder) before improvising extraction; save here, not in ad-hoc locations
- **`plugins/`** — In-tree G6 plugin monorepo + marketplace (`plugins/.claude-plugin/marketplace.json`). Ten plugins to date: `prompt-auto-enhance/` (the first; the capability that graduated from a `core/` template to plugin-as-SSOT — see the G6 state under "Goal Vocabulary" above), `auto-google-analytics/` (autonomous GA4 setup for any project), `branch-lifecycle/` (self-contained git/session lifecycle), `loop-engineering/` (the hub's proven autonomous DISCOVER→PLAN→EXECUTE→VERIFY→SHIP meta-loop, packaged with its 13-skill/2-agent dependency closure so a downstream install gets a working loop with no missing-worker preflight blocks), and `fable-operating-manual/` (Fable 5's reasoning procedures as a portable Operating Manual, hook-injected into every session/sub-agent, with the `/model-parity-test` blind 3-arm trap-test exam that measures how much discipline transferred to a cheaper model; plan: `plans/fable-operating-manual-plugin.md`), and `cbp-workflows/` (the #187 install-not-copy distribution pilot: the quality-trio workflows — code-review, documentation, skill-authoring — plus their level-1 dispatch closure of 13 sub-skills + 4 worker agents), and `cbp-build-test-workflows/` (#187 cluster 2: development-loop + test-pipeline with their universal closure of 15 sub-skills + 7 agents + a bundled default pipeline config; stack helpers stay provisioned), and `cbp-learning-workflow/` (#187 cluster 3: the learning-self-improvement workflow + learn-n-improve/skill-factory/test-knowledge closure and 2 agents), and `cbp-react-stack/` (the first Tier-2 stack pack: vitest/jest runners + Next.js/React/RN patterns that the workflow plugins pick up automatically; rules stay provisioned — plugins can't ship them), and `cbp-python-stack/` (second stack pack: pytest-dev + FastAPI test/migrate/deploy helpers + 2 agents). New installable plugins are built here one-at-a-time, owner-approved. **All plugin create/fix/update work routes through the `/plugin-lifecycle` skill** (PR #247) — it owns the hub-specific lifecycle the generic authoring skills lack: marketplace.json registration on create, and on fix the test-local → **version-bump** → land → installed-test sequence (the bump is load-bearing: Claude Code serves installed plugins from a version-keyed cache at `~/.claude/plugins/cache/`, so an un-bumped source edit never reaches users; also never declare hooks in `plugin.json` — they auto-load and double-declaring errors). Downstream install guide: `docs/installing-plugins-in-downstream-projects.md`.
- **`plans/`** — Durable implementation plans for multi-session initiatives. Write a plan here when work spans sessions or needs cross-subagent handoff; use in-session plan mode for single-session tasks.
- **`goals/`** — The standing-goal invariant ledger: per-deliverable `goals/<slug>.md` files carrying cheap read-only predicates ("a goal verified once is an assumption with a timestamp"), re-verified daily by the `standing-goals.yml` sentinel (`scripts/check_standing_goals.py`). Enrollment happens at `/end-session` STEP 5b for each session-finished deliverable with a standing runtime/wiring surface. Format + enrollment rule: `goals/README.md`
- **`.claude/tasks/`** — `todo.md` (current task checklist per `claude-behavior.md` rule 14) and `lessons.md` (correction patterns accumulated across sessions). Read `lessons.md` at session start; append after corrections.
- **`.claude/sessions/`** — `/end-session` checkpoints; `/start-session` and `/continue` restore from here
- **`.claude/advisor-sessions/`** — `/five-advisors` transcripts
- **`.remember/`** (gitignored) — SessionStart-hook handoff log: `remember.md` (next-handoff buffer) + `now.md`/`recent.md`/`archive.md`/`today-*.md` history. Auto-surfaced at session start; write the next handoff to `remember.md`. Distinct from `.claude/tasks/` (todo + lessons) and auto-memory (cross-session user prefs)

### Stack Detection

Two mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*`. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`scripts/dependency_detection.py`) — matches `flutter-*`, `vue-*`, `bun-elysia-*`, etc. from project dependencies. Universal patterns have no prefix. Adding a new stack requires changes in `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS` (scripts/dependency_detection.py), and optionally `DEP_PATTERN_MAP` (scripts/dependency_detection.py).

Available stacks and their prefixes (full per-stack pattern listing: `docs/STACK-CATALOG.md`):

| Stack | Prefix | Detection |
|-------|--------|-----------|
| FastAPI/Python | `fastapi-*` | `STACK_PREFIXES` |
| Android/Compose | `android-*` | `STACK_PREFIXES` |
| AI/Gemini | `ai-gemini-*` | `STACK_PREFIXES` |
| Firebase | `firebase-*` | `STACK_PREFIXES` |
| React/Next.js | `react-*` | `STACK_PREFIXES` |
| Flutter | `flutter-*` | `DEP_PATTERN_MAP` |
| Vue/Nuxt | `vue-*` / `nuxt-*` | `DEP_PATTERN_MAP` |
| Bun/Elysia | `bun-elysia-*` | `DEP_PATTERN_MAP` |
| Expo | `expo-*` | `DEP_PATTERN_MAP` |
| Hono | `hono-*` | `DEP_PATTERN_MAP` |

### Sync Flows

Six sync directions — see `docs/SYNC-ARCHITECTURE.md`. Key entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory), `aggregate_telemetry.py` (enrolled projects→hub telemetry).

For the INTERNAL `.claude/` ↔ `core/.claude/` relationship — the hub-only/distributable/both scoping decision AND keeping the two copies of a dual-home resource honest — read `docs/HUB-CORE-SYNC.md`. A resource in both trees is classified in `config/dual-home-resources.yml` as `synced` (must match), `shared` (shared skeleton matches; hub/downstream-specific lines fenced `DUAL-SYNC:HUB-ONLY`/`DOWNSTREAM-ONLY` so they can't intermingle), or `divergent`; the gate `scripts/tests/test_dual_home_sync.py` (helper `scripts/sync_dual_home.py`) blocks drift + unclassified resources.

### Workflow Orchestration (skill-at-T0)

The 8 multi-step workflows (testing-pipeline, development-loop, debugging-loop, code-review, documentation, session-continuity, learning, skill-authoring) orchestrate from the user's T0 session via skills, NOT via subagents. This is a deliberate KISS/YAGNI **convention, not a platform constraint**: nested subagent dispatch is GA (Claude Code v2.1.172, ≤5 levels deep), but no hub workflow yet needs it — so workflow skills run in T0 and dispatch flat worker subagents in a single message, adopting nesting only where a concrete workflow clearly benefits (see `core/.claude/rules/agent-orchestration.md` §2 + guard rails in `plans/skill-at-t0-doctrine-relaxation.md`). For the **subagent vs. agent-team vs. worktree** choice, read `core/.claude/rules/agent-team-selection.md` (registered pattern `agent-team-selection` + 3 `team-*` governance hooks): default to a flat subagent; reach for an experimental agent TEAM (default-off, ~4–7× tokens) ONLY when workers must challenge each other mid-flight (peer code review, competing-hypothesis debugging, real multi-advisor debate); use a worktree for parallel file isolation.

The legacy `core/.claude/agents/<workflow>-master-agent.md` files (`deprecated: true`, Phase 3, 2026-04-25) were REMOVED (2026-07-03, #289) after `testing-pipeline-master-agent` was retired (2026-06-19) with the deprecated three-lane agents (→ `/test-pipeline`) — none remain. `workflow-master-template.md` is the LIVE canonical template and was never one of them. New workflow logic goes in the matching `core/.claude/skills/<workflow>/SKILL.md` — but the on-disk skill directory does NOT always equal the logical workflow name above. Resolve via this map before `ls`-ing or editing:

| Logical workflow | Skill directory |
|---|---|
| testing-pipeline | `test-pipeline` (the active skill; the deprecated `testing-pipeline-workflow` was retired 2026-06-19) |
| code-review | `code-review-workflow` |
| documentation | `documentation-workflow` |
| learning | `learning-self-improvement` |
| skill-authoring | `skill-authoring-workflow` |
| development-loop, debugging-loop, session-continuity, loop-engineering | (directory name == logical name) |

The `project-manager-agent` runs the full PRD-to-Production pipeline and MUST run at T0 — it invokes the 8 workflow skills via `Skill("/<workflow>")`. Keep it at T0 by the same single-level convention: PRD-to-Production orchestration stays flat and predictable rather than nesting from a dispatched worker.

`loop-engineering` (PRs #75–77) is a distributable skill-at-T0 autonomous self-* meta-loop (`core/.claude/skills/loop-engineering/SKILL.md`, spec at `docs/specs/loop-engineering-spec.md`), usable standalone (via `/loop`, a `/goal-creator` contract, cron, or a PR). As of 2026-07-14 (owner-approved, `plans/ba-architect-loop-integration.md`) it is ALSO the build engine for the PRD-to-Production pipeline's `stage_7_impl` — `stage_to_workflow.stage_7_impl: loop-engineering`, dispatched with the plan as its DoD/unit + `--no-ship` so the human accept/deploy gates (G2/G3) still own shipping. The other pipeline stages keep their prior workflow mapping (testing-pipeline for pre/post tests, code-review, documentation, development-loop for prd/plan/scaffold); the pipeline now also pauses at T0 (interactive BA grilling of the owner before the run) and A1 (owner design approval after plan+schema, before build).

Canonical references: `core/.claude/agents/workflow-master-template.md` v2.0.0, `docs/specs/test-pipeline-three-lane-spec-v2.md` v2.2.

### Agent Teams vs Subagents (orchestration primitives)

Beyond flat `Agent()` subagents, the hub distributes an **agent-team** primitive (PR #202) — peer Claude Code sessions that message each other and share a task list, gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (must-have-but-dormant: shipped, default-OFF). Pick the **cheapest sufficient** primitive (KISS/YAGNI): subagent (low cost, reports back only) → git worktree (isolated parallel edits, disk-only) → team (~4–7× tokens, a full instance per teammate). Selection rule: `core/.claude/rules/agent-team-selection.md` (companion to `agent-orchestration.md`); feature reference: `docs/claude-references/agent-teams.md`.

Distributable build workflows carry self-gated `--team` modes (`code-review-workflow`, `review-gate`, `auto-verify`, `development-loop`, `executing-plans`, `implement`, `brainstorm`, `research-mode`, `writing-plans`), enforced by three `team-*` hooks wired (pre-but-inert) in `core/.claude/settings.json` (`TaskCreated`/`TaskCompleted`/`TeammateIdle`). **Reliability finding (carried from the 2026-06-23 pipeline-upgrade run):** read-only review/research teams are safe unsupervised once ground-truth-verified, but parallel-edit (**Execute tier**) autonomous end-to-end completion measured **1/3 — below the ≥2/3 bar — so the Execute tier stays human-supervised** until the integration step is hardened. Plan + evidence: `plans/agent-teams-incorporation.md`, `docs/contracts/2026-06-23-agent-teams-pipeline-upgrade.md`.

### Key Scripts

- **`recommend.py`** — Main provisioning entry point. Modes: `--local`/`--repo`, `--provision`, `--diff`, `--apply`. Calls `third_party_skills.py` during provisioning for third-party agent skill detection. (`STACK_DETECTORS` and `DEP_PATTERN_MAP` defined in `scripts/dependency_detection.py`.) Its import-only library modules — `gap_analysis`, `hub_resources`, `overlap_analysis`, `plugin_recommendations`, `provision_local`, `provision_repo`, `provisioning_tiers`, `resource_copy`, `stack_detection`, `sync_manifest` — have no CLI and are intentionally not listed here
- **`bootstrap.py`** — Core copy logic. CLI: `python scripts/bootstrap.py --stacks <stack1,stack2> --target <dir>`. Defines `STACK_PREFIXES`
- **`workflow_quality_gate_validate_patterns.py`** — CI validator for frontmatter, cross-references, registry sync
- **`dedup_check.py`** — Dedup validator (`--validate-all`) and secret scanner (`--secret-scan`)
- **`generate_docs.py`** / **`generate_workflow_docs.py`** — Rebuild docs dashboard and workflow docs
- **`extract_references.py`** — Splits oversized SKILL.md files into `references/` subdirectories
- **`collate.py`** — Project→hub sync: collects patterns from downstream projects
- **`scan_web.py`** — Internet→hub sync: discovers patterns from curated URLs and topics
- **`sync_to_projects.py`** — Hub→projects sync: pushes updated patterns to repos in `config/repos.yml`
- **`check_freshness.py`** — Detects stale patterns based on age and activity
- **`assign_workflow_groups.py`** — Assigns patterns to workflow groups for doc generation
- **`discovery_adapter.py`** — Adapter for the pattern discovery pipeline
- **`discovery_to_issue.py`** — Closes the self-updating loop (Phase 5.1b): turns a migratable discovery from `config/discoveries.json` into a deduplicated GitHub issue. Dry-run by default; `--apply` files via `gh`. Wired into `scan-internet.yml`
- **`aggregate_telemetry.py`** — Collects adoption signals + learnings from enrolled repos, writes effectiveness metrics to `registry/patterns.json`. Remote mode (default) vs local (`--local`). Runs weekly via `aggregate-telemetry.yml`
- **`sync_to_local.py`** — Hub→local sync: pulls patterns into a local project directory
- **`third_party_skills.py`** — Detects and includes third-party agent skills during provisioning (called by `recommend.py`)
- **`pipeline_aggregator.py`** — Standalone aggregator for testing-pipeline results: reads `test-results/*.json` and applies the union-of-failures rule
- **`check_eval_coverage.py`** — Eval-coverage touch-trigger gate. CI (`validate-pr.yml`) runs it with `--enforce` (the RATCHET, owner-approved 2026-07-13): a changed `SKILL.md` lacking an `evals/*.md` report FAILS the PR unless the skill is grandfathered in `config/eval-coverage-grandfather.yml`; without `--enforce` it only warns via `::warning::` and exits 0
- **`check_plugin_version_bump.py`** — BLOCKING CI gate (`validate-pr.yml`): any `plugins/<name>/` source change must bump that plugin's `plugin.json` version, because Claude Code serves installed plugins from a version-pinned cache — an un-bumped edit merges green but never reaches installed copies. New plugins pass; README/evals-only changes are exempt
- **`generate_root_marketplace.py`** — Derives the root-level `.claude-plugin/marketplace.json` (T-145) from the canonical `plugins/.claude-plugin/marketplace.json`, rewriting each `source` to `./plugins/<name>` so a GitHub-URL/shorthand `claude plugin marketplace add abhayla/claude-best-practices` resolves plugin sources against the full clone. `--check` is a BLOCKING CI gate (`validate-pr.yml`) that fails the PR if the root mirror drifts from the canonical file. See `docs/installing-plugins-in-downstream-projects.md`
- **`bootstrap.sh`** (repo root, not in `scripts/`) — Curl-pipe-bash installer for downstream users: `curl -sL .../bootstrap.sh | bash -s -- --stacks <list> [--target <dir>]`. Calls `bootstrap.py` after fetching the repo
- **`trust_score.py`** / **`collect_signals.py`** / **`simulate_walk_phase.py`** / **`generate_trust_dashboard.py`** — the trust-score / walk-phase MVP toolchain (engine, real-signal adapter, sandbox simulator, dashboard generator). See "Trust Score & Walk-Phase (autonomous-factory MVP)" under Architecture before touching scoring, gates, or ledgers
- **`record_task_run.py`** (#196) — honest per-task trust-score accrual: auto-derives real signals + an honest git-history `human_had_to_fix` proxy (never silently `False`) and appends ONE shadow-mode run per branch to the ATLAS ledger; idempotent via `trust-score/.recorded-branches`. Wired into `/git-branch-lifecycle finish` STEP 3
- **`record_merged_prs.py`** — zero-manual counterpart of `record_task_run.py`: sweeps recently MERGED PRs via `gh` and trusts each PR's own CI rollup (the required `validate` check) as evidence instead of re-running tests locally, so the common auto-merge landing path (which never calls `finish`) still accrues trust-score runs; adds per-PR `pr`/`branch`/`skill` fields to the ledger entry for per-skill breakdown (`trust_score.stats_by()`). Idempotent via `trust-score/.recorded-prs`. Swept by `.claude/hooks/auto-pr-reconcile.sh` at SessionStart (fail-safe)
- **`measure_outcomes.py`** (T-144) — the honest outcome scorecard: six delivery metrics computed from data that ALREADY exists (git/`gh` history + `costs/ledger.jsonl`), with no new collection infra — 30-day change-failure rate, 30-day rework rate, checker/CI first-pass rate, guardrail catches (**confirmed true positives only**, so a gate that blocks everything can't inflate its score), invocation-based adoption (reports "no data" honestly when no log exists — never a fabricated rate), and cost per completed task. **Report-only by design**: it prints measurements, never pass/fail verdicts — baseline first, thresholds only once a baseline exists. `--explain` prints the per-PR classification behind every number so a checker can recompute a week by hand. Wired into `aggregate-telemetry.yml` as its metrics source; a failed `gh` read raises `FetchError` and exits non-zero rather than silently reporting zero. Tests: `test_measure_outcomes.py` (hand-computable fixtures)
- **`check_standing_goals.py`** — the standing-goal sentinel: re-verifies every enrolled `goals/*.md` invariant's predicates (`file`/`command`, same vocabulary as `goals.yml`'s `dod:`), reports pass/fail, flags malformed goal files as failures (never silently skipped). `--json` for machine-readable output, `--update-timestamps` to refresh `last_verified` on passing goals only. Run daily by `.github/workflows/standing-goals.yml` (cron-only — never wired into `validate-pr.yml`, so an anticipatory goal can't break PR CI)
- **`cost_ledger.py`** (fable-window item 6) — self-enforcing cost ledger: streams every Claude Code transcript JSONL under `~/.claude/projects/` (main sessions + subagent transcripts), aggregates per-day token/USD totals via `config/model-costs.yml`, and appends idempotent daily rollups to the gitignored `costs/ledger.jsonl`. `--daily` (appends + alerts, wired into `.claude/hooks/auto-pr-reconcile.sh` at SessionStart, 60s soft deadline), `--report [--days N]` (per-day USD/token breakdown + trend), `--cadence-report` (sessions/USD trend + the repo's GH-cron inventory + a cost-vs-merged-PR-growth flag), `--alert` (owner P2 alert via the Notifier gateway when yesterday's spend exceeds `daily_alert_usd`, fail-open)
- **`lint_rule_compliance.py`** (fable-window item 5, Part B) — report-only rule-compliance line-lint: extracts the imperative directive lines (MUST / MUST NOT / NEVER / ALWAYS) from every `# Scope: global` rule file, cross-references the gitignored runtime telemetry logs (`.claude/.*-misses.log`, `.overask-violations.log`), and classifies each directive KEEP / REWRITE / DEMOTE / DELETE as evidence for rule curation (the delete-the-harness audit). Changes nothing by itself; degrades gracefully to static heuristics when telemetry is absent (CI / fresh worktree). `--json` for machine-readable output
- **`check_fleet_script_health.py`** — read-only static gate for the GetWorkDone fleet's "detect-then-discard" defect class (a script correctly detects its failure condition then throws the signal away, so the unattended fleet reports healthy while doing nothing): flags stderr-suppressed interpreter probes, the `grep -c … || echo 0` two-line debounce inversion, dead enforcement gates (docstring claims blocking but no call site) and discarded-exit `.cmd` guards. Exit 0 = clean / 1 = findings; read-only. Referenced by the `get-work-done` fleet dispatcher; test: `test_fleet_script_health.py`
- **`check_prereq_contract.py`** — report-only prerequisites-contract inventory: scans every SKILL.md across the hub (`.claude/skills/`), the distributable template (`core/.claude/skills/`) and the plugin monorepo (`plugins/*/skills/`) for the prerequisites-preflight contract (a `## Prerequisites` section or explicit `Prerequisites: none`, plus a `## STEP 0: Preflight` gate when prerequisites exist); drives the wave-based sweep in `plans/prereq-contract-sweep.md`. Always exits 0 — a future owner-gated `--enforce` mode would turn it into a CI ratchet mirroring `check_eval_coverage.py`. `--json` for machine-readable output
- **`validate_plugin_cleanroom.py`** (+ `validate_plugin_cleanroom.sh` one-command wrapper) — the repeatable clean-room plugin-validation pipeline (fable-window item 10): structural manifest checks (hooks-double-declare, dangling skill/hook references, marketplace registration), `claude plugin validate`, and a headless `--plugin-dir` serve probe that proves a plugin's skills are visible from the plugin alone via Claude Code's own `system/init` session-state event (deterministic — not text-compliance-based). See `docs/plugin-validation-pipeline.md` for what PASS covers vs. the heavier second-project `/plugin install` G6 bar; structural-gate unit tests in `scripts/tests/test_validate_plugin_cleanroom.py` never invoke the `claude` CLI

> One-off migration scripts (e.g. `pr2_premerge_migration.py`, a single-use PR1→PR2 hash-format transition from PR #15) are intentionally omitted from this list — even though the file still sits in `scripts/`, it is a spent one-shot migration, not part of the standing toolchain. Don't "fix" its omission by documenting it.

### Key Config Files

- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit after adding/removing patterns
- **`config/workflow-groups.yml`** — Seed patterns for workflow doc generation. Stale seeds silently break docs
- **`config/workflow-contracts.yaml`** — Per-workflow step DAGs, artifact contracts, gate expressions
- **`config/third-party-skills.yml`** — Registry of third-party agent skills detected during provisioning
- **`config/topics.yml`** / **`config/urls.yml`** — Topic mappings and curated URLs for `scan_web.py`
- **`config/discoveries.json`** — Accumulated pattern discoveries from external sources, dedup'd across runs
- **`config/test-pipeline.yml`** — Test pipeline stage definitions (fix-loop, auto-verify, post-fix stages)
- **`config/repos.yml`** — Downstream project repos for `sync_to_projects.py` and `recommend.yml`
- **`config/settings.yml`** — Hub-level settings
- **`goals.yml`** (repo root) — Host-owned goal SSOT (G0–G6 + machine-checkable DoDs). Drives the SessionStart goal-pulse banner and `goal-anchored-decisions.md`. Edit goal definitions here, never hardcode them
- **`config/pipeline-stages.yaml`** — DAG config for pipeline orchestration
- **`config/trust-score.yml`** — Trust-score rulebook: signal weights (sum 1.0), RECOMMEND `threshold`, and `hard_gates` safety floors. Edit here — `scripts/trust_score.py` mirrors it as a default; never hard-code thresholds
- **`config/telemetry-aggregates.json`** — Historical effectiveness data from `aggregate_telemetry.py` runs. Generated output — may not exist until the first telemetry run; do not treat its absence as an error. Schema (T-144): `{"patterns": {...}, "_outcomes": {...}}` — `_outcomes` holds the `measure_outcomes.py` scorecard, and file-exists `adoption_rate`/`retention_days_p50` are RETIRED below `sample_size` 2 (a 1-of-1 adoption rate is a provisioning tautology, not a measurement). `load_telemetry_aggregates()` reads both this and the older flat schema
- **`config/model-costs.yml`** — Cost-ledger rulebook: USD-per-MTok rates by model family (opus/sonnet/haiku/fable/default), `daily_alert_usd` threshold, `ledger_retention_days`. Edit here — `scripts/cost_ledger.py` reads it at runtime; rates are estimates pending real billing (see `as_of`)
- **`config/dual-home-resources.yml`** — Classifies every resource living in BOTH `.claude/` and `core/.claude/` as `synced`/`shared`/`divergent`; the drift gate `scripts/tests/test_dual_home_sync.py` fails on an unclassified or drifted resource. See `docs/HUB-CORE-SYNC.md`
- **`config/eval-coverage-grandfather.yml`** — Shrink-only allowlist for the eval-coverage ratchet (`check_eval_coverage.py --enforce`): skills predating the blocking gate only WARN when changed without evals. RATCHET RULE: entries may only be REMOVED (as evals are added), never added — new skills ship with evals from day one
- **`config/plugin-recommendations.yml`** — The install-not-copy layer of the #187 distribution model: `recommend.py` reads it to tell a project WHICH marketplace plugins to install (universal workflows + its stack's toolbox) alongside copy-provision. Edit recommendations here, never hardcode plugin sets in scripts

### CI Workflows

- **`validate-pr.yml`** — Runs all 4 validation commands on PRs, plus three blocking gates: eval-coverage ratchet (`check_eval_coverage.py --enforce`), plugin version-bump (`check_plugin_version_bump.py`), and root-marketplace mirror sync (`generate_root_marketplace.py --check`)
- **`update-docs.yml`** — Auto-regenerates docs on main push. Avoid running `generate_docs.py` manually on main
- **`test.yml`** — Runs pytest on `scripts/**` changes
- **`recommend.yml`** — `workflow_dispatch`-only (weekly cron RETIRED, owner-approved 2026-07-14 — all enrolled repos are plugins-first): provisions patterns for repos in `config/repos.yml` on manual trigger; re-enable by restoring the schedule block in the workflow file
- **`apply-selections.yml`** — Triggered by `/apply` comment on PRs to process pattern selections
- **`aggregate-telemetry.yml`** — Weekly cron (Friday): runs `aggregate_telemetry.py` against enrolled repos
- Scheduled: `scan-internet.yml`, `scan-projects.yml`, `sync-to-projects.yml`, `expire-sources.yml`, `standing-goals.yml`

## Testing

- Fixtures: `scripts/tests/fixtures/` + shared in `scripts/tests/conftest.py`
- Uses `tmp_path` for temp files and `sample_registry` fixture for registry tests
- `scripts/tests/smoke-test/` — end-to-end provisioning smoke test (`bootstrap.py` + `recommend.py` against a fixture project)
- Bug fixing: write a failing test first, then fix

## Key Conventions

- **Registry maintenance**: (1) add/remove files in `core/.claude/`, (2) update `registry/patterns.json`, (3) run `generate_docs.py`, (4) run `workflow_quality_gate_validate_patterns.py` to verify sync
- Pattern curation is reactive, not speculative — see `core/.claude/rules/rule-curation.md`
- Pattern quality checks (structure, portability, self-containment) via `/pattern-quality` skill
- `/synthesize-project` provisions projects; `/synthesize-hub` generalizes patterns back into the hub
- `update-docs.yml` auto-regenerates docs on main — do not duplicate this by running `generate_docs.py` manually on main

## Eval Workflow

Skills are validated through an eval workflow before merge. Recent evals live in `evals/` directories within skill folders. Each eval tests the skill against a real or simulated project scenario. When adding or modifying a skill, run its eval to verify correctness.

Invoke via the `/skill-evaluator` skill: `/skill-evaluator full <skill-path>` (modes: `trigger`, `output`, `full`, `conflicts`; add `--baseline` to compare against agent baseline). See `.claude/skills/skill-evaluator/EVAL-WORKFLOW.md` for the mandatory step sequence — do not batch multiple skills into one eval run.

## Third-Party Skills

`config/third-party-skills.yml` registers external agent skills (e.g., from MCP servers). During provisioning, `third_party_skills.py` detects matching third-party skills and includes them. To add a new third-party skill: add an entry to `config/third-party-skills.yml` with detection criteria and the skill definition.

## Rules for Claude

> Demoted to on-demand docs (owner-approved 2026-07-12, rule-compliance lint): the docs-cache procedure → `docs/claude-references/README.md` (check the cache before fetching Anthropic docs; save every fetch); product incubation → `docs/governance/product-incubation.md` (read BEFORE placing product code in/near the hub — product code lives in sibling repos); learning-to-gate doctrine → `docs/governance/learning-to-gate-doctrine.md` (read when converting a failure-learning into a fix: gate-with-self-test where deterministic, recurrence ratchet otherwise; salvaged via PR #501, kept doc-not-rule by the lean-rules gate).

Auto-loaded from `.claude/rules/` — global rules (`# Scope: global`) load always; path-scoped rules (`paths:` frontmatter) load only when editing matching files. Rule files:

- `.claude/rules/claude-behavior.md` — task approach, self-improvement, git hygiene, code quality, scope discipline
- `.claude/rules/context-management.md` — progressive disclosure, scratchpad usage, subagent delegation, compaction survival
- `.claude/rules/model-routing.md` — cheapest sufficient model per dispatch (haiku/sonnet/opus tiers, inherit Fable only for frontier judgment), preemptive security-category routing to opus, refusal→fallback playbook, per-pass effort dial, session-level routing
- `.claude/rules/prompt-auto-enhance.md` — Tier 1/2 context gathering, grade pipeline, clarification gate, resource CRUD detection
- `.claude/rules/verify-before-suggest-do-before-delegate.md` — live-verify actionable recommendations before presenting (evidence: source+date+version); agent is default executor, human steps carry a named blocker

(`notifier-integration.md` is a distributable rule living only in `core/.claude/rules/` — it is not hub-auto-loaded; the Notifier gateway itself is documented in the user-global CLAUDE.md / `GLOBAL.md` §2.)
- `.claude/rules/workflow.md` — 7-step development workflow (understand → test → implement → fix-loop → verify → commit)

## Maintaining This File (/init audits)

This file is auto-loaded every session — keep it accurate and token-flat (compress when adding). An audit is a diff against the live repo, not a rewrite; never touch owner-approved narrative (G6 architecture, governance sections) without approval. Checklist:

1. **Enumerable lists vs disk** — `ls plugins/` vs the `plugins/` entry; `ls .claude/rules/` vs "Rules for Claude"; `ls scripts/*.py` vs Key Scripts (spent one-shots intentionally omitted); `ls config/` vs Key Config Files; workflow map vs `ls core/.claude/skills/`.
2. **CI vs prose** — `.github/workflows/validate-pr.yml` steps vs the "Full local CI replication" block AND the CI Workflows section; gate descriptions (blocking vs advisory, flags like `--enforce`) vs the scripts' actual behavior — read the script docstring, don't trust the old prose.
3. **No pinned counts** — pattern totals, plugin counts, percentages: point at the SSOT (`registry/patterns.json`, `goals.yml`, changelog) instead of pinning numbers that rot. Prefer count-free phrasing ("The pieces:") over "Two hooks + one skill".
4. **Paths exist** — every referenced file/dir must exist at the stated path (a rule listed under `.claude/rules/` that actually lives in `core/.claude/rules/` is a defect).
5. **Close out** — update the header audit-trail comment (one terse line), run the quality gate + secret scan locally, land CI-gated on the autonomous branch lifecycle.
