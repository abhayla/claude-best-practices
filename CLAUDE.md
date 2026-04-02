# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template for downstream projects. NEVER put hub-only config here. NEVER use patterns from this directory (skills, agents, rules, hooks) when working on this hub repo — they are for downstream projects only.
- **`.claude/`** (repo root) — Hub-only operational config (scan skills, `synthesize-hub`, hub agents, hooks). This is what THIS repo uses. NEVER distribute this.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`
- **Windows**: use `set PYTHONPATH=. &&` prefix instead of `PYTHONPATH=.`, or use Git Bash

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

A curated hub of ~225 Claude Code patterns (agents, skills, rules, hooks) organized by stack. Three provisioning modes: (1) copy all from `core/.claude/` and prune, (2) smart provision via `recommend.py --provision` (auto-detects stacks), (3) full synthesis via `/synthesize-project`.

### Key Directories

- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, `config/`, templates
- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when working with matching files
- **`config/`** — `settings.yml`, `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow docs), `pipeline-stages.yaml` (DAG config), `workflow-contracts.yaml` (step DAGs + artifact contracts)
- **`docs/workflows/`** — Auto-generated workflow docs. Do not edit manually — regenerate after pattern changes

### Stack Detection

Two mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*`. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`recommend.py`) — matches `flutter-*`, `vue-*`, `bun-elysia-*`, etc. from project dependencies. Universal patterns have no prefix. Adding a new stack requires changes in `STACK_PREFIXES` (bootstrap.py), `STACK_DETECTORS` (recommend.py), and optionally `DEP_PATTERN_MAP` (recommend.py).

### Sync Flows

Six sync directions — see `docs/SYNC-ARCHITECTURE.md`. Key entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory).

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

### Key Config Files

- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit after adding/removing patterns
- **`config/workflow-groups.yml`** — Seed patterns for workflow doc generation. Stale seeds silently break docs
- **`config/workflow-contracts.yaml`** — Per-workflow step DAGs, artifact contracts, gate expressions
- **`config/third-party-skills.yml`** — Registry of third-party agent skills detected during provisioning
- **`config/topics.yml`** / **`config/urls.yml`** — Topic mappings and curated URLs for `scan_web.py`

### CI Workflows

- **`validate-pr.yml`** — Runs all 4 validation commands on PRs
- **`update-docs.yml`** — Auto-regenerates docs on main push. Avoid running `generate_docs.py` manually on main
- **`test.yml`** — Runs pytest on `scripts/**` changes
- **`recommend.yml`** — Weekly cron: provisions patterns for repos in `config/repos.yml`
- **`apply-selections.yml`** — Triggered by `/apply` comment on PRs to process pattern selections
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
- `update-docs.yml` auto-regenerates docs on main — avoid running `generate_docs.py` manually on main

## Rules for Claude

1. **Bug Fixing**: Use `/fix-loop` or `/fix-issue`. Write a test that reproduces the bug, then fix and prove with a passing test.
2. **Rules**: Auto-loaded from `.claude/rules/` — global rules load always, path-scoped rules load when working with matching files. See rule files for details.
