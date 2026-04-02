# Skill Evaluator — Batch Evaluation Workflow

How to evaluate and fix all core skills using a test downstream project.
Each skill is audited through two complementary lenses:

- **Structural quality** (Step 1) — Is the skill well-constructed? Checks authoring
  standards, failure mode preventions, content quality, security indicators.
- **Behavioral testing** (Step 2) — Does the skill work in practice? Checks trigger
  accuracy, output quality, stress resilience, cross-skill conflicts.

Structural issues are root causes of behavioral failures. Fixing them first
means fewer behavioral failures downstream.

## Prerequisites

- Test downstream project created and provisioned (multi-stack: FastAPI + React + Android)
- Skills provisioned via: `recommend.py --provision --local <test-project-path> --tier nice-to-have`
- Latest writing-skills and skill-evaluator copied to test project
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

### Step 1: Structural Quality Audit

Run the writing-skills quality checklist (Step 5) against the skill. This
catches authoring issues that cause behavioral failures downstream.

**1a. Structure validation:**

| Check | Pass Criteria |
|-------|---------------|
| YAML frontmatter valid | All required fields present, YAML parses without error |
| `name` matches directory name | `name: foo-bar` lives in `skills/foo-bar/SKILL.md` |
| `description` starts with a verb | "Debug...", "Generate...", "Analyze..." |
| `type` declared | `workflow` or `reference` |
| `version` is valid SemVer | Format: `"1.0.0"` |
| `triggers` has 3-6 entries | Mix of slash commands and natural language |
| `allowed-tools` is minimal | No unused tools. Read-only skills MUST NOT include `Write`, `Edit`, or `Bash` |
| No high-risk indicators without justification | Scripts, MCP refs, network access documented and necessary |

**1b. Content validation:**

| Check | Pass Criteria |
|-------|---------------|
| Steps are numbered sequentially | STEP 1, STEP 2, STEP 3... |
| Each step starts with a verb | "Analyze", "Run", "Create" — not "Analysis", "Running" |
| Steps have concrete actions | Commands, file paths, or specific instructions — not "consider" or "think about" |
| Conditional logic uses tables | No nested if/else bullet points |
| Output format is templated | Expected outputs shown in code blocks |
| MUST DO section has 4-8 items | Each has `— Why:` explaining consequence of skipping |
| MUST NOT DO section has 4-8 items | Each states what to do instead |
| No vague language | No "consider", "maybe", "try to", "think about" |
| No Windows-style paths | All file paths use forward slashes |
| No time-sensitive content | No date-dependent logic; use "Old patterns" collapsible section |

**1c. Structural health:**

| Check | Pass Criteria |
|-------|---------------|
| SKILL.md body under 500 lines | 500-1000 = warning, >1000 = must split |
| Reference files one level deep | No SKILL.md → ref1.md → ref2.md chains |
| Reference files >100 lines have TOC | Table of contents at top |
| Failure mode analysis present | At least 3 failure modes identified with mapped preventions |
| Output format locked | Structured output skills have code block template |

**1d. Record findings:**

Log all pass/fail results. Even "all pass" is a finding — record it
explicitly. If structural issues are found, they feed into Step 3 (Fix).

### Step 2: Behavioral Evaluation

Run `/skill-evaluator full` **inside the test project** in a clean subagent.
- Evaluator uses: `<test-project>/.claude/skills/skill-evaluator/SKILL.md`
- Evaluates: `<test-project>/.claude/skills/<skill>/SKILL.md`

This tests trigger accuracy, output quality, stress resilience, and
cross-skill conflicts. See skill-evaluator SKILL.md for the full
evaluation methodology (Steps 0-7).

### Step 3: Fix Skill

Fix ALL issues from both lenses in `<test-project>/.claude/skills/<skill>/SKILL.md`:
- Structural issues from Step 1 (vague steps, missing failure modes, etc.)
- Behavioral issues from Step 2 (trigger failures, output problems, etc.)

Fix structural issues first — they often resolve behavioral issues.

### Step 3.5: Re-Evaluate (MANDATORY gate)

Re-run BOTH evaluations against the fixed version:

1. **Structural re-check:** Verify all Step 1 failures now pass
2. **Behavioral re-eval:** Re-run `/skill-evaluator full` on the fixed skill

Re-provision the fixed skill if needed:
```bash
cp <hub>/core/.claude/skills/<skill>/SKILL.md <test-project>/.claude/skills/<skill>/SKILL.md
```

This step is NOT optional — do not proceed to Step 4 until both lenses pass.
If re-evaluation surfaces new issues, return to Step 3.

### Step 4: Sync Back to Hub

Copy fixed skill from test project to hub's `core/.claude/skills/<skill>/`.
Update registry: hash, version, description, dependencies.

Only sync after Step 3.5 passes. The re-evaluation is the gate.

### Step 5: Record Learnings

Append to `EVAL-LEARNINGS.md` (kept in both test project and hub `core/`):
- What structural audit caught (Step 1)
- What behavioral evaluator caught (Step 2)
- What was missed by both (found manually)
- Proposed evaluator/checklist improvements (pending batch apply)
- Fixes applied to the skill

### Step 6: Commit

Commit hub changes: `core/` fix + registry update + learnings entry.

### Step 7: Report

4-line summary:
- **Structural:** what the quality audit found
- **Behavioral:** what the evaluator found
- **Skill fixed:** what changed
- **Learned:** what was missed (logged, not applied)

### Step 8: Next Skill (AUTO)

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
- If structural audit caught patterns the evaluator missed, propose additions to evaluator pre-flight checks
- Re-provision evaluator to test project
- Verify against 3 already-fixed skills to confirm no regression

## Rules

- All evaluation happens in the **test project's** `.claude/skills/` — never in `core/`
- All fixes start in the **test project**, sync back to hub's `core/` after passing
- `EVAL-LEARNINGS.md` lives in both places, kept in sync
- Evaluator SKILL.md stays **frozen** during evaluation — learnings accumulate, batch-applied at the end
- Ask user only if a fix would fundamentally change a skill's purpose or remove functionality

## CRITICAL RULES — No Exceptions

1. **Every step is mandatory.** Steps 0, 0.5, 1, 2, 3, 3.5, 4, 5, 6, 7 MUST ALL execute for EVERY skill. There are NO shortcuts, NO "registry-only fixes", NO "this skill looks good so I'll skip evaluation". If a step finds nothing wrong, record that explicitly — "Step 1: All structural checks pass" is a valid outcome. Skipping the step is not.

2. **Step 2 MUST use a subagent.** The behavioral evaluator MUST run in a clean subagent context against the test project. Reading the SKILL.md and making a judgment without running the evaluator is NOT Step 2 — it's skipping Step 2.

3. **Step 1 MUST check all tables.** Every row in the structural audit tables (1a, 1b, 1c) must be checked against the skill. Recording "looks fine" without checking each row is not an audit.

4. **Step 0.5 MUST compare against neighbors.** Every skill has 2-3 nearest neighbors. Identify them, compare descriptions, and verify the boundary is clear. "No near-duplicate concern" requires evidence (which neighbors were checked and why they're different).

5. **Triggers MUST be tested, not guessed.** Adding triggers without running them against the 20-query eval set (Step 2 via evaluator) means untested triggers that may conflict with other skills. Triggers added without evaluation are technical debt, not fixes.

6. **No batch shortcuts for SKILL.md changes.** Registry metadata (hashes, descriptions, tags) MAY be batch-fixed via script because they don't change behavior. But any change to a SKILL.md file (triggers, preamble, CRITICAL RULES, steps) MUST go through the full per-skill evaluation workflow.

7. **Speed is not a metric.** The workflow measures quality (issues found, evaluator improvements, trigger accuracy), not throughput (skills per hour). A thorough evaluation of 3 skills is more valuable than a rushed pass over 15.

8. **Record what you checked, not just what you fixed.** EVAL-LEARNINGS entries MUST list what each step found — including "nothing" results. If Step 0.5 found no near-duplicates, say which neighbors were compared. If Step 1 found no structural issues, list which checks passed. Absence of findings is data; absence of checking is a gap.

9. **Minimum time per skill: read the full SKILL.md.** If a skill has 200+ lines and references/ files, evaluation cannot take 30 seconds. Read the full content, understand the workflow, then evaluate. Frontmatter-only evaluation is NOT evaluation.

10. **Fix structural before behavioral.** When both lenses find issues, fix Step 1 findings first. Structural issues (vague steps, missing preventions) are root causes of behavioral failures (poor output, missed edge cases). Fixing structure often resolves behavior.

## Flow Direction

```
Hub core/.claude/skills/ → provision → Test project .claude/skills/
                                              ↓
                                    Step 1: Structural audit
                                              ↓
                                    Step 2: Behavioral eval
                                              ↓
                                    Step 3: Fix (structure first)
                                              ↓
                                    Step 3.5: Re-evaluate both
                                              ↓
Test project .claude/skills/ → sync back → Hub core/.claude/skills/
```

## Stopping Criteria

- Evaluator goes 3 consecutive skills without new learnings → evaluator is stable
- All skills evaluated or time budget exhausted → batch-update evaluator
- If structural audit consistently catches issues the behavioral eval misses → propose adding those checks to skill-evaluator pre-flight (Step 0)
