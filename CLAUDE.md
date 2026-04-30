# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template for downstream projects. NEVER put hub-only config here. NEVER use patterns from this directory (skills, agents, rules, hooks) when working on this hub repo — they are for downstream projects only.
- **`.claude/`** (repo root) — Hub-only operational config (scan skills, `synthesize-hub`, hub agents, hooks). This is what THIS repo uses. NEVER distribute this.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`
- **Windows**: use `set PYTHONPATH=. &&` prefix instead of `PYTHONPATH=.`, or use Git Bash. All commands below assume Unix shell syntax (forward slashes, `PYTHONPATH=.` prefix)
- **New here?** For downstream provisioning options (copy-all, smart, full synthesis), see `README.md`.
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

A curated hub of Claude Code patterns (agents, skills, rules, hooks) organized by stack — for the live count, see `registry/patterns.json` (one top-level key per pattern, excluding `_meta`). Three provisioning modes: (1) copy all from `core/.claude/` and prune, (2) smart provision via `recommend.py --provision` (auto-detects stacks), (3) full synthesis via `/synthesize-project`.

For sync direction semantics (hub↔projects, hub↔internet, aggregation flows), read `docs/SYNC-ARCHITECTURE.md` before modifying any sync script.

### Key Directories

- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, `config/`, templates
- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when working with matching files
- **`config/`** — `settings.yml`, `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow docs), `pipeline-stages.yaml` (DAG config), `workflow-contracts.yaml` (step DAGs + artifact contracts)
- **`docs/workflows/`** — Auto-generated workflow docs. Do not edit manually — regenerate after pattern changes
- **`internet-sources/`** — Pending and archived sources for `scan_web.py` (`pending/`, `archived/`)
- **`plans/`** — Durable implementation plans for multi-session initiatives. Write a plan here when work spans sessions or needs cross-subagent handoff; use in-session plan mode for single-session tasks.
- **`.claude/tasks/`** — `todo.md` (current task checklist per `claude-behavior.md` rule 14) and `lessons.md` (correction patterns accumulated across sessions). Read `lessons.md` at session start; append after corrections.

### Stack Detection

Two mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*`. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`recommend.py`) — matches `flutter-*`, `vue-*`, `bun-elysia-*`, etc. from project dependencies. Universal patterns have no prefix. Adding a new stack requires changes in `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS` (recommend.py), and optionally `DEP_PATTERN_MAP` (recommend.py).

Available stacks and their prefixes:

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

### Sync Flows

Six sync directions — see `docs/SYNC-ARCHITECTURE.md`. Key entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory).

### Workflow Orchestration (skill-at-T0)

The 8 multi-step workflows (testing-pipeline, development-loop, debugging-loop, code-review, documentation, session-continuity, learning, skill-authoring) orchestrate from the user's T0 session via skills, NOT via subagents. Anthropic's Claude Code does not forward the `Agent` tool to dispatched subagents — any `Agent()` call inside a subagent silently inlines at runtime, defeating parallelism. Workflow skills run in T0 and dispatch flat worker subagents in a single message.

The 8 legacy `core/.claude/agents/<workflow>-master-agent.md` files are `deprecated: true` (Phase 3, 2026-04-25) and MUST NOT be dispatched. New workflow logic goes in the matching `core/.claude/skills/<workflow>/SKILL.md`.

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
- **`config/telemetry-aggregates.json`** — Historical effectiveness data from `aggregate_telemetry.py` runs

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

Auto-loaded from `.claude/rules/` — global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when editing matching files. See the rule files directly for behavioral guidance (task approach, git hygiene, context management, workflow, prompt auto-enhance).
