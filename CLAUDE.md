# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template (what users copy to their projects). NEVER put hub-only config here.
- **`.claude/`** (repo root) — Hub-only operational config: scan skills (`scan-repo`, `scan-url`), `synthesize-hub`, hub rules. NEVER distribute this.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`

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

A curated hub of Claude Code patterns (agents, skills, rules) organized by stack. Users provision their project via `recommend.py --provision` or `/synthesize-project`.

### Key Directories

- **`.claude/rules/`** — Auto-loaded rules. Global rules (`# Scope: global`) load always; path-scoped rules (`globs:` frontmatter) load only when working with matching files
- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, templates
- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit directly after adding/removing patterns, then re-run `generate_docs.py`
- **`config/`** — `settings.yml` (dedup thresholds: semantic 85/70, structural 3; scan limits), `repos.yml` (downstream projects, `auto_sync`/`share_synthesized` flags), `urls.yml`/`topics.yml` (scan sources with freshness tracking), `third-party-skills.yml` (external skill registry), `test-pipeline.yml` (externalized pipeline DAG)
- **`docs/stages/`** — Pipeline stage definitions (STAGE-0 through STAGE-11) with executable `Skill()`/`Agent()` dispatch examples
- **`scripts/`** — All Python tooling (see Key Scripts below for the important ones)

### Stack Prefix Convention

Stack-specific patterns use filename prefixes (e.g., `fastapi-*`, `android-*`, `react-*`, `flutter-*`, `vue-*`, `firebase-*`, `ai-gemini-*`, `bun-elysia-*`). Universal patterns have no prefix. The bootstrap script filters by these prefixes.

### Sync Flows (details in `docs/SYNC-ARCHITECTURE.md`)

1. **Project → Hub**: `collate.py` extracts + deduplicates from registered repos
2. **Internet → Hub**: `scan_web.py` discovers patterns from URLs/topics
3. **Hub → Local**: `/update-practices` skill pulls updates
4. **Hub → Registered Projects**: `sync_to_projects.py` creates per-project PRs
5. **Local → Hub**: `/contribute-practice` validates and submits as PR
6. **Hub → Project (Advisory)**: `recommend.py` produces tiered gap report, optionally applies

### Key Scripts

- **`recommend.py`** — Main provisioning entry point. Modes: `--local`/`--repo` (report), `--apply` (copy), `--provision` (apply + generate CLAUDE.md + settings.json), `--diff`, `--use-config`. Defines `STACK_DETECTORS` and `DEP_PATTERN_MAP`.
- **`bootstrap.py`** — Core copy logic. Defines `STACK_PREFIXES` mapping and `copy_claude_dir()`. Imported by `recommend.py`.
- **`workflow_quality_gate_validate_patterns.py`** — CI validator for frontmatter, cross-references, file/registry sync.
- **`generate_docs.py`** — Rebuilds `docs/` dashboard and `core/.claude/README.md` from registry.
- **`collate.py`** — Extracts patterns from downstream repos for hub ingestion.
- **`scan_web.py`** — Discovers patterns from `config/urls.yml` and `config/topics.yml`.
- **`sync_to_projects.py`** — Pushes hub updates to registered projects as PRs (`config/repos.yml`).
- **`dedup_check.py`** — CI dedup validator (`--validate-all`) and secret scanner (`--secret-scan`).
- **`generate_workflow_docs.py`** — Rebuilds `docs/workflows/` from `config/workflow-groups.yml`.

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

