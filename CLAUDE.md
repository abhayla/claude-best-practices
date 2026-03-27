# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template (what users copy to their projects). NEVER put hub-only config here.
- **`.claude/`** (repo root) — Hub-only operational config: scan skills (`scan-repo`, `scan-url`), `synthesize-hub`, hub rules. NEVER distribute this.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt` (Windows: `.venv\Scripts\activate`)
- Windows: use `set PYTHONPATH=. &&` prefix instead of `PYTHONPATH=.` for commands below, or run in Git Bash where the Unix syntax works

## Commands

```bash
# Run all tests (PYTHONPATH=. required for cross-module imports)
PYTHONPATH=. python -m pytest scripts/tests/ -v

# Run a single test
PYTHONPATH=. python -m pytest scripts/tests/test_bootstrap.py::TestCopyClaudeDir::test_copies_core_files -v

# Provision a project
PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

# Full local CI replication (.github/workflows/validate-pr.yml runs all 4 — run before opening a PR)
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

A curated hub of Claude Code patterns (agents, skills, rules) organized by stack. Three provisioning modes: (1) copy all from `core/.claude/` and prune, (2) smart provision via `recommend.py --provision` (auto-detects stacks), (3) full synthesis via `/synthesize-project` (hub patterns + project-specific patterns generated from your code).

### Key Directories

- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when working with matching files
- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, templates
- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit directly after adding/removing patterns, then re-run `generate_docs.py`
- **`config/`** — `settings.yml` (dedup thresholds, scan limits), `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow doc generation — stale seeds silently break docs), plus `urls.yml`, `topics.yml`, `third-party-skills.yml`, `test-pipeline.yml`
- **`docs/stages/`** — Pipeline stage definitions (STAGE-0 through STAGE-11) with executable `Skill()`/`Agent()` dispatch examples
- **`scripts/`** — All Python tooling (see Key Scripts below for the important ones)

### Stack Prefix Convention

Stack-specific patterns use filename prefixes (e.g., `fastapi-*`, `android-*`, `react-*`, `flutter-*`, `vue-*`, `firebase-*`, `ai-gemini-*`, `bun-elysia-*`). Universal patterns have no prefix. The bootstrap script filters by these prefixes.

### Sync Flows

Six sync directions exist — see `docs/SYNC-ARCHITECTURE.md` for details. Key entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory).

### Key Scripts

- **`recommend.py`** — Main provisioning entry point. Modes: `--local`/`--repo`, `--apply`, `--provision`, `--diff`, `--use-config`. Defines `STACK_DETECTORS` and `DEP_PATTERN_MAP`.
- **`bootstrap.py`** — Core copy logic. Defines `STACK_PREFIXES` mapping. Imported by `recommend.py`.
- **`workflow_quality_gate_validate_patterns.py`** — CI validator for frontmatter, cross-references, file/registry sync.
- **`dedup_check.py`** — CI dedup validator (`--validate-all`) and secret scanner (`--secret-scan`).
- **`generate_docs.py`** / **`generate_workflow_docs.py`** — Rebuild `docs/` dashboard and workflow docs respectively.

CI lives in `.github/workflows/validate-pr.yml` — runs all 4 validation commands listed above.

## Testing

- Fixtures: `scripts/tests/fixtures/` + shared in `scripts/tests/conftest.py`
- Uses `tmp_path` for temp files and `sample_registry` fixture for registry tests
- Smoke tests: `scripts/tests/smoke-test/todo-api/`
- Bug fixing: write a failing test first, then fix — see `.claude/rules/workflow.md`

## Key Conventions

- **Registry maintenance workflow**: (1) add/remove files in `core/.claude/`, (2) update `registry/patterns.json`, (3) run `python scripts/generate_docs.py`, (4) run `PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py` to verify sync. CI (`validate-pr.yml`) will catch drift.
- Pattern curation is reactive, not speculative — see `.claude/rules/rule-curation.md`
- Pattern quality rules (structure, portability, self-containment) are in `.claude/rules/pattern-*.md`
- `/synthesize-project` (in `core/.claude/skills/`) provisions projects; `/synthesize-hub` (in `.claude/skills/`) generalizes patterns back into the hub
- Adding a new stack requires changes in three places: `STACK_PREFIXES` in `scripts/bootstrap.py` (prefix→stack mapping), `STACK_DETECTORS` in `scripts/recommend.py` (auto-detection rules), and optionally `DEP_PATTERN_MAP` in `recommend.py` (dependency→pattern promotion).

