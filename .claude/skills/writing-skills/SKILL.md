---
name: writing-skills
description: >
  Guide for intentionally authoring new Claude Code skills from scratch or from
  observed patterns. Covers YAML frontmatter, step structure, trigger design,
  quality validation, testing, hub promotion, and a full template library for
  common skill types. The "how to write skills" manual as a skill itself.
triggers:
  - write-skill
  - create-skill
  - skill-author
  - how to write a skill
  - new skill
  - author skill
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<skill-name or 'from-session' to extract from conversation>"
type: workflow
version: "2.0.0"
---

# Writing Skills — The Skill Authoring Guide

Author new Claude Code skills from scratch, from observed patterns, or from session analysis.

**Request:** $ARGUMENTS

---

## STEP 1: Determine Authoring Mode

Parse `$ARGUMENTS` to choose the path:

| Input | Mode | Starting Point |
|-------|------|----------------|
| A skill name or description | **From Scratch** | Start at Step 2 |
| `from-session` | **From Session Analysis** | Start at Step 3 |
| A URL or file path to existing workflow | **From Reference** | Start at Step 2, pre-fill from reference |
| Empty / vague | **Interactive** | Ask: "What repeated task do you want to automate?" |

---

## STEP 2: Skill Authoring — From Scratch

Build a skill file from the ground up following the canonical format.

### 2.1 Define the YAML Frontmatter

Every skill requires a `SKILL.md` file with YAML frontmatter. Each field has specific requirements:

```yaml
---
name: lowercase-kebab-case-name
description: >
  One to three sentences explaining WHAT the skill does, WHEN to use it,
  and what it produces. Start with an action verb. Include the primary
  use case so Claude can match it from natural language requests.
triggers:
  - slash-command-name
  - natural language phrase 1
  - natural language phrase 2
  - natural language phrase 3
allowed-tools: "Tool1 Tool2 Tool3"
argument-hint: "<required-arg> [optional-arg]"
type: workflow
version: "1.0.0"
---
```

#### Field Reference

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | Lowercase kebab-case. Must match the directory name. 2-4 words max. |
| `description` | Yes | 1-3 sentences. Start with a verb. Include when to use it. Must fit in ~50 words. |
| `triggers` | Recommended | 3-6 entries. Mix of slash commands and natural language phrases. |
| `allowed-tools` | Yes | Space-separated list. Use the minimal set needed. Never include tools you do not use. |
| `argument-hint` | Yes | Show required args in `<angle-brackets>`, optional in `[square-brackets]`. Use descriptive placeholder names. |
| `type` | Yes | `workflow` (multi-step procedure with numbered STEP sections) or `reference` (knowledge base / lookup guide with organized sections, no step numbering required). |
| `version` | Yes | SemVer format (`"1.0.0"`). Bump MAJOR for breaking output/arg changes, MINOR for new optional content, PATCH for wording fixes. |

#### Allowed-Tools Selection Guide

Choose the minimal set. Each tool you add expands what the skill can do — and what can go wrong.

| Tool | Include When |
|------|-------------|
| `Read` | Skill reads existing files |
| `Write` | Skill creates new files from scratch |
| `Edit` | Skill modifies existing files |
| `Bash` | Skill runs commands (tests, builds, git) |
| `Grep` | Skill searches file contents |
| `Glob` | Skill searches for files by name pattern |
| `Skill` | Skill delegates to other skills |
| `Agent` | Skill needs subagent delegation for parallel or bulk work |
| `WebFetch` | Skill fetches content from URLs |
| `WebSearch` | Skill searches the internet |

**Rule of thumb:** If a step does not use a tool, do not include that tool. A read-only analysis skill should NOT include `Write` or `Edit`.

#### Trigger Design

Triggers determine when Claude activates the skill. Poor triggers cause false activations or missed activations.

**Good triggers:**
- Specific slash commands: `write-skill`, `create-skill`
- Natural language that uniquely identifies the task: `how to write a skill`, `author new skill`
- Problem-oriented phrases: `automate this workflow`, `make a reusable pattern`

**Bad triggers:**
- Too broad: `help`, `create`, `write` (matches too many unrelated requests)
- Too narrow: `create a fastapi database migration skill for postgres` (too specific to match)
- Overlapping with other skills: Check existing triggers before adding yours

To check for trigger overlap:
```bash
grep -r "triggers:" core/.claude/skills/*/SKILL.md
```

#### Argument-Hint Design

The argument hint appears in help text and teaches users what to provide.

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `<required>` | `<feature-description>` | Single required input |
| `<required> [optional]` | `<bug-description> [--verbose]` | Required with optional flags |
| `<mode> [details]` | `<scan\|propose\|create> [name]` | Multi-mode skills |
| `<file-or-description>` | `<path/to/file or natural language>` | Flexible input types |

### 2.2 Write the Title and Preamble

After the frontmatter, write a descriptive title and one-line purpose statement:

```markdown
# Skill Title — Brief Subtitle

One sentence explaining what this skill does in practical terms.

**Request:** $ARGUMENTS
```

The `$ARGUMENTS` variable is replaced with the user's input at runtime. Always include it so the skill knows what to act on.

### 2.3 Structure the Steps

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

### N.1 Sub-step Title

1. Specific instruction with concrete action
2. Another specific instruction
3. Expected outcome or decision point

### N.2 Another Sub-step

| Situation | Action |
|-----------|--------|
| Happy path | Do X |
| Error case | Do Y instead |
| Edge case | Ask user for clarification |
```

#### Recommended Step Count

| Skill Type | Steps | Reasoning |
|------------|-------|-----------|
| Simple workflow | 3-5 | Focused task, minimal branching |
| Standard workflow | 5-8 | Most skills fall here |
| Complex workflow | 8-10 | Multi-phase with verification |
| Too many | >10 | Split into multiple skills or use subagent delegation |

### 2.4 Add Tables for Decision Logic

When a step has conditional behavior, use a table instead of nested if-else prose:

```markdown
| Condition | Action | Next Step |
|-----------|--------|-----------|
| All tests pass | Report success | Step 6 |
| 1-2 tests fail | Attempt auto-fix | Step 5 |
| >2 tests fail | Escalate to user | STOP |
| Build error | Check dependencies first | Step 4.2 |
```

Tables are faster for Claude to parse than nested bullet points and reduce errors in conditional logic.

### 2.5 Add Code Block Templates

When a step produces output or requires specific formatting, include a template:

```markdown
Output the results in this format:
\```
Analysis Results:
  Files scanned: {count}
  Issues found: {count}
  Severity breakdown:
    Critical: {n}
    Warning: {n}
    Info: {n}
\```
```

### 2.6 Write MUST DO / MUST NOT DO Sections

Every skill ends with explicit behavioral boundaries. These are the guardrails that prevent the skill from going off-track.

```markdown
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

Rules for writing MUST DO / MUST NOT DO:
- 4-8 items per section (fewer is better — only include non-obvious rules)
- Each item explains the consequence of violation ("...causes cascading errors")
- MUST NOT items always state what to do instead
- Do not repeat what the steps already say — these are for edge cases and guardrails

### 2.7 Validate Before Saving

Before writing the skill file, run through the quality checklist in Step 5.

---

## STEP 3: Session Log Analysis

Extract skill candidates from the current conversation by identifying repeated workflows.

### 3.1 Scan for Repeated Patterns

Review the conversation history for multi-step sequences that were performed 2+ times:

1. **Identify repeated tool call sequences** — Look for the same 3+ tool calls in the same order appearing multiple times
2. **Identify repeated file access patterns** — The same set of files read/edited across multiple tasks
3. **Identify repeated command sequences** — The same bash commands run in succession

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
| `argument-hint` uses `<>` and `[]` correctly | Required in angle brackets, optional in square brackets |
| No placeholder markers | No `<!-- TODO: -->`, `<!-- FIXME: -->`, `<!-- PLACEHOLDER -->` in the body |

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

---

## STEP 6: Skill Testing

Generate test scenarios to validate the skill works correctly before promoting it.

### 6.1 Define Test Scenarios

Create three scenarios for every skill:

#### Happy Path Test

```
Scenario: Standard use case
  Input: <typical argument the user would provide>
  Expected behavior:
    - Step 1 completes: <specific observable outcome>
    - Step 2 completes: <specific observable outcome>
    - ...
    - Final output: <what the user sees>
  Success criteria: <measurable result>
```

#### Edge Case Test

```
Scenario: Unusual but valid input
  Input: <edge case argument — empty string, very long input, special characters>
  Expected behavior:
    - Skill handles gracefully without crashing
    - User receives clear feedback if input is invalid
  Success criteria: <no errors, appropriate fallback behavior>
```

#### Error Case Test

```
Scenario: Invalid input or failed prerequisite
  Input: <missing argument, wrong format, or broken environment>
  Expected behavior:
    - Skill detects the problem in Step 1 or Step 2
    - User receives actionable error message
    - Skill does NOT proceed with partial/broken state
  Success criteria: <clear error message, no side effects>
```

### 6.2 Manual Testing Procedure

To test a skill after creation:

1. Open a new Claude Code session (fresh context)
2. Invoke the skill with each test scenario input
3. Verify each step produces the expected outcome
4. Check that MUST DO rules are followed
5. Deliberately trigger a MUST NOT DO rule and verify it is respected
6. Test with both slash command triggers and natural language triggers

### 6.3 Regression Indicators

After the skill is in use, watch for these signs it needs revision:

| Signal | Meaning | Action |
|--------|---------|--------|
| Users rephrase and re-invoke | Triggers are too narrow | Add more natural language triggers |
| Skill activates for unrelated requests | Triggers are too broad | Make triggers more specific |
| Users skip steps manually | Steps are unnecessary or in wrong order | Restructure |
| Users always modify the output | Output format does not match needs | Update templates |
| Errors in later steps | Earlier steps missed validation | Add prerequisite checks |

---

## STEP 7: Hub Promotion Workflow

If the skill is valuable enough to share across projects via the hub.

### 7.1 Pre-Promotion Checklist

| Check | Action |
|-------|--------|
| Quality checklist passes (Step 5) | All items green |
| Tested with 3 scenarios (Step 6) | All pass |
| Not a duplicate | Run: `PYTHONPATH=. python scripts/dedup_check.py` |
| Follows naming conventions (Step 4) | Directory and name match, correct prefix if stack-specific |
| `version` field present | SemVer format in frontmatter |
| `type` field present | `workflow` or `reference` declared |
| `allowed-tools` is least-privilege | Read-only skills don't include Write/Edit/Bash |
| No project-specific hardcoded paths | Replace with `$ARGUMENTS` or documented placeholders |
| No placeholder markers | No `<!-- TODO: -->` or stub content |
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

## STEP 8: Template Library and Anti-Patterns

Reference material for skill authoring — extracted into separate files for size management.

### 8.1 Skill Templates

Seven pre-built skeletons for common skill types (Workflow, Analysis, Generation, Testing, Deployment, Migration, Reference). Copy and fill in placeholders.

**Read:** `references/templates.md`

### 8.2 Common Anti-Patterns

Eight anti-patterns to avoid: Disguised Rule, Vague Advisor, Kitchen Sink, Trigger Hog, Copy-Paste Trap, Unverified Optimist, Tool Hoarder, Missing Handoff.

**Read:** `references/anti-patterns.md`

### 8.3 Deprecation Workflow

When replacing a skill:

1. Add `deprecated: true` and `deprecated_by: replacement-name` to the old skill's frontmatter
2. Keep the deprecated skill for 2 version cycles
3. Update the replacement skill's description
4. After 2 cycles, remove and update the registry

MUST NOT delete a skill without the deprecation lifecycle.

---

## MUST DO

- Always read at least 2 existing skills before authoring a new one — pattern-match from working examples
- Always validate with the quality checklist (Step 5) before saving
- Always check for trigger overlap with existing skills
- Always include MUST DO and MUST NOT DO sections in every skill
- Always include a verification step in skills that modify state
- Always use concrete, actionable language in steps — verbs, not adjectives
- Always present the draft to the user for review before saving
- Always test the skill with the 3 scenarios from Step 6

## MUST NOT DO

- MUST NOT create a skill for something that should be a rule — if it has no steps, use `.claude/rules/`
- MUST NOT use vague step language ("consider", "think about", "ensure quality") — use specific actions instead
- MUST NOT create skills with >10 steps — split into sub-skills or use delegation
- MUST NOT add tools to `allowed-tools` that the skill does not use
- MUST NOT create skills with overlapping triggers — check existing skills first
- MUST NOT save a skill without running the quality checklist
- MUST NOT create skills that duplicate existing ones — extend or consolidate instead
- MUST NOT skip the MUST DO / MUST NOT DO sections — they are mandatory guardrails
