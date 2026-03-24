---
name: prompt-auto-enhance
description: >
  Strengthen non-trivial prompts by diagnosing weak spots, mapping fixes, and
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
version: "1.5.0"
---

# Prompt Auto-Enhance — Strengthening & Resource CRUD Procedures

This skill strengthens non-trivial prompts before execution (diagnose → fix → rewrite
→ show before/after) and handles the **visible mode** workflow when resource CRUD is
detected. The `prompt-auto-enhance` global rule controls when this activates.

**Arguments:** $ARGUMENTS

---

## Prompt Strengthening

Activates automatically for **non-trivial prompts** — same threshold as the
Clarification Gate (ambiguous, multi-file, or multi-step). Skipped for direct
unambiguous instructions (e.g., "run tests", "rename X to Y", "fix the typo on line 42").

Adapted from community pattern by @heyrimsha (source: x.com/heyrimsha/status/2035995286150234480).

### STEP 1: Diagnose Prompt Weaknesses

Analyze the user's prompt against the failure category table. Classify every
weakness found — a prompt may have multiple.

#### Failure Category Table

| Category | Symptoms | Structural Fix |
|----------|----------|---------------|
| **VAGUE_INTENT** | Unclear what the user wants done; could be interpreted multiple ways | Rewrite as a specific action verb + object + success criteria |
| **MISSING_CONTEXT** | Prompt assumes knowledge not provided (file paths, prior decisions, domain terms) | Add explicit context: which files, which module, what prior state |
| **CONFLICTING_CONSTRAINTS** | Prompt asks for contradictory things ("make it fast and thorough", "simple but handles all edge cases") | Identify the conflict, prioritize one, note the tradeoff |
| **OVER_SCOPED** | Prompt asks for too many things at once; would require 5+ files changed | Break into sequential focused prompts, suggest ordering |
| **UNDER_CONSTRAINED** | Prompt gives freedom where specificity is needed (output format, target files, approach). Apply the measurability test: "Can a reviewer objectively verify this constraint was followed?" (see `references/constraint-engineering.md`) | Add measurable constraints: format, scope boundaries, acceptance criteria. Replace vague terms ("be concise" → "under 100 words", "be thorough" → "cover all N checklist items") |
| **MISSING_OUTPUT_SPEC** | No indication of what the result should look like | Add a locked output template with named sections, explicit order, and numeric length bounds (see `references/format-locking.md`) |
| **AMBIGUOUS_SCOPE** | Unclear which files, modules, or layers are in scope | Add explicit scope boundaries ("only in src/api/", "just the tests") |
| **IMPLICIT_ASSUMPTIONS** | Prompt relies on assumptions that may not hold (env setup, dependencies, prior steps) | Make assumptions explicit or add verification steps |
| **MISSING_STRUCTURE** | Complex multi-part prompt uses flat unstructured text where XML tags would improve clarity and adherence | Restructure with XML tags (see XML Tag Reference below) |

#### XML Tag Reference

Claude is trained on XML-structured prompts. Using XML tags for complex,
multi-part prompts improves constraint adherence by ~12% and response quality
by up to 30% for long-context inputs (per Anthropic's official documentation).

**When to apply XML structuring:**
- Prompt mixes instructions, context, data, and constraints
- Prompt has 3+ distinct parts (task, rules, examples, output format)
- Prompt includes long context or multiple documents

**When NOT to apply:**
- Simple single-intent queries ("run tests", "rename X to Y")
- Prompts that are already 1-2 sentences
- Over-tagging adds noise without benefit — use 3-7 tags, not more

**Core tags (ordered by frequency of use):**

| Tag | Purpose | Use When |
|-----|---------|----------|
| `<task>` | Define what must be done | Every complex prompt — the single most important tag |
| `<context>` | Background information needed for the task | Prompt assumes knowledge not explicitly stated |
| `<instructions>` | Step-by-step directives | Task has a specific procedure to follow |
| `<constraints>` / `<rules>` | Explicit limitations and behavioral rules | Task has non-obvious boundaries or MUST/MUST NOT rules |
| `<output_format>` | Desired response structure | Output must match a specific schema, table, or format |
| `<examples>` | Few-shot demonstrations (3-5 examples) | Task benefits from showing input→output patterns |
| `<input>` | Variable user data, separated from instructions | Prompt mixes static instructions with dynamic data |
| `<documents>` | Container for long multi-document context | Multiple source documents need to be referenced |
| `<thinking>` | Scratchpad for chain-of-thought reasoning | Task requires step-by-step reasoning before answering |
| `<answer>` | Final output, separated from reasoning | Used with `<thinking>` to cleanly extract the result |

**Behavioral tags (self-describing constraint blocks):**

Anthropic uses tag names as the instruction itself in system prompts:
```xml
<default_to_action>Implement changes directly instead of suggesting them.</default_to_action>
<investigate_before_answering>Read relevant files before making claims.</investigate_before_answering>
```

**Structuring rules:**
- Tag names MUST be descriptive and consistent — `<patient_records>` not `<data1>`
- Nest tags when content has natural hierarchy
- Place long context ABOVE the query (improves quality by up to 30%)
- Do not wrap single sentences in tags — tags are for content blocks

**Reference:** See [references/constraint-engineering.md](references/constraint-engineering.md) for the
full constraint engineering methodology, measurability test table, and audit output format.

If no weaknesses are found (prompt scores clean), skip to execution — do not
force unnecessary rewrites.

### STEP 2: Map Fixes

For each diagnosed weakness, determine the minimal structural fix. Each fix
MUST map to exactly one failure category — no fix without a diagnosis, no
diagnosis without a fix.

Format:
```
Diagnosis:
  [1] CATEGORY_NAME → specific fix description
  [2] CATEGORY_NAME → specific fix description
```

### STEP 3: Rewrite the Prompt

Apply all fixes to produce a strengthened version. Rules:
- Targeted changes only — do not rewrite parts that are already clear
- Preserve the user's original intent and voice
- Do not add complexity unless it directly eliminates a diagnosed weakness
- Do not change terminology the user chose unless it causes ambiguity
- When MISSING_STRUCTURE is diagnosed, wrap distinct prompt sections in XML tags
  (e.g., `<task>`, `<context>`, `<constraints>`, `<output_format>`) — use the
  XML Tag Reference above to select appropriate tags
- Place long context above the query, constraints near the task definition

### STEP 4: Show Before/After

MUST show the comparison to the user every time strengthening activates.
This is NOT optional — visibility builds trust and helps users learn.

```
Prompt Strengthened (N fixes):
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
`*Enhanced: prompt strengthened (N fixes), git state, 2 rules*`

### STEP 5: Execute

Proceed with the strengthened prompt as if the user had entered it directly.
The rest of the auto-enhance pipeline (Tier 1/2 context, Clarification Gate,
CRUD detection) applies to the strengthened version, not the original.

### When NOT to Strengthen

| Condition | Action |
|-----------|--------|
| Direct unambiguous instruction | Skip — execute as-is |
| Single-file simple change | Skip — no diagnosis needed |
| User says "do exactly this" or quotes a specific command | Skip — respect explicit intent |
| Prompt is a question (not an action request) | Skip — just answer it |
| All 9 categories score clean | Skip — prompt is already strong |

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
reference to feed launch risks directly into the strengthening workflow (Steps 1-5 above).

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

Use this decision tree when evaluating whether to search the web:

```
Is the prompt about existing code in this project?
  YES → Read the code. DO NOT web search.
  NO  ↓

Is the answer in CLAUDE.md or existing .claude/ patterns?
  YES → Reference those. DO NOT web search.
  NO  ↓

Is this general programming knowledge Claude already has?
  YES → Use training knowledge. DO NOT web search.
  NO  ↓

Does the prompt reference an external library/API/tool?
  YES → Is there existing code/config for it locally?
    YES → Read local code first. Web search only if insufficient.
    NO  → WEB SEARCH: fetch official docs for the technology.
  NO  ↓

Does the prompt ask about versions, compatibility, or deprecations?
  YES → WEB SEARCH: local code cannot answer these.
  NO  ↓

Does the prompt ask to follow an official framework convention?
  YES → WEB SEARCH: fetch authoritative source, do not guess.
  NO  → DO NOT web search. Proceed with available context.
```

### Resource CRUD Exception

When creating or updating a resource that targets a specific external technology:
ALWAYS web search for current documentation regardless of other conditions.
Training data may be outdated for fast-evolving libraries.

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

- ALWAYS gather Tier 1 context before responding to any prompt — Why: without it, you risk duplicating existing patterns or contradicting CLAUDE.md conventions
- ALWAYS run Prompt Strengthening for non-trivial prompts before execution — Why: vague prompts produce inconsistent outputs that require rework
- ALWAYS show the before/after comparison table when strengthening activates — Why: silent changes erode user trust and prevent learning
- ALWAYS include strengthening count in the `*Enhanced:*` indicator when fixes are applied — Why: signals to the user that enhancement ran, enabling feedback
- ALWAYS run the Clarification Gate for ambiguous or multi-file prompts before acting — Why: acting on assumptions wastes effort when the guess is wrong
- ALWAYS read relevant code before asking a clarification question — Why: asking answerable questions signals laziness and breaks flow
- ALWAYS present the batch table when resource CRUD is detected — Why: resource changes without approval create unwanted artifacts
- ALWAYS wait for explicit user approval before creating/updating/deleting — Why: unauthorized changes force manual cleanup and break trust
- ALWAYS delegate to existing authoring tools — Why: ad-hoc generation bypasses quality gates and produces inconsistent patterns
- ALWAYS apply the measurability test to constraints: "Can a reviewer objectively verify this was followed?" (see `references/constraint-engineering.md`) — Why: unmeasurable constraints produce inconsistent behavior across invocations

## MUST NOT DO

- MUST NOT strengthen direct unambiguous instructions — respect explicit user intent instead — Why: over-strengthening adds latency and annoys the user
- MUST NOT add complexity during strengthening that doesn't map to a diagnosed weakness — simplify instead — Why: unnecessary constraints degrade prompt quality
- MUST NOT change the user's original intent during strengthening — only clarify and constrain — Why: intent drift causes the wrong task to be executed
- MUST NOT create, update, or delete resources without batch approval — present the batch table first — Why: unauthorized resource changes create cleanup overhead
- MUST NOT re-prompt for rejected items in the same session — drop them silently — Why: nagging after explicit rejection breaks the approval contract
- MUST NOT web search when local context is sufficient — read code first — Why: web searches add latency and may return outdated information
- MUST NOT generate patterns directly — use `/writing-skills`, `/claude-guardian`, or `skill-author` agent — Why: direct generation bypasses quality checklist validation
- MUST NOT suggest resource changes when signals are ambiguous — default to no CRUD and proceed normally — Why: false positives train the user to ignore CRUD suggestions
