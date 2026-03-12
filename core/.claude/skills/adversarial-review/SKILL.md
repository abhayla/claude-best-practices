---
name: adversarial-review
description: >
  Launch a structured adversarial review using a subagent with a dedicated reviewer
  persona. Supports both plan review (pre-implementation) and code review
  (post-implementation). The reviewer critically examines work for security issues,
  edge cases, performance problems, and design weaknesses through up to 3 rounds of
  structured debate. Catches blind spots that single-model review misses.
triggers:
  - adversarial-review
  - challenge
  - devil-advocate
  - adversarial review
  - challenge this plan
  - challenge this code
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<file-path, plan-path, or PR-diff> [--mode plan|code] [--severity-filter critical|major|minor] [--max-rounds 1-3]"
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

### 2.1 Reviewer Persona

The reviewer subagent MUST be initialized with this system prompt:

```
You are a senior engineer conducting an adversarial review. Your job is to find
flaws, security issues, edge cases, performance problems, and design weaknesses
in the work presented to you. Be thorough and critical.

Your mandate:
- DO NOT rubber-stamp. If you find nothing wrong, look harder.
- Every claim of "this is fine" must be backed by evidence.
- Assume the author has blind spots — your job is to find them.
- Think about what happens at scale, under load, with malicious input,
  with concurrent access, and when things fail.
- Consider not just whether the code/plan works, but whether it is the
  RIGHT approach for the problem.

Your constraints:
- You have READ-ONLY access. You can read files, search code, and run
  non-destructive commands. You CANNOT edit or write files.
- You must use the structured critique format provided.
- You must provide concrete evidence or scenarios for every issue — no
  vague concerns like "this might be a problem."
- You must suggest a specific fix for every issue, not just identify problems.
```

### 2.2 Reviewer Access Controls

The reviewer subagent gets these tools only:

| Tool | Access | Purpose |
|------|--------|---------|
| Bash | Read-only commands (cat, ls, git log, git show, grep) | Explore codebase for context |
| Read | Full access | Read any file for context |
| Grep | Full access | Search for patterns, usages, and related code |
| Glob | Full access | Find files by pattern |
| Edit | DENIED | Reviewer must not modify code |
| Write | DENIED | Reviewer must not create files |

### 2.3 Reviewer Input Package

Pass these items to the reviewer subagent:

```
ADVERSARIAL REVIEW INPUT
=========================

Review Mode: {PLAN REVIEW | CODE REVIEW}

Original Requirements:
{requirements gathered in Step 0.4}

Project Context:
{CLAUDE.md contents, relevant rules}

Work Under Review:
{plan document OR code diff OR file contents}

Review Criteria:
{plan criteria from Section 2.5 OR code criteria from Section 2.6}
```

### 2.4 Cross-Model Option

If multiple models are available, use a different model for the reviewer to maximize blind-spot coverage:

| Scenario | Reviewer Model | Rationale |
|----------|---------------|-----------|
| Default (single model) | Same model, subagent context | Different context window provides a different perspective |
| Cost-optimized | `model: "haiku"` | Fast, cheap first-pass catches obvious issues |
| Thoroughness-optimized | `model: "sonnet"` | Strong reasoning at moderate cost |
| Maximum coverage | Run two reviewers (haiku + sonnet) | Different models catch different classes of issues |

If only one model is available, the subagent persona with its dedicated adversarial prompt is sufficient — the separate context window and focused mandate produce meaningfully different analysis than the author's perspective.

### 2.5 Plan Review Criteria

When reviewing a plan, the reviewer MUST evaluate each of these dimensions:

| Dimension | What to Check | Red Flags |
|-----------|--------------|-----------|
| **Requirements Coverage** | Does the plan address every stated requirement? | Missing requirements, unstated assumptions |
| **Architectural Risks** | Are there single points of failure, tight coupling, or scaling bottlenecks? | Monolithic design for distributed problems, shared mutable state |
| **Edge Case Handling** | Does the plan account for empty inputs, max values, concurrent access, partial failures? | "Happy path only" designs, no error scenarios discussed |
| **Task Estimates** | Are time/effort estimates realistic given complexity? | Optimistic estimates for novel work, no buffer for unknowns |
| **Task Dependencies** | Are dependencies between tasks identified and ordered correctly? | Circular dependencies, missing prerequisites, parallelism assumptions |
| **Security Considerations** | Are authentication, authorization, data protection, and input validation addressed? | "We'll add security later", no threat model |
| **Scalability Concerns** | Will the design work at 10x, 100x current scale? | Linear algorithms on growing datasets, no pagination, unbounded queues |
| **Testing Strategy** | Is there a clear plan for how to test the implementation? | "We'll write tests" with no specifics, no integration test plan |
| **Rollback Plan** | Can the change be reversed if it fails in production? | Irreversible migrations, big-bang deployments |
| **Missing Components** | Are there components needed but not mentioned? | No monitoring, no logging, no documentation updates |

### 2.6 Code Review Criteria

When reviewing code, the reviewer MUST evaluate each of these dimensions:

| Dimension | What to Check | Common Issues |
|-----------|--------------|---------------|
| **Security Vulnerabilities** | Injection (SQL, XSS, command), auth bypass, data exposure, insecure deserialization, SSRF | String concatenation in queries, missing auth middleware, PII in logs |
| **Performance Issues** | N+1 queries, unbounded loops, missing pagination, blocking I/O on hot paths, memory leaks | `for` loop with DB call inside, `SELECT *` without LIMIT, large object accumulation |
| **Correctness** | Off-by-one errors, null/undefined handling, race conditions, integer overflow, floating-point comparison | `<=` vs `<`, missing null checks, `==` on floats, TOCTOU races |
| **Error Handling** | Swallowed exceptions, missing cleanup, unclear error messages, missing retry logic, cascading failures | Empty `catch` blocks, no `finally` for resource cleanup, generic error messages |
| **API Contract Violations** | Response shape changes, missing fields, type mismatches, undocumented endpoints | Returning different shapes for success/error, missing pagination metadata |
| **Test Coverage Gaps** | Untested error paths, missing edge case tests, no integration tests for new integrations | Only happy-path tests, mocked-out critical logic, no test for the fix |
| **Concurrency Issues** | Race conditions, deadlocks, missing locks, thread-unsafe shared state | Global mutable state, non-atomic read-modify-write, lock ordering violations |
| **Resource Management** | Unclosed connections, file handle leaks, missing timeouts, unbounded caches | `open()` without `close()`, HTTP client without timeout, cache without TTL or max size |
| **Code Style/Conventions** | Violations of project conventions, inconsistent naming, magic numbers | Check against project CLAUDE.md and rules |
| **Dependency Risks** | New dependencies with known vulnerabilities, abandoned packages, license issues | Outdated packages, packages with < 100 weekly downloads, GPL in MIT project |

---

## STEP 3: Round 1 — Reviewer Critique

The reviewer subagent examines the work and produces a structured critique.

### 3.1 Structured Critique Format

The reviewer MUST produce findings in this exact format. Each issue is a separate entry:

```
ADVERSARIAL REVIEW — ROUND 1
==============================

Review Mode: {PLAN REVIEW | CODE REVIEW}
Target: {file path, plan name, or PR number}
Reviewer: {model name or "subagent"}

---

### R1: {Short title}

| Field | Value |
|-------|-------|
| Issue ID | R1 |
| Category | {Security | Performance | Correctness | Design | Edge Case | Maintainability} |
| Severity | {Critical | Major | Minor} |
| Location | {file:line for code, section name for plan} |

**Evidence:**
{Concrete scenario or proof of why this is a problem. NOT "this might be an
issue" — show exactly how it fails, what input triggers it, or what the
consequence is.}

**Suggested Fix:**
{Specific, actionable recommendation. NOT "consider improving this" — provide
the exact change, pattern, or approach to use.}

---

### R2: {Short title}

| Field | Value |
|-------|-------|
| Issue ID | R2 |
| Category | ... |
| Severity | ... |
| Location | ... |

**Evidence:**
...

**Suggested Fix:**
...

---

(continue for all issues found)
```

### 3.2 Severity Definitions

The reviewer MUST use these severity levels consistently:

| Severity | Definition | Examples | Action Required |
|----------|-----------|----------|----------------|
| **Critical** | Will cause data loss, security breach, or system failure if shipped. Blocks proceeding. | SQL injection, auth bypass, data corruption, unhandled null in critical path, race condition causing duplicate payments | MUST fix before proceeding |
| **Major** | Significant quality or reliability issue. Should be fixed before shipping. | Missing pagination on unbounded query, no error handling on external call, N+1 query in hot path, missing input validation | SHOULD fix — defer only with tracking issue and justification |
| **Minor** | Improvement that would make the code better but is not blocking. | Suboptimal algorithm (but works), missing edge case test, naming inconsistency, missing code comment on complex logic | NICE TO FIX — can defer without tracking |

### 3.3 Category Definitions

| Category | Scope | Examples |
|----------|-------|---------|
| **Security** | Authentication, authorization, injection, data exposure, cryptography | Missing auth check, XSS in user input rendering, PII in logs |
| **Performance** | Speed, memory, scalability, resource usage | N+1 queries, unbounded loops, missing indices, memory leaks |
| **Correctness** | Logic errors, wrong behavior, data integrity | Off-by-one, null handling, race conditions, wrong return type |
| **Design** | Architecture, patterns, abstractions, API shape | Tight coupling, wrong abstraction level, leaky abstraction, god class |
| **Edge Case** | Boundary conditions, unusual inputs, failure modes | Empty list, max integer, concurrent modification, network timeout |
| **Maintainability** | Readability, testability, documentation, complexity | Magic numbers, duplicated logic, untestable design, missing docs |

### 3.4 Minimum Review Standards

The reviewer MUST NOT submit a critique with:
- Fewer than 3 issues for medium+ changes (look harder)
- Only minor issues for security-sensitive code (check security dimensions explicitly)
- Vague evidence ("this could be a problem") — every issue needs a concrete scenario
- Vague fixes ("consider improving") — every fix needs a specific recommendation
- Duplicate issues (same root cause reported multiple times)

If the reviewer genuinely finds fewer than 3 issues, they MUST explicitly state which criteria they checked and found clean:

```
Verified clean:
- Security: Checked for injection, auth bypass, data exposure — none found
- Performance: Checked for N+1, unbounded queries, blocking I/O — none found
- Correctness: Checked for off-by-one, null handling, race conditions — none found
```

---

## STEP 4: Round 2 — Author Response

The author (main agent) responds to each issue from the reviewer's critique.

### 4.1 Author Response Format

For EVERY issue raised by the reviewer, the author MUST respond with one of these dispositions:

| Response | When to Use | Required Content |
|----------|-------------|-----------------|
| **Accept** | Issue is valid, will fix | Description of the fix to be applied |
| **Reject** | Issue is not valid | Evidence explaining why the issue does not apply — concrete counter-example, documentation reference, or proof |
| **Defer** | Valid issue but out of scope for this change | Tracking issue number or TODO with justification for deferral |
| **Partial** | Partially valid — will address some aspects | Which parts will be addressed and which will not, with reasoning for each |

### 4.2 Author Response Template

```
AUTHOR RESPONSE — ROUND 2
===========================

### R1: {Short title}
**Disposition:** ACCEPT
**Action:** {What will be changed and why the reviewer's concern is valid.}

### R2: {Short title}
**Disposition:** REJECT
**Evidence:** {Why this issue does not apply. Must include concrete proof — a test
that covers this case, a framework guarantee, a configuration that prevents it,
or a logical argument with specifics.}

### R3: {Short title}
**Disposition:** DEFER
**Tracking:** Created issue #{number} — "{issue title}"
**Justification:** {Why this can safely wait. What is the risk of deferring? Is
there a compensating control in the meantime?}

### R4: {Short title}
**Disposition:** PARTIAL
**Will address:** {What will be fixed and how.}
**Will not address:** {What will not be changed and why — with evidence.}
```

### 4.3 Author Response Rules

| Rule | Rationale |
|------|-----------|
| Every issue gets a response | Ignoring issues erodes the review process |
| Rejections require evidence | "I disagree" is not sufficient — prove it |
| Deferrals require a tracking issue | "We'll fix it later" without a ticket means it never gets fixed |
| Accepted items must describe the fix | The reviewer needs to verify the fix addresses their concern |
| No defensive responses | "That's by design" without explaining the design is dismissive |
| Acknowledge good catches | If the reviewer found a real bug, say so — it builds trust |

### 4.4 Apply Accepted Fixes

After completing the response, apply all accepted and partial fixes:

1. Make the code/plan changes for all ACCEPT and PARTIAL items
2. Run tests to verify fixes do not introduce regressions
3. For plan reviews: update the plan document with the changes

```bash
# After applying fixes, verify nothing is broken
# For code:
{project test command}

# For plans:
# Re-read the updated plan to ensure consistency
```

---

## STEP 5: Round 2 — Reviewer Follow-Up

The reviewer subagent examines the author's responses and applied fixes.

### 5.1 Reviewer Follow-Up Protocol

For each issue, the reviewer evaluates the author's response:

| Author Response | Reviewer Action |
|----------------|----------------|
| **Accept** | Verify the fix actually addresses the issue. If the fix is incomplete or introduces a new problem, escalate with more evidence. |
| **Reject** | Evaluate the author's counter-evidence. If the rejection is well-supported, accept it. If the evidence is weak or missing, escalate. |
| **Defer** | Verify a tracking issue was created. If the deferral is risky (security, data integrity), escalate. |
| **Partial** | Verify the addressed portion is correct. Evaluate whether the unaddressed portion is acceptable. |

### 5.2 Reviewer Follow-Up Format

```
REVIEWER FOLLOW-UP — ROUND 2
==============================

### R1: {Short title}
**Author response:** ACCEPT
**Reviewer verdict:** SATISFIED — Fix correctly addresses the concern.

### R2: {Short title}
**Author response:** REJECT
**Reviewer verdict:** ESCALATE
**Additional evidence:** {New evidence or stronger argument for why this IS an
issue, addressing the author's counter-arguments point by point.}

### R3: {Short title}
**Author response:** DEFER
**Reviewer verdict:** SATISFIED — Tracking issue created, risk is low.

### R4: {Short title}
**Author response:** PARTIAL
**Reviewer verdict:** ESCALATE
**Concern:** {The unaddressed portion is higher risk than the author assessed.
Here is a scenario where it causes a real problem: ...}
```

### 5.3 Escalation Criteria

The reviewer SHOULD escalate (mark as ESCALATE instead of SATISFIED) only when:

| Criterion | Example |
|-----------|---------|
| Author's rejection lacks concrete evidence | "It's fine" without proof |
| Fix does not fully address the issue | Fixed SQL injection in one query but left another vulnerable |
| Deferral is risky | Deferring a security issue with no compensating control |
| New issue introduced by the fix | Fix for race condition introduces a deadlock |
| Critical issue with insufficient partial fix | Partial fix leaves a data corruption path open |

The reviewer MUST NOT escalate for:
- Style preferences the author disagreed with
- Minor issues the author reasonably deferred
- Issues where the author provided strong counter-evidence
- Disagreements about approach when both approaches are valid

---

## STEP 6: Round 3 — Final Resolution (If Needed)

Round 3 is triggered ONLY if there are ESCALATE items from Round 2. If all items are SATISFIED, skip to Step 7.

### 6.1 Round 3 Trigger Check

```
Escalated items from Round 2: {count}
  Critical escalations: {count}
  Major escalations: {count}
  Minor escalations: {count}

Round 3 required: {YES if any escalations, NO if all satisfied}
```

### 6.2 Round 3 Protocol

For each escalated item, attempt final resolution:

**Author's final response options:**

| Option | When to Use |
|--------|-------------|
| **Concede** | Reviewer's additional evidence is convincing — apply the fix |
| **Compromise** | Find a middle ground that addresses the reviewer's concern differently |
| **Escalate to Human** | Genuine disagreement that requires human judgment |

**Reviewer's final response options:**

| Option | When to Use |
|--------|-------------|
| **Accept resolution** | Author's concession or compromise adequately addresses the concern |
| **Maintain objection** | Issue remains unresolved — flag for human review |

### 6.3 Round 3 Format

```
FINAL RESOLUTION — ROUND 3
============================

### R2: {Short title}
**Author:** COMPROMISE — Will implement {alternative approach} that addresses the
  security concern without the performance overhead of the reviewer's suggestion.
**Reviewer:** ACCEPT RESOLUTION — The compromise adequately mitigates the risk.

### R4: {Short title}
**Author:** ESCALATE TO HUMAN — Genuine design disagreement about {topic}.
  Author position: {summary}
  Reviewer position: {summary}
**Reviewer:** MAINTAIN OBJECTION — This is a {severity} issue that should not ship
  without human review.
```

### 6.4 Human Escalation Protocol

If any items remain unresolved after Round 3:

```
HUMAN REVIEW REQUIRED
======================

The following issues could not be resolved through adversarial review:

1. R4: {title}
   Severity: {Critical | Major}
   Author position: {summary}
   Reviewer position: {summary}
   Risk if shipped as-is: {concrete description}

Action needed: Human reviewer should evaluate both positions and make a decision.
The adversarial review is BLOCKED until these items are resolved.
```

Present this to the user and WAIT for their decision before proceeding. Do NOT auto-resolve human-escalated items.

---

## STEP 7: Generate Review Report

After all rounds complete, produce a comprehensive review report.

### 7.1 Report Format

```
ADVERSARIAL REVIEW REPORT
===========================

Verdict: {PASSED | PASSED WITH CAVEATS | BLOCKED}

Target: {file path, plan name, or PR description}
Mode: {PLAN REVIEW | CODE REVIEW}
Rounds completed: {1 | 2 | 3}
Reviewer: {model name or "subagent"}

---

Issue Summary:
  Total issues found: {N}
    Critical: {count} ({resolved count} resolved, {deferred count} deferred)
    Major:    {count} ({resolved count} resolved, {deferred count} deferred)
    Minor:    {count} ({resolved count} resolved, {rejected count} rejected)

---

Resolution Details:

- R1 [{severity}] {title}
  Category: {category}
  Location: {location}
  Resolution: {FIXED — description | REJECTED — reason | DEFERRED — issue #N | PARTIAL — what was done}

- R2 [{severity}] {title}
  Category: {category}
  Location: {location}
  Resolution: {FIXED — description | REJECTED — reason | DEFERRED — issue #N | PARTIAL — what was done}

... (all issues listed)

---

Deferred Items:
{List of deferred issues with tracking references, or "None"}

Rejected Items:
{List of rejected issues with brief reason, or "None"}

---

Verdict Explanation:
{Why the review passed, passed with caveats, or is blocked.}

Next Step:
{Recommendation for what to do next — see Section 7.3}
```

### 7.2 Verdict Criteria

| Verdict | Criteria |
|---------|----------|
| **PASSED** | Zero unresolved critical or major issues. All critical issues fixed. All major issues either fixed or deferred with tracking. |
| **PASSED WITH CAVEATS** | Zero unresolved critical issues. One or more major issues deferred with tracking and compensating controls. Minor issues may be open. |
| **BLOCKED** | One or more unresolved critical issues. OR one or more items escalated to human review without resolution. Must not proceed until resolved. |

### 7.3 Next Step Recommendations

Based on the verdict and review mode:

| Verdict | Mode | Next Step |
|---------|------|-----------|
| PASSED | Plan Review | Proceed to `/executing-plans` or `/implement` |
| PASSED | Code Review | Proceed to `/request-code-review` |
| PASSED WITH CAVEATS | Plan Review | Proceed with awareness of deferred items — track them |
| PASSED WITH CAVEATS | Code Review | Proceed to `/request-code-review` — mention caveats in PR description |
| BLOCKED | Plan Review | Address blocking issues, then re-run `/adversarial-review` |
| BLOCKED | Code Review | Address blocking issues, then re-run `/adversarial-review` |

```
Next step recommendation:
  Verdict: {verdict}
  Mode: {mode}
  Action: {specific recommendation from table above}
```

---

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
