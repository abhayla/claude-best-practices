---
name: writing-skills
description: >
  Author new Claude Code skills or update existing ones. Covers YAML frontmatter,
  step structure, trigger design, quality validation, testing, hub promotion,
  and a full template library. Use when creating, updating, or refining skills
  for the .claude/skills/ directory.
triggers:
  - write-skill
  - create-skill
  - skill-author
  - how to write a skill
  - new skill
  - author skill
  - update skill
  - modify skill
  - improve skill
  - edit skill
  - refine skill
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<skill-name or 'from-session' to extract from conversation>"
type: workflow
version: "3.0.0"
---

# Writing Skills — The Skill Authoring Guide

Author new Claude Code skills or update existing ones — from scratch, from observed patterns, or from session analysis.

**Request:** $ARGUMENTS

---

> Aligned with Anthropic's [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and [Skills for Enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise) as of 2026-04.

## STEP 1: Determine Authoring Mode

Parse `$ARGUMENTS` to choose the path:

| Input | Mode | Starting Point |
|-------|------|----------------|
| `from-session` | **From Session** (recommended) | Start at Step 3 — best skills come from real tasks |
| A skill name or description | **From Scratch** or **Update** | Check if skill exists → Update (Step 1.3) or create (Step 2) |
| A URL or file path to existing workflow | **From Reference** | Start at Step 2, pre-fill from reference |
| Empty / vague | **Interactive** | Ask: "What repeated task do you want to automate?" |

**Auto-detect Update mode:** When `$ARGUMENTS` names an existing skill (directory exists in `.claude/skills/` or `core/.claude/skills/`), switch to Update mode (Step 1.3). Do not treat updates as new skill creation.

### 1.1 Skill Necessity Check

Before authoring, verify the skill adds value over the agent's baseline:

1. **Auto-generate 3 representative tasks** from `$ARGUMENTS` — realistic prompts a user would type within the skill's intended scope
2. **Run each task WITHOUT a skill** in a subagent (clean context)
3. **Evaluate results:**

| Result | Action |
|--------|--------|
| Agent handles all 3 well | STOP — report "skill not needed" |
| Agent struggles on 1-2 | Capture gaps — these define the skill's value. Proceed |
| Agent fails on all 3 | Strong signal — use failure patterns to drive Step 2.3 |

The gaps captured here feed directly into the skill's instructions.

### 1.2 Design Initial Evaluations

Before authoring, formalize the gaps from 1.1 into 3 eval scenarios.
These become the acceptance criteria that drive Step 2.

1. **Convert each gap into a test case:** realistic user prompt + expected behavior
2. **Establish baseline:** the without-skill results from 1.1 ARE the baseline
3. **Store scenarios** for use in Step 6 (formal evaluation)

| Gap Identified | Eval Scenario | Expected Behavior |
|---|---|---|
| {from 1.1} | {realistic prompt} | {what success looks like} |

These scenarios drive what to include in Step 2 — write ONLY what's needed
to pass them. Resist comprehensive documentation until evals confirm value.

### 1.3 Update Mode — Modify an Existing Skill

When the target skill already exists, follow this workflow instead of creating from scratch.

1. **Read the existing skill** — load the full SKILL.md and any references
2. **Identify what needs to change** — based on user request, conversation context, or known gaps
3. **Classify the change scope** for SemVer bump:

| Change Type | Version Bump | Examples |
|---|---|---|
| Breaking: output format change, removed steps, renamed arguments | **MAJOR** | Changing JSON output schema, removing a step |
| Additive: new optional steps, new modes, expanded examples | **MINOR** | Adding an update mode, new decision table |
| Fix: typo, wording, formatting, bug fix | **PATCH** | Fixing a code block, clarifying a step |

4. **Apply changes** — edit the existing SKILL.md using the Edit tool (not rewrite)
5. **Bump the version** in frontmatter per the classification above
6. **Skip Steps 1.1–1.2 and Steps 2–3** — the skill's value is already proven
7. **Run Steps 4–5** — validate naming, organization, and quality checklist
8. **Run Step 6** with `--baseline` flag — evaluates the update against the previous version

---

## STEP 2: Skill Authoring — From Scratch

<role>Act as a Claude skill architect who designs prompts with built-in failure prevention from the start.</role>

Build a minimal skill that addresses the gaps identified in Step 1.1.
Write only what's needed to pass the eval scenarios from Step 1.2 — you'll
iterate in Step 6. Focus on failure prevention from the start.

### 2.0 Understand the Runtime Model

**Read:** `references/runtime-model.md` — how Claude loads and navigates
skills at runtime. This shapes every structural decision in Step 2.

### 2.1–2.2 Frontmatter, Naming, Content Standards

**Read:** `references/skill-authoring-from-scratch.md` for the complete
authoring reference: YAML frontmatter fields, naming conventions (gerund
form, 64-char limit), context budget (500-line target), content quality
(consistent terminology, no time-sensitive info, MCP qualified names),
and reference structure (one level deep, TOC for >100 lines).

### 2.3 Failure Mode Analysis

Before writing steps and constraints, identify the 3 most likely failure modes for the skill's domain. This drives what guardrails to build — prevention beats diagnosis.

1. **List 3 failure modes** — What goes wrong when this type of task is done carelessly? (e.g., "reads stale cache instead of live data", "overwrites user changes without confirmation", "proceeds with partial input")
2. **Map each to a prevention** — Each failure mode becomes a specific MUST DO or MUST NOT DO rule with a concrete guardrail (a validation step, a confirmation prompt, or a precondition check)
3. **Embed preventions into steps** — Place the guardrail in the earliest step where the failure could occur, not as an afterthought at the end

| Failure Mode | Prevention Type | Where to Place |
|---|---|---|
| Wrong/stale input | Validation step | Step 1 or earliest data-reading step |
| Destructive action without confirmation | User approval gate | Step before the destructive action |
| Partial execution leaving broken state | Rollback or atomic commit | Step that modifies state |
| Missing prerequisites | Precondition check | Step 1 |
| Ambiguous output format | Locked output template | Output-producing step + MUST DO |

**Output format MUST be locked.** Every skill that produces structured output (JSON, reports, tables) MUST define the exact output format in a code block template within the output-producing step. Ambiguity in output format is the #1 cause of inconsistent skill behavior — lock it down with a concrete template, not prose descriptions.

### 2.4 Multi-Skill Decomposition (When One Prompt → Multiple Skills)

If the prompt or workflow being authored covers a full end-to-end pipeline with 4+ distinct phases (input → processing → validation → output), decompose it into connected phase skills instead of building one monolithic skill.

**Read:** `references/multi-skill-decomposition.md` for the full decomposition workflow: phase mapping, handoff contracts with XML-tagged schemas, checkpoint patterns, and end-to-end testing protocol.

**Quick decision:** If the workflow has ≤3 tightly coupled steps, keep it as one skill. If it has 4+ independent phases or exceeds ~400 lines, decompose.

### 2.5 Structure the Steps

Steps are the core of every skill. Each step must be actionable — a verb phrase, not a vague noun.

#### Step Writing Rules

| Rule | Good Example | Bad Example |
|------|-------------|-------------|
| Start with a verb | "Run the test suite" | "Test execution" |
| Be specific | "Search `src/` for files matching `*Service.ts`" | "Look at the code" |
| Include the command or action | "Run: `pytest tests/ -v`" | "Execute the tests" |
| State the expected outcome | "All tests should pass with 0 failures" | "Verify it works" |
| Handle failure | "If tests fail, proceed to Step 5" | (nothing) |

#### Step Anatomy

Each step follows this structure:

```markdown
## STEP N: Action Verb + Object

Brief explanation of WHY this step exists (1-2 sentences max).


**Read:** `references/step-n-action-verb-object.md` for detailed step n: action verb + object reference material.

## MUST DO

- Always complete Step 1 before proceeding — skipping it causes cascading errors
- Always verify output before reporting completion
- Always clean up temporary files created during execution
- Run the dedup check if skill will be promoted to the hub

## MUST NOT DO

- MUST NOT skip the verification step — unverified output is unreliable
- MUST NOT modify files outside the specified scope
- MUST NOT proceed if prerequisites are not met — ask the user instead
- MUST NOT output partial results as final — either complete the task or report what is missing
```

#### XML Tags Within Steps (Optional)

Use XML tags to separate content types within a step when the step mixes instructions, context, data, and constraints. This improves Claude's parsing accuracy — per [Anthropic's prompt engineering guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags), XML tags reduce misinterpretation in multi-part prompts.

**When to use:** Steps that mix 3+ content types (instructions + context + constraints + data). Skip for simple steps with only instructions.

**When NOT to use:** Do not replace the skill's top-level markdown structure (YAML frontmatter, `## STEP N:` headings, `## MUST DO` sections) with XML. XML tags are for *within-step* content separation only.

Recommended tags (names are flexible — pick what's semantically clear):

| Tag | Purpose | Example |
|---|---|---|
| `<context>` | Background info the step needs | `<context>Read the user's $ARGUMENTS and classify input type.</context>` |
| `<constraints>` | Guardrails for this specific step | `<constraints>MUST NOT proceed if input is empty.</constraints>` |
| `<input>` | Variable data being processed | `<input>$ARGUMENTS</input>` |
| `<output>` | Expected output format for this step | `<output>JSON with {result, summary, failures} fields</output>` |
| `<examples>` | Few-shot examples within a step | Wrap 2-3 input/output pairs |

Example of a step using XML tags:

```markdown
## STEP 2: Classify the Input

Determine the input type to route to the correct processing path.

<context>
The user provides either a file path, a URL, or a natural language description.
Each type requires different validation and processing.
</context>

<constraints>
- MUST detect input type before processing — wrong classification causes silent failures
- MUST reject inputs that match none of the 3 types with a clear error message
</constraints>

<output>
One of: `file_path`, `url`, or `description` — stored for use in Step 3.
</output>
```

**Key rules for XML tag usage:**
- Use consistent tag names throughout all steps in one skill — do not mix `<constraints>` and `<rules>` for the same purpose
- Reference tags by name when pointing to them: "Using the context in `<context>` tags..." not "the context above"
- No canonical "magic" tag names exist — Claude treats all XML tag names equally (per Anthropic docs)

Rules for writing MUST DO / MUST NOT DO:
- 4-8 items per section (fewer is better — only include non-obvious rules)
- Each item MUST have a `— Why:` suffix explaining the consequence of violation (e.g., "Always validate input before processing — Why: unvalidated input caused silent data corruption in downstream steps")
- Every constraint must have a reason — no rules without purpose. If you cannot articulate why a rule exists, do not include it
- MUST NOT items always state what to do instead
- Do not repeat what the steps already say — these are for edge cases and guardrails
- Constraints from the failure mode analysis (Step 2.3) MUST appear here with their mapped preventions

#### Instruction Writing Patterns

Eleven patterns improve instruction quality within steps.

**Read:** `references/instruction-writing-patterns.md` for calibrating control, gotchas sections, validation loops, plan-validate-execute, defaults over menus, procedures over declarations, script design for agentic use, checklists, input/output examples, conditional workflow routing, and install-then-use patterns.

### 2.6 Validate Before Saving

Before writing the skill file, run through the quality checklist in Step 5.

---

## STEP 3: Session Log Analysis

Extract skill candidates from the current conversation by identifying repeated workflows.

### 3.1 Scan for Repeated Patterns

Review conversation history for multi-step sequences performed 2+ times:
1. **Steps that worked** — action sequence that led to success
2. **Corrections you made** — where you steered the agent's approach
3. **Input/output formats** — data shape going in and out
4. **Context you provided** — project-specific facts the agent didn't know
5. **Repeated tool call sequences** — same 3+ calls in same order
6. **Repeated file access patterns** — same files across tasks

### 3.1b Synthesize from Project Artifacts

**Warning:** Do NOT generate a skill from LLM general knowledge alone — the result is vague procedures ("handle errors appropriately"). Always ground in project-specific material:

- Internal documentation, runbooks, and style guides
- API specifications, schemas, and configuration files
- Code review comments and issue trackers
- Version control history, especially patches and fixes
- Real-world failure cases and their resolutions

### 3.2 Classify Candidates

For each detected pattern, classify it:

| Pattern | Times Seen | Steps | Parameterizable? | Skill Candidate? |
|---------|-----------|-------|-------------------|-------------------|
| {description} | {N} | {count} | Yes/No | Strong/Weak/No |

A **strong candidate** has:
- 3+ steps in a consistent order
- Appeared 2+ times in the session
- Variable parts that can be parameterized (file names, feature names, etc.)
- Not already covered by an existing skill

A **weak candidate** has:
- Only 2 steps, or appeared only once but is clearly reusable
- Investigate further before creating a skill

### 3.3 Present Findings to User

Present findings conversationally:

```
I noticed you performed this workflow 3 times this session:

  1. Search for files matching a pattern in src/
  2. Read each file and extract the interface definition
  3. Generate a mock implementation
  4. Write the mock to tests/mocks/

Want me to create a /generate-mock skill for this?
```

Wait for user approval before creating the skill. If approved, proceed to Step 2 with the extracted pattern as the starting point, parameterizing the variable parts (file pattern, source directory, output directory).

---

## STEP 4: Naming and Organization

### 4.1 Directory Naming Convention

Skills live in `core/.claude/skills/<name>/SKILL.md` (or `.claude/skills/<name>/SKILL.md` for project-local skills).

| Type | Naming Rule | Example |
|------|------------|---------|
| Universal skill | Descriptive kebab-case | `systematic-debugging`, `writing-plans` |
| Stack-specific skill | Stack prefix + descriptive name | `fastapi-db-migrate`, `android-run-tests` |
| Compound skill | Primary-action + object | `fix-loop`, `request-code-review` |

#### Stack Prefixes

| Stack | Prefix |
|-------|--------|
| FastAPI + Python | `fastapi-` |
| Android + Compose | `android-` |
| React + Next.js | `react-` |
| Flutter | `flutter-` |
| Firebase | `firebase-` |
| AI / Gemini | `ai-gemini-` |
| Vue / Nuxt | `vue-` or `nuxt-` |
| Expo | `expo-` |

### 4.2 When to Create a New Skill vs. Extend an Existing One

| Situation | Action |
|-----------|--------|
| New workflow that does not overlap with any existing skill | Create new skill |
| Existing skill covers 80%+ of the workflow | Extend the existing skill with a new mode or step |
| Two skills share 50%+ of their steps | Consolidate into one skill with modes |
| Skills scoped too narrowly for one task | Broaden — multiple narrow skills loading risks overhead and conflicting instructions |
| Workflow is a single rule (no steps) | Use `.claude/rules/` instead — skills are for multi-step workflows |
| Workflow is a one-liner command | Use a hook instead — skills are overkill for single commands |

### 4.3 When to Use Rules Instead of Skills

Skills and rules serve different purposes:

| Aspect | Skill | Rule |
|--------|-------|------|
| Activation | On-demand (slash command or natural language) | Automatic (always loaded or glob-matched) |
| Structure | Multi-step workflow | Declarative constraints |
| Length | 100-600 lines | 5-30 lines |
| Context cost | Zero when unused (loaded on-demand) | Always consumes context when matched |
| Use for | "Do this workflow" | "Always/never do X" |

**If your "skill" has no steps and is just a list of rules, make it a rule file instead.**

---

## STEP 5: Quality Checklist

Before saving the skill, validate every item. Do NOT skip this step.

### 5.1 Structure Validation

| Check | Pass Criteria |
|-------|---------------|
| YAML frontmatter is valid | All required fields present, YAML parses without error |
| `name` matches directory name | `name: foo-bar` lives in `skills/foo-bar/SKILL.md` |
| `description` starts with a verb | "Debug...", "Generate...", "Analyze..." |
| `type` is declared | `workflow` or `reference` — determines required body structure |
| `version` is valid SemVer | Format: `"1.0.0"` — required for version tracking |
| `triggers` has 3-6 entries | Mix of slash commands and natural language |
| `allowed-tools` is minimal | No unused tools listed. Read-only skills MUST NOT include `Write`, `Edit`, or `Bash` |
| No high-risk indicators without justification | Scripts, MCP refs, network access, or broad file access are documented and necessary (see `references/security-review.md` risk tiers) |
| `argument-hint` uses `<>` and `[]` correctly | Required in angle brackets, optional in square brackets |
| No placeholder markers | No TODO/FIXME/PLACEHOLDER HTML comment markers in the body |

### 5.2 Content Validation

| Check | Pass Criteria |
|-------|---------------|
| Steps are numbered sequentially | STEP 1, STEP 2, STEP 3... |
| Each step starts with a verb | "Analyze", "Run", "Create" — not "Analysis", "Running", "Creation" |
| Steps have concrete actions | Commands, file paths, or specific instructions — not "consider" or "think about" |
| Conditional logic uses tables | No nested if/else bullet points |
| Output format is templated | Expected outputs shown in code blocks |
| MUST DO section has 4-8 items | Each explains the consequence of skipping |
| MUST NOT DO section has 4-8 items | Each states what to do instead |
| No vague language | No "consider", "maybe", "try to", "think about" |
| No Windows-style paths | All file paths use forward slashes (`/`), even on Windows |
| Install-then-use for deps | Package usage shows install command before import |

### 5.3 Overlap Check

Scan existing skills for trigger and purpose overlap:

```bash
# Check for trigger overlap
grep -r "triggers:" core/.claude/skills/*/SKILL.md -A 8

# Check for name similarity
ls core/.claude/skills/

# Check for description overlap
grep -r "description:" core/.claude/skills/*/SKILL.md -A 3
```

If overlap is found:
- **Same triggers, different purpose** — Rename triggers to be more specific
- **Different triggers, same purpose** — Consolidate into one skill
- **Partial overlap** — Consider whether extending the existing skill is better than creating a new one

### 5.4 Length Validation

| Length | Assessment |
|--------|-----------|
| <50 lines | Suspiciously short — verify it's not a stub. May belong as a rule instead of a skill. |
| 50-200 lines | Acceptable for simple, focused skills |
| 200-500 lines | Ideal range for standard skills |
| 500-1000 lines | Warning zone — consider splitting reference material into `references/` subdirectory |
| >1000 lines | Too long — MUST split into smaller skills or extract reference material into `skill-name/references/*.md` |

For skills with extensive reference material, use this directory structure:
```
skill-name/
  SKILL.md           # Core workflow (under 500 lines)
  references/        # Supplementary knowledge (loaded on-demand)
    setup-guide.md
    api-reference.md
  templates/         # Reusable templates
    config.yaml
```

### 5.5 Model Compatibility

If the skill will be used across model tiers, test with the smallest
target model. What works for Opus may need more guidance for Haiku:
- **Haiku:** Does the skill provide enough guidance for the task?
- **Sonnet:** Is the skill clear and efficient?
- **Opus:** Does the skill avoid over-explaining?

---

## STEP 6: Evaluate and Iterate with /skill-evaluator

Invoke `/skill-evaluator` via the Agent tool. The entire evaluate-fix-re-evaluate loop runs autonomously with one human approval at the end.

**Read:** `references/iterative-development.md` for the full Claude A/B
development methodology — how to test with fresh instances, diagnose issues
from observation, and gather team feedback.

**Before formal eval:** Run the skill informally against one real task. Read the execution trace (not just output). Fix obvious issues first.

### 6.1 Invoke Evaluation

For new skills:
```
Agent(subagent_type="general-purpose",
  prompt="/skill-evaluator full <skill-path>")
```

For updated skills:
```
Agent(subagent_type="general-purpose",
  prompt="/skill-evaluator full <skill-path> --baseline")
```

### 6.2 Auto-Fix Routing

When skill-evaluator returns FIX or FAIL, apply the mapped fix:

| Eval Failure Type | Automated Fix |
|---|---|
| Should-trigger failing (<80%) | Broaden description: add user-intent phrases, expand scope |
| Should-not-trigger firing (>20%) | Narrow description: add boundary ("do NOT use when...") |
| Cross-skill conflict | Make triggers more specific, add distinguishing context |
| Trigger regression (--baseline) | Restore key phrases from old description |
| Scenario assertion failures | Add/clarify the step that produces the failing output |
| Stress test CRITICAL | Add guardrail to MUST DO, embed prevention in earliest step |
| Stress test MAJOR | Add edge case handling to relevant step's decision table |
| Stress score <90% overall | Re-run failure mode analysis (Step 2.3), add preventions |
| Skill adds no value over baseline | STOP — report to user: "skill not needed" |

### 6.3 Iterate Until PASS

1. Apply fix from routing table
2. Re-invoke `/skill-evaluator full <skill-path>`
3. If FIX/FAIL: apply next fix (each iteration MUST try a different fix)
4. If PASS: proceed to 6.4

**Max 5 iterations.** After 5 without PASS: STOP, present full iteration history, user decides.

### 6.4 Present for Approval

Present to user: final skill draft, eval report, iteration history, skill necessity delta.

**Wait for user approval before proceeding to Step 7.** This is the single human touchpoint.

### 6.5 Failure Prevention Map

Before promoting, produce a failure prevention map that documents every guardrail in the skill. This is the "proof of failure resistance" artifact.

```
## Failure Prevention Map: <skill-name>

| # | Failure Mode | Prevention | Step Where Embedded | Constraint (MUST DO/MUST NOT DO) |
|---|---|---|---|---|
| 1 | <from Step 2.3> | <validation/gate/check> | Step N | "Always X — Why: Y" |
| 2 | <from Step 2.3> | <validation/gate/check> | Step N | "MUST NOT X — do Y instead" |
| 3 | <from Step 2.3> | <validation/gate/check> | Step N | "Always X — Why: Y" |

Output format locked: <YES with template / NO — flag for fix>
Stress test score: <N%> (from Step 6.3)
```

Present this map to the user alongside the skill draft. The map makes failure prevention layers visible and auditable — without it, guardrails are buried in the skill body and easy to miss during review.

---

### 6.6 Domain Pattern Review

When the authored pattern is an agent or orchestration-related skill, validate it against
domain-specific reference patterns — not just structural quality gates.

### When to Trigger

| Authored Pattern Type | Domain References to Check |
|----------------------|---------------------------|
| Agent (any `agents/*.md`) | `agent-orchestration.md` rule (tier model, responsibilities, state) |
| Orchestration agent or skill | `anthropic-agent-orchestration-guide` (5 workflow patterns, decision framework) |
| Multi-agent system pattern | `anthropic-multi-agent-research-system-skill` (8 principles, evaluation, production) |
| Non-orchestration skill or rule | **SKIP** — domain review is not applicable |

### How to Review

1. **Identify the authored pattern type** from the table above
2. **Read the matched reference pattern(s)** — these are the audit baseline
3. **Spawn `anthropic-multi-agent-reviewer-agent`** with the authored pattern and matched references:
   ```
   Agent(subagent_type="anthropic-multi-agent-reviewer-agent",
         prompt="Review this pattern against the 8 principles: <pattern content>")
   ```
4. **Evaluate the gap report:**
   - **Grade A-B** → PASS — proceed to Step 7
   - **Grade C** → WARN — present gaps to user, fix if user agrees, then proceed
   - **Grade D-F** → FAIL — must fix before hub promotion

### Why This Step Exists

Structural quality gates (Step 5) check *shape* — does the pattern have frontmatter, steps,
MUST DO sections? Domain review checks *substance* — does the orchestrator follow the
8 principles? Does it scale effort appropriately? Does it have evaluation infrastructure?

A pattern can pass every structural gate while violating every orchestration best practice.
This step closes that gap.

---

## STEP 7: Hub Promotion Workflow

If the skill is valuable enough to share across projects via the hub.

### 7.1 Pre-Promotion Checklist

| Check | Action |
|-------|--------|
| Quality checklist passes (Step 5) | All items green |
| Tested with 5 scenarios (Step 6.1) | All pass |
| Stress tested with 10 adversarial inputs (Step 6.3) | Score >= 90% |
| Not a duplicate | Run: `PYTHONPATH=. python scripts/dedup_check.py` |
| Follows naming conventions (Step 4) | Directory and name match, correct prefix if stack-specific |
| `version` field present | SemVer format in frontmatter |
| `type` field present | `workflow` or `reference` declared |
| `allowed-tools` is least-privilege | Read-only skills don't include Write/Edit/Bash |
| No project-specific hardcoded paths | Replace with `$ARGUMENTS` or documented placeholders |
| Team feedback gathered (if applicable) | At least one teammate has used the skill on a real task |
| No placeholder markers | No TODO/FIXME HTML comment markers or stub content |
| Under size limit | SKILL.md under 1000 lines; use `references/` for supplementary material |
| No secrets or credentials | Scan for API keys, tokens, passwords |

### 7.2 Add to Registry

After placing the skill in `core/.claude/skills/<name>/SKILL.md`, update the registry:

1. Add an entry to `registry/patterns.json` with: name, type, category, version, hash, dependencies
2. Run: `python scripts/generate_docs.py` to update the dashboard
3. Verify the skill appears in `docs/DASHBOARD.md`

### 7.3 Submit via Contribution Flow

If contributing from a downstream project:

1. Invoke `/contribute-practice` to validate and package the skill
2. The contribution flow handles PR creation, dedup verification, and registry updates

---


## STEP 8: Post-Promotion Lifecycle

What happens after a skill ships: security vetting, deployment governance,
monitoring, version management, deprecation, and scaling considerations.

**Read:** `references/post-promotion-lifecycle.md` for the full lifecycle
covering security review gates (8.1), deployment governance with registry
requirements (8.2), monitoring and drift detection (8.3), version management
with rollback plans (8.4), deprecation lifecycle (8.5), and scaling
considerations including recall limits and consolidation triggers (8.6).

**Also read:** `references/security-review.md` for the detailed risk tier
assessment and 8-step review checklist referenced by Step 8.1.

---

## STEP 9: Template Library

Pre-built starting skeletons for common skill types. Copy the appropriate template and fill in the placeholders.

> **Reference:** See [references/skill-templates.md](references/skill-templates.md) for the full template library (Templates A-G: Workflow, Analysis, Generation, Testing, Deployment, Migration, Reference).

---

## Anti-Patterns

> **Reference:** See [references/anti-patterns.md](references/anti-patterns.md) for 9 common skill anti-patterns to avoid.

---


## MUST DO

- Always read at least 2 existing skills before authoring a new one — pattern-match from working examples
- Always validate with the quality checklist (Step 5) before saving
- Always check for trigger overlap with existing skills
- Always include MUST DO and MUST NOT DO sections in every skill
- Always include a verification step in skills that modify state
- Always use concrete, actionable language in steps — verbs, not adjectives
- Always present the draft to the user for review before saving
- Always test the skill with 5 scenarios from Step 6 (3 happy-path + 2 edge-case)
- Always complete failure mode analysis (Step 2.3) before writing constraints — prevention beats diagnosis
- Always include a `— Why:` justification on every MUST DO / MUST NOT DO item
- Always lock the output format with a code block template for skills that produce structured output — Why: ambiguous output formats cause inconsistent behavior across invocations
- Always produce a failure prevention map (Step 6.5) before hub promotion — Why: makes guardrails visible and auditable during review
- Always evaluate multi-phase decomposition (Step 2.4) when a prompt covers a full end-to-end workflow — Why: monolithic skills exceeding 400 lines become hard to test, reuse, and maintain
- Always run domain pattern review (Step 6.6) for agents and orchestration patterns before hub promotion — Why: structural gates pass patterns that violate orchestration best practices; domain review catches substance violations
- Always invoke `/skill-evaluator` via Agent tool for evaluation — do not evaluate inline
- Always apply auto-fix routing for FIX/FAIL verdicts — do not ask user what to fix
- Always present final skill + eval report for user approval before hub promotion
- Always use gerund or action-oriented naming for skill names — Why: consistent naming improves discoverability and professionalism across the skill library
- Always keep reference files one level deep from SKILL.md — Why: Claude partially reads deeply nested files, resulting in incomplete information

## MUST NOT DO

- MUST NOT create a skill for something that should be a rule — if it has no steps, use `.claude/rules/`
- MUST NOT use vague step language ("consider", "think about", "ensure quality") — use specific actions instead
- MUST NOT create skills with >10 steps — split into sub-skills or use delegation
- MUST NOT add tools to `allowed-tools` that the skill does not use
- MUST NOT create skills with overlapping triggers — check existing skills first
- MUST NOT save a skill without running the quality checklist
- MUST NOT create skills that duplicate existing ones — extend or consolidate instead
- MUST NOT skip the MUST DO / MUST NOT DO sections — they are mandatory guardrails
- MUST NOT ask user to manually invoke `/skill-evaluator` — invoke it autonomously via Agent tool
- MUST NOT proceed to Step 7 without user approval of the final skill + eval report
- MUST NOT write descriptions in first or second person ("I analyze...", "You can use...") — always third person ("Analyzes...") because descriptions are injected into the system prompt and inconsistent POV causes discovery problems
- MUST NOT chain reference files (SKILL.md → ref1.md → ref2.md) — keep one level deep from SKILL.md
- MUST NOT include time-sensitive content ("before August 2025") — use collapsible "Old patterns" section instead
- MUST NOT be the sole reviewer of your own skill for hub promotion — Why: separation of duties prevents blind spots and catches adversarial patterns the author may overlook (see Step 8.1)
