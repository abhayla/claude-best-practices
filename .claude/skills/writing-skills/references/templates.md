# Skill Template Library

Pre-built starting skeletons for common skill types. Copy the appropriate template and fill in the placeholders.

## Template A: Workflow Skill

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

## Template B: Analysis Skill

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

## Template C: Generation Skill

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

## Template D: Testing Skill

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

## Template E: Deployment Skill

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

## Template F: Migration Skill

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

## Template G: Reference Skill

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
