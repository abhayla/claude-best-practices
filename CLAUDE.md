# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# Full local CI replication (run before opening a PR)
PYTHONPATH=. python scripts/dedup_check.py --validate-all
PYTHONPATH=. python scripts/dedup_check.py --secret-scan
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
PYTHONPATH=. python -m pytest scripts/tests/ -v

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
- **Rules** (`core/.claude/rules/*.md`) — auto-loaded directives. `# Scope: global` loads always; `globs:` frontmatter scopes to matching paths.
- **Hooks** (`core/.claude/hooks/*.sh`) — shell scripts wired into `settings.json` events (pre/post-tool, prompt-submit, etc.).

### Synthesize Flywheel

Projects can opt in to share back synthesized patterns by setting `allow_hub_sharing: true` in their `.claude/synthesis-config.yml`. `/synthesize-hub` then collates `synthesized: true` patterns from enrolled repos in `config/repos.yml`, dedups via 3-level matching (hash/structural/semantic), and drafts generalized hub PRs. Default is local-only — sharing is bilateral and opt-in. See `docs/synthesize-flywheel.md`.

### Key Directories

- **`core/.claude/`** — All **distributable** patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, `config/`, templates. These ship to downstream projects — never run them against this hub repo (see "Two `.claude/` Directories" above)
- **`.claude/agents/`** — Hub-only **operational** agents (NOT distributed): `planner-researcher-agent`, `code-reviewer-agent`, `quality-gate-evaluator-agent`, `skill-author-agent`, `web-research-specialist-agent`, `anthropic-multi-agent-reviewer-agent`. Distinct from `core/.claude/agents/` (the downstream template). Dispatch these when doing hub work
- **`.claude/skills/`** — Hub-only operational skills (NOT distributed): scan/discovery (`scan-repo`, `scan-url`, `scan-discovery-report`, `self-improve`), synthesis (`synthesize-hub`, `synthesize-project`), governance/authoring (`pattern-quality`, `claude-guardian`, `ssot-workflow-audit`, `writing-skills`, `skill-evaluator`), and session tooling. New hub-only skills go HERE, never in `core/.claude/skills/`
- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when working with matching files
- **`.claude/hooks/`** — Hub-only governance/telemetry hooks wired into `.claude/settings.json`: `session-governance-status.sh` (session-start governance banner), `prompt-enhance-reminder.sh` (gates prompt-auto-enhance triggering), `no-overask-guard.sh` (Stop-hook telemetry for missed enhance banners), `ba-usecase-discovery-reminder.sh` (UserPromptSubmit BA/deep-research OFFER gate, wired hub-wide PRs #113/#114), `verifier-edge-guard.sh` (Stop-hook telemetry for builder done-claims missing verifier evidence — the 3 hookable fragile gates, PRs #116/#117), `prompt-logger.sh`, `auto-learn-trigger.sh`, `pattern-quality-gate.sh`, `post-failure-capture.sh`. Their runtime state files (`.claude/.enhance-misses.log`, `.claude/.verifier-misses.log`, etc.) are gitignored
- **`config/`** — `settings.yml`, `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow docs), `pipeline-stages.yaml` (DAG config), `workflow-contracts.yaml` (step DAGs + artifact contracts)
- **`docs/specs/`** — Canonical workflow/feature specs (e.g., `test-pipeline-three-lane-spec-v2.md`). Reference these — do not duplicate spec content elsewhere
- **`docs/workflows/`** — Auto-generated workflow docs. Do not edit manually — regenerate after pattern changes
- **`docs/WORKFLOW-DIAGRAM.md`** — Visual reference for the skill-at-T0 workflow orchestration model. Read alongside the "Workflow Orchestration (skill-at-T0)" section below
- **`internet-sources/`** — Pending and archived sources for `scan_web.py` (`pending/`, `archived/`)
- **`plans/`** — Durable implementation plans for multi-session initiatives. Write a plan here when work spans sessions or needs cross-subagent handoff; use in-session plan mode for single-session tasks.
- **`.claude/tasks/`** — `todo.md` (current task checklist per `claude-behavior.md` rule 14) and `lessons.md` (correction patterns accumulated across sessions). Read `lessons.md` at session start; append after corrections.
- **`.claude/sessions/`** — `/save-session` checkpoints; `/start-session` and `/continue` restore from here
- **`.claude/advisor-sessions/`** — `/five-advisors` transcripts
- **`.remember/`** (gitignored) — SessionStart-hook handoff log: `remember.md` (next-handoff buffer) + `now.md`/`recent.md`/`archive.md`/`today-*.md` history. Auto-surfaced at session start; write the next handoff to `remember.md`. Distinct from `.claude/tasks/` (todo + lessons) and auto-memory (cross-session user prefs)

### Stack Detection

Two mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*`. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`recommend.py`) — matches `flutter-*`, `vue-*`, `bun-elysia-*`, etc. from project dependencies. Universal patterns have no prefix. Adding a new stack requires changes in `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS` (recommend.py), and optionally `DEP_PATTERN_MAP` (recommend.py).

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

### Workflow Orchestration (skill-at-T0)

The 8 multi-step workflows (testing-pipeline, development-loop, debugging-loop, code-review, documentation, session-continuity, learning, skill-authoring) orchestrate from the user's T0 session via skills, NOT via subagents. Anthropic's Claude Code does not forward the `Agent` tool to dispatched subagents — any `Agent()` call inside a subagent silently inlines at runtime, defeating parallelism. Workflow skills run in T0 and dispatch flat worker subagents in a single message.

The 8 legacy `core/.claude/agents/<workflow>-master-agent.md` files are `deprecated: true` (Phase 3, 2026-04-25) and MUST NOT be dispatched. New workflow logic goes in the matching `core/.claude/skills/<workflow>/SKILL.md` — but the on-disk skill directory does NOT always equal the logical workflow name above. Resolve via this map before `ls`-ing or editing:

| Logical workflow | Skill directory |
|---|---|
| testing-pipeline | `testing-pipeline-workflow` |
| code-review | `code-review-workflow` |
| documentation | `documentation-workflow` |
| learning | `learning-self-improvement` |
| skill-authoring | `skill-authoring-workflow` |
| development-loop, debugging-loop, session-continuity, loop-engineering | (directory name == logical name) |

The `project-manager-agent` runs the full PRD-to-Production pipeline and MUST run at T0 — it invokes the 8 workflow skills via `Skill("/<workflow>")`. Dispatching it as a subagent will silently break parallelism for the same reason workflow masters did.

`loop-engineering` (PRs #75–77) is a 9th distributable skill-at-T0 workflow (`core/.claude/skills/loop-engineering/SKILL.md`, spec at `docs/specs/loop-engineering-spec.md`) — a standalone autonomous self-* meta-loop. It is NOT part of the PRD-to-Production pipeline, which is why the counts above (legacy master-agents, project-manager-agent's workflow skills) remain 8.

Canonical references: `core/.claude/agents/workflow-master-template.md` v2.0.0, `docs/specs/test-pipeline-three-lane-spec-v2.md` v2.2.

### Key Scripts

- **`recommend.py`** — Main provisioning entry point. Modes: `--local`/`--repo`, `--provision`, `--diff`, `--apply`. Defines `STACK_DETECTORS` and `DEP_PATTERN_MAP`. Calls `third_party_skills.py` during provisioning for third-party agent skill detection
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
- **`aggregate_telemetry.py`** — Collects adoption signals + learnings from enrolled repos, writes effectiveness metrics to `registry/patterns.json`. Remote mode (default) vs local (`--local`). Runs weekly via `aggregate-telemetry.yml`
- **`sync_to_local.py`** — Hub→local sync: pulls patterns into a local project directory
- **`third_party_skills.py`** — Detects and includes third-party agent skills during provisioning (called by `recommend.py`)
- **`pipeline_aggregator.py`** — Standalone aggregator for testing-pipeline results: reads `test-results/*.json` and applies the union-of-failures rule
- **`bootstrap.sh`** (repo root, not in `scripts/`) — Curl-pipe-bash installer for downstream users: `curl -sL .../bootstrap.sh | bash -s -- --stacks <list> [--target <dir>]`. Calls `bootstrap.py` after fetching the repo

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
- **`config/pipeline-stages.yaml`** — DAG config for pipeline orchestration
- **`config/telemetry-aggregates.json`** — Historical effectiveness data from `aggregate_telemetry.py` runs. Generated output — may not exist until the first telemetry run; do not treat its absence as an error

### CI Workflows

- **`validate-pr.yml`** — Runs all 4 validation commands on PRs
- **`update-docs.yml`** — Auto-regenerates docs on main push. Avoid running `generate_docs.py` manually on main
- **`test.yml`** — Runs pytest on `scripts/**` changes
- **`recommend.yml`** — Weekly cron: provisions patterns for repos in `config/repos.yml`
- **`apply-selections.yml`** — Triggered by `/apply` comment on PRs to process pattern selections
- **`aggregate-telemetry.yml`** — Weekly cron (Friday): runs `aggregate_telemetry.py` against enrolled repos
- Scheduled: `scan-internet.yml`, `scan-projects.yml`, `sync-to-projects.yml`, `expire-sources.yml`

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

Auto-loaded from `.claude/rules/` — global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when editing matching files. Rule files:

- `.claude/rules/claude-behavior.md` — task approach, self-improvement, git hygiene, code quality, scope discipline
- `.claude/rules/context-management.md` — progressive disclosure, scratchpad usage, subagent delegation, compaction survival
- `.claude/rules/prompt-auto-enhance.md` — Tier 1/2 context gathering, grade pipeline, clarification gate, resource CRUD detection
- `.claude/rules/workflow.md` — 7-step development workflow (understand → test → implement → fix-loop → verify → commit)
