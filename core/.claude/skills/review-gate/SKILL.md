---
name: review-gate
description: >
  Orchestrate all review sub-skills (code-quality-gate, architecture-fitness,
  security-audit, adversarial-review, change-risk-scoring, pr-standards) into a
  single autonomous pipeline. Aggregates results into a consolidated review report
  with a go/no-go verdict. Use when running the Stage 9 pre-merge review gate
  before deployment.
triggers:
  - review-gate
  - stage-9
  - full review
  - review pipeline
  - quality gate pipeline
  - pre-merge review
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[--skip <skill1,skill2>] [--fix] [--pr] [--threshold <0-100>] [--include-test-health]"
version: "2.3.0"
type: workflow
---

# Review Gate — Stage 9 Orchestrator

Run the full Stage 9 review pipeline: quality checks, architecture fitness, security audit, adversarial review, risk scoring, and PR standards. Aggregate all results into a single consolidated report with a go/no-go verdict.

**Arguments:** $ARGUMENTS

---

## STEP 0: Parse Arguments and Gather Context

### 0.1 Argument Parsing

| Argument | Default | Effect |
|----------|---------|--------|
| `--skip <skills>` | none | Comma-separated list of sub-skills to skip (e.g., `--skip architecture-fitness,change-risk-scoring`) |
| `--fix` | off | Automatically fix blocking findings via `fix-loop` + `auto-verify` |
| `--pr` | off | Create a PR via `request-code-review` after a passing review |
| `--threshold <0-100>` | 50 | Maximum acceptable risk score from `change-risk-scoring` |
| `--include-test-health` | off | Run Batch D (test-maintenance audit) as a non-blocking health check |

### 0.2 Validate Preconditions

Before running the pipeline, verify the environment is ready:

```bash
# Must be on a feature branch, not main
CURRENT_BRANCH=$(git branch --show-current)
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
if [ "$CURRENT_BRANCH" = "$BASE_BRANCH" ]; then
  echo "ERROR: You are on $BASE_BRANCH. Switch to a feature branch first."
  exit 1
fi

# Must have changes to review
DIFF_LINES=$(git diff --name-only "$BASE_BRANCH"...HEAD | wc -l)
if [ "$DIFF_LINES" -eq 0 ]; then
  echo "No changes detected between $CURRENT_BRANCH and $BASE_BRANCH. Nothing to review."
  exit 0
fi

# All changes must be committed
UNCOMMITTED=$(git status --porcelain | wc -l)
if [ "$UNCOMMITTED" -gt 0 ]; then
  echo "ERROR: $UNCOMMITTED uncommitted changes. Commit or stash before running the review gate."
  exit 1
fi

# Tests must pass before review
echo "Running pre-review test check..."
```

### 0.3 Detect Project Context

Gather project information needed by sub-skills:

```bash
# Changed files summary
git diff --stat "$BASE_BRANCH"...HEAD

# Detect test runner
if [ -f package.json ]; then TEST_CMD="npm test"
elif [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.cfg ]; then TEST_CMD="python -m pytest"
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then TEST_CMD="./gradlew test"
elif [ -f Cargo.toml ]; then TEST_CMD="cargo test"
elif [ -f go.mod ]; then TEST_CMD="go test ./..."
else TEST_CMD=""
fi

echo "Test command: ${TEST_CMD:-'not detected'}"
echo "Changed files: $DIFF_LINES"
```

### 0.4 Initialize Report Tracking

Create the tracking structure for aggregating results:

```
REVIEW GATE — PIPELINE STARTED
================================

Branch: $CURRENT_BRANCH → $BASE_BRANCH
Changed files: $DIFF_LINES
Date: <date>

Sub-skill results will be collected below.
```

---

## STEP 1: Batch A — Code Quality + Architecture (Parallel)

Launch code-quality-gate and architecture-fitness as parallel subagents. These are independent static analysis checks with no side effects.

```
Agent(prompt="Run /code-quality-gate on all changed files between $BASE_BRANCH and HEAD. Skip Step 5 (layer validation) — architecture-fitness handles that. Return structured results: status (PASS/WARN/BLOCK), complexity, duplication, SOLID issues, PII leaks, swallowed exceptions, coverage diff, blocking count.")

Agent(prompt="Run /architecture-fitness on all changed files between $BASE_BRANCH and HEAD. This is the authoritative layer/dependency check. Return structured results: status (PASS/WARN/BLOCK), dependency violations, circular deps, coupling, module size, ADR drift, blocking count.")
```

### 1.1 Record Results

```
BATCH A — Code Quality Gate:
  Status: {PASS / WARN / BLOCK / UNKNOWN}
  Complexity: {max CC and file}
  Duplication: {percentage}
  SOLID: {issues count}
  Logging: {PII leaks found}
  Error handling: {swallowed exceptions count}
  Coverage diff: {percentage on new lines}
  Blocking issues: {count}

BATCH A — Architecture Fitness:
  Status: {PASS / WARN / BLOCK / UNKNOWN}
  Dependency direction: {violations count}
  Circular dependencies: {cycles count}
  Coupling: {high-risk modules}
  Module size: {oversized modules}
  ADR conformance: {drift/missing count}
  Blocking issues: {count}
```

If either result is BLOCK and `--fix` is enabled, invoke `/fix-loop` for each blocking issue before proceeding.

---

## STEP 2: Batch B — Security + Risk Scoring (Parallel)

Launch security-audit and change-risk-scoring as parallel subagents. Both are read-only analysis with no side effects.

```
Agent(prompt="Run /security-audit on all changed files between $BASE_BRANCH and HEAD. Produce a structured security audit report with findings categorized by CVSS severity. Return: status (PASS/WARN/BLOCK), critical/high/medium/low finding counts, blocking count.")

Skill("change-risk-scoring", args="--format json")
```


**Read:** `references/batch-b-security-risk-scoring-parallel.md` for detailed step 2: batch b — security + risk scoring (parallel) reference material.

## STEP 3: Batch C — Adversarial Review → PR Standards (Sequential)

Run adversarial-review with findings from Batches A+B as context, then pr-standards. These are sequential because adversarial-review benefits from knowing what earlier checks found.


**Read:** `references/batch-c-adversarial-review-pr-standards-sequential.md` for detailed step 3: batch c — adversarial review → pr standards (sequential) reference material.

## STEP 4: Fix Loop (Conditional)

This step runs ONLY if:
1. Any previous step produced BLOCK status, AND
2. `--fix` flag is enabled


**Read:** `references/fix-loop-conditional.md` for detailed step 4: fix loop (conditional) reference material.

# Get directories touched by the fix
FIX_DIRS=$(git diff --name-only HEAD~1 HEAD | xargs -I{} dirname {} | sort -u)

# Get directories from the original finding
FINDING_DIRS=$(echo "<original_finding_files>" | xargs -I{} dirname {} | sort -u)

# If fix introduced new directories not in the finding, it's cross-cutting
NEW_DIRS=$(comm -23 <(echo "$FIX_DIRS") <(echo "$FINDING_DIRS"))
if [ -n "$NEW_DIRS" ]; then
  echo "Cross-cutting fix detected — re-running ALL checks"
else
  echo "Scoped fix — re-running only failed checks"
fi
```

4. **Execute re-runs**:

```
Re-running checks after fixes:
  Fix reach: {SCOPED|CROSS-CUTTING}
  Re-run scope: {FAILED_ONLY|ALL}
  Code Quality Gate: {RE-RUN|SKIP} → {new status}
  Architecture Fitness: {RE-RUN|SKIP} → {new status}
  Security Audit: {RE-RUN|SKIP} → {new status}
  Adversarial Review: {RE-RUN|SKIP} → {new status}
  Change Risk Scoring: {RE-RUN|SKIP} → {new status}
  PR Standards: {RE-RUN|SKIP} → {new status}
```

Update the recorded results with the re-run outcomes.

---

## STEP 5: Generate Consolidated Review Report

Aggregate all sub-skill results into a single report. This is the artifact consumed by Stage 10 (Deploy) for go/no-go decisions.

### 5.1 Consolidated Report Format

```markdown
# Review Gate Report

**Branch:** {branch} → {base_branch}
**Date:** <date>
**Changed files:** {count}
**Risk score:** {score}/100 ({classification})

## Overall Verdict: {APPROVED / APPROVED WITH CAVEATS / REJECTED}

## Sub-Skill Results

| # | Check | Status | Blocking | Details |
|---|-------|--------|----------|---------|
| 1 | Code Quality Gate | {PASS/WARN/BLOCK/UNKNOWN} | {count} | CC max: {N}, duplication: {%}, coverage diff: {%} |
| 2 | Architecture Fitness | {PASS/WARN/BLOCK/UNKNOWN} | {count} | Dep violations: {N}, cycles: {N}, ADR drift: {N} |
| 3 | Security Audit | {PASS/WARN/BLOCK/UNKNOWN} | {count} | Critical: {N}, High: {N}, Medium: {N} |
| 4 | Adversarial Review | {PASS/WARN/BLOCK/UNKNOWN} | {count} | Issues: {N} ({resolved} resolved, {deferred} deferred) |
| 5 | Change Risk Scoring | {PASS/WARN/BLOCK/UNKNOWN} | — | Score: {N}/100, hotspots: {list} |
| 6 | PR Standards | {PASS/WARN/BLOCK/UNKNOWN} | {count} | Critical: {N}, Warning: {N}, Info: {N} |

## Blocking Issues (if any)

{List each unresolved blocking issue with its source skill, file, line, and description}

## Deferred Items

{List each deferred issue with its tracking reference (GitHub Issue URL or TODO)}

### Deferred Item Validation

For each deferred item in the report:

1. **Verify tracking reference exists** — check that the GitHub Issue URL resolves:
   ```bash
   gh issue view <issue_number> --json state,title 2>/dev/null
   ```
   If the issue does not exist or is already closed, promote the deferred item to BLOCK.

2. **TTL enforcement** — each deferred item carries a `deferred_date` (ISO-8601). If the item is older than 14 days, auto-promote it to BLOCK on this review-gate run. Stale deferrals are unresolved problems, not accepted risk.

3. **Deferred count threshold** — if >5 deferred items exist across all prior review-gate runs (check `test-results/review-gate.json` history or PR comments), emit a WARN: "Deferred item accumulation detected ({count} items). Review and resolve outstanding deferrals before adding more."

## Fix Loop Summary (if --fix was used)

| Finding | Fix Applied | Verification |
|---------|------------|--------------|
| {finding} | {description of fix} | {PASS/FAIL} |

## Recommendations

{Based on the aggregate results:}
- {If APPROVED: "Proceed to PR creation and Stage 10."}
- {If APPROVED WITH CAVEATS: "Proceed with awareness of deferred items. Mention caveats in PR description."}
- {If REJECTED: "Address N blocking issues before re-running /review-gate."}
```


**Read:** `references/recommendations.md` for detailed recommendations reference material.

## STEP 6: PR Creation (Conditional)

This step runs ONLY if:
1. The verdict is APPROVED or APPROVED WITH CAVEATS, AND
2. `--pr` flag is enabled

### 6.1 Create PR with Review Context

Invoke `request-code-review` and include the consolidated review report in the PR description:

```
Skill("request-code-review", args="<branch>")
```

Append the consolidated review summary to the PR body:

```markdown
## Automated Review Gate Results

| Check | Status |
|-------|--------|
| Code Quality | ✅ PASS |
| Architecture | ✅ PASS |
| Security | ⚠️ WARN (1 medium finding) |
| Adversarial Review | ✅ PASS (1 deferred) |
| Risk Score | 42/100 (MEDIUM) |
| PR Standards | ✅ PASS |

**Verdict: APPROVED WITH CAVEATS**
Full report: see `test-results/review-gate.json`
```

### 6.2 Record PR URL

```
STEP 9: PR Creation
  PR URL: {url}
  Reviewers assigned: {list}
  Labels: {list}
```

---

## STEP 7: Post-Review Feedback Loop (Conditional)

This step runs when invoked after a PR has received review feedback.

If the review gate was run with `--pr` and the PR subsequently receives review comments, the user can re-invoke `/review-gate` to handle the feedback:

```
Skill("receive-code-review", args="<PR-number>")
```

After addressing feedback:

```
Skill("auto-verify", args="--files <changed_files>")
```

Then re-run only the sub-skills affected by the changes made during feedback resolution.

---

## Pipeline Flow Summary

**Read:** `references/pipeline-flow-summary.md` for detailed pipeline flow summary reference material.

## Parallelization Strategy

The 6 analysis checks are grouped into 3 batches for optimal throughput:

| Batch | Checks | Execution | Rationale |
|-------|--------|-----------|-----------|
| Batch A | code-quality-gate + architecture-fitness | Parallel agents | Both are static analysis, no side effects |
| Batch B | security-audit + change-risk-scoring | Parallel (agent + skill) | Both are read-only analysis |
| Batch C | adversarial-review → pr-standards | Sequential after A+B | Adversarial review benefits from A+B findings as context |
| Fix loop | fix-loop + auto-verify | Conditional after A+B+C | Only if --fix flag and blocking findings exist |
| Final | report → PR → feedback | Sequential | Depends on all prior results |
| Batch D | test-maintenance audit | Conditional after A+B+C | Only if `--include-test-health` flag is passed |

---

## Batch D: Test Health Audit (Optional)

This batch runs ONLY if `--include-test-health` is passed. It invokes the first step (audit) of `/test-maintenance` as a non-blocking diagnostic check. Results appear as warnings in the consolidated report — they never produce BLOCK status.


**Read:** `references/batch-d-test-health-audit-optional.md` for detailed batch d: test health audit (optional) reference material.

## MUST DO

- Always run ALL six sub-skills unless explicitly skipped via `--skip` — partial reviews create false confidence
- Always produce the consolidated report (Step 8) even if some checks fail — downstream stages need the full picture
- Always write `test-results/review-gate.json` — this is the machine-readable contract with Stage 10
- Always run `architecture-fitness` as the authoritative layer check — skip `code-quality-gate` Step 5 to avoid duplication
- Always aggregate blocking issues from ALL sub-skills before deciding the verdict
- Always apply override rules from `change-risk-scoring` (security files, migrations → minimum MEDIUM)
- Always include deferred items with tracking references in the consolidated report
- Always check fix scope after fix-loop — if fix touched files outside the original finding's directory/module, re-run ALL checks; if fix is scoped to the same files, re-run only failed checks
- When invoking fix-loop + auto-verify for post-review fixes, pass `--capture-proof` to ensure screenshot evidence is captured for the review fix cycle (consistent with Stages 7-8 proof capture)
- If a sub-skill crashes, times out, or returns unparseable output, record its status as UNKNOWN and treat it as BLOCK — never silently ignore a sub-skill that failed to produce a result

## MUST NOT DO

- MUST NOT skip the security audit for any change — security is non-negotiable
- MUST NOT proceed to PR creation (Step 9) when the verdict is REJECTED
- MUST NOT run `code-quality-gate` Step 5 (layer validation) when `architecture-fitness` is also running — it duplicates the check
- MUST NOT auto-fix blocking findings without `--fix` flag — the user must opt into automatic fixes
- MUST NOT report a passing verdict when any critical security finding is unresolved
- MUST NOT silently swallow sub-skill failures — if a sub-skill crashes or times out, report it as UNKNOWN status in the consolidated report
- MUST NOT create the PR without including the review gate summary in the PR description
- MUST NOT re-run only failed checks when the fix touched files outside the original finding's scope — cross-cutting fixes require a full re-run of ALL checks to catch regressions in previously-passing areas
- MUST NOT block on warnings from `change-risk-scoring` alone — risk score is advisory, not a hard gate (unless score exceeds threshold + 15)
