# Implementation Plan: SSOT Workflow Audit & Auto-Assignment

**Created:** 2026-03-28
**Spec:** docs/specs/ssot-workflow-audit-spec.md
**Estimated total time:** ~23m (with 20% buffer)
**Critical path:** Task 1 → Task 2 → Task 4 → Task 6

## Atomic Plan 1: Assignment Script (Core Engine)

- [x] **Task 1:** Create `scripts/assign_workflow_groups.py` with scoring algorithm
  - Files: `scripts/assign_workflow_groups.py` (create)
  - Verify: `PYTHONPATH=. python scripts/assign_workflow_groups.py --dry-run`
  - Time: ~9m
  - Depends on: None

- [x] **Task 2:** Write tests for `assign_workflow_groups.py`
  - Files: `scripts/tests/test_assign_workflow_groups.py` (create)
  - Verify: `PYTHONPATH=. python -m pytest scripts/tests/test_assign_workflow_groups.py -v`
  - Time: ~5m
  - Depends on: Task 1

## Atomic Plan 2: Skill Rename + Creation

- [x] **Task 3:** Delete `.claude/skills/ssot-audit/` and create `.claude/skills/ssot-workflow-audit/SKILL.md`
  - Files: `.claude/skills/ssot-audit/` (delete), `.claude/skills/ssot-workflow-audit/SKILL.md` (create)
  - Verify: skill file exists, old dir deleted
  - Time: ~5m
  - Depends on: None (parallel)

## Atomic Plan 3: Integration Glue

- [x] **Task 4:** Modify `generate_workflow_docs.py` to call assignment script before generation
  - Files: `scripts/generate_workflow_docs.py` (modify)
  - Verify: `PYTHONPATH=. python scripts/generate_workflow_docs.py --dry-run`
  - Time: ~2m
  - Depends on: Task 1

- [x] **Task 5:** Add bot-commit filter to `.github/workflows/update-docs.yml`
  - Files: `.github/workflows/update-docs.yml` (modify)
  - Verify: grep for `github-actions[bot]`
  - Time: ~1m
  - Depends on: None (parallel)

- [x] **Task 6:** Run assignment script end-to-end and regenerate docs
  - Files: `config/workflow-groups.yml` (auto-modified), `docs/workflows/*.md` (regenerated)
  - Verify: orphan count in INDEX.md near zero
  - Time: ~3m
  - Depends on: Tasks 1, 4
