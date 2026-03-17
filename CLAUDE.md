# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template (what users copy to their projects). NEVER put hub-only config here.
- **`.claude/`** (repo root) — Hub-only operational config (scan skills, hub settings). NEVER distribute this.

## Commands

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Run all tests (PYTHONPATH=. required for cross-module imports)
PYTHONPATH=. python -m pytest scripts/tests/ -v

# Run a single test
PYTHONPATH=. python -m pytest scripts/tests/test_bootstrap.py::TestCopyClaudeDir::test_copies_core_files -v

# Validate patterns before PR
PYTHONPATH=. python scripts/validate_patterns.py

# Provision a project (auto-detect stacks, copy patterns, generate CLAUDE.md)
PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

# Regenerate docs after registry changes
python scripts/generate_docs.py
```

## Architecture

A curated hub of Claude Code patterns (agents, skills, rules) organized by stack. Users provision their project via `recommend.py --provision` or `/synthesize-project`.

### Key Directories

- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, templates
- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit directly after adding/removing patterns, then re-run `generate_docs.py`
- **`config/`** — `settings.yml` (dedup thresholds), `repos.yml` (downstream projects), `urls.yml`/`topics.yml` (scan sources)
- **`scripts/`** — All Python: `bootstrap.py`, `recommend.py`, `collate.py`, `scan_web.py`, `validate_patterns.py`, `generate_docs.py`, `dedup_check.py`, `check_freshness.py`, `sync_to_local.py`, `sync_to_projects.py`

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

- **`bootstrap.py`** — Core copy logic. Defines `STACK_PREFIXES` mapping and `copy_claude_dir()` which filters patterns by stack prefix. Imported by `recommend.py`.
- **`recommend.py`** — Main entry point for provisioning. Modes: `--local`/`--repo` (report only), `--apply` (copy files), `--provision` (apply + generate CLAUDE.md + settings.json), `--diff` (compare overlapping content). Uses `bootstrap.py` for copying and `collate.py` for extraction.
- **`validate_patterns.py`** — CI validator. Checks frontmatter, cross-references, file/registry sync. Run before every PR.
- **`generate_docs.py`** — Rebuilds `docs/` dashboard and `core/.claude/README.md` from `registry/patterns.json`.
- **`collate.py`** — Extracts patterns from downstream project repos for hub ingestion.
- **`scan_web.py`** — Discovers patterns from URLs/topics configured in `config/urls.yml` and `config/topics.yml`.

### GitHub Actions

Nine workflows: `test.yml`, `scan-projects.yml`, `scan-internet.yml`, `validate-pr.yml`, `update-docs.yml`, `sync-to-projects.yml`, `expire-sources.yml`, `recommend.yml`, `apply-selections.yml`.

## Testing

- Fixtures: `scripts/tests/fixtures/` + shared in `scripts/tests/conftest.py`
- Uses `tmp_path` for temp files and `sample_registry` fixture for registry tests
- Smoke tests: `scripts/tests/smoke-test/todo-api/`
- Bug fixing: write a failing test first, then fix. Use subagents to attempt fixes.

## Key Conventions

- `registry/patterns.json` MUST stay in sync with actual files in `core/.claude/`. After adding/removing patterns: edit the registry, then run `python scripts/generate_docs.py` to regenerate docs. CI (`validate-pr.yml`) will catch drift.
- Pattern curation is reactive, not speculative — see `.claude/rules/rule-curation.md`
- Pattern quality rules (structure, portability, self-containment) are in `.claude/rules/pattern-*.md`
- `/synthesize-project` (in `core/.claude/skills/`) provisions projects; `/synthesize-hub` (in `.claude/skills/`) generalizes patterns back into the hub
- Stack prefix filtering depends on `STACK_PREFIXES` in `scripts/bootstrap.py`. To add a new stack, add the prefix mapping there AND update stack detection in `scripts/recommend.py`.
