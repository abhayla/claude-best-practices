# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A curated knowledge hub of Claude Code patterns (agents, skills, rules) organized by technology stack. It serves as both a template system for bootstrapping new projects and a continuously-updated registry of battle-tested patterns. Users copy the `core/.claude/` directory to their project with one command.

## Commands

```bash
# Run all tests
PYTHONPATH=. python -m pytest scripts/tests/ -v

# Run a single test file
PYTHONPATH=. python -m pytest scripts/tests/test_bootstrap.py -v

# Run a single test
PYTHONPATH=. python -m pytest scripts/tests/test_bootstrap.py::TestCopyClaudeDir::test_copies_core_files -v

# Install dependencies
pip install -r scripts/requirements.txt

# Bootstrap a project with specific stacks
python scripts/bootstrap.py --stacks fastapi-python,android-compose --target /path/to/project

# Generate documentation dashboard
python scripts/generate_docs.py

# Check pattern freshness
python scripts/check_freshness.py

# Run deduplication check
PYTHONPATH=. python scripts/dedup_check.py

# Scan registered projects for new patterns
PYTHONPATH=. python scripts/collate.py --all

# Scan internet sources
PYTHONPATH=. python scripts/scan_web.py --all
```

## Architecture

### Pattern Organization

- **`core/.claude/`** — All distributable patterns. Stack-specific patterns use filename prefixes (e.g., `fastapi-*`, `android-*`). Contains:
  - `agents/` — 13 agent definitions (10 universal + 3 stack-specific)
  - `skills/` — 24 skill directories, each with a `SKILL.md`
  - `rules/` — 10 rule files (2 universal + 4 stack-specific + 4 placeholders)
  - `hooks/` — Hook examples (README only, no executables)
  - `README.md` — Self-documenting index of all patterns
  - `settings.json` — Minimal defaults
  - `CLAUDE.md.template` / `CLAUDE.local.md.template` — Pre-filled templates with TODOs

- **`.claude/`** — Hub-only operational config (not distributed). Contains:
  - `skills/scan-repo/` — Scan downstream repos for patterns
  - `skills/scan-url/` — Scan internet for patterns
  - `settings.json` — Hub settings

- **`registry/patterns.json`** — Machine-readable index of all patterns with hashes, versions, categories, and dependency info. Source of truth for sync operations.

- **`config/`** — Hub-level configuration: `settings.yml` (scan schedules, dedup thresholds), `repos.yml` (registered downstream projects), `urls.yml` and `topics.yml` (internet scanning sources).

### Stack Prefix Convention

Stack-specific patterns use filename prefixes instead of separate directories:

| Stack | Prefix | Examples |
|-------|--------|---------|
| FastAPI + Python | `fastapi-` | `fastapi-api-tester.md`, `fastapi-db-migrate/` |
| Android + Compose | `android-` | `android-compose.md`, `android-run-tests/` |
| AI / Gemini | `ai-gemini-` | `ai-gemini-api/` |
| Firebase Auth | `firebase-` | `firebase-auth.md` (rule placeholder) |
| React + Next.js | `react-` | `react-nextjs.md` (rule placeholder) |
| Superpowers | `superpowers-` | `superpowers.md` (rule placeholder) |

The bootstrap script filters by these prefixes when copying patterns to a target project.

### Sync Flows (5 total, defined in `docs/SYNC-ARCHITECTURE.md`)

1. **Project → Hub**: `scripts/collate.py` extracts patterns from registered repos, deduplicates, creates PRs.
2. **Internet → Hub**: `scripts/scan_web.py` discovers patterns from URLs/topics with 3-level dedup.
3. **Hub → Local**: `/update-practices` skill compares local `.claude/` against registry, copies updates.
4. **Hub → Registered Projects**: `scripts/sync_to_projects.py` creates per-project PRs on hub changes.
5. **Local → Hub**: `/contribute-practice` skill validates and submits local patterns as hub PRs.

### Scripts (`scripts/`)

All Python. Key modules:
- `bootstrap.py` — Copies `core/.claude/` patterns to target project, filtering by stack prefix.
- `collate.py` — Extracts patterns from downstream project repos.
- `dedup_check.py` — 3-level deduplication (SHA256 hash, structural similarity, semantic comparison).
- `generate_docs.py` — Renders `docs/DASHBOARD.md`, `docs/STACK-CATALOG.md`, and `docs/dashboard.html` from registry data.
- `sync_to_local.py` / `sync_to_projects.py` — Sync implementations for flows 3 and 4.
- `check_freshness.py` — Flags patterns that haven't been updated within configured staleness thresholds.

### GitHub Actions (`.github/workflows/`)

Seven workflows: `test.yml` (CI on script changes), `scan-projects.yml` / `scan-internet.yml` (weekly scans), `validate-pr.yml`, `update-docs.yml`, `sync-to-projects.yml`, `expire-sources.yml`.

## Key Conventions

- Scripts use `PYTHONPATH=.` when run from the repo root (needed for cross-module imports).
- Pattern dedup thresholds are configured in `config/settings.yml`: strong semantic ≥85, weak ≥70, structural ≥3 shared fields.
- The `registry/patterns.json` must stay in sync with actual files — `generate_docs.py` reads it to produce dashboards.
- Stack-specific patterns are identified by filename prefix (e.g., `fastapi-backend.md` belongs to the `fastapi-python` stack).
