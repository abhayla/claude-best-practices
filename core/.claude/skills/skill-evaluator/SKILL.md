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
version: "2.2.0"
---

# Skill Evaluator — Evaluate Skill Quality

Structured evaluation of skill trigger reliability, output quality, and
cross-skill compatibility. Produces a graded verdict (PASS/FIX/FAIL) with
evidence and recommended fixes.

**Request:** $ARGUMENTS

---

## STEP 0: Pre-Flight Checks

Run these checks BEFORE evaluation. They catch the issues most commonly missed
during Skills #1-5 evaluation batch (registry drift, missing frontmatter,
structural defects). Each check is pass/fail with specific evidence.

### 0.1 Registry Sync

Compare `registry/patterns.json` entry against the skill's SKILL.md:

| Check | How | Fail Condition |
|-------|-----|----------------|
| Description match | Compare registry `description` vs frontmatter `description` | Empty registry description, or semantic mismatch |
| Hash freshness | Compute SHA-256 of SKILL.md, compare to registry `hash` | Hash differs |
| Version consistency | Compare registry `version` vs frontmatter `version` vs latest `changelog` entry | Any mismatch |
| Dependency completeness | Scan body for `Agent("...agent")`, `Skill("...skill")`, `/skill-name` references → verify each in registry `dependencies` | Referenced but not listed |

### 0.2 Frontmatter Completeness

Verify these fields against platform constraints:

| Field | Validation Rules |
|-------|-----------------|
| `name` | Required. Max 64 chars. Lowercase letters/numbers/hyphens only. No XML tags. No reserved words (`anthropic`, `claude`). Prefer gerund form (`processing-pdfs`). MUST match directory name |
| `description` | Required. Non-empty. Max 1024 chars. No XML tags. Must be third-person ("Processes..." not "I process..." or "You can..."). Should start with verb. Must describe what AND when to use |
| `type` | Required. Must be `workflow` or `reference` |
| `triggers` | Required. ≥3 entries (BLOCKING if missing — skill is invisible to natural language) |
| `allowed-tools` | Scan body for `Agent()`, `Skill()`, `Write`, `Edit`, `Bash` usage. Flag under-declared or over-declared tools |
| `version` | Required. SemVer format |

### 0.3 Structural Integrity

| Check | How | Fail Condition |
|-------|-----|----------------|
| Code fence balance | Count ``` openings vs closings per section | Unequal (orphaned fence) |
| Numbered-list continuity | Scan for numbered items (1., 2., ...) between `##` headers | Orphaned items not part of a contiguous list |
| Step cross-references | Find all "Step N" mentions, verify each N exists as `## STEP N:` | Reference to nonexistent step |
| Skill name references | Find all `/skill-name` mentions, verify each exists in `.claude/skills/` | Dead reference |
| Agent references | Find all `*-agent` mentions, verify each exists in `.claude/agents/` | Dead reference |
| Placeholder markers | Scan for `<!-- TODO -->`, `<!-- FIXME -->`, `<!-- PLACEHOLDER -->` | Any found |
| Preamble constraints | For workflow skills, verify critical constraints appear in BOTH preamble (top) AND CRITICAL RULES section (bottom) | Missing from either location |
| Reference depth | Scan all `Read:` / `See:` / link references in SKILL.md and referenced files | Any file that references another file (depth >1 from SKILL.md) |
| Reference TOC | Check reference files >100 lines for a table of contents section at top | Missing TOC in long reference file |

### 0.4 Reference Self-Update Mechanism

For skills that have a `references/` directory, verify they include a Reference Completeness Check step:

| Check | How | Fail Condition |
|-------|-----|----------------|
| Self-update step exists | Scan for a step containing "Reference Completeness Check" or equivalent (scans conversation for new knowledge, compares against existing references, presents gaps to user) | Skill has `references/` but no self-update step |
| User approval gate | Verify the step requires user approval before writing reference updates | Updates written without user confirmation |
| Version bump on update | Verify the step bumps patch version after reference updates | References updated without version bump |
| Knowledge filtering | Verify the step distinguishes domain-specific knowledge from generic/ephemeral content | No filtering criteria defined |

**Severity:** Skills with `references/` that lack a self-update mechanism get a **MAJOR** finding (not CRITICAL — the skill works, but it won't improve over time).

If ANY check in 0.1-0.4 fails, report it in the evaluation output as a
**PRE-FLIGHT FAILURE** and include it in the fix recommendations. Do not skip
these checks — they caught issues in 5/5 evaluated skills.

---

## STEP 1: Parse Mode and Load Skill

| Mode | What It Tests |
|------|--------------|
| `trigger` | Description activation, trigger rate, cross-skill conflicts |
| `output` | Output quality: scenarios, stress test, assertions, benchmarks |
| `full` | Both trigger + output, aggregated report |
| `conflicts` | Cross-skill conflict scan across ALL installed skills |

1. Load target skill's SKILL.md, extract: name, description, triggers, allowed-tools
2. If `--baseline`: snapshot current version (`cp -r <skill-path> <workspace>/skill-snapshot/`)
3. Detect invocation context:
   - **Standalone**: include human review (Step 5)
   - **Delegated from writing-skills**: skip human review, return verdict directly

---

## STEP 2: Trigger Evaluation (modes: trigger, full)

**Read:** `references/description-optimization.md` for description writing
principles, eval query design, and optimization loop methodology.

### 2.1 Generate 20 Eval Queries

**10 should-trigger queries:**
- Vary phrasing (formal, casual, typos/abbreviations)
- Vary explicitness (names domain directly vs describes the need)
- Vary detail (terse one-liners vs context-heavy with file paths)
- Vary complexity (single-step vs multi-step where skill is buried in chain)
- Most valuable: queries where the skill helps but connection isn't obvious

**10 should-not-trigger queries:**
- Near-misses that share keywords but need a different skill
- NOT obviously irrelevant queries — those test nothing
- Include realistic context (file paths, personal context, casual language)

### 2.2 Test Activation

- Run each query 3 times (model nondeterminism), each in clean context (subagent)
- Compute trigger rate per query (triggers / runs)
- Should-trigger threshold: ≥80% trigger rate
- Should-not-trigger threshold: ≤20% trigger rate
- Note: agents may not consult skills for simple tasks — this is expected

### 2.3 Cross-Skill Conflict Check

- Run should-trigger queries with ALL installed skills active
- Verify the target skill activates, not a competitor
- Report: competing skill name + the conflicting query + trigger rates
- **Bidirectional signposting**: when a conflict is detected, check if BOTH skills' descriptions mention the other with clear boundary language. If not, flag as "missing reciprocal boundary"
- **Near-duplicate resolution**: if overlap is HIGH, check whether the target skill delegates to the neighbor (orchestrator wrapper pattern) or reimplements its logic (true duplicate). Read the skill body and any dispatched agents to determine this
- **Skill-vs-rule overlap**: compare skill steps against auto-loaded rules in `.claude/rules/` for redundancy (e.g., a skill that restates a globally-loaded workflow rule)

### 2.4 Trigger Regression (--baseline only)

- Run old version's trigger queries against new description
- No regressions: every old query must still trigger

### 2.5 Description Optimization (if trigger verdict is FIX)

1. Identify failing queries from train set (60% of queries)
2. Revise description — generalize from the category, don't add specific keywords
3. If stuck after 3 incremental tweaks, try structurally different framing
4. Validate against held-out set (40% of queries)
5. Final: test with 5 fresh queries never seen during optimization
6. Verify description stays under 1024 characters

---

## STEP 3: Output Evaluation (modes: output, full)

**Read:** `references/eval-driven-iteration.md` for test case design,
assertion writing, grading methodology, and iteration patterns.

### 3.1 Skill Necessity Baseline

- Run 3 representative prompts WITHOUT the skill (subagent, clean context)
- Run same prompts WITH the skill
- If with-skill doesn't meaningfully improve: flag "skill may not be adding value"

### 3.2 Design or Load Test Cases

- If `evals/evals.json` exists in skill directory: load it
- Otherwise: generate 5 scenarios (3 happy-path + 2 edge-case)
- Start with 2-3 cases; expand after first results

### 3.3 Run Scenarios

- Each run in clean context (subagent isolation — no leftover state)
- With-skill run for each test case
- If `--baseline`: also run against old version
- Capture outputs + timing (`{total_tokens, duration_ms}`)

### 3.3b Model Matrix (optional but recommended)

If the skill targets multiple model tiers, run scenarios across available
models (e.g., Haiku, Sonnet, Opus). Flag divergent results — a skill
that works on Opus but fails on Haiku needs more explicit guidance.

When model matrix is not feasible (time/cost), note "Tested on
\<model\> only" in the evaluation report. If the skill requires MCP tools
not available in the eval context, document as "untestable dependency"
in the report — do not report false FAIL.

### 3.4 Stress Test

10 adversarial inputs — pick most realistic for the skill's domain:

| # | Category | What It Exposes |
|---|----------|----------------|
| 1 | Ambiguous request | Routing/classification failures |
| 2 | Off-topic query | Missing scope guard |
| 3 | Conflicting constraints | Silent data loss |
| 4 | Oversized input | Truncation, timeout |
| 5 | Minimal/empty input | Crash or null proceeding |
| 6 | Partial prerequisite | Broken state from incomplete setup |
| 7 | Repeated invocation | Duplicate output, state corruption |
| 8 | Malformed format | Unhelpful error or silent wrong behavior |
| 9 | Stale context | Acting on outdated data |
| 10 | Adversarial phrasing | Trigger misfire |

Score each: CRITICAL (wrong output/data loss) / MAJOR (partial/misleading) / MINOR (cosmetic) / PASS (handled correctly).

**Delegation edge cases** (for skills that call other skills/agents):
- What happens when the delegate returns empty/zero results?
- Does the skill handle standalone vs pipeline mode differently? Test both paths.
- If the skill has dual-mode operation, verify skip conditions work correctly.

### 3.4b Reference Self-Update Behavior (skills with references/ only)

For skills that have a `references/` directory, test that the Reference Completeness Check step actually works during execution:

1. **Introduce novel knowledge** — run the skill with a scenario that surfaces a domain-specific pattern, edge case, or gotcha NOT already in any reference file
2. **Verify detection** — the skill should identify the gap and present it to the user with: what was found, which reference file to update/create, and the proposed action
3. **Verify gating** — the skill MUST ask for user approval before writing any reference updates (auto-writing without approval is a CRITICAL failure)
4. **Verify filtering** — the skill should NOT propose adding generic programming knowledge, one-time user-specific data, or ephemeral conversation context
5. **Verify version bump** — after approved reference updates, the skill should bump its patch version

| Test | Pass Criteria | Failure Severity |
|---|---|---|
| Gap detection | Skill identifies ≥1 new knowledge item from novel scenario | MAJOR if missed |
| User approval gate | Skill presents findings and waits before writing | CRITICAL if skipped |
| Knowledge filtering | Skill does NOT propose adding generic/ephemeral content | MAJOR if unfiltered |
| Version bump | Patch version incremented after reference update | MINOR if missed |
| No-gap scenario | When all knowledge is already covered, skill reports "References are up to date" and skips | MINOR if still proposes updates |

Add results to the evaluation report under a `REFERENCE SELF-UPDATE` section.

### 3.5 Write and Grade Assertions

- Write assertions AFTER first run — you don't know "good" until the skill runs
- Good: "output is valid JSON", "chart has labeled axes", "report has ≥3 recs"
- Weak: "output is good" (vague), "uses exact phrase X" (brittle)
- Grade each PASS/FAIL with specific evidence (quote output, reference files)
- Review assertions themselves: too easy (always pass)? too hard? unverifiable?

### 3.6 Aggregate Benchmarks

```json
{
  "with_skill": {"pass_rate": 0.83, "tokens_mean": 3800, "time_mean_s": 45},
  "without_skill": {"pass_rate": 0.33, "tokens_mean": 2100, "time_mean_s": 32},
  "delta": {"pass_rate": "+0.50", "tokens": "+1700", "time_s": "+13"}
}
```

### 3.7 Pattern Analysis

- Remove assertions that always pass in both configs (inflating pass rate)
- Investigate always-fail in both (broken assertion or impossible task)
- Study skill-only-pass (where skill adds value — understand WHY)
- For inconsistent results (high stddev): tighten ambiguous instructions
- Check time/token outliers: read execution transcript for bottleneck

### 3.8 Blind Comparison (--baseline only)

- Present both outputs to a judge without revealing which is old vs new
- Score holistic qualities: organization, formatting, usability, polish
- Complements assertion grading — two outputs can pass all assertions but differ in quality

---

## STEP 4: Conflicts Mode (mode: conflicts)

1. Scan all installed skills in `.claude/skills/` and `core/.claude/skills/`
2. For each skill, generate 3 representative should-trigger queries
3. Run each query with all skills active
4. Report any query that activates the wrong skill
5. Output: conflict matrix showing which skills compete

---

## STEP 5: Human Review (standalone only)

**When invoked standalone** (not delegated from writing-skills):
- Present outputs alongside grades for each test case
- Record specific, actionable feedback per case
- Empty feedback = output passed review
- Feedback feeds into iteration

**When delegated from writing-skills:** SKIP this step — return verdict directly. Writing-skills handles the single user approval gate.

---

## STEP 6: Produce Evaluation Report

Locked output format:

```
SKILL EVALUATION REPORT: <skill-name>
=====================================
Mode: <trigger|output|full|conflicts>
Iteration: <N>

SKILL NECESSITY
  Without skill: <pass_rate>% | With skill: <pass_rate>%
  Delta: +<N>% — <adds clear value | marginal | not adding value>

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

REFERENCE SELF-UPDATE (skills with references/ only)
  Self-update step:  <present | missing>
  Gap detection:     <PASS | MAJOR — missed novel knowledge>
  Approval gate:     <PASS | CRITICAL — auto-wrote without approval>
  Knowledge filter:  <PASS | MAJOR — proposed generic content>
  Version bump:      <PASS | MINOR — not bumped>
  No-gap handling:   <PASS | MINOR — proposed updates when none needed>

MODEL COVERAGE
  Tested on:         <model list or "single model: X">
  Divergent results: <list or "N/A">

OVERALL VERDICT: PASS | FIX | FAIL
Blocking issues: <list or "none">
Recommended fixes: <prioritized, mapped to failure types>
```

---

## STEP 7: Return Verdict

| Verdict | Criteria | What Caller Should Do |
|---------|----------|----------------------|
| PASS | Trigger ≥80%, stress ≥90%, no conflicts, no regressions, skill adds value | Proceed |
| FIX | Minor issues below threshold | Fix specific issues, re-run eval |
| FAIL | Critical failures, design gaps, skill adds no value | Major rework |

---

## MUST DO

- Always run each eval in clean context (subagent isolation) — Why: leftover state produces unreliable results
- Always test both trigger AND output for full mode — Why: a skill that triggers correctly but produces bad output is broken
- Always check cross-skill conflicts, not just target in isolation — Why: isolated testing misses real activation conflicts
- Always run skill necessity baseline for new skills — Why: the most important question is "should this skill exist?"
- Always provide evidence for every assertion grade — Why: "looks good" is not a grade
- Always include fix-type-mapped recommendations with FIX/FAIL — Why: a verdict without actionable fixes wastes the caller's time
- Always test with 5 fresh queries after description optimization — Why: optimized descriptions can overfit to the eval set
- Always review assertions during grading — Why: broken assertions waste iterations
- When delegated from writing-skills: skip human review, return verdict directly — Why: writing-skills manages the approval gate
- Always validate name constraints (64 chars, lowercase/hyphens, no reserved words) in pre-flight — Why: platform rejects non-conforming names
- Always check description is third-person in pre-flight — Why: first/second person causes discovery problems per platform docs
- Always check reference depth ≤1 from SKILL.md in pre-flight — Why: Claude partially reads deeply nested files
- Always check for Reference Self-Update step in skills with `references/` directory — Why: skills without self-update become stale as their domain evolves; this is the mechanism that makes skills iteratively self-improving
- Always test reference self-update behavior with a novel knowledge scenario in output evaluation — Why: structural presence of the step is not enough; it must actually detect gaps and gate on user approval

## MUST NOT DO

- MUST NOT report PASS without running all evaluations for the mode — report only what was tested
- MUST NOT skip cross-skill conflict check — isolated testing misses real conflicts
- MUST NOT grade without evidence — every assertion needs specific output reference
- MUST NOT suggest fixes contradicting writing-skills best practices — fixes must align with authoring guidance
- MUST NOT add specific keywords from failed queries to description — that's overfitting; generalize from the category
- MUST NOT block on human review when delegated from writing-skills — return verdict immediately
