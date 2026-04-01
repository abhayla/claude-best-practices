---
name: prompt-auto-enhance
description: >
  Diagnose and strengthen non-trivial prompts by mapping weak spots to fixes and
  rewriting before execution — with visible before/after comparison. Also handles
  resource CRUD batch approval flow, delegation routing, and web search decisions.
  Invoked by the prompt-auto-enhance rule when resource changes are detected,
  or explicitly via /prompt-auto-enhance for manual enhancement.
triggers:
  - prompt-auto-enhance
  - auto-enhance
  - enhance prompt
  - enrich prompt
  - strengthen prompt
  - fix my prompt
  - score prompt
  - evaluate prompt
allowed-tools: "Read Grep Glob Skill Agent"
argument-hint: "[prompt text to enhance or 'score' to evaluate reliability]"
type: workflow
version: "2.0.0"
---

# Prompt Auto-Enhance — Strengthening & Resource CRUD Procedures

This skill strengthens non-trivial prompts before execution (grade → diagnose → fix → rewrite
→ show grade card + before/after) and handles the **visible mode** workflow when resource CRUD is
detected. The `prompt-auto-enhance` global rule controls when this activates.

**Arguments:** $ARGUMENTS

---

Activates automatically for **non-trivial prompts** — same threshold as the
Clarification Gate (ambiguous, multi-file, or multi-step). Skipped for direct
unambiguous instructions (e.g., "run tests", "rename X to Y", "fix the typo on line 42").

Adapted from community pattern by @heyrimsha (source: x.com/heyrimsha/status/2035995286150234480).

## STEP 0: Quick Grade

Score the prompt across 6 dimensions to determine pipeline depth.

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Intent Clarity | 0.25 | Is the action verb, target, and success criteria explicit? |
| Context Sufficiency | 0.20 | Does the prompt provide all needed background (files, prior state, domain)? |
| Constraint Precision | 0.20 | Are boundaries measurable and unambiguous? |
| Output Specification | 0.15 | Is the expected result format defined? |
| Role & Framing | 0.10 | Is there a persona, domain frame, or expertise level? |
| Example Grounding | 0.10 | Are input/output examples provided for complex tasks? |

**Score formula:** `Overall = Sum(weight_i x score_i)` — each dimension scored 1.0-5.0.

**Grade thresholds:**

| Grade | Range | Action |
|-------|-------|--------|
| A | 4.0-5.0 | Skip strengthening — prompt is strong |
| B | 3.0-3.9 | Targeted fix — compact mode (1-2 fixes only) |
| C | 2.0-2.9 | Full pipeline — diagnose all weak dimensions |
| D | 1.5-1.9 | Full pipeline with heavy warning to user |
| F | 1.0-1.4 | Suggested rewrite with caveats — original may be unsalvageable |

**Floor rules:**
- Any dimension scoring 1 caps the grade at B (regardless of overall score)
- Intent Clarity OR Context Sufficiency scoring 1 forces Grade F
- More than 5 Critical issues (from STEP 1) forces Grade F

**Dimension-to-Category mapping:**

| Dimension < 4 | Diagnose These Categories |
|----------------|--------------------------|
| Intent Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE |
| Context Sufficiency | MISSING_CONTEXT, IMPLICIT_ASSUMPTIONS |
| Constraint Precision | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS |
| Output Specification | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE |
| Role & Framing | MISSING_ROLE |
| Example Grounding | MISSING_EXAMPLES |

**Read:** `references/grading-rubric.md` for full scoring anchors per dimension.

Only diagnose categories mapped from dimensions scoring < 4 — skip categories
whose parent dimension already scores 4+.

## STEP 1: Diagnose Prompt Weaknesses

Analyze the user's prompt against the failure category table. Classify every
weakness found — a prompt may have multiple.

#### Failure Category Table

| Category | Severity | Symptoms | Structural Fix |
|----------|----------|----------|---------------|
| **VAGUE_INTENT** | Critical | Unclear what the user wants done; could be interpreted multiple ways | Rewrite as a specific action verb + object + success criteria |
| **MISSING_CONTEXT** | Critical | Prompt assumes knowledge not provided (file paths, prior decisions, domain terms) | Add explicit context: which files, which module, what prior state |
| **CONFLICTING_CONSTRAINTS** | High | Prompt asks for contradictory things ("make it fast and thorough", "simple but handles all edge cases") | Identify the conflict, prioritize one, note the tradeoff |
| **OVER_SCOPED** | High | Prompt asks for too many things at once; would require 5+ files changed | Break into sequential focused prompts, suggest ordering |
| **UNDER_CONSTRAINED** | Medium | Prompt gives freedom where specificity is needed (output format, target files, approach). Apply the measurability test: "Can a reviewer objectively verify this constraint was followed?" (see `references/constraint-engineering.md`) | Add measurable constraints: format, scope boundaries, acceptance criteria. Replace vague terms ("be concise" -> "under 100 words", "be thorough" -> "cover all N checklist items") |
| **MISSING_OUTPUT_SPEC** | Medium | No indication of what the result should look like | Add a locked output template with named sections, explicit order, and numeric length bounds (see `references/format-locking.md`) |
| **AMBIGUOUS_SCOPE** | Medium | Unclear which files, modules, or layers are in scope | Add explicit scope boundaries ("only in src/api/", "just the tests") |
| **IMPLICIT_ASSUMPTIONS** | Low | Prompt relies on assumptions that may not hold (env setup, dependencies, prior steps) | Make assumptions explicit or add verification steps |
| **MISSING_STRUCTURE** | Low | Complex multi-part prompt uses flat unstructured text where XML tags would improve clarity and adherence | Restructure with XML tags (see XML Tag Reference below) |
| **MISSING_ROLE** | Low | No persona or domain frame | Add role with expertise and perspective |
| **MISSING_EXAMPLES** | Low | No input/output examples for complex tasks | Add 2-3 diverse examples in `<examples>` tags |

**Severity handling:**

| Severity | Behavior |
|----------|----------|
| Critical | Always included — Critical fixes are NEVER capped |
| High | Included up to the max changes cap |
| Medium | Included up to the max changes cap |
| Low | Included only if budget remains |

#### XML Tag Reference

Use XML tags when prompts mix instructions, context, data, and constraints
(3+ distinct parts). Skip for simple single-intent queries or 1-2 sentence prompts.
Use 3-7 tags max — over-tagging adds noise.

**Core tags:** `<task>` (what to do), `<context>` (background), `<instructions>` (steps),
`<constraints>`/`<rules>` (limits), `<output_format>` (result shape), `<examples>` (few-shot),
`<input>` (variable data), `<documents>` (multi-doc context), `<thinking>` (reasoning),
`<answer>` (final output).

**Rules:** Descriptive tag names (`<patient_records>` not `<data1>`), nest for hierarchy,
place long context ABOVE the query, do not wrap single sentences.

**Reference:** See [references/constraint-engineering.md](references/constraint-engineering.md) for the
full constraint engineering methodology and measurability test table.

#### Weakening Language Flags

After category diagnosis, scan for words and phrases that weaken instruction
clarity. These are automatic flags — every occurrence MUST be evaluated for
removal or replacement (see `references/prompt-pruning.md` for the full source pattern):

**Category A — Hedging & Filler:**

| Flag Pattern | Problem | Replace With |
|---|---|---|
| "try to", "attempt to" | Permits failure as acceptable | Direct imperative ("do X") |
| "if possible", "when feasible" | Creates an opt-out clause | Remove, or state the specific condition |
| "maybe", "perhaps", "might" | Introduces uncertainty into instructions | Commit to a direction or use conditional logic |
| "I think", "I believe" | Weakens authority of the instruction | State the requirement directly |
| "please", "kindly" | Politeness filler in technical prompts | Remove — instructions are not requests |
| "etc.", "and so on", "and more" | Unbounded scope | List all items explicitly |
| "simple", "just", "easily" | Minimizes complexity, sets false expectations | Remove — let the task speak for itself |
| "as needed", "as appropriate" | Delegates decision without criteria | Specify the criteria for when/how |
| "feel free to" | Implied optionality for required behavior | Remove |
| "don't worry about" | Unclear exclusion scope | State what TO do |
| "roughly/approximately" (when precision needed) | Vague threshold where exact value matters | State exact threshold |

#### Category B — Aggressive Enforcement Anti-Patterns (Claude 4.x specific)

Model condition: These flags apply to Claude 4.x and later.

| Flag Pattern | Problem | Replace With |
|---|---|---|
| "CRITICAL:/IMPORTANT:/YOU MUST" | Aggressive emphasis degrades compliance in newer models | Normal directive |
| "NEVER EVER/ABSOLUTELY MUST" | Over-emphatic phrasing triggers resistance | Standard MUST/NEVER |
| "think step by step" (reasoning models) | Redundant for models with built-in reasoning | "evaluate"/"reason through" |

#### Category C — Output-Side Anti-Patterns (Claude self-correction)

| Flag Pattern | Problem | Replace With |
|---|---|---|
| "Certainly!/Of course!/Absolutely!" | Sycophantic opener wastes tokens | Lead with the answer |
| "Based on the information provided..." | Filler preamble | Remove |
| "I'd be happy to help with..." | Unnecessary pleasantry | Remove |

**Pruning rule:** Every removal MUST improve precision — do not cut words just
to reduce length. If a qualifier serves a genuine purpose (e.g., "if the file
exists" is a real condition, not hedging), keep it.

If no weaknesses are found (prompt scores clean), skip to execution — do not
force unnecessary rewrites.

## STEP 2: Map Fixes

For each diagnosed weakness, determine the minimal structural fix. Each fix
MUST map to exactly one failure category — no fix without a diagnosis, no
diagnosis without a fix.

Format:
```
Diagnosis:
  [1] CATEGORY_NAME → specific fix description
  [2] CATEGORY_NAME → specific fix description
```

## STEP 3: Rewrite with Guardrails

Apply all fixes to produce a strengthened version.

#### Guardrail 1: Max Changes Cap

- Maximum **5 non-Critical fixes** per rewrite
- Critical severity fixes are NEVER capped — always apply all of them
- Grade D: full pipeline runs but show a heavy warning to the user
- Grade F: present a suggested rewrite with caveats (original may need rethinking)

#### Guardrail 2: Intent Preservation Check

Every rewrite MUST preserve: same action verb, same target, same output type,
no new requirements added. Verify before presenting.

| | Original | Rewritten | Verdict |
|---|---|---|---|
| PASS | "fix the login bug" | "resolve auth failure in login.py:42" | Same intent, more specific |
| FAIL | "review auth module" | "refactor auth module to use JWT" | Changed intent from review to refactor |

#### Guardrail 3: Over-Constraint Detection

- Soft warning if >3 constraints added in a single rewrite
- Hard gate: intent preservation check (Guardrail 2) overrides constraint additions
- Check for contradictions between added constraints

**General rewrite rules:**
- Targeted changes only — do not rewrite parts that are already clear
- Preserve the user's original intent and voice
- Do not add complexity unless it directly eliminates a diagnosed weakness
- Do not change terminology the user chose unless it causes ambiguity
- Remove qualifiers and hedging language flagged in Step 1
- When MISSING_STRUCTURE is diagnosed, wrap distinct prompt sections in XML tags
- Place long context above the query, constraints near the task definition

## STEP 4: Show Grade Card + Before/After

MUST show the grade card and comparison to the user every time strengthening activates.

**Compact mode** (Grade B, 1-2 fixes):
```
Grade: B (3.4) — 1 fix applied
  [1] UNDER_CONSTRAINED → added output format spec
```

**Full mode** (Grade C/D/F):
```
Prompt Grade Card:
┌────────────────────────┬───────┬────────┬─────────────┐
│ Dimension              │ Score │ Weight │ Action       │
├────────────────────────┼───────┼────────┼─────────────┤
│ Intent Clarity         │  4.0  │  0.25  │ —            │
│ Context Sufficiency    │  2.5  │  0.20  │ Fixed [1,2]  │
│ Constraint Precision   │  3.0  │  0.20  │ Fixed [3]    │
│ Output Specification   │  2.0  │  0.15  │ Fixed [4]    │
│ Role & Framing         │  4.5  │  0.10  │ —            │
│ Example Grounding      │  3.0  │  0.10  │ Skipped      │
├────────────────────────┼───────┼────────┼─────────────┤
│ Overall                │  3.15 │        │ Grade: C     │
└────────────────────────┴───────┴────────┴─────────────┘

Prompt Strengthened (4 fixes, 12 words removed):
┌─────────────────┬──────────────────────────────────────────────┐
│ Original        │ [user's original prompt text]                │
├─────────────────┼──────────────────────────────────────────────┤
│ Strengthened    │ [rewritten prompt text]                      │
├─────────────────┼──────────────────────────────────────────────┤
│ Changes Applied │                                              │
│  [1]            │ CATEGORY → what was changed and why          │
│  [2]            │ CATEGORY → what was changed and why          │
└─────────────────┴──────────────────────────────────────────────┘
Proceeding with strengthened prompt...
```

Update the `*Enhanced:*` indicator to include strengthening:
`*Enhanced: prompt strengthened (N fixes, Grade X), git state, 2 rules*`

## STEP 5: Execute

Proceed with the strengthened prompt as if the user had entered it directly.
The rest of the auto-enhance pipeline (Tier 1/2 context, Clarification Gate,
CRUD detection) applies to the strengthened version, not the original.

### When NOT to Strengthen

| Condition | Action |
|-----------|--------|
| Direct unambiguous instruction | Skip — execute as-is |
| Single-file simple change | Skip — no diagnosis needed |
| User says "do exactly this" or quotes a specific command | Skip — respect explicit intent |
| Pure knowledge question (not an action request) | Skip — just answer it |
| Action-oriented question ("how should I test this?") | DO NOT skip — strengthen before answering |
| Multi-turn continuation ("now do", "same for", "also", "next") | Skip grading — apply prior context |
| All dimensions score >= 4 (Grade A) | Skip — prompt is already strong |

## Clarification Gate Sequencing

Strengthening runs FIRST, before the Clarification Gate is evaluated.

After strengthening, re-evaluate against Clarification Gate triggers:
- If all dimensions >= 4 post-fix: skip Clarification Gate entirely
- If unresolved ambiguity remains (dimensions still < 3): trigger Clarification Gate on the **strengthened** version
- NEVER show both full grade card AND clarification question in the same response without the grade card appearing first

---

## Prompt Reliability Scoring

Activates when the user explicitly asks to **score**, **evaluate**, or **audit** a prompt's
production readiness — not during automatic strengthening.

Score the prompt across 5 dimensions (instruction clarity, output format, constraint strength,
edge case handling, tone consistency) on a 1-10 scale. Every score requires a specific quote
from the prompt as evidence. Dimensions below 7 are flagged as launch risks.

**Read:** `references/prompt-reliability-scoring.md` for the full scoring rubric with dimension
definitions, output template, category mapping to the 9-category diagnosis, and anti-patterns.

**After scoring:** If the user asks to fix the prompt, use the category mapping table in the
reference to feed launch risks directly into the strengthening workflow (Steps 0-5 above).

---

## Batch Approval Flow

When the global rule detects that a user's prompt implies creating, updating, or
deleting Claude Code resources (skills, agents, rules, hooks), execute this flow:

### Step 1: Show Enhancement Summary

Present the user with what was understood and gathered:

```
Enhancement Summary:
  Intent: [interpreted user intent in one sentence]
  Context gathered:
    - [Tier 1/2 sources read, e.g., "CLAUDE.md", "git status", ".claude/rules/"]
    - [Web sources fetched, if any]
  Reasoning: [why resource changes are needed]
```

### Step 2: Present Batch Table

List ALL proposed resource changes in a single table:

```
Proposed resource changes:
  [1] CREATE rule:  <name>  — <one-line description>
  [2] UPDATE skill: <name>  — <what changes>
  [3] DELETE hook:  <name>  — <why obsolete>
  [4] CREATE agent: <name>  — <one-line description>

Approve which? (all / none / 1,3 / ...)
```

Rules for the batch table:
- Group related changes together (e.g., a skill + its supporting rule)
- For items where purpose or content cannot be determined with confidence,
  append `[NEEDS CLARIFICATION: <question>]` and let the user clarify
- Show the action verb (CREATE / UPDATE / DELETE) and resource type for each

### Step 3: Wait for User Selection

The user responds with one of:
- `all` — approve every item
- `none` — reject everything, proceed with the original prompt normally
- `1,3` — approve only items 1 and 3 (comma-separated numbers)
- Clarification text — if they answer a `[NEEDS CLARIFICATION]` question,
  update the batch table and re-present

### Step 4: Execute Approved Items

For each approved item, delegate to the appropriate authoring tool:

| Resource Type | Delegate To | How |
|---------------|-------------|-----|
| **Skill** | `/writing-skills` | `Skill(skill="writing-skills")` with the skill name and description |
| **Rule** | `/claude-guardian` | `Skill(skill="claude-guardian")` with the rule text |
| **Agent** | `skill-author` agent | `Agent(prompt="Create agent: <description>", subagent_type="skill-author")` |
| **Hook** | Manual workflow | Create shell script in `.claude/hooks/`, update `settings.json` |

Execute items sequentially — each resource may depend on the previous one
(e.g., a skill might reference a rule created in the same batch).

### Step 5: Skip Rejected Items

Items the user did not approve are dropped silently. MUST NOT re-prompt for
rejected items later in the same session.

---

## Web Search Decision Tree

DO NOT web search if: prompt is about existing code, answer is in CLAUDE.md/.claude/ patterns,
or it is general programming knowledge. WEB SEARCH only for: external library/API docs (when
no local code exists), version/compatibility/deprecation questions, official framework conventions.
Read local code first when local config exists for the library.

**CRUD Exception:** When creating/updating a resource targeting an external technology,
ALWAYS web search for current docs — training data may be outdated.

---

## Context Gathering Reference

### Tier 1 — Always (every prompt)

| Source | What to Read | Why |
|--------|-------------|-----|
| `.claude/` patterns | `Glob("core/.claude/{rules,skills,agents,hooks}/**")` and `Glob(".claude/{rules,skills,agents,hooks}/**")` | Know what exists to avoid duplication |
| CLAUDE.md | Already loaded by system | Architecture, commands, conventions |
| Git state | `git status`, `git log --oneline -5` | Current branch, recent work, uncommitted changes |

### Tier 2 — Conditional

| Source | When to Read | What to Read |
|--------|-------------|-------------|
| Nearby files | Prompt mentions a specific file/feature/module | Imports, dependencies, tests, related modules |
| `registry/patterns.json` | Prompt involves pattern creation or comparison | Check if pattern already exists, verify sync |

### Clarification Gate (after Tier 1/2)

After context gathering, if the prompt is ambiguous or multi-file, enter a
clarification loop before acting. See the `prompt-auto-enhance` rule for full
trigger/skip conditions. Key principles:
- Read relevant code before each question — MUST NOT ask what you can answer yourself
- One question at a time, with a recommendation and reasoning
- 3-5 questions max, then present the plan section by section for approval

---

## CRUD Detection Signals

### CREATE signals
- User describes a repeated workflow they do manually
- User states a convention that should always be followed
- User asks "can we enforce X" or "how do I make Claude always do Y"
- User describes a review persona or specialized analysis task

### UPDATE signals
- User corrects Claude's behavior that an existing rule/skill should have caught
- User says "also do X when running /skill-name"
- User extends a convention beyond what the current rule covers
- Existing pattern is outdated or incomplete for the user's needs

### DELETE signals
- User says "we no longer use X" or "remove the X rule"
- User's codebase has migrated away from a technology a pattern targets
- A pattern contradicts a newer pattern the user approved

### NO CRUD signals
- User asks a question (just answer it)
- User asks to implement a feature (just implement it)
- User asks to fix a bug (just fix it)
- User asks to run tests (just run them)

When in doubt, default to NO CRUD — do not suggest resource changes unless
the signals are clear.

---

## MUST DO

- ALWAYS run STEP 0 (Quick Grade) before diagnosing — skip diagnosis entirely for Grade A
- ALWAYS gather Tier 1 context before responding to any prompt — Why: without it, you risk duplicating existing patterns or contradicting CLAUDE.md conventions
- ALWAYS run Prompt Strengthening for non-trivial prompts before execution — Why: vague prompts produce inconsistent outputs that require rework
- ALWAYS show the grade card + before/after comparison when strengthening activates — Why: silent changes erode user trust and prevent learning
- ALWAYS include strengthening count in the `*Enhanced:*` indicator when fixes are applied — Why: signals to the user that enhancement ran, enabling feedback
- ALWAYS run the Clarification Gate for ambiguous or multi-file prompts before acting — Why: acting on assumptions wastes effort when the guess is wrong
- ALWAYS read relevant code before asking a clarification question — Why: asking answerable questions signals laziness and breaks flow
- ALWAYS present the batch table when resource CRUD is detected — Why: resource changes without approval create unwanted artifacts
- ALWAYS wait for explicit user approval before creating/updating/deleting — Why: unauthorized changes force manual cleanup and break trust
- ALWAYS delegate to existing authoring tools — Why: ad-hoc generation bypasses quality gates and produces inconsistent patterns
- ALWAYS apply the measurability test to constraints: "Can a reviewer objectively verify this was followed?" (see `references/constraint-engineering.md`) — Why: unmeasurable constraints produce inconsistent behavior across invocations
- ALWAYS enforce Guardrail 2 (Intent Preservation) — rewrite MUST NOT change the user's action verb, target, or output type

## MUST NOT DO

- MUST NOT strengthen direct unambiguous instructions — respect explicit user intent instead — Why: over-strengthening adds latency and annoys the user
- MUST NOT add complexity during strengthening that doesn't map to a diagnosed weakness — simplify instead — Why: unnecessary constraints degrade prompt quality
- MUST NOT change the user's original intent during strengthening — only clarify and constrain — Why: intent drift causes the wrong task to be executed
- MUST NOT exceed the max changes cap (5 non-Critical) without explicit user request — Why: over-fixing degrades the original voice and adds noise
- MUST NOT create, update, or delete resources without batch approval — present the batch table first — Why: unauthorized resource changes create cleanup overhead
- MUST NOT re-prompt for rejected items in the same session — drop them silently — Why: nagging after explicit rejection breaks the approval contract
- MUST NOT web search when local context is sufficient — read code first — Why: web searches add latency and may return outdated information
- MUST NOT generate patterns directly — use `/writing-skills`, `/claude-guardian`, or `skill-author` agent — Why: direct generation bypasses quality checklist validation
- MUST NOT suggest resource changes when signals are ambiguous — default to no CRUD and proceed normally — Why: false positives train the user to ignore CRUD suggestions
