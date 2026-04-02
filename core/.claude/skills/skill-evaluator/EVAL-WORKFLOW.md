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
- Verify: reference files are one level deep from SKILL.md (no chained references)
- Verify: reference files >100 lines have a table of contents at the top

**Frontmatter platform compliance:**
- `name`: max 64 chars, lowercase/numbers/hyphens only, no reserved words (`anthropic`, `claude`)
- `description`: must be third-person ("Processes..." not "I process..."), max 1024 chars
- Check for time-sensitive content ("before August 2025") — flag for removal
- Check for consistent terminology within the skill (no mixed terms for same concept)

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

## CRITICAL RULES — No Exceptions

1. **Every step is mandatory.** Steps 0, 0.5, 1, 2, 2.5, 3, 4, 5, 6 MUST ALL execute for EVERY skill. There are NO shortcuts, NO "registry-only fixes", NO "this skill looks good so I'll skip evaluation". If a step finds nothing wrong, record that explicitly — "Step 0.5: No near-duplicates found" is a valid outcome. Skipping the step is not.

2. **Step 1 MUST use a subagent.** The evaluator MUST run in a clean subagent context against the test project. Reading the SKILL.md and making a judgment without running the evaluator is NOT Step 1 — it's skipping Step 1.

3. **Step 0.5 MUST compare against neighbors.** Every skill has 2-3 nearest neighbors. Identify them, compare descriptions, and verify the boundary is clear. "No near-duplicate concern" requires evidence (which neighbors were checked and why they're different).

4. **Triggers MUST be tested, not guessed.** Adding triggers without running them against the 20-query eval set (Step 2 via evaluator) means untested triggers that may conflict with other skills. Triggers added without evaluation are technical debt, not fixes.

5. **No batch shortcuts for SKILL.md changes.** Registry metadata (hashes, descriptions, tags) MAY be batch-fixed via script because they don't change behavior. But any change to a SKILL.md file (triggers, preamble, CRITICAL RULES, steps) MUST go through the full per-skill evaluation workflow.

6. **Speed is not a metric.** The workflow measures quality (issues found, evaluator improvements, trigger accuracy), not throughput (skills per hour). A thorough evaluation of 3 skills is more valuable than a rushed pass over 15.

7. **Record what you checked, not just what you fixed.** EVAL-LEARNINGS entries MUST list what each step found — including "nothing" results. If Step 0.5 found no near-duplicates, say which neighbors were compared. If Step 1 found no trigger issues, say how many queries were tested. Absence of findings is data; absence of checking is a gap.

8. **Minimum time per skill: read the full SKILL.md.** If a skill has 200+ lines and references/ files, evaluation cannot take 30 seconds. Read the full content, understand the workflow, then evaluate. Frontmatter-only evaluation is NOT evaluation.

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
