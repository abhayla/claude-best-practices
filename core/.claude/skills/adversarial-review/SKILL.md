---
name: adversarial-review
description: >
  Launch a structured adversarial review using a subagent with a dedicated reviewer
  persona. Supports both plan review (pre-implementation) and code review
  (post-implementation). The reviewer critically examines work for security issues,
  edge cases, performance problems, and design weaknesses through up to 3 rounds of
  structured debate. Use when finalizing a plan or code change that needs rigorous
  challenge before committing.
triggers:
  - adversarial-review
  - challenge
  - devil-advocate
  - adversarial review
  - challenge this plan
  - challenge this code
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<file-path, plan-path, or PR-diff> [--mode plan|code] [--severity-filter critical|major|minor] [--max-rounds 1-3]"
version: "1.0.0"
type: workflow
---

# Adversarial Review

Launch a structured adversarial review of a plan or code change. A subagent with a dedicated reviewer persona critically examines the work through multi-round debate, producing a structured critique with issue IDs, categories, severities, and suggested fixes.

**Target:** $ARGUMENTS

---

## STEP 0: Determine Review Mode and Gather Context

Before launching the reviewer, determine what is being reviewed and collect all necessary context.

### 0.1 Detect Review Mode

Determine the review mode from the arguments or by inspecting the target:

| Signal | Mode | Rationale |
|--------|------|-----------|
| Argument contains `--mode plan` | **Plan Review** | Explicit mode selection |
| Argument contains `--mode code` | **Code Review** | Explicit mode selection |
| Target is a `.md` file with headings like "Tasks", "Architecture", "Design" | **Plan Review** | Looks like a design document |
| Target is a diff, PR number, or source code file | **Code Review** | Looks like implementation |
| Target is output from `/brainstorm` or `/writing-plans` | **Plan Review** | Upstream skill output |
| Target is output from `/implement` or `/pr-standards` | **Code Review** | Upstream skill output |
| Ambiguous | **Ask the user** | Do not guess — the criteria differ significantly |

Set the mode explicitly:

```
Review Mode: PLAN REVIEW
  or
Review Mode: CODE REVIEW
```

### 0.2 Gather the Work Under Review

Collect the full content to be reviewed based on the mode:

**For Plan Review:**

```bash
# If the plan is a file
cat "$PLAN_FILE"

# If the plan was output from a previous skill, it should be in the conversation context
# Ensure you have: objectives, architecture decisions, task breakdown, dependencies
```

**For Code Review:**

```bash
# If reviewing a PR diff
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff "$BASE_BRANCH"...HEAD

# If reviewing specific files
cat "$TARGET_FILE"

# If reviewing a PR by number
gh pr diff $PR_NUMBER
```

### 0.3 Gather Project Context

The reviewer needs project context to give informed feedback. Collect:

```bash
# Project conventions and rules
cat CLAUDE.md 2>/dev/null || true
cat .claude/rules/*.md 2>/dev/null || true

# Architecture documentation if available
cat docs/ARCHITECTURE.md 2>/dev/null || true
cat docs/ADR/*.md 2>/dev/null || true
```

### 0.4 Gather Original Requirements

Identify what the work is supposed to achieve:

| Source | How to Find |
|--------|-------------|
| Issue/ticket | Check PR description, commit messages, or ask the user |
| Skill output | If preceded by `/brainstorm` or `/writing-plans`, the requirements are in the conversation |
| User request | The original message that triggered the work |
| Specification | Check for linked spec documents |

Document the requirements clearly — the reviewer will check coverage against them.

```
Original Requirements:
1. {requirement 1}
2. {requirement 2}
3. {requirement 3}
...
```

---

## STEP 1: Applicability Check

Before launching the full adversarial review, determine whether it is warranted for this change.

### 1.1 Decision Guide

| Category | Recommendation | Examples |
|----------|---------------|----------|
| **ALWAYS review** | Security-sensitive code | Auth, payment handling, token management, encryption, PII processing, access control, session management |
| **ALWAYS review** | Data integrity | Database migrations, data transformations, backup/restore, import/export |
| **ALWAYS review** | High-blast-radius | Shared libraries, core abstractions, middleware, API contracts consumed by multiple clients |
| **RECOMMENDED** | New features | New endpoints, new UI flows, new integrations, new data models |
| **RECOMMENDED** | Architectural changes | New patterns, service boundaries, state management approaches, dependency changes |
| **RECOMMENDED** | API design | New or changed public APIs, webhook contracts, event schemas |
| **OPTIONAL** | Bug fixes | Isolated fixes with clear root cause and targeted tests |
| **OPTIONAL** | Documentation | Architecture docs, API docs, onboarding guides |
| **OPTIONAL** | Configuration | Environment variables, feature flags, build config |
| **SKIP** | Trivial changes | Typo fixes, formatting, comment updates, dependency bumps with no API changes |
| **SKIP** | Auto-generated | Generated code, lock files, compiled assets |

### 1.2 Skip Protocol

If the change falls in the SKIP category:

```
Adversarial Review: SKIPPED
Reason: {category} — adversarial review adds overhead without proportional value.
Recommendation: Proceed directly to /request-code-review.
```

If the user explicitly requested adversarial review for a SKIP-category change, proceed anyway — the user's judgment overrides the heuristic.

### 1.3 Scope Calibration

Adjust review depth based on change size:

| Change Size | Max Rounds | Expected Issues | Review Time |
|-------------|-----------|-----------------|-------------|
| Small (< 100 lines) | 2 | 0-5 | 5-10 min |
| Medium (100-500 lines) | 3 | 3-10 | 15-30 min |
| Large (500+ lines) | 3 | 8-20+ | 30-60 min |

For large changes, consider splitting the review by component or file group to keep each review focused.

---

## STEP 2: Launch Adversarial Reviewer Subagent

Launch a subagent with a dedicated reviewer persona. The reviewer operates in a separate context with read-only access.


**Read:** `references/launch-adversarial-reviewer-subagent.md` for detailed step 2: launch adversarial reviewer subagent reference material.

## STEP 3: Round 1 — Reviewer Critique

The reviewer subagent examines the work and produces a structured critique.


**Read:** `references/round-1-reviewer-critique.md` for detailed step 3: round 1 — reviewer critique reference material.

## STEP 4: Round 2 — Author Response

The author (main agent) responds to each issue from the reviewer's critique.


**Read:** `references/round-2-author-response.md` for detailed step 4: round 2 — author response reference material.

# After applying fixes, verify nothing is broken
# For code:
{project test command}

# For plans:
# Re-read the updated plan to ensure consistency
```

---

## STEP 5: Round 2 — Reviewer Follow-Up

The reviewer subagent examines the author's responses and applied fixes.


**Read:** `references/round-2-reviewer-follow-up.md` for detailed step 5: round 2 — reviewer follow-up reference material.

## STEP 6: Round 3 — Final Resolution (If Needed)

Round 3 is triggered ONLY if there are ESCALATE items from Round 2. If all items are SATISFIED, skip to Step 7.


**Read:** `references/round-3-final-resolution-if-needed.md` for detailed step 6: round 3 — final resolution (if needed) reference material.

## STEP 7: Generate Review Report

After all rounds complete, produce a comprehensive review report.


**Read:** `references/generate-review-report.md` for detailed step 7: generate review report reference material.

## STEP 8: Apply Final Fixes and Verify

After the review report is generated, apply any remaining accepted fixes and verify the result.

### 8.1 Fix Application Checklist

```
Fixes to apply:
  [ ] R1: {description of fix}
  [ ] R3: {description of fix}
  [ ] R5: {description of fix}
  ...

Already applied during review:
  [x] R2: {applied in Round 2}
  [x] R4: {applied in Round 2}
```

### 8.2 Post-Fix Verification

After applying all fixes:

**For Code Review:**

```bash
# Run tests to verify fixes
{project test command}

# Run linters
{project lint command}

# Verify no regressions
git diff --stat
```

**For Plan Review:**

1. Re-read the updated plan end-to-end
2. Verify all accepted issues are reflected in the plan
3. Verify the plan is internally consistent after changes
4. Check that deferred items are noted in the plan's risks/caveats section

### 8.3 Verification Report

```
Post-Review Verification:
  Tests: {PASS | FAIL — details}
  Lint: {CLEAN | WARNINGS — details}
  Build: {SUCCESS | FAILURE — details}
  Regressions: {NONE | DETECTED — details}

All accepted fixes applied and verified.
```

---

## Integration with Pipeline

This skill integrates with other skills at specific points in the development pipeline.

### Plan Review Pipeline

```
/brainstorm or /writing-plans
        |
        v
  /adversarial-review --mode plan
        |
        v
  (fix plan issues)
        |
        v
  /executing-plans or /implement
```

### Code Review Pipeline

```
/implement
        |
        v
  /pr-standards (optional)
        |
        v
  /adversarial-review --mode code
        |
        v
  (fix code issues)
        |
        v
  /request-code-review
```

### Standalone Usage

The skill can also be invoked standalone on any file or diff:

```
/adversarial-review src/auth/TokenService.ts --mode code
/adversarial-review docs/design/payment-flow.md --mode plan
/adversarial-review --mode code   (reviews current branch diff)
```

---

## Common Scenarios

### Scenario 1: Reviewer Finds Nothing

If the reviewer reports zero issues:

1. This is suspicious — verify the reviewer examined all criteria
2. Check that the reviewer had access to the full work (not a truncated diff)
3. If the review is genuinely clean, document which criteria were checked
4. Proceed with PASSED verdict

### Scenario 2: All Issues Are Minor

If the reviewer only finds minor issues:

1. Verify the reviewer checked security and correctness criteria explicitly
2. If security-sensitive code is involved, ask the reviewer to do a focused security pass
3. If genuinely only minor issues, accept/reject each and proceed with PASSED

### Scenario 3: Author Rejects Everything

If the author rejects all reviewer findings:

1. This is a red flag — pattern-match against "defensive author" anti-pattern
2. Verify each rejection has concrete evidence (not just "it's fine")
3. If rejections are well-evidenced, they are valid — proceed
4. If rejections lack evidence, the reviewer should escalate in Round 2

### Scenario 4: Reviewer Finds Critical Security Issue

If a critical security issue is found:

1. STOP — do not proceed with any other review items
2. Fix the security issue immediately
3. Verify the fix with the reviewer
4. Resume review of remaining items
5. Consider whether the security issue indicates a broader pattern that needs a security audit

### Scenario 5: Review Scope Creep

If the reviewer raises issues in code that was not changed:

1. Classify pre-existing issues separately from issues in the changed code
2. Pre-existing critical issues: flag to the user but do not block the current review
3. Pre-existing non-critical issues: note in report as "pre-existing, out of scope"
4. Changed code issues: handle normally through the review process

### Scenario 6: Plan Review Leads to Major Redesign

If the adversarial review of a plan reveals fundamental architectural problems:

1. Do NOT try to patch the plan — a fundamentally flawed plan needs rethinking
2. Summarize the architectural concerns clearly
3. Recommend returning to `/brainstorm` with the reviewer's concerns as constraints
4. Mark the review as BLOCKED with clear explanation

---

## CRITICAL RULES

- **Always use structured format** — Every issue MUST have an ID, category, severity, location, evidence, and suggested fix. No free-form complaints.
- **Evidence is mandatory** — "This might be a problem" is not acceptable. Show the scenario, the input, the failure mode, or the proof.
- **Every issue gets a response** — The author MUST respond to every issue with Accept, Reject, Defer, or Partial. No silent ignoring.
- **Rejections require proof** — "I disagree" is not a valid rejection. Provide counter-evidence.
- **Critical issues block** — Any unresolved critical issue prevents proceeding. No exceptions.
- **Maximum 3 rounds** — If issues are not resolved after 3 rounds, escalate to human. Do not loop.
- **Reviewer is read-only** — The reviewer subagent MUST NOT modify any files. Separation of concerns prevents conflicts.
- **Fixes must be verified** — After applying fixes, run tests and linters. Do not trust that fixes are correct without verification.
- **Human escalation is final** — When an issue is escalated to human review, WAIT for their decision. Do not auto-resolve.
- **Deferred items need tracking** — Every deferred issue MUST have a tracking issue or TODO with a reference. "We'll fix it later" without tracking means it never gets fixed.

## MUST NOT DO

- MUST NOT skip the applicability check — reviewing trivial changes wastes time; skipping review on security code risks vulnerabilities
- MUST NOT allow the reviewer to modify files — the reviewer is read-only to prevent conflicts with the author's changes
- MUST NOT proceed with unresolved critical issues — critical issues block by definition, regardless of schedule pressure
- MUST NOT accept vague evidence from the reviewer — demand concrete scenarios, not hypothetical concerns
- MUST NOT accept vague fixes from the reviewer — demand specific recommendations, not "consider improving"
- MUST NOT allow the author to reject issues without evidence — "it's fine" is not evidence
- MUST NOT exceed 3 rounds of debate — escalate to human after Round 3 to prevent infinite loops
- MUST NOT auto-resolve human-escalated items — wait for the human's decision
- MUST NOT defer critical security issues — they must be fixed, not deferred
- MUST NOT skip post-fix verification — fixes can introduce regressions; always run tests after applying changes
- MUST NOT review trivially and then claim PASSED — a PASSED verdict with zero issues on security-sensitive code is suspicious and should be justified
- MUST NOT mix pre-existing issues with new issues — separate them clearly in the report to avoid scope creep
