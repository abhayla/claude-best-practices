# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical: Two `.claude/` Directories

- **`core/.claude/`** — Distributable template (what users copy to their projects). NEVER put hub-only config here.
- **`.claude/`** (repo root) — Hub-only operational config: scan skills (`scan-repo`, `scan-url`), `synthesize-hub`, hub rules, hub-only agents (`code-reviewer-agent`, `planner-researcher-agent`, etc.), and hooks (`auto-learn-trigger.sh`, `pattern-quality-gate.sh`, `prompt-enhance-reminder.sh`). NEVER distribute this.

## Environment

- **Python 3.12** required (all CI workflows use 3.12)
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt`
- **Windows**: activate with `.venv\Scripts\activate`, use `set PYTHONPATH=. &&` prefix instead of `PYTHONPATH=.` for all commands below, or use Git Bash where Unix syntax works

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
- **`core/.claude/`** — All distributable patterns: `agents/`, `skills/` (each with `SKILL.md`), `rules/`, `hooks/`, `config/` (runtime pipeline configs), templates (`CLAUDE.md.template`, `CLAUDE.local.md.template`)
- **`registry/patterns.json`** — Machine-readable index of all patterns. Manually maintained — edit directly after adding/removing patterns, then re-run `generate_docs.py`
- **`config/`** — `settings.yml` (dedup thresholds, scan limits), `repos.yml` (downstream projects), `workflow-groups.yml` (seed patterns for workflow doc generation — stale seeds silently break docs), `pipeline-stages.yaml` (DAG config for project-manager agent), `workflow-contracts.yaml` (per-workflow step DAGs, artifact contracts, gate expressions — read by workflow-master agents), `discoveries.json` (accumulated scan findings), plus `urls.yml`, `topics.yml`, `third-party-skills.yml`, `test-pipeline.yml`
- **`docs/stages/`** — Pipeline stage definitions (STAGE-0 through STAGE-11) with executable `Skill()`/`Agent()` dispatch examples
- **`docs/workflows/`** — Auto-generated workflow docs (output of `generate_workflow_docs.py`). Do not edit manually — regenerate after pattern changes
- **`scripts/`** — All Python tooling (see Key Scripts below for the important ones)

### Stack Prefix Convention

Two pattern detection mechanisms: (1) **Stack prefixes** in `STACK_PREFIXES` (`bootstrap.py`) — `fastapi-*`, `android-*`, `react-*`, `firebase-*`, `ai-gemini-*` — selected via `--stacks` flag. (2) **Dependency detection** via `DEP_PATTERN_MAP` (`recommend.py`) — matches `flutter-*`, `vue-*`, `bun-elysia-*`, `tailwind-*`, `vitest-*`, `prisma-*`, etc. from project dependencies. Universal patterns have no prefix.

### Sync Flows

Six sync directions exist — see `docs/SYNC-ARCHITECTURE.md` for details. Key entry points: `collate.py` (project→hub), `scan_web.py` (internet→hub), `sync_to_projects.py` (hub→projects), `recommend.py` (hub→project advisory).

### Key Scripts

- **`recommend.py`** — Main provisioning entry point. Modes: `--local`/`--repo`, `--apply`, `--provision`, `--diff`, `--use-config`. Additional flags: `--tier {must-have,nice-to-have}`, `--json`, `--multi-pr`/`--single-pr`, `--skip-third-party`. Defines `STACK_DETECTORS` and `DEP_PATTERN_MAP`.
- **`bootstrap.py`** — Core copy logic. Standalone CLI: `python scripts/bootstrap.py --stacks <stack1,stack2> --target <dir> [--hub <path>] [--dry-run]`. Defines `STACK_PREFIXES` mapping. Also imported by `recommend.py`.
- **`workflow_quality_gate_validate_patterns.py`** — CI validator for frontmatter, cross-references, file/registry sync.
- **`dedup_check.py`** — CI dedup validator (`--validate-all`) and secret scanner (`--secret-scan`).
- **`generate_docs.py`** / **`generate_workflow_docs.py`** — Rebuild `docs/` dashboard and workflow docs respectively.
- **`extract_references.py`** — Splits oversized SKILL.md files into `references/` subdirectories: `python scripts/extract_references.py [--threshold 500] [--skill SKILL_NAME]`
- **`third_party_skills.py`** — Detects third-party skills from project dependencies and recommends install commands.
- **`check_freshness.py`** — Checks source freshness for internet-sourced patterns.
- **`sync_to_local.py`** — Syncs hub patterns to local projects.
- **`discovery_adapter.py`** — Adapts discovery results from scans into normalized format.
- **`sync_to_projects.py`** — Pushes hub patterns to downstream repos in `config/repos.yml` (hub→projects sync direction). Includes telemetry functions for provision manifests and adoption scanning.
- **`aggregate_telemetry.py`** — Aggregates pattern effectiveness telemetry from enrolled projects. Computes adoption rates, retention, and error prevention rates. Writes effectiveness data to `registry/patterns.json`.
- **`collate.py`** — Extracts reusable patterns from project repositories (project→hub sync direction).
- **`scan_web.py`** — Scans internet sources for Claude Code best practices (internet→hub sync direction).
- **`assign_workflow_groups.py`** — Auto-assigns orphan `core/` patterns to workflow groups in `config/workflow-groups.yml`. Called automatically by `generate_workflow_docs.py`.

### CI Workflows

- **`validate-pr.yml`** — Runs all 4 validation commands listed above on PRs.
- **`update-docs.yml`** — Auto-regenerates and commits `docs/` when registry or `core/.claude/` changes on main. Avoid running `generate_docs.py` manually on main — this workflow handles it.
- **`test.yml`** — Runs pytest on `scripts/**` changes.
- **`recommend.yml`** — Weekly cron + manual: runs `recommend.py --provision` for repos in `config/repos.yml`.
- **`apply-selections.yml`** — Applies user-selected pattern recommendations to downstream repos.
- Other scheduled workflows: `scan-internet.yml`, `scan-projects.yml`, `sync-to-projects.yml`, `expire-sources.yml`.

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


<!-- hub:best-practices:start -->

<!-- PROTECTED SECTION — managed by claude-best-practices hub. -->
<!-- Do NOT condense, rewrite, reorganize, or remove.          -->
<!-- Any /init or optimization request must SKIP this section.  -->

## Rules for Claude

1. **Bug Fixing**: Use `/fix-loop` or `/fix-issue`. Start by writing a test that reproduces the bug, then fix and prove with a passing test.

### Rules Reference

| Rule File | What It Covers |
|-----------|---------------|
| `rules/agent-orchestration.md` | Constraints for multi-agent orchestration patterns in agents and skills. |
| `rules/claude-behavior.md` | Universal behavioral rules for how Claude should approach all tasks. |
| `rules/configuration-ssot.md` | Single source of truth for Claude Code configuration — prevents duplication across CLAUDE.md, rules, skills, and settings.json. |
| `rules/context-management.md` | Rules for managing context window, token usage, and documentation references. |
| `rules/fastapi-backend.md` | FastAPI backend development rules and patterns. |
| `rules/fastapi-database.md` | Database and migration rules for FastAPI + SQLAlchemy + Alembic. |
| `rules/firebase.md` | Firebase Auth, Firestore, and backend token verification patterns. |
| `rules/pattern-portability.md` | Portability standards for patterns distributed via core/.claude/. Ensures patterns work in any project without modification. |
| `rules/pattern-self-containment.md` | Self-containment and completeness standards for patterns in core/.claude/. Prevents placeholders, oversized files, and broken dependencies. |
| `rules/pattern-structure.md` | Structural requirements for skills, agents, and rules in core/.claude/. Enforces frontmatter, versioning, type classification, and scope. |
| `rules/prompt-auto-enhance.md` | Prompt Auto Enhance |
| `rules/prompt-auto-enhance-rule.md` | Auto-enhance every user prompt with project-specific context before acting. Prefix every response with a brief *Enhanced: ...* indicator.
 |
| `rules/rule-curation.md` | Guidelines for curating all patterns (skills, agents, rules) added to the distributed core/.claude/ template. |
| `rules/rule-writing-meta.md` | Meta-guidance for writing effective CLAUDE.md rules, choosing config file placement, and structuring project instructions. |
| `rules/tdd-rule.md` | Test-driven development workflow rules for red-green-refactor cycle. |
| `rules/testing.md` | Testing conventions and best practices. |
| `rules/workflow.md` | Development workflow guidelines for structured feature implementation and bug fixes. |
| `rules/workflow-change-verification.md` | Workflow Change Verification |
| `rules/workflow-docs-sync.md` | Workflow Docs Sync |
| `rules/workflow-quality-gate.md` | Workflow Quality Gate |

## Claude Code Configuration

The `core/.claude/` directory contains 152 skills, 37 agents, and 24 rules for Claude Code.

<!-- hub:best-practices:end -->
