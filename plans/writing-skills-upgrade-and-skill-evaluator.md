# Implementation Plan: Writing-Skills Upgrade + Skill-Evaluator Creation

**Version:** v7 (Implemented + Cross-Checked Against All 4 URLs)
**Date:** 2026-04-02
**Status:** IMPLEMENTED
**Source:** agentskills.io/skill-creation/best-practices (+ evaluating-skills, optimizing-descriptions, using-scripts)

## Overview

Separate authoring from evaluation at the skill boundary. Upgrade writing-skills with instruction-writing patterns and context budget guidance. Create skill-evaluator as a standalone evaluation skill covering trigger testing, output quality, and cross-skill conflicts. The entire workflow runs autonomously with a single human approval gate before hub promotion.

## File Inventory

| # | File | Action | Est. Lines |
|---|---|---|---|
| 1 | `.claude/skills/writing-skills/SKILL.md` | Edit — 7 insertions, Step 6 rewrite | ~45 added, ~80 moved out |
| 2 | `.claude/skills/writing-skills/references/instruction-writing-patterns.md` | Create | ~220 |
| 3 | `.claude/skills/skill-evaluator/SKILL.md` | Create | ~400 |
| 4 | `.claude/skills/skill-evaluator/references/description-optimization.md` | Create | ~170 |
| 5 | `.claude/skills/skill-evaluator/references/eval-driven-iteration.md` | Create | ~240 |

---

## Autonomous Workflow

```
User: /writing-skills create my-new-skill
         |
         v
  Step 1: Parse mode
  Step 1.1: Auto-generate 3 tasks -> run without skill (subagent)
            All pass -> STOP "skill not needed"
            Gaps found -> capture, proceed
         |
         v
  Steps 2-5: Author skill autonomously
         |
         v
  Step 6.1: Invoke /skill-evaluator full via Agent tool
         |
         v
  +----------------------------------+
  | skill-evaluator runs             |
  | (triggers + output + conflicts)  |
  | Skips human review (delegated)   |
  | Returns verdict + report         |
  +----------+-----------------------+
             |
      +------+------+
      |             |
   PASS          FIX/FAIL
      |             |
      |      Step 6.2: Auto-fix routing
      |        Read report -> map failure type -> apply fix
      |      Step 6.3: Re-invoke skill-evaluator
      |        (max 5 iterations, each different fix)
      |             |
      |      +------+------+
      |      |             |
      |   PASS        Still FIX/FAIL
      |      |             |
      |      |        Loop back
      |      |
      v      v
  Step 6.4: Present to user
    - Final skill draft
    - Eval report (trigger rates, stress score, benchmarks)
    - Iteration history
    - Skill necessity delta
    *** SINGLE HUMAN APPROVAL GATE ***
         |
         v
  Step 7: Hub promotion (if approved)
```

One human touchpoint: approval of final skill + eval report before promotion.
Everything else is autonomous.

---

## FILE 1: `.claude/skills/writing-skills/SKILL.md` -- Edits

### Frontmatter Change

Add `Agent` to allowed-tools:
```yaml
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
```

### Edit A: Rewrite Step 1.1 -- Auto Skill Necessity Check

Insert between Step 1 and Step 2:

```markdown
### 1.1 Skill Necessity Check

Before authoring, verify the skill adds value over the agent's baseline:

1. **Auto-generate 3 representative tasks** from `$ARGUMENTS` -- realistic
   prompts a user would type that fall within the skill's intended scope
2. **Run each task WITHOUT a skill** in a subagent (clean context)
3. **Evaluate results:**

| Result | Action |
|--------|--------|
| Agent handles all 3 well | STOP -- report "skill not needed, agent handles this without assistance" |
| Agent struggles on 1-2 tasks | Capture what went wrong -- these gaps define the skill's value proposition. Proceed |
| Agent fails on all 3 | Strong signal -- proceed with authoring, use failure patterns to drive Step 2.3 (failure mode analysis) |

The gaps captured here feed directly into the skill's instructions --
they are what the agent gets wrong without the skill.
```

### Edit B: Add Context Budget Guidance (after Step 2.2)

```markdown
### 2.2b Context Budget

Every token competes for the agent's attention. Targets:
- **SKILL.md body**: under 500 lines / 5,000 tokens
- **References**: loaded on demand via conditional `**Read:**` pointers

**Include:** Project-specific conventions, domain-specific procedures,
non-obvious edge cases, particular tools/APIs -- things the agent wouldn't
know without the skill.

**Cut:** General knowledge, obvious steps, exhaustive edge case coverage.
Concise stepwise guidance with a working example outperforms exhaustive
documentation. Most edge cases are better handled by the agent's judgment.

**Test:** "Would the agent get this wrong without this instruction?"
If no, cut it. If unsure, test with `/skill-evaluator output`.

**Conditional disclosure:** "Read `references/X.md` if the API returns
a non-200 status" -- not "see references/ for details."
```

### Edit C: Expand Step 3.1 -- Session Extraction + Artifact Synthesis

```markdown
### 3.1 Scan for Repeated Patterns

Review conversation history for multi-step sequences performed 2+ times:
1. **Steps that worked** -- action sequence that led to success
2. **Corrections you made** -- where you steered the agent's approach
3. **Input/output formats** -- data shape going in and coming out
4. **Context you provided** -- project-specific facts the agent didn't know
5. **Repeated tool call sequences** -- same 3+ calls in same order
6. **Repeated file access patterns** -- same files across tasks

### 3.1b Synthesize from Project Artifacts

**Warning:** Do NOT generate a skill from LLM general knowledge alone --
the result is vague procedures ("handle errors appropriately"). Always
ground in project-specific material:

- Internal documentation, runbooks, and style guides
- API specifications, schemas, and configuration files
- Code review comments and issue trackers
- Version control history, especially patches and fixes
- Real-world failure cases and their resolutions
```

### Edit D: Add Instruction-Writing-Patterns Pointer (Step 2.5 area)

Insert after step anatomy section:

```markdown
#### Instruction Writing Patterns

Eight patterns improve instruction quality within steps.

**Read:** `references/instruction-writing-patterns.md` for calibrating
control, gotchas sections, validation loops, plan-validate-execute,
defaults over menus, procedures over declarations, script design for
agentic use, and checklists for progress tracking.
```

### Edit E: Add Too-Narrow Row to Step 4.2 Table

```markdown
| Skills scoped too narrowly for one task | Broaden -- multiple narrow skills loading together risks overhead and conflicting instructions |
```

### Edit F: Rewrite Step 6 -- Fully Autonomous Evaluate-Fix Loop

Replace current Steps 6.1, 6.3, 6.4 with:

```markdown
## STEP 6: Evaluate and Iterate with /skill-evaluator

Invoke `/skill-evaluator` via the Agent tool. The entire evaluate -> fix ->
re-evaluate loop runs autonomously with one human approval at the end.

**Before formal eval:** Run the skill informally against one real task.
Read the execution trace (not just output). Fix obvious issues first.

### 6.1 Invoke Evaluation

For new skills:

  Agent(subagent_type="general-purpose",
    prompt="/skill-evaluator full <skill-path>")

For updated skills:

  Agent(subagent_type="general-purpose",
    prompt="/skill-evaluator full <skill-path> --baseline")

### 6.2 Auto-Fix Routing

When skill-evaluator returns FIX or FAIL, read the report and apply
the fix mapped to each failure type:

| Eval Failure Type | Automated Fix |
|---|---|
| Should-trigger queries failing (<80%) | Broaden description: add user-intent phrases, expand scope |
| Should-not-trigger queries firing (>20%) | Narrow description: add boundary ("do NOT use when...") |
| Cross-skill conflict | Make triggers more specific, add distinguishing context |
| Trigger regression (--baseline) | Restore key phrases from old description |
| Scenario assertion failures | Add/clarify the step that produces the failing output |
| Stress test CRITICAL | Add guardrail to MUST DO, embed prevention in earliest step |
| Stress test MAJOR | Add edge case handling to relevant step's decision table |
| Stress score <90% overall | Re-run failure mode analysis (Step 2.3), add preventions |
| Skill adds no value over baseline | STOP -- report to user: "skill not needed" |

### 6.3 Iterate Until PASS

1. Apply fix from routing table
2. Re-invoke `/skill-evaluator full <skill-path>`
3. Read new verdict
4. If FIX/FAIL: apply next fix, re-invoke (each iteration MUST try a different fix)
5. If PASS: proceed to 6.4

**Max 5 iterations.** After 5 without PASS: STOP, present full iteration
history (what was tried, what failed, what's blocking), user decides.

### 6.4 Present for Approval

Present to user:
- Final skill draft
- Evaluation report (trigger rates, stress score, benchmarks)
- Iteration history (if any fixes were applied)
- Skill necessity delta (with-skill vs without-skill improvement)

**Wait for user approval before proceeding to Step 7.**
This is the single human touchpoint in the entire workflow.

### 6.5 Failure Prevention Map
(existing Step 6.5 content, renumbered)

### 6.6 Domain Pattern Review
(existing Step 6.7 content, renumbered)
```

### Edit G: Update MUST DO / MUST NOT DO

Add to MUST DO:
```markdown
- Always invoke `/skill-evaluator` via Agent tool for evaluation -- do not evaluate inline
- Always apply auto-fix routing for FIX/FAIL verdicts -- do not ask user what to fix
- Always present final skill + eval report for user approval before hub promotion
```

Add to MUST NOT DO:
```markdown
- MUST NOT ask user to manually invoke `/skill-evaluator` -- invoke it autonomously via Agent tool
- MUST NOT proceed to Step 7 without user approval of the final skill + eval report
```

---

## FILE 2: `references/instruction-writing-patterns.md` -- Create (~220 lines)

Eight patterns, each with: when to use, concise explanation, one working example.

### 1. Calibrating Control

Match specificity to fragility. Freedom when flexible (explain WHY),
prescriptive when fragile (exact commands). Calibrate each part independently.

Example: code review (flexible, describe what to look for) vs database
migration (prescriptive, exact command sequence, do not modify).

### 2. Gotchas Sections

Environment-specific facts that defy assumptions. Keep in SKILL.md where
agent reads BEFORE encountering the situation. Add corrections iteratively
when agent makes mistakes.

Example: soft deletes requiring WHERE deleted_at IS NULL, inconsistent
field naming across services (user_id vs uid vs accountId).

### 3. Validation Loops

do -> validate -> fix -> repeat. Validator can be: script, test suite,
linter, or reference document to check work against.

Example: edit -> python scripts/validate.py -> fix issues -> re-validate
-> proceed only when validation passes.

### 4. Plan-Validate-Execute

For batch/destructive ops: create plan -> validate against source of truth
-> execute. Key: validation step with actionable error messages.

Example: extract form fields -> create field mapping -> validate mapping
against form fields -> fill form only after validation passes.

### 5. Defaults Over Menus

Pick one default, mention alternatives briefly. Don't present equal options.

Example: "Use pdfplumber. For scanned PDFs, fall back to pdf2image."
NOT: "You can use pypdf, pdfplumber, PyMuPDF, or pdf2image..."

### 6. Procedures Over Declarations

Teach HOW to approach a class of problems, not WHAT to produce for one case.
Approach generalizes; specific details (templates, constraints) are fine.

Example: "Read schema, join on _id convention, apply filters, aggregate"
NOT: "Join orders to customers on customer_id, filter region = 'EMEA'"

### 7. Bundling and Designing Scripts

**When to bundle:** Agent reinvents same logic across runs.
**Don't bundle:** One-off logic; use version-pinned commands instead. When a one-off grows complex (hard to get right on first try), move to scripts/.
**State prerequisites:** "Requires Node.js 18+" in SKILL.md. Use `compatibility` frontmatter for runtime requirements.

**Agentic script design (10-row table):**

| Principle | Why |
|---|---|
| No interactive prompts | Agents hang on TTY input -- accept via flags/env/stdin |
| --help with examples | Primary way agent learns interface |
| Helpful error messages | Say what went wrong, expected, and what to try |
| Structured output (JSON/CSV) | Data to stdout, diagnostics to stderr |
| Idempotent operations | Agents retry -- "create if not exists" |
| Safe defaults | --confirm/--force for destructive ops |
| Dry-run support | Preview before committing |
| Meaningful exit codes | Distinct codes, documented in --help |
| Predictable output size | Default summary, --offset for pagination |
| Input constraints | Reject ambiguous input with clear error; use enums and closed sets |

**Referencing scripts:** Relative paths from skill directory root. List available scripts + show bash commands in SKILL.md. Same convention works in references/*.md files.
**Self-contained scripts:** PEP 723 (Python + uv), Deno npm: imports, Bun auto-install, Ruby bundler/inline -- declare deps inline, no manifest needed.

Short templates inline; longer templates in assets/ or references/ with conditional loading.

### 8. Checklists for Progress Tracking

Explicit progress checklist for 4+ sequential steps with dependencies.

```markdown
Progress:
- [ ] Step 1: Analyze input (run scripts/analyze.py)
- [ ] Step 2: Create mapping (edit config.json)
- [ ] Step 3: Validate mapping (run scripts/validate.py)
- [ ] Step 4: Execute (run scripts/execute.py)
- [ ] Step 5: Verify output (run scripts/verify.py)
```

---

## FILE 3: `.claude/skills/skill-evaluator/SKILL.md` -- Create (~400 lines)

### Frontmatter

```yaml
---
name: skill-evaluator
description: >
  Evaluate Claude Code skills for trigger reliability, output quality, and
  cross-skill conflicts. Use when testing a new or updated skill before
  promotion, auditing existing skills for trigger conflicts, or verifying
  a skill adds value over the agent's baseline. Invoked automatically by
  /writing-skills during authoring, or standalone for auditing existing skills.
triggers:
  - skill-evaluator
  - evaluate skill
  - test skill triggers
  - test skill quality
  - skill evaluation
  - audit skill
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<trigger|output|full|conflicts> <skill-path> [--baseline]"
type: workflow
version: "1.0.0"
---
```

### Steps

```
STEP 1: Parse Mode and Load Skill
  - Modes: trigger | output | full | conflicts
  - Load SKILL.md, extract metadata
  - If --baseline: snapshot current version
  - Detect invocation context:
    - Standalone: include human review (Step 5)
    - Delegated from writing-skills: skip human review, return verdict directly

STEP 2: Trigger Evaluation (modes: trigger, full)
  2.1 Generate 20 eval queries (10 should-trigger + 10 should-not-trigger)
      Should-trigger: varied phrasing, explicitness, detail, complexity
      Should-not-trigger: near-misses sharing keywords
      Read: references/description-optimization.md
  2.2 Test activation
      - 3 runs per query, clean context (subagent)
      - Compute trigger rate per query
      - Should-trigger threshold: >=80%
      - Should-not-trigger threshold: <=20%
      - Note: agents may not consult skills for simple tasks -- expected
  2.3 Cross-skill conflict check
      - All installed skills active
      - Verify target skill activates, not competitor
      - Report: competing skill name + conflicting query
  2.4 Trigger regression (--baseline only)
      - Old should-trigger queries against new description
      - No regressions allowed
  2.5 Description optimization loop (if verdict is FIX)
      - Identify failing queries, revise description
      - Generalize from categories, don't add specific keywords
      - If stuck after 3 incremental tweaks, try structurally different framing
      - After optimization: 5 fresh queries never seen in eval set
      - Verify description under 1024 characters

STEP 3: Output Evaluation (modes: output, full)
  3.1 Skill necessity baseline
      - 3 representative prompts without skill vs with skill
      - Flag if no meaningful improvement
  3.2 Design or load test cases
      - If evals/evals.json exists: load it
      - Otherwise: generate 5 (3 happy-path + 2 edge-case)
      - Start with 2-3; expand after first results
  3.3 Run scenarios
      - Clean context per run (subagent isolation)
      - With-skill + without-skill (or old version for --baseline)
      - Capture outputs + timing (tokens, duration)
  3.4 Stress test
      - 10 adversarial inputs from categories:
        ambiguous, off-topic, conflicting, oversized, empty,
        partial prerequisite, repeated, malformed, stale, adversarial phrasing
      - Score: CRITICAL / MAJOR / MINOR / PASS
  3.5 Write and grade assertions
      - Write after first run
      - Grade PASS/FAIL with specific evidence
      - Review assertions themselves: too easy? too hard? unverifiable?
  3.6 Aggregate benchmarks
      - Per config: pass_rate (mean, stddev), time, tokens
      - Delta vs baseline
  3.7 Pattern analysis
      - Remove always-pass, investigate always-fail, study skill-only-pass
      - Tighten for inconsistent results, check outliers
  3.8 Blind comparison (--baseline only)
      - Both outputs to judge without revealing source
      - Score holistic quality

STEP 4: Conflicts Mode (mode: conflicts)
  - Scan all skills in .claude/skills/ and core/.claude/skills/
  - 3 representative queries per skill
  - Report cross-activation conflicts

STEP 5: Human Review (standalone only)
  - When standalone: present outputs + grades, record feedback
  - When delegated from writing-skills: SKIP, return verdict directly

STEP 6: Produce Evaluation Report
  Locked format:

  SKILL EVALUATION REPORT: <skill-name>
  =====================================
  Mode: <trigger|output|full|conflicts>
  Iteration: <N>

  SKILL NECESSITY
    Without skill: <pass_rate>% | With skill: <pass_rate>%
    Delta: +<N>% -- <adds clear value | marginal | not adding value>

  TRIGGER EVALUATION
    Should-trigger:    N/10 activated (N% rate)
    Should-not:        N/10 correctly ignored
    Cross-skill:       N conflicts [list]
    Regressions:       N/N (--baseline only)
    Fresh validation:  N/5 passed
    Trigger verdict:   PASS | FIX | FAIL

  OUTPUT EVALUATION
    Scenarios:         N/5 passed
    Stress test:       N% (N CRIT, N MAJOR, N MINOR)
    Assertions:        N/N (N%)
    Baseline delta:    +N% pass rate, +N tokens, +Ns
    Output verdict:    PASS | FIX | FAIL

  OVERALL VERDICT: PASS | FIX | FAIL
  Blocking issues: <list or "none">
  Recommended fixes: <prioritized, mapped to failure types>

STEP 7: Return Verdict
  PASS: all thresholds met, skill adds value, no conflicts
  FIX: minor issues + specific actionable fixes mapped to failure types
  FAIL: major failures + specific rework areas
```

### MUST DO

- Always run each eval in clean context (subagent isolation)
- Always test trigger AND output for full mode
- Always check cross-skill conflicts
- Always run skill necessity baseline for new skills
- Always provide evidence for every assertion grade
- Always include fix-type-mapped recommendations with FIX/FAIL
- Always test with 5 fresh queries after description optimization
- Always review assertions during grading (fix broken assertions)
- When delegated from writing-skills: skip human review, return verdict

### MUST NOT DO

- MUST NOT report PASS without running all evaluations for the mode
- MUST NOT skip cross-skill conflict check
- MUST NOT grade without evidence
- MUST NOT suggest fixes contradicting writing-skills best practices
- MUST NOT add specific keywords from failed queries to description (overfitting)
- MUST NOT block on human review when delegated from writing-skills

---

## FILE 4: `references/description-optimization.md` -- Create (~170 lines)

### How Triggering Works
- Description carries entire triggering burden
- Agents consult skills for tasks beyond baseline capability
- Simple tasks may not trigger even with perfect description

### Writing Descriptions
- Imperative: "Use this skill when..."
- User intent focus, not implementation
- Err on pushy: "even if they don't mention 'CSV'"
- Under 1024 characters

Before/after example:
  Before: "Process CSV files."
  After: "Analyze CSV and tabular data files -- compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this skill
  when the user has a CSV, TSV, or Excel file and wants to explore,
  transform, or visualize the data, even if they don't explicitly mention
  'CSV' or 'analysis.'"

### Eval Queries (20 total)
- 10 should-trigger: vary phrasing, explicitness, detail, complexity
- 10 should-not-trigger: near-misses, not obviously irrelevant
- Realistic: file paths, personal context, typos
- Store in eval_queries.json with {query, should_trigger} structure

### Testing
- 3 runs per query, trigger rate thresholds (>=80% / <=20%)
- Train/validation split (60/40), fixed across iterations
- Only use train set failures to guide revisions -- keep validation results out of process

### Optimization Loop
1. Eval on train + validation
2. Identify train failures -> revise (generalize, don't add keywords)
3. Too broad -> add specificity, clarify boundary between this skill and adjacent capabilities
4. If stuck after 3 tweaks -> structurally different framing
5. Max 5 iterations, select best by VALIDATION pass rate
6. If not improving -> issue may be with queries (too easy, too hard, mislabeled), not description

### Fresh Validation
- 5-10 never-seen queries after selecting best description
- If fresh queries fail -> overfit, revisit

---

## FILE 5: `references/eval-driven-iteration.md` -- Create (~280 lines)

### Test Case Design
- Prompt + expected output + optional files
- Store in evals/evals.json, start with 2-3 cases
- Vary prompts, include edge cases, realistic context
- Include at least one edge case (malformed input, unusual request, ambiguous)
- Use realistic context: file paths, column names, personal context ("my manager asked...")
- evals.json is hand-authored; grading.json, timing.json, benchmark.json are auto-generated

### Workspace Structure
```
workspace/iteration-N/eval-<name>/{with_skill,without_skill}/
  outputs/, timing.json, grading.json
workspace/iteration-N/benchmark.json
```

### Running Evals
- Clean context per run (subagent isolation)
- With-skill + without-skill (or old version for --baseline)
- Capture timing: {total_tokens, duration_ms}

### Assertions
- Write after first run
- Good: "output is valid JSON", "chart has labeled axes"
- Weak: "output is good", "uses exact phrase X"
- Not everything needs an assertion -- style caught in human review

### Grading
- PASS/FAIL with evidence, using grading.json format: {assertion_results: [{text, passed, evidence}], summary: {passed, failed, total, pass_rate}}
- For mechanical checks (valid JSON, row count), use verification scripts -- more reliable than LLM grading
- Use LLM grading for subjective assertions
- Substance not label: "Summary" section with vague sentence = FAIL even if heading matches
- Review assertions: always-pass (remove), always-fail (fix), unverifiable (replace)

### Aggregating Benchmarks
- benchmark.json with nested mean/stddev for pass_rate, time_seconds, tokens + delta
- Delta interpretation: what skill costs (time, tokens) vs what it buys (pass rate)
- stddev only meaningful with multiple runs; early iterations focus on raw counts and delta

### Blind Comparison (--baseline)
- Both outputs to judge without revealing source
- Complements assertions for holistic quality

### Pattern Analysis
- Remove always-pass assertions (inflating rate without measuring value)
- Investigate always-fail (broken assertion, too hard, or wrong check)
- Study skill-only-pass -- understand WHY (which instructions/scripts made the difference)
- Tighten for inconsistent results (high stddev): add examples or more specific guidance
- Check time/token outliers: read execution transcript for bottleneck

### Execution Trace Review

| Trace Pattern | Root Cause | Fix |
|---|---|---|
| Multiple approaches tried | Instructions too vague | Be more specific |
| Non-applicable instructions followed | No conditional gating | Add "only if X" |
| Time choosing between options | No default | Pick default, mention alternatives |

### Adversarial Categories (10)
ambiguous, off-topic, conflicting, oversized, empty, partial prerequisite,
repeated, malformed, stale, adversarial phrasing

Severity: CRITICAL > MAJOR > MINOR > PASS

### Iteration Loop
Three signals: failed assertions, human feedback, execution traces.
Feed all + SKILL.md -> propose changes:
- Generalize, don't patch specific cases
- Keep lean -- try removing instructions if plateaued
- Explain why ("Do X because Y") over rigid ("ALWAYS X")
- Bundle repeated logic into scripts/

### Stop Criteria
Satisfied, feedback empty, no improvement between iterations, or 5 max.

---

## Gap Closure Verification

All 25 original gaps + 2 new gaps from scripts page + autonomy gaps: CLOSED.

| # | Gap | Closed By |
|---|---|---|
| 1 | Anti-pattern: LLM general knowledge | Edit C (Step 3.1b warning) |
| 3 | Session extraction sub-points | Edit C (Step 3.1 rewrite) |
| 5 | Informal "run once and revise" | Edit F (Step 6 preamble) |
| 7-9 | Trace diagnostic patterns | eval-driven-iteration.md Execution Trace Review |
| 12 | Positive framing: what to include | Edit B (context budget) |
| 13 | Skill necessity check | Edit A (Step 1.1) + skill-evaluator Step 3.1 |
| 15 | Too-narrow skill risks | Edit E (Step 4.2 row) |
| 16-17 | Concise stepwise, agent judgment | Edit B (context budget) |
| 19 | Conditional progressive disclosure | Edit B (context budget) |
| 25 | Skills CAN include specifics | instruction-writing-patterns Pattern 6 |
| 27-28 | Gotchas placement + iteration | instruction-writing-patterns Pattern 2 |
| 29 | assets/ directory | instruction-writing-patterns Pattern 7 |
| 30 | Checklists | instruction-writing-patterns Pattern 8 |
| 32 | Reference as validator | instruction-writing-patterns Pattern 3 |
| 35 | Scripts page content | instruction-writing-patterns Pattern 7 |
| 40 | Workspace structure | eval-driven-iteration.md |
| 41 | Clean context per run | skill-evaluator Steps 2.2 + 3.3 |
| 46 | Review assertions during grading | eval-driven-iteration.md Grading |
| 47 | Blind comparison | skill-evaluator Step 3.8 |
| 53 | LLM iteration prompting | eval-driven-iteration.md Iteration Loop |
| 57 | Agent trigger nuance | description-optimization.md How Triggering Works |
| 62 | Query count 10+10 | skill-evaluator Step 2.1 |
| 70 | Before/after example | description-optimization.md |
| 71 | Fresh validation queries | skill-evaluator Step 2.5 + description-optimization.md |
| 72 | Structural approach when stuck | description-optimization.md Optimization Loop |
| NEW | Script design for agentic use | instruction-writing-patterns Pattern 7 |
| NEW | One-off commands vs bundled | instruction-writing-patterns Pattern 7 |
| AUTO | Skill-evaluator invoked automatically | Edit F Step 6.1 via Agent tool |
| AUTO | Auto-fix routing | Edit F Step 6.2 routing table |
| AUTO | Single human approval gate | Edit F Step 6.4 |
| AUTO | Human review conditional | skill-evaluator Step 5 context detection |

## What Does NOT Change

- Steps 2-5 (authoring): unchanged except additions
- Step 6.5/6.6 (failure prevention map, domain review): renumbered only
- Steps 7-8 (hub promotion, templates): unchanged
- Existing references: anti-patterns.md, skill-templates.md, step-n-action-verb-object.md, multi-skill-decomposition.md, skill-authoring-from-scratch.md -- unchanged
- skill-testing.md: content adapted into skill-evaluator refs, original kept for backward compat

---

## Implementation Record

**Implemented:** 2026-04-02
**TDD:** 103 tests written before implementation, all passing after.
**Test file:** `scripts/tests/test_skill_evaluator_and_writing_skills_upgrade.py`

### Post-Implementation Fixes

| # | Issue | Source | Fix Applied |
|---|---|---|---|
| 1 | Threshold contradiction: description-optimization.md had 50%/50% vs skill-evaluator's 80%/20% | Quality gate agent | Fixed to 80%/20% in description-optimization.md |
| 2 | Missing eval_queries.json format for trigger query storage | Cross-check vs optimizing-descriptions URL | Added JSON example to description-optimization.md |
| 3 | "Keep validation results out of revision process" not explicit | Cross-check vs optimizing-descriptions URL | Added one-liner to Train/Validation Split section |
| 4 | "Clarify boundary with adjacent capabilities" missing from too-broad fix | Cross-check vs optimizing-descriptions URL | Expanded too-broad bullet in description-optimization.md |
| 5 | "If not improving, issue may be queries not description" missing | Cross-check vs optimizing-descriptions URL | Added step 6 to optimization loop in description-optimization.md |

| 6 | Edge case tip missing from test case design | Cross-check vs evaluating-skills URL | Added to eval-driven-iteration.md test case tips |
| 7 | Realistic context tip missing from test case design | Cross-check vs evaluating-skills URL | Added to eval-driven-iteration.md test case tips |
| 8 | Hand-authored vs auto-generated files not clarified | Cross-check vs evaluating-skills URL | Added note to eval-driven-iteration.md workspace section |
| 9 | LLM vs script grading distinction missing | Cross-check vs evaluating-skills URL | Added to eval-driven-iteration.md grading section |
| 10 | grading.json structure not specified | Cross-check vs evaluating-skills URL | Added JSON example to eval-driven-iteration.md |
| 11 | "Substance not label" grading principle missing | Cross-check vs evaluating-skills URL | Added to eval-driven-iteration.md grading principles |
| 12 | benchmark.json missing stddev format | Cross-check vs evaluating-skills URL | Added full benchmark.json with nested mean/stddev to eval-driven-iteration.md |
| 13 | Delta interpretation not framed | Cross-check vs evaluating-skills URL | Added "costs vs buys" framing |
| 14 | stddev note (only meaningful with multiple runs) | Cross-check vs evaluating-skills URL | Added practical guidance note |
| 15 | Pattern analysis details missing from reference | Cross-check vs evaluating-skills URL | Added Pattern Analysis section to eval-driven-iteration.md |
| 16 | skill-only-pass analysis not in reference | Cross-check vs evaluating-skills URL | Added to Pattern Analysis section |
| 17 | State prerequisites in SKILL.md missing | Cross-check vs using-scripts URL | Added to instruction-writing-patterns.md Pattern 7 |
| 18 | compatibility frontmatter field not mentioned | Cross-check vs using-scripts URL | Added to Pattern 7 |
| 19 | Escalation signal (complex one-off -> scripts) | Cross-check vs using-scripts URL | Added to Pattern 7 |
| 20 | Script referencing example not shown | Cross-check vs using-scripts URL | Added full markdown example to Pattern 7 |
| 21 | references/*.md relative path convention | Cross-check vs using-scripts URL | Added note to Pattern 7 |
| 22 | Self-contained scripts (PEP 723, Deno, Bun, Ruby) | Cross-check vs using-scripts URL | Added summary to Pattern 7 |
| 23 | Input constraints missing from agentic table | Cross-check vs using-scripts URL | Added 10th row to table |

### Quality Gate Results

- 99 items checked across 5 files (initial implementation)
- 98 PASS, 1 WARN (minor text truncation in Step 1.1 stop message)
- 30/30 gap closures verified
- 7/7 cross-references verified
- 38/38 items from optimizing-descriptions URL verified after fixes
- 48/48 items from evaluating-skills URL verified after fixes
- 36/36 items from using-scripts URL verified after fixes
