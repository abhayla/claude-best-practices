# Skill Evaluator — Batch Evaluation Workflow

How to evaluate and fix all core skills using a test downstream project.

## Prerequisites

- Test downstream project created and provisioned (multi-stack: FastAPI + React + Android)
- Skills provisioned via: `recommend.py --provision --local <test-project-path>`
- Skills live in `<test-project>/.claude/skills/` — this is the only skill location for evaluation

## Workflow (per skill)

### Step 0: Registry Sync

Check if registry description in `registry/patterns.json` matches the file description in `core/.claude/skills/<skill>/SKILL.md`. Fix registry if out of sync.

### Step 1: Run Evaluator

Run `/skill-evaluator full` **inside the test project**.
- Evaluator uses: `<test-project>/.claude/skills/skill-evaluator/SKILL.md`
- Evaluates: `<test-project>/.claude/skills/<skill>/SKILL.md`

### Step 2: Fix Skill

Fix the skill in `<test-project>/.claude/skills/<skill>/SKILL.md`.
Re-run evaluator to verify fix passes.

### Step 3: Sync Back to Hub

Copy fixed skill from test project to hub's `core/.claude/skills/<skill>/`.
Update registry: hash, version, description, dependencies.

### Step 4: Record Learnings

Append to `EVAL-LEARNINGS.md` (kept in both test project and hub `core/`):
- What evaluator caught
- What evaluator missed (found manually)
- Proposed evaluator improvements (pending batch apply)
- Fixes applied to the skill

### Step 5: Commit

Commit hub changes: `core/` fix + registry update + learnings entry.

### Step 6: Report

3-line summary:
- **Skill fixed:** what changed
- **Registry fixed:** what synced
- **Evaluator learned:** what was missed (logged, not applied)

### Step 7: Next Skill

Pick next skill, repeat from Step 0.

## Checkpoints

**After every 5 skills:**
- Re-provision all to test project (picks up cumulative fixes)
- Regression check: re-run evaluator on last 5 fixed skills
- Progress checkpoint with cumulative stats

**After all skills (or enough evidence):**
- Review `EVAL-LEARNINGS.md` as a batch
- Apply accumulated improvements to `skill-evaluator/SKILL.md` in one deliberate update
- Re-provision evaluator to test project
- Verify against 3 already-fixed skills to confirm no regression

## Rules

- All evaluation happens in the **test project's** `.claude/skills/` — never in `core/`
- All fixes start in the **test project**, sync back to hub's `core/` after passing
- `EVAL-LEARNINGS.md` lives in both places, kept in sync
- Evaluator SKILL.md stays **frozen** during evaluation — learnings accumulate, batch-applied at the end
- Ask user only if a fix would fundamentally change a skill's purpose or remove functionality

## Flow Direction

```
Hub core/.claude/skills/ → provision → Test project .claude/skills/
                                              ↓
                                        Evaluate + Fix
                                              ↓
Test project .claude/skills/ → sync back → Hub core/.claude/skills/
```

## Stopping Criteria

- Evaluator goes 3 consecutive skills without new learnings → evaluator is stable
- All skills evaluated or time budget exhausted → batch-update evaluator
