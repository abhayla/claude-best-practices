---
name: prompt-auto-enhance
description: >
  Diagnose and strengthen non-trivial prompts by mapping weak spots to fixes and
  rewriting before execution — with visible step transcript, final prompt preview,
  and before/after comparison. Also handles resource CRUD batch approval flow,
  delegation routing, and web search decisions. Invoked by the prompt-auto-enhance
  rule when resource changes are detected, or explicitly via /prompt-auto-enhance
  for manual enhancement.
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
version: "3.0.2"
---

# Prompt Auto-Enhance — Strengthening, Step Transcript, Final Preview, Resource CRUD

This skill strengthens non-trivial prompts before execution and shows the full
working — every step's output, the final strengthened prompt, and the
before/after comparison — so the user can see exactly what was changed and why.
The `prompt-auto-enhance` global rule controls when this activates; the
`prompt-enhance-reminder.sh` hook gates triggering at the deterministic layer
(prompts ≤15 chars and continuation phrases never reach this skill).

**Arguments:** $ARGUMENTS

---

## Activation

Activates for **non-trivial prompts** — anything the hook did not filter out.
Skipped at the hook layer for:
- Prompts ≤ 15 characters (after trimming whitespace)
- Known continuation phrases ("yes", "ok", "continue", "now do …", "also …", etc.)

Adapted from community pattern by @heyrimsha (source: x.com/heyrimsha/status/2035995286150234480).

## STEP 0: Quick Grade

Score the prompt across 6 base dimensions (plus Tone if active) on a **1-10**
scale. Only dimensions scoring below 7 are diagnosed.

| Dimension | Default Weight | Weight w/ Tone Active | Measures |
|-----------|---------------|----------------------|----------|
| Intent Clarity | 0.25 | 0.25 | Action verb + target + success criteria explicit |
| Context Sufficiency | 0.20 | 0.20 | All needed background present |
| Constraint Precision | 0.20 | 0.20 | Boundaries measurable and unambiguous |
| Output Specification | 0.15 | 0.15 | Expected result format defined |
| Role & Framing | 0.10 | 0.05 | Persona, domain, expertise level |
| Example Grounding | 0.10 | 0.05 | Input/output examples for complex tasks |
| Tone Consistency | 0.00 | 0.10 | Voice/register/audience (prose only) |

**Tone activation signals:** prompt targets prose, creative writing, marketing
copy, UX/UI text, email, blog post, tweet, landing page, error message text.
Triggered by words like "write", "draft", "compose", "rewrite", "tone",
"voice", "audience", "copy".

**Score formula:** `Overall = Sum(weight_i x score_i)` — Range 1.0-10.0

**Grade thresholds:**

| Grade | Range | Action |
|-------|-------|--------|
| A | 8.0-10.0 | Skip strengthening — prompt is strong |
| B | 6.0-7.9 | Targeted fix — compact mode (1-2 fixes only) |
| C | 4.0-5.9 | Full pipeline — diagnose all weak dimensions |
| D | 3.0-3.9 | Full pipeline with heavy warning to user |
| F | 1.0-2.9 | Suggested rewrite with caveats — original may be unsalvageable |

**Floor rules (precedence — first match wins):**

1. Intent Clarity OR Context Sufficiency scoring 1-2 → **Grade F**
2. More than 5 Critical issues diagnosed → **Grade F**
3. Any other single dimension scoring 1-2 → cap at **Grade B (max 7.9)**
4. Otherwise → use the threshold table above

**Dimension-to-Category mapping:**

| Dimension < 7 | Diagnose These Categories |
|----------------|--------------------------|
| Intent Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE |
| Context Sufficiency | MISSING_CONTEXT, IMPLICIT_ASSUMPTIONS |
| Constraint Precision | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS |
| Output Specification | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE |
| Role & Framing | MISSING_ROLE |
| Example Grounding | MISSING_EXAMPLES |
| Tone Consistency | MISSING_TONE_FRAME (when Tone active) |

**Read:** `references/grading-rubric.md` for full scoring anchors per dimension.

Diagnose only categories mapped from dimensions scoring < 7 — skip categories
whose parent dimension already scores 7+.

## STEP 1: Diagnose Prompt Weaknesses

Analyze the prompt against the failure category table. Classify every
weakness found — a prompt may have multiple.

#### Failure Category Table

| Category | Severity | Symptoms | Structural Fix |
|----------|----------|----------|---------------|
| **VAGUE_INTENT** | Critical | Unclear what the user wants done; could be interpreted multiple ways | Rewrite as specific action verb + object + success criteria |
| **MISSING_CONTEXT** | Critical | Prompt assumes knowledge not provided (file paths, prior decisions, domain terms) | Add explicit context: which files, which module, what prior state |
| **CONFLICTING_CONSTRAINTS** | High | Prompt asks for contradictory things ("make it fast and thorough") | Identify the conflict, prioritize one, note the tradeoff |
| **OVER_SCOPED** | High | Asks for too many things at once; would require 5+ files changed | Break into sequential focused prompts, suggest ordering |
| **UNDER_CONSTRAINED** | Medium | Vague where specificity is needed. Apply the measurability test: "Can a reviewer objectively verify this constraint was followed?" (see `references/constraint-engineering.md`) | Add measurable constraints. Replace vague terms ("be concise" -> "under 100 words", "be thorough" -> "cover all N checklist items") |
| **MISSING_OUTPUT_SPEC** | Medium | No indication of what the result should look like | Add a locked output template with named sections, explicit order, numeric length bounds (see `references/format-locking.md`) |
| **AMBIGUOUS_SCOPE** | Medium | Unclear which files, modules, or layers are in scope | Add explicit scope boundaries ("only in src/api/", "just the tests") |
| **IMPLICIT_ASSUMPTIONS** | Low | Prompt relies on assumptions that may not hold (env setup, dependencies, prior steps) | Make assumptions explicit or add verification steps |
| **MISSING_STRUCTURE** | Low | Multi-part prompt uses flat unstructured text where XML tags would improve clarity | Restructure with XML tags (see XML Tag Reference below) |
| **MISSING_ROLE** | Medium | No explicit persona or domain frame (Role dim < 7) | Always add a task-class-appropriate role using the "Role Selection Guide" below — never skip |
| **MISSING_EXAMPLES** | Low | No input/output examples for complex tasks | Add 2-3 diverse examples in `<examples>` tags |
| **MISSING_TONE_FRAME** | Medium (Tone-active prompts only) | No voice, register, or audience guidance for prose output | Add tone spec: register (formal/casual), audience, length bounds, voice attributes |

**Severity handling:**

| Severity | Behavior |
|----------|----------|
| Critical | Always included — Critical fixes are never capped |
| High | Included up to the max changes cap |
| Medium | Included up to the max changes cap |
| Low | Included only if budget remains |

#### Role Selection Guide

**Policy: never skip MISSING_ROLE.** When Role dim < 7, always add a
task-class-appropriate role to the strengthened prompt. Position the
role as the first line, before context. Use the imperative form
(`Act as a …`) — Anthropic's prompting docs document this as the
strongest persona pattern for Claude 4.x.

Detect the task class from the prompt's main verb + nearest object,
then pick the role from the table. If no row matches, fall back to
the **template** at the bottom.

| Task class | Detection signals | Default role |
|---|---|---|
| **Mechanical execution** | rename, move, run, delete, format, list (no specialty) | "Act as a careful engineer who executes mechanical changes without scope creep — no refactors, no comments, no surrounding cleanup." |
| **Standard implementation** | implement, add, fix, update (clear scope, no specialty) | "Act as a senior software engineer who writes simple, idiomatic code in the surrounding style and avoids speculative abstraction." |
| **Information retrieval** | what is, explain, describe, where is, how does | "Act as a senior engineer who explains code precisely, citing specific files and line numbers as evidence." |
| **Specialized analysis — security** | review, audit, evaluate + (auth / token / session / SQL injection / XSS / OWASP / threat) | "Act as a security auditor focused on OWASP Top 10 — flag injection, broken auth, broken access control, and sensitive data exposure with specific code references." |
| **Specialized analysis — perf** | review, audit, profile + (latency / p95 / p99 / slow / bottleneck / N+1 / cache) | "Act as a performance engineer specializing in p95/p99 latency analysis — identify N+1 queries, cache misses, allocation hot paths, and serialization overhead with measurements." |
| **Specialized analysis — accessibility** | review, audit + (a11y / accessibility / WCAG / aria / contrast / screen reader / keyboard) | "Act as an accessibility auditor working from WCAG 2.2 AA — flag color contrast failures, keyboard nav gaps, ARIA misuse, and screen-reader hazards with line-level fixes." |
| **Specialized synthesis — system design** | design, architect + (system / service / pipeline / scale / distributed) | "Act as a staff engineer designing for the stated scale and failure modes. Call out trade-offs, rejected alternatives, and the failure cases your design does NOT handle." |
| **Specialized synthesis — API design** | design, define + (API / endpoint / schema / contract / interface) | "Act as an API designer optimizing for backwards compatibility, naming consistency, and a clean error surface. Surface every breaking change risk explicitly." |
| **Specialized synthesis — data modeling** | design, model + (schema / table / DB / migration / index) | "Act as a database engineer who optimizes schemas for the stated query pattern, write throughput, and migration safety. Call out N+1 and lock contention risks up front." |
| **Tone-sensitive — onboarding/UX** | write, draft + (onboarding / welcome / first-time / activation) | "Act as a B2B onboarding copywriter who writes for first-time non-technical users — warm + professional, second-person, no jargon, scannable structure." |
| **Tone-sensitive — error/UX strings** | write, draft + (error / warning / banner / toast / empty state) | "Act as a UX writer specializing in error messages — clear about what went wrong, actionable about what to do next, never blames the user, max 1 sentence." |
| **Tone-sensitive — marketing copy** | write, draft + (landing / hero / pitch / launch / announcement) | "Act as a B2B marketing copywriter focused on benefit-led messaging that respects technical readers' intelligence — no hype, no buzzwords." |
| **Tone-sensitive — developer docs** | write, draft + (docs / README / guide / how-to / tutorial) | "Act as a technical writer specializing in developer documentation — accuracy first, scannable structure, copy-pasteable examples, every claim verified against current code." |
| **Advisory / decision support** | should we, recommend, compare, trade-off, evaluate options | "Act as a senior engineer who gives opinionated, source-cited recommendations grounded in stated constraints. Name a default position with reasoning, not a multiple-choice menu." |
| **Translation / adaptation** | rewrite for X audience, port from Y to Z, simplify, expand | "Act as a translator who preserves the source's intent and structure while replacing tone/idiom for the target audience. Flag every place where literal translation breaks meaning." |
| **Bug investigation** | debug, why is, what's wrong, find root cause | "Act as a root-cause debugger who reproduces before hypothesizing — isolate the failure, gather evidence, name the smallest hypothesis that explains all observed symptoms." |

**Template for novel task classes:**

If no row matches, synthesize a role using this skeleton:

```
Act as a <senior|specialized> <profession> who <does the task verb> with
attention to <1-2 specific failure modes>.
```

Worked example: prompt is "design the feature flag schema for a global
rollout" — no exact row match, but it's a synthesis task with data
modeling + reliability concerns. Synthesized role:

```
Act as a feature-flag platform engineer who designs schemas for global
rollouts with attention to staleness, cache invalidation, and the
delete-flag lifecycle.
```

**Rules for role selection:**

- Always **one role**, not a list of options.
- Always **task-class appropriate** — generic "AI assistant" framing
  is never the answer when Role < 7.
- Position the role as the **first line** of the strengthened prompt,
  before context.
- If the user's prompt already names a domain or seniority (e.g.,
  "as a senior dev…"), preserve their wording and only add what's
  missing (concerns, focus area).
- If the user's prompt explicitly contradicts a default role (e.g.,
  "be casual" against a formal-default class), the user wins.

#### XML Tag Reference

Use XML tags when prompts mix instructions, context, data, and constraints
(3+ distinct parts). Skip for simple single-intent queries or 1-2 sentence prompts.
Use 3-7 tags max — over-tagging adds noise.

**Core tags:** `<task>` (what to do), `<context>` (background), `<instructions>` (steps),
`<constraints>`/`<rules>` (limits), `<output_format>` (result shape), `<examples>` (few-shot),
`<input>` (variable data), `<documents>` (multi-doc context), `<thinking>` (reasoning),
`<answer>` (final output).

**Rules:** descriptive tag names (`<patient_records>` not `<data1>`), nest for hierarchy,
place long context ABOVE the query, do not wrap single sentences.

**Reference:** See [references/constraint-engineering.md](references/constraint-engineering.md) for the
full constraint engineering methodology and measurability test table.

#### Weakening Language Flags

After category diagnosis, scan for words and phrases that weaken instruction
clarity. These are automatic flags — every occurrence is evaluated for removal
or replacement (see `references/prompt-pruning.md` for the full source pattern):

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

| Flag Pattern | Problem | Replace With |
|---|---|---|
| "CRITICAL:/IMPORTANT:/YOU MUST" | Aggressive emphasis degrades compliance in newer models | Normal directive |
| "NEVER EVER/ABSOLUTELY MUST" | Over-emphatic phrasing triggers resistance | Standard MUST/NEVER |
| "think step by step" (reasoning models) | Redundant for models with built-in reasoning | "evaluate"/"reason through" |

#### Category C — Output-Side Anti-Patterns (model self-correction)

| Flag Pattern | Problem | Replace With |
|---|---|---|
| "Certainly!/Of course!/Absolutely!" | Sycophantic opener wastes tokens | Lead with the answer |
| "Based on the information provided..." | Filler preamble | Remove |
| "I'd be happy to help with..." | Unnecessary pleasantry | Remove |

**Pruning rule:** every removal improves precision. Cutting words just to
reduce length is not pruning. If a qualifier serves a real purpose
("if the file exists" is a real condition, not hedging), keep it.

If no weaknesses are found (prompt scores clean), skip to STEP 4.5
(transcript) and STEP 4.6 (final preview) — these run even for Grade A
to maintain uniform transparency.

## STEP 2: Map Fixes

For each diagnosed weakness, determine the minimal structural fix. Each fix
maps to exactly one failure category — no fix without a diagnosis, no
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
- Critical severity fixes are never capped — apply all of them
- Grade D: full pipeline runs but show a heavy warning
- Grade F: present a suggested rewrite with caveats (original may need rethinking)

#### Guardrail 2: Intent Preservation Check (hard contract)

Every rewrite preserves: same action verb, same target, same output type, no
new requirements added beyond what the user implied. Verify before presenting.

| | Original | Rewritten | Verdict |
|---|---|---|---|
| PASS | "fix the login bug — error in screenshot attached" | "fix the login bug shown in the screenshot — restore expected behavior" | Same intent, sharpened wording |
| FAIL | "review auth module" | "refactor auth module to use JWT" | Changed intent from review to refactor |
| FAIL | "fix the login bug" | "resolve auth failure in login.py:42" | Invented file/line that user did not specify — move file-pinning into Clarification Gate, not the rewrite |

#### Guardrail 3: Over-Constraint Detection

- Soft warning if >3 constraints added in a single rewrite
- Hard gate: intent preservation (Guardrail 2) overrides constraint additions
- Check for contradictions between added constraints

**General rewrite rules:**
- Targeted changes only — leave clear parts alone
- Preserve the user's original intent and voice
- Add complexity only when it directly eliminates a diagnosed weakness
- Keep terminology the user chose unless it causes ambiguity
- Remove qualifiers and hedging language flagged in Step 1
- For MISSING_STRUCTURE diagnoses, wrap distinct sections in XML tags
- Long context above the query, constraints near the task definition

## STEP 4: Show Grade Card + Changes Applied

Step 4 is **metadata only** — grade card with per-dimension scores and a
one-line list of every fix the rewrite intends to apply. The full prompt
text (original → strengthened) is rendered exactly once, in STEP 4.6,
after the Clarification Gate has resolved any pending values. This avoids
"pending" placeholders inside Step 4 and gives the prompt text a single
source of truth.

**Compact mode** (Grade A or B with 1-2 fixes):
```
Grade: B (7.4 / 10) — 1 fix applied
  [1] UNDER_CONSTRAINED → added output format spec
```

**Full mode** (Grade C/D/F):
```
Prompt Grade Card:
┌────────────────────────┬───────┬────────┬─────────────┐
│ Dimension              │ Score │ Weight │ Action      │
├────────────────────────┼───────┼────────┼─────────────┤
│ Intent Clarity         │  8.0  │  0.25  │ —           │
│ Context Sufficiency    │  5.0  │  0.20  │ Fixed [1,2] │
│ Constraint Precision   │  6.0  │  0.20  │ Fixed [3]   │
│ Output Specification   │  4.0  │  0.15  │ Fixed [4]   │
│ Role & Framing         │  9.0  │  0.10  │ —           │
│ Example Grounding      │  6.0  │  0.10  │ Skipped     │
├────────────────────────┼───────┼────────┼─────────────┤
│ Overall                │  6.30 │        │ Grade: B    │
└────────────────────────┴───────┴────────┴─────────────┘

Changes Applied (4):
  [1] MISSING_CONTEXT (Critical) → defer to Clarification Gate Q1
  [2] IMPLICIT_ASSUMPTIONS (Low)  → pin precondition explicitly
  [3] UNDER_CONSTRAINED (Medium)  → replace vague phrase with measurable target
  [4] MISSING_OUTPUT_SPEC (Medium)→ add deliverable triple
  Pruning: removed "please" (Cat A — politeness filler)
```

Step 4 deliberately does NOT show the original or strengthened prompt
text — that's STEP 4.6's job. Showing it here would either duplicate
Step 4.6 (when no clarification is pending) or require a "[pending]"
placeholder cell (when one is). Both were judged worse than splitting
metadata from text.

Update the `*Enhanced:*` indicator to include strengthening:
`*Enhanced: prompt strengthened (N fixes, Grade X), git state, 2 rules*`

## STEP 4.5: Show Step Transcript

Render a compact transcript of pipeline **counts and deltas only** — no
per-dimension scores, no per-category enumeration, no per-fix list. Those
already live in Step 4's grade card and Changes Applied. The transcript is
the audit trail (what ran, how many, how long), not a recap of the
diagnosis.

**Transcript format:**
```
Pipeline Transcript:
  Step 0 — Quick Grade:    <Grade letter> (<overall score> / 10), Tone dim: <yes|no>
  Step 1 — Diagnose:       <N> categories flagged (Critical: <X>, High: <Y>, Medium: <Z>, Low: <W>)
  Step 1b — Pruning Flags: <N> weakening phrases found
  Step 2 — Map Fixes:      <N> fixes mapped (<X> Critical applied uncapped, <Y> non-Critical within 5-cap)
  Step 3 — Rewrite:        <N> changes applied; word count <before> → <after> (Δ <delta>)
                           Guardrail 2 (Intent Preservation): PASS|FAIL[, reason]
                           Guardrail 3 (Over-Constraint): clean | <N> constraints added
  Clarification Gate:      <N> questions asked, <resolved|in-progress>
```

For Grade A:
```
Pipeline Transcript:
  Step 0 — Quick Grade:    A (8.6 / 10) — strengthening skipped
  Steps 1-4:               n/a (Grade A)
```

This block is informational only — the user does not need to act on it.
If the user wants per-dimension scores, they're in Step 4. If they want
the per-fix list, that's also in Step 4. If they want the actual prompt
text, that's in Step 4.6. Transcript stays metadata.

## STEP 4.6: Show Original → Final Strengthened Prompt

The single source of truth for the actual prompt text. Render the original
prompt and the final strengthened prompt in fenced blocks so the user can
diff them visually. Step 4 owns the metadata (scores, change list);
Step 4.6 owns the text. No other step renders the prompt — duplication
is intentionally avoided.

**Format (with strengthening applied):**
```
─── Original Prompt ───

<the original prompt verbatim>

─── Final Strengthened Prompt (will execute next) ───

<the strengthened prompt verbatim — all Clarification Gate values filled in>

────────────────────────────────────────────────────
```

For Grade A (no changes — original IS the final prompt):
```
─── Final Prompt (unchanged from original) ───

<original prompt verbatim>

────────────────────────────────────────────
```

The skill does not pause for approval here — execution proceeds to STEP 5
in the same response. Showing the final prompt is for transparency, not
gating. The Clarification Gate has already resolved before this step, so
the strengthened block contains real values, not placeholders.

## STEP 5: Execute

Proceed with the strengthened prompt as if the user had entered it directly.
The rest of the auto-enhance pipeline (Tier 1/2 context, CRUD detection)
applies to the strengthened version, not the original.

### When NOT to Strengthen

Most filtering happens at the hook layer. Within the skill, additional skips:

| Condition | Action |
|-----------|--------|
| Grade A (8.0+) | Skip strengthening; still show transcript + final prompt |
| User says "do exactly this" or quotes a specific command | Skip strengthening; still show transcript + final prompt |
| Pure knowledge question (not an action request) | Skip strengthening; just answer |
| Action-oriented question ("how should I test this?") | Strengthen before answering |

## Clarification Gate

The Clarification Gate runs AFTER strengthening and BEFORE STEP 4.6 (final
prompt preview), so the previewed prompt reflects the resolved intent.

**Trigger:** the prompt is > 15 characters (the only floor — handled
deterministically by the hook). For every prompt that reaches this skill,
evaluate whether ambiguity remains after strengthening. If yes, ask
clarifying questions.

**Question budget:** no upper limit. Ask one question at a time and keep
asking until you have full confidence in the user's intent. Stop when
confidence is reached, not when a question count is hit.

**How:**
- One question per turn, with a count ("Question N of unbounded") and a
  recommendation labeled clearly
- Read the codebase before asking — do not ask what you can answer yourself
- Each question must be unanswerable from Tier 1/2 context
- Present any plan section by section after questions resolve, not all at once

**Question format (locked template):**
```
Question N of unbounded — Clarification Gate

<one specific question, unanswerable from Tier 1/2 context>

Recommendation: <a single concrete value — file path, command, scope, etc. —
                 not a list of options, not a hedge>.
Why: <one sentence citing a specific source — file path with line number,
      commit SHA, pattern name, or CLAUDE.md section — that informs the
      guess. No hand-wave reasoning>.

(Confirm, correct, or specify a different value.)
```

Rules for this format:
- The Recommendation is a **single value**, not a multiple-choice list. The
  user can override it, but the default position is opinionated.
- The Why line cites a **specific source** (file:line, SHA, pattern name).
  If you can't cite one, you don't have enough context to recommend yet —
  read more code first instead of asking.
- The question stem is one sentence, ending with a question mark. Multi-part
  questions become multiple turns.

**Sequencing summary:**
1. STEP 0-3: grade, diagnose, rewrite (internal)
2. STEP 4: show grade card + Changes Applied (metadata only — no prompt text)
3. **Clarification Gate** (if ambiguity remains, ask until confident, locked format)
4. STEP 4.5: show step transcript (counts and deltas only — no per-dim or per-fix lists)
5. STEP 4.6: show original → final strengthened prompt (single source of truth for text)
6. STEP 5: execute

---

## Verbose Grade Mode (replaces former Reliability Scoring)

Activates when the user explicitly asks to **score**, **evaluate**, or **audit**
a prompt — not during automatic strengthening. Verbose mode runs the same
6-7 dimension Quick Grade rubric, with three additions:

1. **Quote-as-evidence**: every dimension score cites a specific phrase from
   the prompt that justifies it. Score with no quote → invalid.
2. **Use case input**: ask the user to describe the prompt's use case before
   scoring. The same prompt scores differently for a CLI tool vs. a customer chatbot.
3. **Launch-risk flagging**: dimensions scoring below 7 are labeled "launch
   risks" with: the offending quote, the failure mode it will cause in
   production, and the concrete fix that would raise the score to 7+.

Verbose mode produces a report only — it does not auto-strengthen. If the
user asks to fix afterwards, feed the launch risks into Steps 1-5 of the
strengthening pipeline.

**Read:** `references/grading-rubric.md` for the verbose-mode subsection
with the report template and verdict thresholds.

---

## Batch Approval Flow

When the global rule detects that a user's prompt implies creating, updating, or
deleting Claude Code resources (skills, agents, rules, hooks), execute this flow.

### Step 1: Show Enhancement Summary

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
- Clarification text — answer to a `[NEEDS CLARIFICATION]` question; update
  the batch table and re-present

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

Items the user did not approve are dropped silently. Do not re-prompt for
rejected items later in the same session.

---

## Web Search Decision Tree

Skip web search when: prompt is about existing code, answer is in CLAUDE.md or
`.claude/` patterns, or it is general programming knowledge. Search the web only
for: external library/API docs (when no local code exists), version /
compatibility / deprecation questions, official framework conventions. Read
local code first when local config exists for the library.

**CRUD Exception:** when creating/updating a resource targeting an external
technology, search the web for current docs — training data may be outdated.

---

## Context Gathering Reference

### Tier 1 — Always (every prompt that reaches this skill)

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

## Pipeline Rules

These are the load-bearing contracts. The rest of the skill is procedure.

- Run STEP 0 (Quick Grade) before any diagnosis, and skip diagnosis entirely for Grade A
- Gather Tier 1 context before responding to any prompt — without it, responses risk duplicating existing patterns or contradicting CLAUDE.md
- Show the grade card, step transcript, and final prompt every time strengthening activates — silent changes erode trust
- Include the strengthening count in the `*Enhanced:*` indicator when fixes are applied
- Run the Clarification Gate after strengthening when ambiguity remains — ask one question at a time, no upper limit
- Read relevant code before asking a clarification question — asking answerable questions wastes the user's time
- Apply the measurability test to every constraint added: "Can a reviewer objectively verify this was followed?"
- Guardrail 2 (Intent Preservation) is a hard contract — a rewrite that changes the user's action verb, target, or output type is invalid
- Critical-severity fixes are never subject to the 5-fix cap
- Present the batch table when resource CRUD is detected, and wait for explicit user approval before creating, updating, or deleting
- Delegate resource creation to the existing authoring tools (`/writing-skills`, `/claude-guardian`, `skill-author` agent) rather than generating directly

## Anti-Patterns

These are common ways the pipeline goes wrong.

- Strengthening direct unambiguous instructions — respect explicit user intent
- Adding complexity during strengthening that doesn't map to a diagnosed weakness
- Changing the user's original intent during strengthening — clarify and constrain only
- Exceeding the max non-Critical changes cap (5) without explicit user request
- Creating, updating, or deleting resources without batch approval
- Re-prompting for items the user already rejected in the same session
- Web searching when local context is sufficient — read code first
- Generating patterns directly instead of using `/writing-skills`, `/claude-guardian`, or `skill-author`
- Suggesting resource changes when CRUD signals are ambiguous — default to no CRUD
- Hiding the step transcript or final prompt preview to save tokens — these are non-optional
