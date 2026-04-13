# Implementation Plan: Self-Updating References for Skills

**Created:** 2026-04-13
**Spec:** `docs/specs/self-updating-references-spec.md`
**Estimated total time:** ~23m (with 20% buffer)
**Critical path:** Task 1 → 2 → 3 → 4 → 5 → 11 → 12

## Atomic Plan 1: Protocol File
- [x] **Task 1:** Create `references/self-update-protocol.md` (~120 lines)

## Atomic Plan 2: Writing-Skills Updates
- [x] **Task 2:** Replace Step 2.6 with protocol pointer
- [x] **Task 3:** Update Step 5.1 quality checklist
- [x] **Task 4:** Replace MUST DO / MUST NOT DO self-update items
- [x] **Task 5:** Bump version 3.1.0 → 3.2.0

## Atomic Plan 3: Skill-Evaluator Updates
- [x] **Task 6:** Replace Step 0.4 pre-flight (10 checks)
- [x] **Task 7:** Replace Step 3.4b output eval (5 tests A–E)
- [x] **Task 8:** Update evaluation report template
- [x] **Task 9:** Update MUST DO
- [x] **Task 10:** Bump version 2.2.0 → 2.3.0

## Atomic Plan 4: Sync & Verify
- [x] **Task 11:** Sync to core/.claude/
- [x] **Task 12:** Run CI validation
