# Prompt Auto-Enhance v2.0 Workflow

**Implementation Status: DESIGN** -- This spec describes the target state for
v2.0. The currently deployed files are v1.5.1 (skill) and v1.2.0 (rule).
All changes described here MUST be implemented atomically in a single PR
(hook + rule + skill updated together to avoid conflicting instructions).

## Purpose

A three-layer system (hook + rule + skill) that grades and strengthens every
non-trivial user prompt before execution. The hook provides deterministic
triggering, the rule provides always-loaded behavioral context, and the skill
provides the full Grade -> Diagnose -> Fix pipeline.

**What changed in v2.0:** Added prompt grading (Step 0) as the entry point,
expanded from 9 to 11 failure categories, added 3 guardrails against
auto-enhancement failure modes, slimmed the rule to fix SSOT violation.

**Adversarial review completed:** 27 findings addressed (2026-03-31). Key
mitigations: floor rule for catastrophic single-dimension scores, Grade D
added for bad-but-fixable prompts, Clarification Gate sequencing protocol,
Critical fixes never capped, compact output for Grade B.

---

## Architecture

```
+-------------------------------------------------------------+
| HOOK (deterministic -- fires every prompt)                    |
| prompt-enhance-reminder.sh                                    |
| +----------------------------------------------------------+ |
| | 1. Mandate *Enhanced:* indicator on every response        | |
| | 2. Mandate Tier 1 context gathering                       | |
| | 3. Trigger Grade -> Diagnose -> Fix for non-trivial       | |
| |    prompts (delegates to /prompt-auto-enhance skill)      | |
| +----------------------------------------------------------+ |
+----------------------------+---------------------------------+
                             | triggers
                             v
+-------------------------------------------------------------+
| RULE (advisory -- always loaded in context, ~40 lines)       |
| prompt-auto-enhance-rule.md                                   |
| +----------------------------------------------------------+ |
| | 1. *Enhanced:* indicator format + examples                | |
| | 2. Tier 1/2 context sources (compact)                     | |
| | 3. Grade -> Strengthen trigger (pointer to skill)         | |
| | 4. Clarification Gate (UNIQUE to rule)                    | |
| | 5. CRUD detection trigger (delegates to skill)            | |
| | 6. Critical rules (rule-specific only)                    | |
| +----------------------------------------------------------+ |
+----------------------------+---------------------------------+
                             | invokes for non-trivial prompts
                             v
+-------------------------------------------------------------+
| SKILL (on-demand -- full workflow, ~480 lines)               |
| /prompt-auto-enhance (SKILL.md + references/)                |
| +----------------------------------------------------------+ |
| | STEP 0: Quick Grade (6 weighted dimensions)               | |
| | STEP 1: Diagnose (11 categories with severity)            | |
| | STEP 2: Map Fixes (prioritized by severity)               | |
| | STEP 3: Rewrite with Guardrails (3 safeguards)            | |
| | STEP 4: Show Grade Card + Before/After                    | |
| | STEP 5: Execute                                           | |
| | --------------------------------------------------------- | |
| | Batch Approval Flow (resource CRUD)                       | |
| | Web Search Decision Tree                                  | |
| | Prompt Reliability Scoring (explicit /score mode)         | |
| +----------------------------------------------------------+ |
| references/                                                   |
|   constraint-engineering.md                                   |
|   format-locking.md                                           |
|   prompt-pruning.md (expanded -- 3 anti-pattern categories)   |
|   prompt-reliability-scoring.md                               |
|   grading-rubric.md (NEW)                                     |
+-------------------------------------------------------------+
```

### Layer Responsibilities (SSOT)

| Layer | SSOT For | NOT For |
|-------|----------|---------|
| **Hook** | Deterministic trigger -- fires every prompt, non-blocking | Procedural detail, grading logic |
| **Rule** | Behavioral contract -- indicator, context tiers, Clarification Gate | Strengthening steps, failure categories, XML tags |
| **Skill** | Full workflow -- grading, diagnosis, rewriting, CRUD flow | Always-loaded context (loaded on-demand only) |

Per `configuration-ssot.md`: hooks enforce with zero exceptions, rules provide
advisory context, skills hold multi-step procedures. No content is duplicated
across layers.

---

## Hook: `prompt-enhance-reminder.sh`

**Event:** `UserPromptSubmit` (every user message, no matcher filter)
**Exit code:** Always 0 (non-blocking)

```bash
#!/bin/bash
echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
echo "Gather Tier 1 context (patterns, CLAUDE.md, git state) before responding."
echo "For non-trivial prompts (ambiguous, multi-file, multi-step): run the Grade -> Diagnose -> Fix pipeline from /prompt-auto-enhance. Grade on 6 dimensions first -- only fix dimensions scoring below 4. Skip for direct instructions, single-file changes, and questions."
exit 0
```

**Settings.json registration:**
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/prompt-enhance-reminder.sh"
      }]
    }]
  }
}
```

**v2.0 change:** Added line 3 -- the grading pipeline trigger. This is the root
cause fix: the hook now carries the full behavioral contract (indicator +
context + grading trigger), not just the indicator reminder.

---

## Rule: `prompt-auto-enhance-rule.md` (~40 lines)

**Scope:** Global (`globs: ["**/*"]`) -- loaded into every conversation.
**Role:** Lean trigger + Clarification Gate (unique to rule).

### What the rule contains

1. `*Enhanced:*` indicator mandate with format and examples
2. Tier 1/2 context sources (compact list, no procedural detail)
3. One-line pointer to `/prompt-auto-enhance` for the Grade -> Strengthen pipeline
4. **Clarification Gate** -- full logic for when/how to ask questions before acting
   (this section is UNIQUE to the rule, not duplicated in the skill)
5. Resource CRUD detection trigger (3-line pointer to skill's batch flow)
6. Critical rules (5 rule-specific items only, no skill-duplicated rules)

### What the rule does NOT contain (moved to skill)

- Failure category list (9 or 11 categories)
- Strengthening steps (diagnose, map, rewrite, show)
- XML tag reference
- Weakening language flags
- Before/after display template
- Batch approval flow details
- Web search decision tree

**v2.0 change:** Cut from 97 -> ~40 lines by removing all content duplicated
from the skill. Fixes the SSOT violation identified in the gap analysis.

---

## Skill: `/prompt-auto-enhance` — Full Workflow

### STEP 0: Quick Grade (NEW in v2.0)

Score the prompt before diagnosing -- only fix what is actually weak. This
prevents over-constraint (the #1 failure mode of auto-enhancement systems)
and saves tokens by skipping diagnosis on strong dimensions.

#### 6 Weighted Grading Dimensions

| # | Dimension | Weight | What It Measures |
|---|-----------|--------|-----------------|
| 1 | **Intent Clarity** | 0.25 | Can there be only one interpretation of what must be done? |
| 2 | **Context Sufficiency** | 0.20 | Does the prompt provide all background needed? |
| 3 | **Constraint Precision** | 0.20 | Are limitations measurable and non-contradictory? |
| 4 | **Output Specification** | 0.15 | Is the expected result format defined? |
| 5 | **Role & Framing** | 0.10 | Is there a persona or domain frame? |
| 6 | **Example Grounding** | 0.10 | Are input/output examples provided? |

**Scoring anchors (per dimension):**

| Score | Meaning | Example (Intent Clarity) |
|-------|---------|-------------------------|
| 1 | Weak | Multiple interpretations, no action verb |
| 2 | Poor | Vague intent, reader must guess what "done" looks like |
| 3 | Adequate | Clear intent but minor ambiguity in scope |
| 4 | Good | Specific action + object, minor gaps only |
| 5 | Strong | Single interpretation, explicit action + object + success criteria |

Full anchors for all 6 dimensions: see `references/grading-rubric.md`

**Score formula:** `Overall = Sum(weight_i x score_i)` -- Range 1.0-5.0

#### Floor Rule (prevents degenerate scores)

Regardless of overall score, these overrides apply:
- If **any** dimension scores 1: grade CANNOT exceed B (cap at 3.9)
- If **Intent Clarity** or **Context Sufficiency** scores 1: auto-escalate to Grade F
- If more than 5 Critical issues diagnosed: auto-escalate to Grade F

**Why:** A prompt with perfect structure but ambiguous intent (score 1 on
Intent Clarity) can compute to 4.0 overall via high scores on other dimensions.
The floor rule prevents decorative dimensions from masking fundamental defects.

#### Grade Thresholds and Actions

| Grade | Score | Action | Rationale |
|-------|-------|--------|-----------|
| **A** | 4.0-5.0 | Skip strengthening, execute as-is | Strong prompt -- enhancing adds latency with no benefit |
| **B** | 3.0-3.9 | Strengthen ONLY dimensions scoring < 4 | Targeted fixes -- don't touch what works |
| **C** | 2.0-2.9 | Full strengthening (all weak dimensions) | Significant gaps cause inconsistent output |
| **D** | 1.5-1.9 | Full strengthening with heavy warning | Bad but fixable -- "Heavily rewritten, verify intent" |
| **F** | 1.0-1.4 | Show grade + suggested rewrite with caveats | Fundamental issues -- provide a draft rewrite but flag intent-drift risk |

**Grade D rationale:** Prompts scoring 1.5-1.9 are bad but not unrewritable.
Refusing to fix them (old Grade F behavior) frustrates users who wrote the
prompt because they didn't know how to write it better. Grade D auto-fixes
with an extra guardrail: the intent preservation check is mandatory and the
output includes "Heavily rewritten -- verify this matches your intent."

**Grade F rationale:** Prompts scoring 1.0-1.4 have fundamental ambiguity that
auto-fixing would likely distort. Instead of refusing ("ask user to rewrite"),
provide a suggested rewrite with heavy caveats: "This is a best-guess rewrite
that may not preserve your intent -- please review before proceeding."

#### Dimension -> Category Mapping

| Dimension | Maps to Diagnosis Categories |
|-----------|------------------------------|
| Intent Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE |
| Context Sufficiency | MISSING_CONTEXT, IMPLICIT_ASSUMPTIONS |
| Constraint Precision | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS, OVER_SCOPED |
| Output Specification | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE |
| Role & Framing | MISSING_ROLE |
| Example Grounding | MISSING_EXAMPLES |

---

### STEP 1: Diagnose Prompt Weaknesses (11 categories with severity)

**Only diagnose categories mapped from dimensions scoring < 4.** Skip diagnosis
for high-scoring areas -- this prevents over-constraint.

#### Failure Category Table

| Category | Severity | Symptoms | Structural Fix |
|----------|----------|----------|---------------|
| VAGUE_INTENT | Critical | Multiple interpretations of what must be done | Rewrite as action verb + object + success criteria |
| MISSING_CONTEXT | Critical | Assumes knowledge not provided | Add explicit context: files, module, prior state |
| AMBIGUOUS_SCOPE | High | Unclear which files/modules are in scope | Add scope boundaries ("only in src/api/") |
| CONFLICTING_CONSTRAINTS | High | Contradictory requirements | Prioritize one, note the tradeoff |
| OVER_SCOPED | High | Would require 5+ files changed | Break into sequential focused prompts |
| UNDER_CONSTRAINED | Medium | Freedom where specificity needed | Add measurable constraints (format, bounds) |
| MISSING_OUTPUT_SPEC | Medium | No result format defined | Add locked output template |
| IMPLICIT_ASSUMPTIONS | Medium | Relies on unverified assumptions (incl. temporal: "after the migration", "once PR merges") | Make assumptions explicit; verify temporal preconditions hold |
| MISSING_STRUCTURE | Medium | Flat text, XML tags would help | Restructure with `<task>`, `<context>`, `<constraints>` |
| MISSING_ROLE | Low | No persona or domain frame | Add role with expertise and perspective |
| MISSING_EXAMPLES | Low | No input/output examples | Add 2-3 examples in `<examples>` tags |

**v2.0 additions:** MISSING_ROLE and MISSING_EXAMPLES (categories 10-11).

#### Severity Fix Priority

| Severity | Fix Priority | Action |
|----------|-------------|--------|
| Critical | MUST fix | Always included -- Critical fixes are NEVER capped |
| High | SHOULD fix | Included if within max-5 cap |
| Medium | MAY fix | Included if within max-5 cap |
| Low | SUGGEST only | Only if room remains in cap |

---

### STEP 1b: Scan Weakening Language (Enhanced in v2.0)

Three categories of anti-patterns (expanded from one flat list):

#### Category A -- Prompt-Side Anti-Patterns (what the user writes)

| Flag | Problem | Replace With |
|------|---------|-------------|
| "try to", "attempt to" | Permits failure | Direct imperative ("do X") |
| "if possible", "when feasible" | Opt-out clause | Remove, or state specific condition |
| "maybe", "perhaps", "might" | Uncertainty in instructions | Commit to a direction |
| "I think", "I believe" | Weakens authority | State requirement directly |
| "please", "kindly" | Politeness filler | Remove |
| "etc.", "and so on" | Unbounded scope | List all items explicitly |
| "simple", "just", "easily" | False minimizer | Remove |
| "as needed", "as appropriate" | Delegation without criteria | Specify the criteria |
| "better", "modern", "clean", "good" | Vague qualitative | Define specific attribute |
| "stuff", "things", "it" (ambiguous) | Unclear reference | Name the specific object |
| "feel free to [ignore/skip]" | Explicit opt-out invitation | Remove -- instructions should be directive |
| "don't worry about" | Negative framing draws attention to X | State what TO do instead |
| "roughly", "approximately" (when precision needed) | False precision tolerance | State exact threshold or range |

#### Category B -- Aggressive Enforcement Anti-Patterns (Claude 4.x specific)

**Model condition:** These flags apply to Claude 4.x and later. For Claude 3.5
or non-Anthropic models, aggressive enforcement and "think step by step" may
still be beneficial. Check the target model before flagging.

| Flag | Problem | Replace With |
|------|---------|-------------|
| "CRITICAL:", "IMPORTANT:", "YOU MUST" | Over-triggers on Claude 4.x | Normal directive ("Use X when Y") |
| "NEVER EVER", "ABSOLUTELY MUST" | Hyperbolic emphasis | Standard "MUST" / "NEVER" |
| "think step by step" (reasoning models) | Redundant, causes double-reasoning | "evaluate" / "reason through" |

#### Category C -- Output-Side Anti-Patterns (Claude self-correction)

| Flag | Problem | Replace With |
|------|---------|-------------|
| "Certainly!", "Of course!", "Absolutely!" | Sycophantic opener | Lead with the answer |
| "Based on the information provided..." | Filler preamble | Remove |
| "I'd be happy to help with..." | Service language | Remove -- just do the task |

**Pruning rule:** Every removal MUST improve precision. If a qualifier serves
a genuine purpose ("if the file exists" is a real condition), keep it.

---

### STEP 2: Map Fixes

For each diagnosed weakness, determine the minimal structural fix:
- Each fix maps to exactly one failure category
- Fixes prioritized by severity: Critical -> High -> Medium -> Low
- **Max 5 fixes total** -- if more diagnosed, select top 5 by severity,
  list the rest as suggestions

Output format:
```
Diagnosis (N issues found, M within fix cap):
  [1] CRITICAL: VAGUE_INTENT -> rewrite as specific action + object + criteria
  [2] HIGH: AMBIGUOUS_SCOPE -> add explicit scope boundary
  [3] MEDIUM: UNDER_CONSTRAINED -> add measurable constraint
  [4] MEDIUM: MISSING_OUTPUT_SPEC -> add locked output template
  ---
  Suggestions (beyond cap):
  [5] LOW: MISSING_ROLE -> consider adding role with expertise
```

---

### STEP 3: Rewrite with Guardrails (NEW guardrails in v2.0)

Apply mapped fixes to produce a strengthened version.

#### Guardrail 1: Max Changes Cap (prevents over-constraint)

- **Critical fixes are never capped** -- if there are 6 Critical issues, all 6 are applied (and the prompt auto-escalates to Grade F per the floor rule)
- Maximum 5 non-Critical fixes per rewrite
- If > 5 non-Critical diagnosed: apply top 5 by severity, list rest as suggestions
- If Grade F (1.0-1.4): provide suggested rewrite with intent-drift caveats
- If Grade D (1.5-1.9): apply full strengthening with heavy warning

**Why:** Research shows adding too many constraints increases hallucination
rates. The over-constraint paradox: more rules does not mean better output.
But Critical issues (wrong task execution) must always be fixed -- they are
not a constraint problem, they are a correctness problem.
(Source: Prompt Optimization research, Data Science Collective)

#### Guardrail 2: Intent Preservation Check

After rewriting, verify the strengthened prompt accomplishes the same task:
- Same action verb (or clear equivalent)
- Same target files/modules/scope
- Same expected output type
- No new requirements added beyond the original

If intent drifts: revert that specific fix and note it in output.

**Intent preservation examples:**

- PASS: "fix the login bug" -> "resolve the authentication failure in
  login.py:42 that returns 500 on invalid credentials" (same intent, more specific)
- PASS: "refactor the auth module" -> "restructure the auth module to reduce
  cyclomatic complexity" (synonym substitution, same intent)
- FAIL: "review the auth module" -> "refactor the auth module to use JWT"
  (added new requirement -- JWT -- that was not in the original)
- FAIL: "add tests for the API" -> "rewrite the API and add tests"
  (scope expanded beyond testing to rewriting)

**Why:** Semantic drift is the #1 failure mode of auto-enhancement systems.
Rewrites that "sound better" but shift intent cause the wrong task to execute.

#### Guardrail 3: Over-Constraint Detection

After rewriting, check if more than 3 new constraint clauses were added:
- Soft warning: "Heavily constrained rewrite -- verify constraints match intent"
- Show which constraints were added vs. original
- This is a WARNING, not a hard gate -- the intent preservation check
  (Guardrail 2) is the hard gate

Also check for contradictions: verify no two added constraints conflict.
If contradictions found, that is a hard failure -- revert the conflicting fix.

**Why:** Verbosity is a byproduct of automated rewriting. Each added token
dilutes attention. Correct criterion: shortest prompt achieving target quality.

#### Rewrite Rules

- Targeted changes only -- do not rewrite clear parts
- Preserve user's original intent and voice
- Do not add complexity unless it eliminates a diagnosed weakness
- Do not change user's terminology unless it causes ambiguity
- Remove flagged weakening language per Step 1b
- When MISSING_STRUCTURE diagnosed, wrap sections in XML tags
- Place long context above the query, constraints near the task

---

### STEP 4: Show Grade Card + Before/After

MUST show every time strengthening activates. NOT optional -- visibility
builds trust and helps users learn prompt engineering.

**Compact mode (Grade B, 1-2 fixes):** Show only the before/after table and
the overall grade in the `*Enhanced:*` indicator. Skip the full dimension
breakdown -- it is diagnostic noise for minor improvements.

**Full mode (Grade C, D, F, or 3+ fixes):** Show the complete grade card
with dimension scores, then the before/after table.

#### Full Mode Output (Grade C/D/F)

```
Prompt Grade Card:
+----------------------+-------+--------+-------------------------+
| Dimension            | Score | Weight | Action                  |
+----------------------+-------+--------+-------------------------+
| Intent Clarity       |  4/5  |  0.25  | Strong                  |
| Context Sufficiency  |  2/5  |  0.20  | Fix: added file paths   |
| Constraint Precision |  3/5  |  0.20  | Improved: added bounds  |
| Output Specification |  2/5  |  0.15  | Fix: added template     |
| Role & Framing       |  4/5  |  0.10  | Strong                  |
| Example Grounding    |  1/5  |  0.10  | Fix: added 2 examples   |
+----------------------+-------+--------+-------------------------+
| Overall              |  2.9  |        | Grade C -- Full pipeline|
+----------------------+-------+--------+-------------------------+

Prompt Strengthened (3 fixes, 12 words removed):
+-----------------+----------------------------------------------+
| Original        | [user's original prompt text]                |
+-----------------+----------------------------------------------+
| Strengthened    | [rewritten prompt text]                      |
+-----------------+----------------------------------------------+
| Word Count      | 45 -> 62 (+17 words, net after pruning)      |
+-----------------+----------------------------------------------+
| Changes Applied |                                              |
|  [1] CRITICAL   | MISSING_CONTEXT -> added file paths + module |
|  [2] MEDIUM     | MISSING_OUTPUT_SPEC -> added JSON template   |
|  [3] MEDIUM     | UNDER_CONSTRAINED -> added word count bound  |
+-----------------+----------------------------------------------+
| Guardrails      | Intent: preserved | Constraints: 2 added     |
+-----------------+----------------------------------------------+
| Suggestions     | MISSING_EXAMPLES -- add 2 input->output      |
| (not applied)   | examples for more consistent output          |
+-----------------+----------------------------------------------+
Proceeding with strengthened prompt...
```

Update the `*Enhanced:*` indicator to include grade:
`*Enhanced: prompt graded (C, 3 fixes), git state, 2 rules*`

---

### STEP 5: Execute

Proceed with the strengthened prompt as if the user had entered it directly.
The rest of the pipeline (Tier 1/2 context, Clarification Gate, CRUD detection)
applies to the strengthened version, not the original.

---

## Skip Conditions

| Condition | Action | Rationale |
|-----------|--------|-----------|
| Direct unambiguous instruction | Skip all -- execute as-is | "rename X to Y" needs no grading |
| Single-file simple change | Skip all -- execute as-is | Overhead exceeds benefit |
| User says "do exactly this" | Skip all -- respect intent | User opted out |
| Pure knowledge question | Skip all -- just answer it | "What is X?" needs answers, not strengthening |
| Action-oriented question | DO NOT skip -- treat as action request | "How should I refactor X?" is an implicit action request |
| Multi-turn continuation | Skip grading -- context provides clarity | "now do the same for", "also", "next" derive clarity from conversation |
| Grade A (4.0-5.0) | Skip Steps 1-5 -- execute as-is | Prompt is already strong |
| Grade F (1.0-1.4) | Show grade + suggested rewrite with caveats | Fundamental issues -- draft rewrite, flag intent risk |

## Clarification Gate Sequencing

**Problem:** Both strengthening and the Clarification Gate can fire on the same
prompt, causing double-questioning (grade card + questions before any work).

**Sequencing protocol:**
1. Strengthening runs FIRST (Step 0-4)
2. After strengthening, re-evaluate the strengthened prompt against Clarification
   Gate triggers
3. If strengthening resolved the ambiguity (all dimensions now >= 4 post-fix):
   **skip the Clarification Gate** -- the prompt is clear enough to act on
4. If the strengthened prompt still has unresolved ambiguity (user's underlying
   intent is unclear, not just phrasing): **trigger the Clarification Gate**
   on the strengthened version
5. NEVER show both a full grade card AND a Clarification Gate question in the
   same response -- if both are needed, show the grade card first, then the
   first clarification question below it

---

## Context Gathering

### Tier 1 -- Always (every prompt)

| Source | What to Read | Why |
|--------|-------------|-----|
| `.claude/` patterns | Glob rules, skills, agents, hooks | Know what exists, avoid duplication |
| CLAUDE.md | Already loaded by system | Architecture, commands, conventions |
| Git state | `git status`, `git log --oneline -5` | Branch, recent work, uncommitted changes |

### Tier 2 -- Conditional

| Source | When to Read | What to Read |
|--------|-------------|-------------|
| Nearby files | Prompt mentions specific file/feature | Imports, dependencies, tests |
| `registry/patterns.json` | Pattern creation or comparison | Check existence, verify sync |

---

## Web Search Decision Tree

```
Is the prompt about existing code in this project?
  YES -> Read the code. DO NOT web search.
  NO  |
      v
Is the answer in CLAUDE.md or existing .claude/ patterns?
  YES -> Reference those. DO NOT web search.
  NO  |
      v
Is this general programming knowledge Claude already has?
  YES -> Does the answer depend on post-training-cutoff information?
    YES -> WEB SEARCH: training data may be stale.
    NO  -> Use training knowledge. DO NOT web search.
  NO  |
      v
Does the prompt reference an external library/API/tool?
  YES -> Is there existing code/config for it locally?
    YES -> Read local code first. Web search only if insufficient.
    NO  -> WEB SEARCH: fetch official docs.
  NO  |
      v
Does the prompt ask about versions, compatibility, or deprecations?
  YES -> WEB SEARCH: local code cannot answer these.
  NO  |
      v
Does the prompt ask to follow an official framework convention?
  YES -> WEB SEARCH: fetch authoritative source.
  NO  -> DO NOT web search. Proceed with available context.
```

**Resource CRUD exception:** When creating/updating a resource targeting a
specific external technology, ALWAYS web search for current docs.

---

## Resource CRUD Detection & Batch Approval

### Detection Signals

| Signal Type | Examples |
|------------|---------|
| CREATE | User describes repeated manual workflow; states convention to enforce; asks "can we enforce X" |
| UPDATE | User corrects Claude behavior an existing pattern should catch; extends a convention |
| DELETE | User says "we no longer use X"; codebase migrated away from a pattern's target |
| NO CRUD | Questions, feature implementation, bug fixes, test runs |

Default to NO CRUD when signals are ambiguous.

### Batch Approval Flow

1. Show enhancement summary (intent, context gathered, reasoning)
2. Present batch table with all proposed changes
3. User selects: `all` / `none` / `1,3` (comma-separated)
4. Execute approved items via delegation:
   - Skills -> `/writing-skills`
   - Rules -> `/claude-guardian`
   - Agents -> `skill-author` agent
   - Hooks -> manual workflow (create script + update settings.json)
5. Skip rejected items silently -- no re-prompting
6. **Timeout:** If the user's next message does not respond to the batch table
   (does not contain "all", "none", or comma-separated numbers), treat it as
   implicit "none" and proceed with the new topic. Do not re-present the batch.

---

## Prompt Reliability Scoring (Explicit Mode)

Activates when user explicitly asks to **score**, **evaluate**, or **audit** a
prompt. NOT used during automatic strengthening.

**How this differs from Step 0 grading:**

| Aspect | Step 0 Grading | Reliability Scoring |
|--------|---------------|-------------------|
| Purpose | Pre-execution triage (should we strengthen?) | Production-readiness audit (is this prompt safe to ship?) |
| When | Automatic, every non-trivial prompt | Explicit user request only |
| Scale | 1-5 per dimension, 6 dimensions | 1-10 per dimension, 5 dimensions |
| Unique dims | Role & Framing, Example Grounding | Edge-case Handling, Tone Consistency |
| Output | Grade card -> feeds into strengthening | Scoring report -> feeds into fix workflow |

Score across 5 dimensions (1-10 each): instruction clarity, output format,
constraint strength, edge-case handling, tone consistency. Every score requires
a specific quote from the prompt as evidence. Dimensions below 7 are launch risks.

Full scoring rubric: see `references/prompt-reliability-scoring.md`

**After scoring:** If user asks to fix, use the dimension->category mapping to
feed launch risks into the strengthening pipeline (Steps 0-5).

---

## File Inventory

| File | Location | Role | Lines |
|------|----------|------|-------|
| `prompt-enhance-reminder.sh` | `.claude/hooks/` + `core/.claude/hooks/` | Deterministic trigger | ~30 |
| `prompt-auto-enhance-rule.md` | `core/.claude/rules/` | Always-loaded behavioral context | ~40 |
| `prompt-auto-enhance.md` | `.claude/rules/` | Hub-only copy (kept in sync) | ~40 |
| `SKILL.md` | `core/.claude/skills/prompt-auto-enhance/` | Full workflow | ~480 |
| `grading-rubric.md` | `core/.claude/skills/prompt-auto-enhance/references/` | Dimension definitions | ~120 |
| `constraint-engineering.md` | `core/.claude/skills/prompt-auto-enhance/references/` | Constraint methodology | existing |
| `format-locking.md` | `core/.claude/skills/prompt-auto-enhance/references/` | Output format control | existing |
| `prompt-pruning.md` | `core/.claude/skills/prompt-auto-enhance/references/` | Weakening language (expanded) | existing |
| `prompt-reliability-scoring.md` | `core/.claude/skills/prompt-auto-enhance/references/` | Explicit scoring mode | existing |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-17 | Initial: 9 categories, context tiers, CRUD flow |
| 1.5.0 | 2026-03-23 | Added prompt reliability scoring mode |
| 1.5.1 | 2026-03-23 | Added constraint engineering + format locking references |
| **2.0.0** | **2026-03-31** | **Added Step 0 grading (6 dimensions), expanded to 11 categories, 3 guardrails, slimmed rule for SSOT, expanded weakening language (3 categories incl. Claude 4.x anti-patterns)** |

---

## Research Sources

Design decisions in v2.0 are grounded in external research:

| Decision | Source | URL | Key Finding |
|----------|--------|-----|-------------|
| Grade before diagnosing | Anthropic Prompt Improver | platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/prompt-improver | 4-step pipeline: extract -> restructure -> add CoT -> enhance |
| 6 weighted dimensions | KeepMyPrompts TCOF scoring | keepmyprompts.com/blog/en/ai-prompt-scoring-what-makes-a-good-prompt-and-how-to-measure-it | Cross-source consensus on clarity (25%), context (20%), structure (20%), role (15%), examples (10%), CoT (10%) |
| Max 5 fixes cap | Over-constraint paradox | medium.com/data-science-collective/the-science-of-prompt-optimization-and-automated-refinement | Too many constraints increase hallucination rates |
| Intent preservation check | Semantic drift in auto-rewriting | Same as above | #1 failure mode: rewrites shift intent while "sounding better" |
| Claude 4.x enforcement language | Anthropic Claude 4 Best Practices | platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices | "CRITICAL: YOU MUST" over-triggers on newer models; use normal directives |
| Weakening language expansion | Prompt Sensitivity Analysis | brics-econ.org/prompt-sensitivity-analysis-how-small-changes-in-instructions-break-llm-performance | Single word changes cause up to 463% accuracy variance (Llama-2-70B) |
| Prompt bloat threshold | Impact of Prompt Bloat on LLM Output Quality | home.mlops.community/public/blogs/the-impact-of-prompt-bloat-on-llm-output-quality | Quality degrades starting at ~3,000 tokens; semantically similar irrelevant context is most damaging |
| Recency bias | LLM positional bias research | Same as bloat source | Final items in lists get 2-3x weight |
| Prompt taxonomy | A Taxonomy of Prompt Defects in LLM Systems | arxiv.org/html/2509.14404v1 | Six-category defect taxonomy: overloaded, missing delimiters, undefined format, negative-only, implicit, placement |
| Meta-prompt structure | Anthropic Metaprompt Cookbook | github.com/anthropics/anthropic-cookbook/blob/main/misc/metaprompt.ipynb | Role + input vars + guidelines + examples + output format + scratchpad |

---

## Adversarial Review Summary

27 findings from adversarial review (2026-03-31). All Critical and High
findings have been mitigated in this spec:

| Severity | Count | Key Mitigations Applied |
|----------|-------|------------------------|
| Critical (4) | 4/4 addressed | Implementation status header, grading-rubric.md marked for creation, Clarification Gate sequencing, SSOT future-state labeled |
| High (5) | 5/5 addressed | Floor rule for degenerate scores, Critical fixes uncapped, Grade D added, atomic deployment note, allowed-tools documented |
| Medium (10) | 10/10 addressed | Temporal dependencies in IMPLICIT_ASSUMPTIONS, model condition on Category B, missing weakening words added, training cutoff in decision tree, batch timeout, compact output for Grade B, Grade F provides suggested rewrite, multi-turn skip, question skip refined, intent examples added |
| Low (8) | 5/8 accepted | Weight justification noted, scoring systems distinguished, grade in indicator; hub sync and full regression testing deferred |
