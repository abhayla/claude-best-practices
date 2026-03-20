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
version: "2.0.1"
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


**Read:** `references/skill-authoring-from-scratch.md` for detailed step 2: skill authoring — from scratch reference material.

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


**Read:** `references/skill-testing.md` for detailed step 6: skill testing reference material.

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


## STEP 8: Template Library

Pre-built starting skeletons for common skill types. Copy the appropriate template and fill in the placeholders.

> **Reference:** See [references/skill-templates.md](references/skill-templates.md) for the full template library (Templates A-G: Workflow, Analysis, Generation, Testing, Deployment, Migration, Reference).

---

## Deprecation Workflow and Anti-Patterns

> **Reference:** See [references/anti-patterns.md](references/anti-patterns.md) for the deprecation lifecycle and 8 common skill anti-patterns to avoid.

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
