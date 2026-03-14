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

## STEP 8: Template Library

Pre-built starting skeletons for common skill types. Copy the appropriate template and fill in the placeholders.

### Template A: Workflow Skill

Multi-step process that transforms input to output (like `/implement`).

```markdown
---
name: {name}
description: >
  {Verb} {object} following a structured workflow: {phase1}, {phase2},
  {phase3}, and {verification}. Use when {trigger condition}.
triggers:
  - {slash-command}
  - {natural-language-1}
  - {natural-language-2}
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<{primary-input}>"
type: workflow
version: "1.0.0"
---

# {Title}

{One-sentence purpose.}

**Request:** $ARGUMENTS

---

## STEP 1: Analyze Requirements

1. Read the request and identify scope
2. Check existing code/tests in the affected area
3. Identify prerequisites and dependencies

## STEP 2: Prepare

1. {Setup action 1}
2. {Setup action 2}
3. Verify prerequisites are met before proceeding

## STEP 3: Execute

1. {Core action 1}
2. {Core action 2}
3. {Core action 3}

## STEP 4: Verify

1. Run tests/checks to confirm the work is correct
2. Review output for completeness
3. Check for regressions or side effects

| Check | Status |
|-------|--------|
| {Check 1} | ⬜ |
| {Check 2} | ⬜ |
| {Check 3} | ⬜ |

## STEP 5: Report

Output summary of what was done, decisions made, and any follow-up needed.

---

## MUST DO

- Always complete Step 1 before executing — skipping analysis causes rework
- Always run verification — unverified work is unreliable
- {Skill-specific rule with consequence}

## MUST NOT DO

- MUST NOT skip verification — report only after all checks pass
- MUST NOT modify files outside the stated scope — ask user first
- {Skill-specific prohibition with alternative}
```

### Template B: Analysis Skill

Read-only investigation that produces a report (like `/systematic-debugging`).

```markdown
---
name: {name}
description: >
  {Verb} {subject} using a structured diagnosis: {phase1}, {phase2},
  {phase3}. Use when {trigger condition} instead of {inferior alternative}.
triggers:
  - {slash-command}
  - {natural-language-1}
  - {natural-language-2}
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<{description-of-what-to-analyze}>"
type: workflow
version: "1.0.0"
---

# {Title}

{One-sentence purpose. Emphasize this is read-only — no code changes.}

**Subject:** $ARGUMENTS

---

## STEP 1: Gather Context

1. Identify the relevant files, modules, or components
2. Read the code/config/logs at the center of the investigation
3. Note initial observations

## STEP 2: Investigate

1. {Investigation technique 1}
2. {Investigation technique 2}
3. Record findings in a structured format

| Finding | Location | Severity |
|---------|----------|----------|
| {finding} | {file:line} | {High/Medium/Low} |

## STEP 3: Analyze

1. Identify root causes or patterns in the findings
2. Rank by severity or impact
3. Cross-reference with known issues or documentation

## STEP 4: Report

Output a structured analysis report:

\```
ANALYSIS REPORT
===============
Subject: {what was analyzed}
Scope: {files/components examined}

Findings:
  1. {finding with evidence}
  2. {finding with evidence}

Root Cause: {if applicable}
Recommendations: {prioritized list}
\```

---

## MUST DO

- Always read the actual code/data — do not analyze from memory or assumptions
- Always provide evidence (file paths, line numbers) for every finding
- Always rank findings by severity

## MUST NOT DO

- MUST NOT modify any files — this skill is read-only. Use /implement for fixes.
- MUST NOT report findings without evidence — every claim needs a file path and line number
- MUST NOT skip the structured report — raw observations without synthesis are not useful
```

### Template C: Generation Skill

Creates new output artifacts (like `/brainstorm`).

```markdown
---
name: {name}
description: >
  {Verb} {output-type} through structured exploration: {phase1}, {phase2},
  {phase3}. Use before {downstream-activity} to ensure quality input.
triggers:
  - {slash-command}
  - {natural-language-1}
  - {natural-language-2}
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<{what-to-generate}>"
type: workflow
version: "1.0.0"
---

# {Title}

{One-sentence purpose.}

**Topic:** $ARGUMENTS

---

## STEP 1: Understand Requirements

Ask 3-5 clarifying questions before generating anything:

1. {Question about scope}
2. {Question about audience/consumer}
3. {Question about constraints}
4. {Question about format preferences}

Wait for answers before proceeding.

## STEP 2: Research

1. Scan the codebase for relevant context
2. Identify patterns, conventions, and constraints
3. Note dependencies and integration points

## STEP 3: Generate

1. Produce the output following project conventions
2. Include all required sections
3. Use templates where applicable

## STEP 4: Review with User

Present the output section by section. Wait for feedback between sections.
Do NOT dump everything at once.

## STEP 5: Finalize

1. Incorporate feedback
2. Save to the appropriate location
3. Suggest next steps

---

## MUST DO

- Always ask clarifying questions in Step 1 — assumptions lead to rework
- Always ground generation in codebase research (Step 2)
- Always present output incrementally for review

## MUST NOT DO

- MUST NOT skip questioning and jump to generation — misunderstood requirements waste time
- MUST NOT present a single option — always offer alternatives where applicable
- MUST NOT save output without user approval
```

### Template D: Testing Skill

Runs tests and validates results (like `android-run-tests`).

```markdown
---
name: {name}
description: >
  Run {test-type} tests for {target} with structured validation: setup,
  execute, analyze failures, fix-loop, and regression check.
triggers:
  - {slash-command}
  - run {stack} tests
  - test {component}
allowed-tools: "Bash Read Edit Grep Glob"
argument-hint: "<test-target or 'all'> [--fix]"
type: workflow
version: "1.0.0"
---

# {Title}

Run and validate tests with structured failure analysis.

**Target:** $ARGUMENTS

---

## STEP 1: Identify Test Scope

1. Parse the target from `$ARGUMENTS`
2. Locate the relevant test files
3. Check prerequisites (dependencies installed, services running)

## STEP 2: Run Tests

```bash
{test-command} {target}
```

Capture full output including exit code.

## STEP 3: Analyze Results

| Outcome | Action |
|---------|--------|
| All pass | Report success, proceed to Step 5 |
| 1-3 failures | Analyze each failure, proceed to Step 4 |
| >3 failures | Report summary, ask user before proceeding |
| Build error | Fix build first, re-run |

## STEP 4: Fix Loop (if --fix flag provided)

For each failing test:
1. Read the test and the code under test
2. Identify the root cause of the failure
3. Apply a targeted fix
4. Re-run the specific test
5. Maximum 3 fix iterations per test

## STEP 5: Regression Check

Run the broader test suite to verify no regressions:
```bash
{broader-test-command}
```

## STEP 6: Report

\```
TEST RESULTS
============
Target: {target}
Command: {command}
Result: {PASS/FAIL}
  Passed: {n}
  Failed: {n}
  Skipped: {n}
  Duration: {time}

{If failures: detailed failure list with file:line references}
\```

---

## MUST DO

- Always run the exact test command — do not guess at results
- Always analyze failures before attempting fixes
- Always run regression check after fixes

## MUST NOT DO

- MUST NOT report tests as passing without running them
- MUST NOT fix tests by deleting or skipping them — fix the underlying issue
- MUST NOT proceed past 3 fix iterations without user input
```

### Template E: Deployment Skill

Builds and ships artifacts.

```markdown
---
name: {name}
description: >
  Deploy {target} to {environment}: pre-flight checks, build, deploy,
  smoke test, and rollback plan. Use for structured, safe deployments.
triggers:
  - {slash-command}
  - deploy {target}
  - ship {target}
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<target> <environment: staging|production>"
type: workflow
version: "1.0.0"
---

# {Title}

Structured deployment with safety checks and rollback plan.

**Target:** $ARGUMENTS

---

## STEP 1: Pre-Flight Checks

Verify all deployment prerequisites:

| Check | Command | Required |
|-------|---------|----------|
| Tests pass | `{test-command}` | Yes |
| Build succeeds | `{build-command}` | Yes |
| No uncommitted changes | `git status` | Yes |
| On correct branch | `git branch --show-current` | Yes |
| Dependencies up to date | `{dep-check-command}` | Yes |

If ANY required check fails, STOP and report the issue. Do NOT deploy with failing checks.

## STEP 2: Build

1. Run the build command
2. Verify build artifacts are created
3. Record the build hash/version for rollback reference

## STEP 3: Deploy

1. Execute the deployment command for the target environment
2. Wait for deployment to complete
3. Record the deployment ID/timestamp

## STEP 4: Smoke Test

Run minimal health checks against the deployed environment:

1. {Health check 1}
2. {Health check 2}
3. {Critical path check}

## STEP 5: Report or Rollback

| Smoke Test Result | Action |
|-------------------|--------|
| All pass | Report success with deployment details |
| Partial failure | Investigate, report findings, ask user whether to rollback |
| Complete failure | Execute rollback immediately, report what happened |

---

## MUST DO

- Always run pre-flight checks — deploying broken code is worse than not deploying
- Always record the previous version for rollback
- Always run smoke tests after deployment

## MUST NOT DO

- MUST NOT deploy with failing tests — fix tests first
- MUST NOT skip smoke tests — "it deployed successfully" is not verification
- MUST NOT deploy to production without explicit user confirmation
```

### Template F: Migration Skill

Transforms code, data, or configuration from one format/version to another.

```markdown
---
name: {name}
description: >
  Migrate {source} from {old-format} to {new-format}: analyze current state,
  plan migration, execute with backups, verify correctness, clean up.
triggers:
  - {slash-command}
  - migrate {subject}
  - convert {subject}
  - upgrade {subject}
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<source-path or description> [--dry-run]"
type: workflow
version: "1.0.0"
---

# {Title}

Structured migration with backup, validation, and rollback support.

**Target:** $ARGUMENTS

---

## STEP 1: Analyze Current State

1. Inventory all items to be migrated
2. Identify patterns and variations in the source format
3. Detect edge cases (special characters, missing fields, legacy formats)
4. Count total items and estimate scope

Report:
\```
Migration Scope:
  Items to migrate: {count}
  Patterns detected: {list}
  Edge cases: {list}
  Estimated effort: {assessment}
\```

## STEP 2: Plan Migration

1. Define the transformation rules for each pattern
2. Plan the migration order (dependencies first)
3. Identify items that require manual review
4. Create the rollback strategy

## STEP 3: Backup

1. Create a backup of all files/data that will be modified
2. Verify the backup is complete and readable
3. Record the backup location

If `--dry-run` flag is set, proceed to Step 4 but write output to a preview location instead of modifying originals.

## STEP 4: Execute Migration

For each item:
1. Apply transformation rules
2. Validate the output format
3. Record success or failure

## STEP 5: Verify

1. Compare migrated output against expected format
2. Run tests/validators on the migrated data
3. Spot-check edge cases identified in Step 1
4. Verify no data loss (count input items vs output items)

## STEP 6: Clean Up

1. Remove backup files (only after verification passes)
2. Update documentation to reflect the new format
3. Report migration results

---

## MUST DO

- Always create a backup before modifying any files
- Always verify migrated output — transformation bugs are silent
- Always support `--dry-run` mode for previewing changes

## MUST NOT DO

- MUST NOT delete backups until verification passes
- MUST NOT migrate without analyzing edge cases first — they cause silent data corruption
- MUST NOT skip the count verification (input items == output items)
```

### Template G: Reference Skill

Knowledge base or lookup guide (like `/ai-gemini-api`). No step-by-step workflow — organized sections for quick reference.

```markdown
---
name: {name}
description: >
  {Subject} reference guide covering {topic1}, {topic2}, and {topic3}.
  Use as a lookup when working with {technology/domain}.
triggers:
  - {slash-command}
  - {natural-language-1}
  - {natural-language-2}
allowed-tools: "Read Grep Glob"
argument-hint: "<topic or 'all' for full reference>"
type: reference
version: "1.0.0"
---

# {Title} — Reference Guide

Quick reference for {subject}. Look up specific topics or browse the full guide.

**Topic:** $ARGUMENTS

---

## {Section 1: Core Concepts}

{Concise explanation with code examples}

## {Section 2: Common Patterns}

| Pattern | When to Use | Example |
|---------|------------|---------|
| {pattern} | {context} | {code} |

## {Section 3: Troubleshooting}

| Problem | Cause | Solution |
|---------|-------|----------|
| {error} | {why} | {fix} |

## {Section 4: Known Issues}

- {issue with workaround}

---

## CRITICAL RULES

- This is a read-only reference — do NOT modify project files based on this guide alone
- Always verify code examples against the project's actual version/configuration
- If a pattern conflicts with project conventions, follow project conventions
```

---

## Deprecation Workflow

When a skill is being replaced by a better version:

1. **Add deprecation fields** to the old skill's frontmatter:
   ```yaml
   deprecated: true
   deprecated_by: replacement-skill-name
   ```

2. **Keep the deprecated skill** for 2 version cycles — downstream projects may still reference it

3. **Update the replacement skill's description** to mention it replaces the old one

4. **After 2 cycles**, remove the deprecated skill and update the registry

MUST NOT delete a skill without the deprecation lifecycle. Abrupt removal breaks downstream projects that depend on it.

---

## Common Skill Anti-Patterns

### Anti-Pattern 1: The Disguised Rule

**What it looks like:** A "skill" with no steps — just a list of do/don't instructions.

**Why it fails:** Rules load automatically, skills load on-demand. If the guidance should always be active, it belongs in `.claude/rules/`, not `.claude/skills/`.

**Fix:** Move it to `core/.claude/rules/{name}.md` with appropriate `globs:` frontmatter.

### Anti-Pattern 2: The Vague Advisor

**What it looks like:** Steps contain phrases like "consider the implications", "think carefully about", "ensure quality".

**Why it fails:** Claude cannot execute vague instructions reliably. "Consider" is not an action — "Run X and check the output for Y" is.

**Fix:** Replace every vague phrase with a concrete action, command, or decision table.

### Anti-Pattern 3: The Kitchen Sink

**What it looks like:** A skill with 12+ steps that tries to handle every possible scenario.

**Why it fails:** Long skills exceed useful context. Claude loses track of where it is in the process. Users lose patience.

**Fix:** Split into 2-3 focused skills, or use a primary skill that delegates to sub-skills.

### Anti-Pattern 4: The Trigger Hog

**What it looks like:** Triggers include broad terms like "help", "fix", "code", "build".

**Why it fails:** The skill activates for unrelated requests, annoying users and wasting time.

**Fix:** Use specific, multi-word triggers. Test by asking: "Would someone say this ONLY when they want this specific skill?"

### Anti-Pattern 5: The Copy-Paste Trap

**What it looks like:** Two skills that share 70%+ of their steps, with minor variations.

**Why it fails:** Maintenance burden doubles. Fixes to shared logic must be applied twice. They drift apart over time.

**Fix:** Consolidate into one skill with modes (see `skill-factory` for an example of mode-based skills).

### Anti-Pattern 6: The Unverified Optimist

**What it looks like:** A skill that performs actions but has no verification step. It reports success after executing commands without checking results.

**Why it fails:** Commands can fail silently. Files can be written with wrong content. Tests can be skipped. Without verification, the skill produces false confidence.

**Fix:** Every skill that modifies state MUST have a verification step that checks the actual outcome.

### Anti-Pattern 7: The Tool Hoarder

**What it looks like:** `allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill WebFetch WebSearch"`

**Why it fails:** Listing every tool signals to Claude that all are expected to be used, increasing the chance of unnecessary actions. It also makes the skill harder to reason about.

**Fix:** List only the tools actually used in the skill's steps. A read-only analysis skill should NOT include `Write` or `Edit`.

### Anti-Pattern 8: The Missing Handoff

**What it looks like:** A skill that ends with "Done!" but does not tell the user what to do next.

**Why it fails:** Skills are often part of larger workflows. Without a handoff, the user has to figure out the next step themselves.

**Fix:** End with a clear next-step recommendation: "Proceed with `/implement`" or "Review the report and decide whether to fix or defer."

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
