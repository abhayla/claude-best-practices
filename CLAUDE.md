# CLAUDE.md

Guidance for Claude Code (claude.ai/code) in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template for downstream projects. NEVER put hub-only config here; NEVER dispatch skills/agents/rules/hooks from here for hub work — downstream only.
- **`.claude/`** (repo root) — Hub-only operational config (scan skills, `synthesize-hub`, hub agents, hooks). This is what THIS repo uses. NEVER distribute this.
- **Exception — governance SSOT reads**: the auto-loaded `.claude/rules/prompt-auto-enhance.md` pipeline cites SSOT detail files (`engineering-roles.md`, `decision-authority.md`, `supervisor-verification.md`, `configuration-ssot.md`, `plan-before-coding.md`, `independent-test-verification.md`, `git-collaboration.md`) living only in `core/.claude/rules/`; same for the BA-gate SSOTs (`ba-discovery-checklist.md`, `full-space-first.md`, `human-approval-gates.md`). READING those when pointed to is correct; the prohibition above is about dispatching core skills/agents/hooks, not reading rule docs.

## Environment

- **Python 3.12** (all CI workflows). Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`
- **Windows (PowerShell)**: prefix with `$env:PYTHONPATH = "."` + `;` (e.g. `$env:PYTHONPATH = "."; python -m pytest scripts/tests/ -v`). cmd.exe: `set PYTHONPATH=. &&`. Git Bash: Unix syntax below. Ad-hoc one-liners on `registry/patterns.json` etc.: set `$env:PYTHONUTF8 = "1"` (or `encoding="utf-8"` in `open()`) — non-ASCII bytes trip cp1252.
- Downstream provisioning options: `README.md`; deeper setup: `docs/GETTING-STARTED.md`.
- **`CLAUDE.local.md`** (repo root, gitignored) — per-developer overrides/local notes. Distinct from auto-memory and `.claude/tasks/lessons.md`. Safe to read/update; never commit.

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

A curated hub of Claude Code patterns (agents, skills, rules, hooks) by stack — live count: `registry/patterns.json` (one key/pattern, excl. `_meta`); human history: `registry/changelog.md`. Three provisioning modes: (1) copy all from `core/.claude/` and prune, (2) smart via `recommend.py --provision` (auto-detects stacks), (3) full synthesis via `/synthesize-project`.

Two delivery tiers: atomic patterns (above) and reusable workflows — the 9 orchestrated multi-step processes the hub maintains for downstream adoption (original 8 + `loop-engineering`; see "Workflow Orchestration" below).

Sync direction semantics (hub↔projects, hub↔internet, aggregation): `docs/SYNC-ARCHITECTURE.md` — read before touching any sync script.

### Pattern Types

- **Agents** (`core/.claude/agents/*.md`) — sub-agents, isolated context, dispatched via `Agent()`; YAML frontmatter declares allowed tools.
- **Skills** (`core/.claude/skills/<name>/SKILL.md`) — slash-command workflows; frontmatter `name`, `description`, optional `triggers`; body is the procedure.
- **Rules** (`core/.claude/rules/*.md`) — auto-loaded directives; `# Scope: global` loads always, `paths:` scopes to matching paths.
- **Hooks** (`core/.claude/hooks/*.sh`) — shell scripts wired into `settings.json` events (pre/post-tool, prompt-submit, etc).

### Synthesize Flywheel

Projects opt in via `allow_hub_sharing: true` in their `.claude/synthesis-config.yml`. `/synthesize-hub` collates `synthesized: true` patterns from enrolled repos in `config/repos.yml`, dedups via 3-level matching (hash/structural/semantic), drafts generalized hub PRs. Default local-only, sharing bilateral+opt-in. See `docs/synthesize-flywheel.md`.

### Goal Vocabulary (`goals.yml`)

`goals.yml` (repo root) is the host-owned goal SSOT — G0–G6 (G0 infra; G1 distribute patterns; G2 maintain workflows; G3 idea→deployed; G4 thin-layer-on-platform; G5 north-star: autonomous self-improving machine; G6 package capabilities as installable plugins). Each goal has a `dod:` (machine-checkable proxies, mostly `file`-exists checks, except G5 which also gates on the REAL bar (trust-score graduated over 30 runs)). SessionStart "Atlas Goal Pulse" banner + `core/.claude/rules/goal-anchored-decisions.md` both read this file — edit definitions/DoDs here, never hardcode.

**G6 architecture** (live %: Atlas Goal Pulse banner / `goals.yml`, never pinned here; PR/date trail: `registry/changelog.md`): plugins built one at a time, owner-approved (strategic builds need approval BEFORE building), under the in-tree monorepo marketplace (`plugins/.claude-plugin/marketplace.json`) — see `plugins/` under Key Directories for each. Two-tier validation vocabulary (owner-delegated 2026-07-10): **G6-validated** = formal second-project `/plugin install` + maker≠checker graduation bar; **serve-validated** = automated clean-room pipeline `scripts/validate_plugin_cleanroom.py` (`docs/plugin-validation-pipeline.md`), a cheaper prerequisite gate, necessary but not sufficient alone. Status: ALL plugins are serve-validated AND G6-validated; DoD's ≥9 count MET 2026-07-12 (evidence: `docs/g6-graduation-2026-07-10.md`, `docs/g6-graduation-2026-07-12.md`); % now gates on building more plugins. `prompt-auto-enhance` is the first capability graduated from a copied `core/` template to plugin-as-SSOT (thin `/plugin install` pointer; classified `divergent` in `config/dual-home-resources.yml`; retirement plan `plans/prompt-auto-enhance-core-retirement.md`). Deferred: the hub consuming its own plugin (full dogfood).

### Trust Score & Walk-Phase (autonomous-factory MVP)

The trust-score subsystem gates whether an autonomous-factory pipeline run is trustworthy enough to auto-land vs. escalate to a human. Motto: prove the trust score before building for autonomy. Shadow mode (only recommends, human still acts, until calibration proves the score) + hard gates (per-signal safety floors) + per-stage graduation (reversible stage earns autonomy before irreversible).

- **`config/trust-score.yml`** — rulebook: 6 weighted verification signals (`tests_pass`, `independent_verification`, `coverage`, `regression_clean`, `secret_scan_clean`, `production_health`; weights sum 1.0), `threshold` to be RECOMMENDED, `hard_gates` floors. Edit here, never hardcode. Unmeasurable-signal rule (T-144): a `null` signal is EXCLUDED and weights renormalized — recording "no evidence" as `0.0` flatlined all 133 ATLAS runs at 60 (fixed defect: `record_merged_prs.py` passed `coverage=0.0`). `hard_gates` deliberately FAIL CLOSED on `null`.
- **`scripts/trust_score.py`** — engine: signals (0.0–1.0) → weighted 0–100 score → hard-gate veto → `graduation_status()` per stage; `config/trust-score.yml` mirrored as importable default.
- **`scripts/collect_signals.py`** — real-signal adapter: assembles signals from actual evidence, records a run to `trust-score/calibration-ledger.jsonl`. `--secret-scan-clean` overrides for accurate per-project scoring.
- **`scripts/simulate_walk_phase.py`** — sandbox: fabricates realistic runs to stress-test the controller; writes ONLY to `trust-score/sim-ledger.jsonl` (never contaminates real calibration).
- **`scripts/generate_trust_dashboard.py`** → `trust-score/dashboard.html` (self-contained, auto-refreshing) from `trust-score/build-state.json` + `trust-score/ledgers/atlas.jsonl`.
- **`trust-score/`** — `build-state.json`, `calibration-ledger.jsonl` (real), `sim-ledger.jsonl` (sandbox), `ledgers/`, `dashboard.html`. Tests: `test_trust_score.py`, `test_walk_phase.py`, `test_collect_signals.py`.

### Autonomous Branch Lifecycle

Hub manages its own branches end-to-end: edit → auto-commit → auto-push → auto-PR → merge-on-green → auto-prune, leaving only CI-red or strategic PRs for a human.

- **`.claude/hooks/auto-git.sh`** (SessionStart+Stop) — commits+pushes each turn's work to a task branch; keeps `main` clean; guardrail 1b refuses to stack onto an already-merged branch. Secret-scan-gated, fail-open.
- **`.claude/hooks/auto-pr.sh`** (SessionEnd) — opens the PR, arms native CI-gated auto-merge (squash), prunes local branches `gh` confirms MERGED. Off-switches `AUTO_PR_DISABLE=1` / `AUTO_MERGE=0`.
- **`.claude/hooks/auto-pr-reconcile.sh`** (SessionStart) — self-healing catch-up: `auto-pr.sh` only fires at unreliable SessionEnd for the current branch, so a missed SessionEnd leaves a PR unarmed/unpruned; this hook (reliable SessionStart) sweeps all open PRs — prunes merged, arms auto-merge on every open non-draft not-already-armed PR except current HEAD branch. Same off-switches; fail-safe; hub-only for now. Test: `scripts/tests/test_auto_pr_reconcile.py`.
- **`/git-branch-lifecycle`** skill (v1.1.0) — `status`; `work <name>` (worktree, true parallel isolation); `finish` (agent code-review before merge); `cleanup` (reconcile every branch — merged→prune, unmerged→auto-PR+merge-on-green, escalate only CI-red/strategic via open-PR veto).
- **`/branch-choice` skill + `branch-choice-gate.sh` (PreToolUse) + `stale-branch-reaper.sh` (SessionStart)** — owner-driven front door (PRs #217/#218/#227): once-per-session branch menu (new-from-main/keep/switch/merge-then-new/stash) before the first file edit, skipped when `.claude/.branch-choice-active.<session_id>` exists; reaper flags branches >24h for owner-approved CI-gated landing. Both emit SessionStart banners (`BRANCH-CHOICE:` / `stale-branch-reaper:`). Promoted to `core/` (#227).
- **Hold marker** (T-118, 2026-08-13) — every `gh pr merge` call site in `.claude/hooks/session-git-landing.sh` (shared landing SSOT) skips a PR carrying the `hold` label or body matching "owner review required" (case-insensitive, fails closed on `gh` query error).
- **GitHub config** — `main` protected on required check `validate` (full suite every PR; `enforce_admins=false` escape hatch); repo-level auto-merge + delete-branch-on-merge enabled. Note: `.claude/` is gitignored — new hooks/skills need `git add -f` to commit (auto-git's `git add -A` skips them).
- **Distributable** — also ship in `core/.claude/` (genericized: pluggable `SECRET_SCAN_CMD`→gitleaks, `AUTO_MERGE=0` opt-out, branch-protection as prerequisite). Registered as `auto-git`, `auto-pr`, `git-branch-lifecycle`, `branch-choice`, `branch-choice-gate`, `stale-branch-reaper`. `auto-pr-reconcile.sh` stays hub-only until proven cross-session.

### Key Directories

- **`core/.claude/`** — distributable `agents/`, `skills/` (each `SKILL.md`), `rules/`, `hooks/`, `config/`, templates. Never run against this hub repo. Notable: `karpathy-advisor` (+ `karpathy-advisor-agent`) is the expert-persona decision lens ("what would Karpathy do?") for AI/ML/agents/build-vs-buy, surfaced via `engineering-roles` Decision Advisor router alongside `/five-advisors` (PRs #154/#157; future #156). `web-deploy-readiness.md` (PRs #204/#205) is the ship-readiness DoD for web apps (4 reactive gates: visual responsive verification at 390/768/1280, static-host cache headers, auth-provider authorized-domains, shared-host config-validity), composing with `supervisor-verification`/`independent-test-verification`/`e2e-persistence-verification` and `/vps-deploy`.
- **`.claude/agents/`** — hub-only operational agents: `planner-researcher-agent`, `code-reviewer-agent`, `quality-gate-evaluator-agent`, `skill-author-agent`, `web-research-specialist-agent`, `anthropic-multi-agent-reviewer-agent`, `pre-git-merge-checker-agent` (full local gate in isolation → PASS/FAIL; pairs with `/promote-to-core`). Distinct from `core/.claude/agents/`. Dispatch these for hub work.
- **`.claude/skills/`** — hub-only, grouped: scan/discovery (`scan-repo`, `scan-url`, `scan-discovery-report`, `self-improve`), synthesis/provisioning (`synthesize-hub`, `synthesize-project`, `apply-selections`, `provision-report`), governance/authoring (`pattern-quality`, `claude-guardian`, `ssot-workflow-audit`, `writing-skills`, `skill-evaluator`, `skill-master`, `workflow-doc-reviewer`, `promote-to-core`, `plugin-lifecycle`), git lifecycle (`git-branch-lifecycle`), prompt/decision support (`prompt-auto-enhance`, `brainstorm`, `grill-me`, `five-advisors`, `writing-plans`, `executing-plans`), session continuity (`continue`, `end-session`, `start-session`), fleet dispatch (`get-work-done`), external research (`github`, `reddit`, `twitter-x`, `bootstrap-dogfood-project`, `anthropic-multi-agent-research-system-skill`). Representative, not exhaustive — `ls .claude/skills/` is SSOT. New hub-only skills go HERE, never `core/.claude/skills/`.
- **`.claude/rules/`** — auto-loaded; global rules load always, path-scoped rules load only when matching files touched.
- **`.claude/hooks/`** — hub-only governance/telemetry, wired in `.claude/settings.json`. Git lifecycle: `auto-git.sh`, `auto-pr.sh`, `auto-pr-reconcile.sh` (see above). Governance gates: `session-governance-status.sh`, `prompt-enhance-reminder.sh` + `turn-origin.sh`, `no-overask-guard.sh`, `ba-usecase-discovery-reminder.sh`, `verifier-edge-guard.sh`, `subagent-governance-inject.sh`, `config-change-crud-guard.sh`, `compaction-handoff.sh`, plus `prompt-logger.sh`, `auto-learn-trigger.sh`, `pattern-quality-gate.sh`, `post-failure-capture.sh`. Goal pulse/safety: `atlas-session-start.sh`, `atlas-post-edit.sh`, `session-concurrency-guard.sh`. On-disk not event-wired: `session-git-landing.sh`. Runtime state files (`.claude/.*-misses.log` etc.) gitignored. Platform-event status (CC v2.1.183): `SubagentStart`+`ConfigChange` verified live; `PreCompact` wired unverified; `subagent-verifier-edge.sh` (SubagentStop) UNWIRED on disk (`additionalContext` never reaches T0 parent, #144) — re-wire when the platform surfaces it; T0 `verifier-edge-guard.sh` already covers the done-claim boundary.
- **`config/`** — `settings.yml`, `repos.yml`, `workflow-groups.yml`, `pipeline-stages.yaml`, `workflow-contracts.yaml`.
- **`docs/specs/`** — canonical workflow/feature specs (e.g. `test-pipeline-three-lane-spec-v2.md`); reference, don't duplicate.
- **`docs/workflows/`** — auto-generated; do not edit manually, regenerate after pattern changes.
- **`docs/WORKFLOW-DIAGRAM.md`** — visual reference for skill-at-T0 orchestration; read alongside "Workflow Orchestration" below.
- **`internet-sources/`** — pending/archived sources for `scan_web.py` (`pending/`, `archived/`).
- **`docs/process-improvement/`** — capture store for external content (X/Twitter articles, web posts, research notes): full captures in `sources/`, registered in `INBOX.md`. Capture with `twitter-x` skill (ADHX → Jina Reader) before improvising extraction.
- **`plugins/`** — in-tree G6 plugin monorepo + marketplace (`plugins/.claude-plugin/marketplace.json`). To date: `prompt-auto-enhance/` (first, plugin-as-SSOT — see G6 above), `auto-google-analytics/` (autonomous GA4 setup), `branch-lifecycle/` (self-contained git/session lifecycle), `loop-engineering/` (autonomous DISCOVER→PLAN→EXECUTE→VERIFY→SHIP meta-loop, 13-skill/2-agent closure), `fable-operating-manual/` (Fable 5's reasoning procedures, hook-injected, `/model-parity-test`; plan `plans/fable-operating-manual-plugin.md`), `cbp-workflows/` (#187 pilot: code-review, documentation, skill-authoring quality-trio + 13 sub-skills/4 worker agents), `cbp-build-test-workflows/` (#187 cluster 2: development-loop+test-pipeline, 15 sub-skills/7 agents+default pipeline config; stack helpers stay provisioned), `cbp-learning-workflow/` (#187 cluster 3: learning-self-improvement + learn-n-improve/skill-factory/test-knowledge closure + 2 agents), `cbp-react-stack/` (first Tier-2 stack pack: vitest/jest + Next.js/React/RN; rules stay provisioned), `cbp-python-stack/` (second stack pack: pytest-dev + FastAPI test/migrate/deploy helpers + 2 agents). New plugins built one-at-a-time, owner-approved. **All plugin create/fix/update work routes through `/plugin-lifecycle`** (PR #247) — marketplace.json registration on create; on fix: test-local → version-bump → land → installed-test (bump is load-bearing: CC serves installed plugins from a version-keyed cache at `~/.claude/plugins/cache/`; never declare hooks in `plugin.json` — auto-load, double-declaring errors). Downstream install guide: `docs/installing-plugins-in-downstream-projects.md`.
- **`plans/`** — durable implementation plans for multi-session initiatives; use in-session plan mode for single-session tasks.
- **`goals/`** — standing-goal invariant ledger: per-deliverable `goals/<slug>.md` cheap read-only predicates, re-verified daily by `standing-goals.yml` (`scripts/check_standing_goals.py`). Enrollment at `/end-session` STEP 5b. Format/enrollment: `goals/README.md`.
- **`.claude/tasks/`** — `todo.md` (current checklist per `claude-behavior.md` rule 14) and `lessons.md` (correction patterns). Read `lessons.md` at session start; append after corrections.
- **`.claude/sessions/`** — `/end-session` checkpoints; `/start-session`/`/continue` restore from here.
- **`.claude/advisor-sessions/`** — `/five-advisors` transcripts.
- **`.remember/`** (gitignored) — SessionStart-hook handoff log: `remember.md` (next-handoff buffer) + `now.md`/`recent.md`/`archive.md`/`today-*.md`. Auto-surfaced at session start; write next handoff to `remember.md`. Distinct from `.claude/tasks/` and auto-memory.

### Stack Detection

Two mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*`. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`scripts/dependency_detection.py`) — `flutter-*`, `vue-*`, `bun-elysia-*`, etc. Universal patterns have no prefix. New stack requires changes in `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS` (scripts/dependency_detection.py), optionally `DEP_PATTERN_MAP`.

Stacks + prefixes (full listing: `docs/STACK-CATALOG.md`):

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

Six sync directions — `docs/SYNC-ARCHITECTURE.md`. Entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory), `aggregate_telemetry.py` (enrolled projects→hub telemetry).

For internal `.claude/` ↔ `core/.claude/` scoping AND keeping dual-home resources honest: `docs/HUB-CORE-SYNC.md`. A resource in both trees is classified in `config/dual-home-resources.yml` as `synced` (must match), `shared` (skeleton matches; hub/downstream lines fenced `DUAL-SYNC:HUB-ONLY`/`DOWNSTREAM-ONLY`), or `divergent`; gate `scripts/tests/test_dual_home_sync.py` (helper `scripts/sync_dual_home.py`) blocks drift + unclassified resources.

### Workflow Orchestration (skill-at-T0)

The 8 multi-step workflows (testing-pipeline, development-loop, debugging-loop, code-review, documentation, session-continuity, learning, skill-authoring) orchestrate from the user's T0 session via skills, NOT subagents — a deliberate KISS/YAGNI convention, not a platform constraint (nested subagent dispatch is GA, CC v2.1.172, ≤5 levels deep; no hub workflow yet needs it — see `core/.claude/rules/agent-orchestration.md` §2 + `plans/skill-at-t0-doctrine-relaxation.md`). For subagent vs. agent-team vs. worktree choice: `core/.claude/rules/agent-team-selection.md` (pattern `agent-team-selection` + 3 `team-*` governance hooks); default flat subagent; agent TEAM (default-off, ~4-7× tokens) only when workers must challenge each other mid-flight; worktree for parallel file isolation.

Legacy `core/.claude/agents/<workflow>-master-agent.md` files (`deprecated: true`, Phase 3, 2026-04-25) were REMOVED (2026-07-03, #289) after `testing-pipeline-master-agent` was retired (2026-06-19, → `/test-pipeline`) — none remain. `workflow-master-template.md` is the LIVE canonical template, never one of them. New workflow logic goes in the matching `core/.claude/skills/<workflow>/SKILL.md` — skill directory does NOT always equal the logical workflow name:

| Logical workflow | Skill directory |
|---|---|
| testing-pipeline | `test-pipeline` (deprecated `testing-pipeline-workflow` retired 2026-06-19) |
| code-review | `code-review-workflow` |
| documentation | `documentation-workflow` |
| learning | `learning-self-improvement` |
| skill-authoring | `skill-authoring-workflow` |
| development-loop, debugging-loop, session-continuity, loop-engineering | (directory name == logical name) |

`project-manager-agent` runs the PRD-to-Production pipeline and MUST run at T0 — invokes the 8 workflow skills via `Skill("/<workflow>")`; kept flat by the same convention.

`loop-engineering` (PRs #75-77) is a distributable skill-at-T0 autonomous self-* meta-loop (`core/.claude/skills/loop-engineering/SKILL.md`, spec `docs/specs/loop-engineering-spec.md`), usable standalone (`/loop`, `/goal-creator`, cron, PR). As of 2026-07-14 (`plans/ba-architect-loop-integration.md`) it's ALSO the build engine for `stage_7_impl` — `stage_to_workflow.stage_7_impl: loop-engineering`, dispatched with the plan as DoD/unit + `--no-ship` so human accept/deploy gates (G2/G3) still own shipping. Other stages keep prior mapping (testing-pipeline pre/post tests, code-review, documentation, development-loop for prd/plan/scaffold); pipeline now also pauses at T0 (interactive BA grilling) and A1 (owner design approval after plan+schema, before build).

Canonical references: `core/.claude/agents/workflow-master-template.md` v2.0.0, `docs/specs/test-pipeline-three-lane-spec-v2.md` v2.2.

### Agent Teams vs Subagents (orchestration primitives)

Beyond flat `Agent()` subagents, agent-team primitive (PR #202) — peer CC sessions messaging each other, sharing a task list, gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (shipped, default-OFF). Cheapest-sufficient selection: subagent (low cost, reports back only) → git worktree (isolated parallel edits, disk-only) → team (~4-7× tokens, full instance/teammate). Rule: `core/.claude/rules/agent-team-selection.md`; feature ref: `docs/claude-references/agent-teams.md`.

Distributable build workflows carry self-gated `--team` modes (`code-review-workflow`, `review-gate`, `auto-verify`, `development-loop`, `executing-plans`, `implement`, `brainstorm`, `research-mode`, `writing-plans`), enforced by three `team-*` hooks (pre-but-inert) in `core/.claude/settings.json` (`TaskCreated`/`TaskCompleted`/`TeammateIdle`). Reliability finding (2026-06-23): read-only review/research teams safe unsupervised once ground-truth-verified; parallel-edit (Execute tier) autonomous completion measured 1/3 — below ≥2/3 bar — stays human-supervised until integration is hardened. Plan+evidence: `plans/agent-teams-incorporation.md`, `docs/contracts/2026-06-23-agent-teams-pipeline-upgrade.md`.

### Key Scripts

- **`recommend.py`** — main provisioning entry point (`--local`/`--repo`, `--provision`, `--diff`, `--apply`); calls `third_party_skills.py` during provisioning. (`STACK_DETECTORS`/`DEP_PATTERN_MAP` in `scripts/dependency_detection.py`.) Import-only library modules (no CLI, not listed): `gap_analysis`, `hub_resources`, `overlap_analysis`, `plugin_recommendations`, `provision_local`, `provision_repo`, `provisioning_tiers`, `resource_copy`, `stack_detection`, `sync_manifest`.
- **`bootstrap.py`** — core copy logic; CLI `python scripts/bootstrap.py --stacks <stack1,stack2> --target <dir>`; defines `STACK_PREFIXES`.
- **`workflow_quality_gate_validate_patterns.py`** — CI validator for frontmatter, cross-references, registry sync.
- **`dedup_check.py`** — dedup validator (`--validate-all`) and secret scanner (`--secret-scan`).
- **`generate_docs.py`** / **`generate_workflow_docs.py`** — rebuild docs dashboard / workflow docs.
- **`extract_references.py`** — splits oversized SKILL.md into `references/`.
- **`collate.py`** — project→hub sync. **`scan_web.py`** — internet→hub sync. **`sync_to_projects.py`** — hub→projects sync. **`check_freshness.py`** — detects stale patterns. **`assign_workflow_groups.py`** — assigns patterns to workflow groups. **`discovery_adapter.py`** — discovery-pipeline adapter. **`discovery_to_issue.py`** — turns a migratable discovery from `config/discoveries.json` into a deduped GitHub issue (dry-run default, `--apply` files via `gh`; wired into `scan-internet.yml`). **`aggregate_telemetry.py`** — collects adoption signals+learnings from enrolled repos → `registry/patterns.json` (remote default vs `--local`; weekly via `aggregate-telemetry.yml`). **`sync_to_local.py`** — hub→local project sync. **`third_party_skills.py`** — detects+includes third-party agent skills during provisioning (called by `recommend.py`). **`pipeline_aggregator.py`** — standalone aggregator for testing-pipeline results (reads `test-results/*.json`, union-of-failures rule).
- **`check_eval_coverage.py`** — eval-coverage touch-trigger gate; CI (`validate-pr.yml`) runs `--enforce` (RATCHET, 2026-07-13): changed `SKILL.md` lacking `evals/*.md` FAILS unless grandfathered in `config/eval-coverage-grandfather.yml`; without `--enforce` only warns (`::warning::`, exit 0).
- **`check_plugin_version_bump.py`** — BLOCKING CI gate: any `plugins/<name>/` source change must bump `plugin.json` version (CC serves installed plugins from a version-pinned cache; an un-bumped edit never reaches installed copies). New plugins pass; README/evals-only exempt.
- **`generate_root_marketplace.py`** — derives root `.claude-plugin/marketplace.json` (T-145) from canonical `plugins/.claude-plugin/marketplace.json`, rewriting each `source` to `./plugins/<name>` so `claude plugin marketplace add abhayla/claude-best-practices` resolves against the full clone. `--check` is a BLOCKING CI gate (`validate-pr.yml`) on drift. See `docs/installing-plugins-in-downstream-projects.md`.
- **`bootstrap.sh`** (repo root) — curl-pipe-bash installer: `curl -sL .../bootstrap.sh | bash -s -- --stacks <list> [--target <dir>]`; calls `bootstrap.py` after fetching.
- **`trust_score.py`** / **`collect_signals.py`** / **`simulate_walk_phase.py`** / **`generate_trust_dashboard.py`** — trust-score/walk-phase toolchain, see "Trust Score & Walk-Phase" above.
- **`record_task_run.py`** (#196) — per-task trust-score accrual: auto-derives real signals + honest git-history `human_had_to_fix` proxy (never silently `False`), appends ONE shadow-mode run/branch to the ATLAS ledger; idempotent via `trust-score/.recorded-branches`. Wired into `/git-branch-lifecycle finish` STEP 3.
- **`record_merged_prs.py`** — zero-manual counterpart: sweeps recently MERGED PRs via `gh`, trusts each PR's own `validate` CI rollup, so auto-merge landings (skip `finish`) still accrue runs; adds per-PR `pr`/`branch`/`skill` ledger fields (`trust_score.stats_by()`). Idempotent via `trust-score/.recorded-prs`. Swept by `.claude/hooks/auto-pr-reconcile.sh` at SessionStart.
- **`measure_outcomes.py`** (T-144) — honest outcome scorecard: six delivery metrics from existing git/`gh` history + `costs/ledger.jsonl`, no new collection infra — 30-day change-failure rate, 30-day rework rate, checker/CI first-pass rate, guardrail catches (confirmed true positives only), invocation-based adoption (reports "no data" honestly if no log), cost per completed task. Report-only — prints measurements, never verdicts. `--explain` prints per-PR classification. Wired into `aggregate-telemetry.yml`; a failed `gh` read raises `FetchError`, non-zero exit. Tests: `test_measure_outcomes.py`.
- **`check_standing_goals.py`** — standing-goal sentinel: re-verifies every `goals/*.md` invariant's predicates (`file`/`command`), reports pass/fail, flags malformed goal files as failures. `--json`, `--update-timestamps` to refresh `last_verified` (passing goals only). Daily via `.github/workflows/standing-goals.yml` (cron-only, never in `validate-pr.yml`).
- **`cost_ledger.py`** — self-enforcing cost ledger: streams every CC transcript JSONL under `~/.claude/projects/`, aggregates per-day token/USD via `config/model-costs.yml` (`scripts/cost_ledger.py` reads it at runtime), appends idempotent daily rollups to gitignored `costs/ledger.jsonl`. `--daily` (wired into `.claude/hooks/auto-pr-reconcile.sh` at SessionStart, 60s soft deadline), `--report [--days N]`, `--cadence-report`, `--alert` (Notifier gateway P2 alert when yesterday's spend exceeds `daily_alert_usd`, fail-open).
- **`lint_rule_compliance.py`** — report-only rule-compliance line-lint: extracts MUST/MUST NOT/NEVER/ALWAYS directive lines from every `# Scope: global` rule, cross-references gitignored telemetry logs (`.claude/.*-misses.log`, `.overask-violations.log`), classifies each KEEP/REWRITE/DEMOTE/DELETE. Degrades to static heuristics when telemetry absent. `--json`.
- **`check_fleet_script_health.py`** — read-only static gate for the fleet's "detect-then-discard" defect class (stderr-suppressed probes, `grep -c … || echo 0` debounce inversion, dead enforcement gates, discarded-exit `.cmd` guards). Exit 0 clean / 1 findings; read-only. Referenced by `get-work-done`; test: `test_fleet_script_health.py`.
- **`feature_utilization.py`** (T-395) — report-only meter of CC feature utilization: streams transcripts under `~/.claude/projects/` for N days, reports platform primitives/skills/agents(×model)/MCP servers/model mix actually USED (bucketed owner/owner-subagent/fleet-workers) against genuinely-available inventory (settings-resolved enabled plugins only; cached-not-enabled listed separately, excluded from denominator). Never pass/fail; missing inputs = `unverified` notes; hooks declared unmeasurable. Calibrated against `docs/claude-references/capability-catalogue-<date>.md`. Cold run ~50s/1GB (warm ~4s) — background tick only. Drives `plans/capability-advisor.md`. Tests: `test_feature_utilization.py`.
- **`check_prereq_contract.py`** — report-only prerequisites-contract inventory: scans every SKILL.md across `.claude/skills/`, `core/.claude/skills/`, `plugins/*/skills/` for the prerequisites-preflight contract (`## Prerequisites` section or explicit `Prerequisites: none`, + `## STEP 0: Preflight` when prerequisites exist); drives `plans/prereq-contract-sweep.md`. Always exits 0. `--json`.
- **`validate_plugin_cleanroom.py`** (+ `validate_plugin_cleanroom.sh` wrapper) — clean-room plugin-validation pipeline: structural manifest checks (hooks-double-declare, dangling refs, marketplace registration), `claude plugin validate`, headless `--plugin-dir` serve probe via CC's `system/init` session-state event. See `docs/plugin-validation-pipeline.md`; structural-gate unit tests `scripts/tests/test_validate_plugin_cleanroom.py` never invoke `claude` CLI.
- **`check_provisioned_rule_drift.py`** (T-401) — report-only drift detector: rules ship downstream only as one-time copies, so a hub fix never reaches an already-provisioned project. For every repo in `D:/Abhay/GetWorkDone/settings.json` → `repo_registry`, hashes each `.claude/rules/*.md` (`dedup_check.hash_content`, split out of `hash_pattern` for this) and classifies CURRENT/STALE (matches an older hub version via git history capped at 30 commits; flags CONTRADICTION on fix/resolve/contradict keyword match)/MODIFIED/RETIRED (`git log --diff-filter=D` shows hub deletion)/PROJECT-ONLY/UNKNOWN (hub history unreadable). Each repo section opens with `read: working tree @ <branch> (ahead N / behind M of <upstream>)`. Always exits 0; missing path/unreadable file/timeout (`SUBPROCESS_TIMEOUT_SECONDS`) is a NOTE, never silent; soft wall-clock deadline (`DEFAULT_SCAN_DEADLINE_SECONDS`). `--weekly` caches to gitignored `rule-drift/.last-run.json`, ticked by `.claude/hooks/auto-pr-reconcile.sh`. Tests: `test_check_provisioned_rule_drift.py`.
- **`context_report.py`** (T-446, token-waste program) — report-only context/token-usage measurement over the last N days of transcripts (`--days`, default 7): streams every `*.jsonl` under `~/.claude/projects/` (same discovery approach as `cost_ledger.py`), classifies each as `main` or `sub` (a `subagents/` parent dir or an `agent-*` basename), prints totals, the fixed-prelude share (`sum(first_call_context * calls)`), the top `--top` (default 20) transcripts by input, a subagent histogram, tool-call counts, and per-model totals. `--json`. Tests: `test_context_report.py`.

> One-off migration scripts (e.g. `pr2_premerge_migration.py`, a single-use PR1→PR2 hash-format transition from PR #15) intentionally omitted — spent one-shots, not the standing toolchain. Don't "fix" the omission.

### Key Config Files

- **`registry/patterns.json`** — machine-readable index of all patterns; manually maintained.
- **`config/workflow-groups.yml`** — seed patterns for workflow doc generation; stale seeds silently break docs.
- **`config/workflow-contracts.yaml`** — per-workflow step DAGs, artifact contracts, gate expressions.
- **`config/third-party-skills.yml`** — registry of third-party agent skills.
- **`config/topics.yml`** / **`config/urls.yml`** — topic mappings / curated URLs for `scan_web.py`.
- **`config/discoveries.json`** — accumulated pattern discoveries, dedup'd across runs.
- **`config/test-pipeline.yml`** — test pipeline stage definitions.
- **`config/repos.yml`** — downstream repos for `sync_to_projects.py`/`recommend.yml`.
- **`config/settings.yml`** — hub-level settings.
- **`goals.yml`** — host-owned goal SSOT; drives Atlas Goal Pulse banner + `goal-anchored-decisions.md`.
- **`config/pipeline-stages.yaml`** — DAG config for pipeline orchestration.
- **`config/trust-score.yml`** — trust-score rulebook; edit here, never hardcode.
- **`config/telemetry-aggregates.json`** — historical effectiveness data from `aggregate_telemetry.py`; may not exist until first run — absence isn't an error. Schema (T-144): `{"patterns": {...}, "_outcomes": {...}}` — `_outcomes` holds `measure_outcomes.py`'s scorecard; `adoption_rate`/`retention_days_p50` RETIRED below `sample_size` 2. `load_telemetry_aggregates()` reads both this and the older flat schema.
- **`config/model-costs.yml`** — cost-ledger rulebook: USD/MTok by model family, `daily_alert_usd`, `ledger_retention_days`; edit here — `scripts/cost_ledger.py` reads it at runtime; rates are estimates (see `as_of`).
- **`config/dual-home-resources.yml`** — classifies resources in BOTH `.claude/` and `core/.claude/` as synced/shared/divergent; drift gate `scripts/tests/test_dual_home_sync.py`.
- **`config/eval-coverage-grandfather.yml`** — shrink-only allowlist for the eval-coverage ratchet; entries only REMOVED as evals are added, never added.
- **`config/plugin-recommendations.yml`** — install-not-copy layer (#187): `recommend.py` reads it to tell a project which marketplace plugins to install; edit here, never hardcode plugin sets in scripts.

### CI Workflows

- **`validate-pr.yml`** — runs all 4 validation commands on PRs + 3 blocking gates: eval-coverage ratchet (`check_eval_coverage.py --enforce`), plugin version-bump (`check_plugin_version_bump.py`), root-marketplace mirror sync (`generate_root_marketplace.py --check`).
- **`update-docs.yml`** — auto-regenerates docs on main push; avoid running `generate_docs.py` manually on main.
- **`test.yml`** — pytest on `scripts/**` changes.
- **`recommend.yml`** — `workflow_dispatch`-only (weekly cron RETIRED 2026-07-14, all enrolled repos plugins-first); re-enable by restoring the schedule block.
- **`apply-selections.yml`** — triggered by `/apply` PR comment.
- **`aggregate-telemetry.yml`** — weekly cron (Friday): `aggregate_telemetry.py` against enrolled repos.
- Scheduled: `scan-internet.yml`, `scan-projects.yml`, `sync-to-projects.yml`, `expire-sources.yml`, `standing-goals.yml`.

## Testing

- Fixtures: `scripts/tests/fixtures/` + shared in `scripts/tests/conftest.py`.
- Uses `tmp_path` for temp files, `sample_registry` fixture for registry tests.
- `scripts/tests/smoke-test/` — end-to-end provisioning smoke test (`bootstrap.py`+`recommend.py` vs a fixture project).
- Bug fixing: write a failing test first, then fix.

## Key Conventions

- **Registry maintenance**: (1) add/remove files in `core/.claude/`, (2) update `registry/patterns.json`, (3) run `generate_docs.py`, (4) run `workflow_quality_gate_validate_patterns.py` to verify sync.
- Pattern curation is reactive, not speculative — `core/.claude/rules/rule-curation.md`.
- Pattern quality checks (structure, portability, self-containment) via `/pattern-quality`.
- `/synthesize-project` provisions projects; `/synthesize-hub` generalizes patterns back into the hub.
- `update-docs.yml` auto-regenerates docs on main — do not duplicate by running `generate_docs.py` manually on main.

## Eval Workflow

Skills validated through an eval workflow before merge; recent evals in `evals/` within skill folders. Invoke via `/skill-evaluator`: `/skill-evaluator full <skill-path>` (modes `trigger`, `output`, `full`, `conflicts`; add `--baseline` to compare against agent baseline). See `.claude/skills/skill-evaluator/EVAL-WORKFLOW.md` for the mandatory step sequence — do not batch multiple skills into one eval run.

## Third-Party Skills

`config/third-party-skills.yml` registers external agent skills (e.g. from MCP servers); `third_party_skills.py` detects+includes matches during provisioning. To add: entry in `config/third-party-skills.yml` with detection criteria + skill definition.

## Rules for Claude

> Demoted to on-demand docs (2026-07-12): docs-cache procedure → `docs/claude-references/README.md`; product incubation → `docs/governance/product-incubation.md` (read BEFORE placing product code in/near the hub — it lives in sibling repos); learning-to-gate doctrine → `docs/governance/learning-to-gate-doctrine.md` (gate-with-self-test where deterministic, recurrence ratchet otherwise; kept doc-not-rule by the lean-rules gate).

Auto-loaded from `.claude/rules/` — global rules load always, path-scoped rules load only on matching files:

- `.claude/rules/claude-behavior.md` — task approach, self-improvement, git hygiene, code quality, scope discipline.
- `.claude/rules/context-management.md` — progressive disclosure, scratchpad usage, subagent delegation, compaction survival.
- `.claude/rules/model-routing.md` — cheapest sufficient model per dispatch, preemptive security-category routing to opus, refusal→fallback playbook, per-pass effort dial, session-level routing.
- `.claude/rules/prompt-auto-enhance.md` — Tier 1/2 context gathering, grade pipeline, clarification gate, resource CRUD detection.
- `.claude/rules/verify-before-suggest-do-before-delegate.md` — live-verify actionable recommendations before presenting (evidence: source+date+version); agent is default executor, human steps carry a named blocker.

(`notifier-integration.md` is distributable, `core/.claude/rules/` only — not hub-auto-loaded; the Notifier gateway itself is in user-global CLAUDE.md / `GLOBAL.md` §2.)
- `.claude/rules/workflow.md` — 7-step development workflow (understand → test → implement → fix-loop → verify → commit).

## Maintaining This File (/init audits)

Auto-loaded every session — keep accurate and token-flat; audit is a diff against the live repo, never touch owner-approved narrative (G6 architecture, governance) without approval. Checklist:

1. **Enumerable lists vs disk** — `ls plugins/` vs the `plugins/` entry; `ls .claude/rules/` vs "Rules for Claude"; `ls scripts/*.py` vs Key Scripts (one-shots intentionally omitted); `ls config/` vs Key Config Files; workflow map vs `ls core/.claude/skills/`.
2. **CI vs prose** — `.github/workflows/validate-pr.yml` steps vs "Full local CI replication" + CI Workflows section; gate descriptions vs scripts' actual behavior — read the docstring, don't trust old prose.
3. **No pinned counts** — pattern totals, plugin counts, %s: point at SSOT (`registry/patterns.json`, `goals.yml`, changelog) instead of pinning rotting numbers; prefer "The pieces:" over "Two hooks + one skill".
4. **Paths exist** — every referenced file/dir must exist at the stated path.
5. **Close out** — update header audit-trail comment, run quality gate + secret scan locally, land CI-gated on the autonomous branch lifecycle.
