# Skill Evaluator — Batch Evaluation Workflow

How to evaluate and fix all core skills using a test downstream project.

## Prerequisites

- Test downstream project created and provisioned (multi-stack: FastAPI + React + Android)
- Skills provisioned via: `recommend.py --provision --local <test-project-path>`
- Skills live in `<test-project>/.claude/skills/` — this is the only skill location for evaluation

## Workflow (per skill)

### Step 0: Registry Sync

Check if registry description in `registry/patterns.json` matches the file description in `core/.claude/skills/<skill>/SKILL.md`. Fix registry if out of sync.

Also check registry field consistency:
- `version` field matches latest `changelog` entry
- `hash` matches actual file hash
- `dependencies` lists all skills/agents referenced in the body

### Step 0.5: Ecosystem Check

Before evaluating the skill in isolation, check how it fits in the system:

**Overlap scan:**
- Search all provisioned skills for overlapping purpose (similar description, shared triggers)
- If a near-duplicate exists (e.g., `debugging-loop` vs `systematic-debugging`), flag it
- Decision: merge, differentiate, or deprecate one

**Description differentiation:**
- Compare description against the 2-3 nearest-neighbor skills
- The description must make the boundary clear — when to use THIS skill vs the neighbor
- If the escalation path between related skills isn't stated, add it (e.g., "Use /fix-loop first; use this when root cause is unclear")

**Reference integrity:**
- Read all `references/*.md` files in the skill directory
- Verify: no orphaned code fences (opening without closing or vice versa)
- Verify: every `**Read:** references/foo.md` directive in SKILL.md has a matching file
- Verify: no content leaks between reference files and SKILL.md (broken code blocks split across extraction boundary)

### Step 1: Run Evaluator

Run `/skill-evaluator full` **inside the test project**.
- Evaluator uses: `<test-project>/.claude/skills/skill-evaluator/SKILL.md`
- Evaluates: `<test-project>/.claude/skills/<skill>/SKILL.md`

### Step 2: Fix Skill

Fix the skill in `<test-project>/.claude/skills/<skill>/SKILL.md`.

### Step 2.5: Re-Evaluate (MANDATORY gate)

Re-provision the fixed skill to the test project (or copy directly if single-skill fix):
```bash
cp <hub>/core/.claude/skills/<skill>/SKILL.md <test-project>/.claude/skills/<skill>/SKILL.md
```

Re-run the evaluator against the fixed version. This step is NOT optional — do not proceed to Step 3 until the re-evaluation passes. If the re-evaluation surfaces new issues, return to Step 2.

### Step 3: Sync Back to Hub

Copy fixed skill from test project to hub's `core/.claude/skills/<skill>/`.
Update registry: hash, version, description, dependencies.

Only sync after Step 2.5 passes. The re-evaluation is the gate.

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

### Step 7: Next Skill (AUTO)

Automatically pick the next skill and repeat from Step 0 without waiting for
user input. Selection priority:

1. **Empty registry description** — highest signal of incomplete metadata
2. **Registry hash mismatch** — file changed but registry not updated
3. **Missing triggers field** — activation reliability gap
4. **High-frequency skills first** — skills in the core testing/dev workflow
   (implement, tdd, code-quality-gate) before niche/stack-specific skills
5. **Near-duplicates** — if flagged during a previous evaluation (e.g.,
   debugging-loop vs systematic-debugging), evaluate next to resolve

Skip skills already evaluated in this batch (check EVAL-LEARNINGS.md headers).
Do NOT pause between skills — proceed immediately after commit.

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
