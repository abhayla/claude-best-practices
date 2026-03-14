---
name: review-gate
description: >
  Stage 9 orchestrator: sequences all review sub-skills (code-quality-gate,
  architecture-fitness, security-audit, adversarial-review, change-risk-scoring,
  pr-standards) into a single autonomous pipeline. Aggregates results into a
  consolidated review report with a go/no-go verdict for Stage 10 (Deploy).
  Handles fix loops for blocking findings and creates the PR when approved.
triggers:
  - review-gate
  - stage-9
  - full review
  - review pipeline
  - quality gate pipeline
  - pre-merge review
allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill"
argument-hint: "[--skip <skill1,skill2>] [--fix] [--pr] [--threshold <0-100>]"
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

## STEP 1: Code Quality Gate

Run `code-quality-gate` for complexity, duplication, SOLID, logging, error handling, and coverage diff checks.

**Important:** Pass `--skip-layer-check` context to avoid duplicating the layer validation that `architecture-fitness` will perform in Step 2. Specifically, skip Step 5 (Clean Architecture Layer Validation) of `code-quality-gate` — that check is subsumed by the deeper analysis in `architecture-fitness`.

```
Skill("code-quality-gate", args="all changed files")
```

### 1.1 Record Result

```
STEP 1: Code Quality Gate
  Status: {PASS / WARN / BLOCK}
  Complexity: {max CC and file}
  Duplication: {percentage}
  SOLID: {issues count}
  Logging: {PII leaks found}
  Error handling: {swallowed exceptions count}
  Coverage diff: {percentage on new lines}
  Blocking issues: {count}
```

If the result is BLOCK and `--fix` is enabled, invoke `/fix-loop` for each blocking issue before proceeding.

If the result is BLOCK and `--fix` is not enabled, record the block and continue — the final verdict will aggregate all blocks.

---

## STEP 2: Architecture Fitness

Run `architecture-fitness` for dependency direction, circular deps, coupling metrics, module boundaries, and ADR lifecycle.

This is the authoritative check for architectural conformance — it supersedes the layer validation in `code-quality-gate` Step 5.

```
Skill("architecture-fitness", args="all changed files")
```

### 2.1 Record Result

```
STEP 2: Architecture Fitness
  Status: {PASS / WARN / BLOCK}
  Dependency direction: {violations count}
  Circular dependencies: {cycles count}
  Coupling: {high-risk modules}
  Module size: {oversized modules}
  ADR conformance: {drift/missing count}
  Blocking issues: {count}
```

---

## STEP 3: Security Audit

Launch the `security-auditor` agent for a dedicated security assessment. This runs deeper than the `code-reviewer` agent's security section — it performs threat modeling, OWASP Top 10 scanning, and static analysis triage.

```
Agent(subagent_type="general-purpose", prompt="Run /security-audit on all changed files between $BASE_BRANCH and HEAD. Produce a structured security audit report with findings categorized by CVSS severity.")
```

### 3.1 Record Result

```
STEP 3: Security Audit
  Status: {PASS / WARN / BLOCK}
  Critical findings: {count}
  High findings: {count}
  Medium findings: {count}
  Low findings: {count}
  Blocking issues: {count}
```

If any Critical findings exist, this step is automatically BLOCK regardless of other results.

---

## STEP 4: Adversarial Review

Run `adversarial-review` in code review mode. This launches a subagent with a dedicated reviewer persona to find flaws through structured debate.

```
Skill("adversarial-review", args="--mode code")
```

### 4.1 Record Result

```
STEP 4: Adversarial Review
  Status: {PASSED / PASSED WITH CAVEATS / BLOCKED}
  Rounds completed: {1-3}
  Issues found: {total}
    Critical: {count} ({resolved} resolved)
    Major: {count} ({resolved} resolved)
    Minor: {count} ({resolved} resolved)
  Unresolved critical: {count}
  Deferred with tracking: {count}
  Blocking issues: {count}
```

---

## STEP 5: Change Risk Scoring

Run `change-risk-scoring` to compute a quantified risk score (0-100) for the changeset.

```
Skill("change-risk-scoring", args="--format json")
```

### 5.1 Record Result

```
STEP 5: Change Risk Scoring
  Risk score: {0-100}
  Classification: {LOW / MEDIUM / HIGH / CRITICAL}
  Recommendation: {AUTO-DEPLOY / HUMAN REVIEW / EXTRA TESTING / HOLD}
  Hotspots: {list or "none"}
  Top risk files: {list}
```

### 5.2 Threshold Check

Compare the risk score against the threshold (default: 50):

| Score vs Threshold | Action |
|--------------------|--------|
| Score ≤ threshold | PASS — risk is within acceptable bounds |
| Score > threshold by ≤ 15 | WARN — flag for awareness but do not block |
| Score > threshold by > 15 | BLOCK — risk exceeds acceptable bounds, recommend scope reduction |

---

## STEP 6: PR Standards

Run `pr-standards` to check the diff against team standards and built-in rules.

```
Skill("pr-standards", args="")
```

### 6.1 Record Result

```
STEP 6: PR Standards
  Status: {PASS / FAIL / WARN}
  Critical violations: {count}
  Warning violations: {count}
  Info violations: {count}
  Auto-fixable: {count}
```

If the result is FAIL and `--fix` is enabled:

```
Skill("pr-standards", args="--fix")
```

Then re-run to verify:

```
Skill("pr-standards", args="")
```

---

## STEP 7: Fix Loop (Conditional)

This step runs ONLY if:
1. Any previous step produced BLOCK status, AND
2. `--fix` flag is enabled

### 7.1 Collect All Blocking Findings

Gather all BLOCK/CRITICAL findings from Steps 1-6 into a single fix list:

```
BLOCKING FINDINGS TO FIX:
  [QG-1] Cyclomatic complexity 22 in src/services/order.py:process_order
  [SEC-1] SQL injection in src/api/routes.py:42
  [AR-1] Unresolved critical: missing null check in payment flow
  [PS-1] Debugger statement in src/routes/users.py:45
```

### 7.2 Apply Fixes

For each blocking finding:

1. Apply the fix (using the suggested fix from the sub-skill's report)
2. Verify the fix does not introduce regressions:

```
Skill("auto-verify", args="--files <fixed_files>")
```

3. If `auto-verify` fails:

```
Skill("fix-loop", args="retest_command: <TEST_CMD> max_iterations: 3")
```

### 7.3 Re-Run Failed Checks

After fixing, re-run ONLY the sub-skills that produced BLOCK status. Do NOT re-run passing checks — this avoids wasting time.

```
Re-running failed checks after fixes:
  Code Quality Gate: RE-RUN → {new status}
  Security Audit: RE-RUN → {new status}
  PR Standards: RE-RUN → {new status}
```

Update the recorded results with the re-run outcomes.

---

## STEP 8: Generate Consolidated Review Report

Aggregate all sub-skill results into a single report. This is the artifact consumed by Stage 10 (Deploy) for go/no-go decisions.

### 8.1 Consolidated Report Format

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
| 1 | Code Quality Gate | {PASS/WARN/BLOCK} | {count} | CC max: {N}, duplication: {%}, coverage diff: {%} |
| 2 | Architecture Fitness | {PASS/WARN/BLOCK} | {count} | Dep violations: {N}, cycles: {N}, ADR drift: {N} |
| 3 | Security Audit | {PASS/WARN/BLOCK} | {count} | Critical: {N}, High: {N}, Medium: {N} |
| 4 | Adversarial Review | {PASS/WARN/BLOCK} | {count} | Issues: {N} ({resolved} resolved, {deferred} deferred) |
| 5 | Change Risk Scoring | {PASS/WARN/BLOCK} | — | Score: {N}/100, hotspots: {list} |
| 6 | PR Standards | {PASS/WARN/BLOCK} | {count} | Critical: {N}, Warning: {N}, Info: {N} |

## Blocking Issues (if any)

{List each unresolved blocking issue with its source skill, file, line, and description}

## Deferred Items

{List each deferred issue with its tracking reference (GitHub Issue URL or TODO)}

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

### 8.2 Machine-Readable Output

Write the consolidated results to `test-results/review-gate.json` for programmatic consumption by Stage 10:

```json
{
  "skill": "review-gate",
  "timestamp": "<ISO-8601>",
  "result": "APPROVED",
  "branch": "<branch>",
  "base_branch": "<base_branch>",
  "risk_score": 42,
  "risk_classification": "MEDIUM",
  "checks": {
    "code_quality_gate": {"status": "PASSED", "blocking": 0},
    "architecture_fitness": {"status": "PASSED", "blocking": 0},
    "security_audit": {"status": "WARNED", "blocking": 0, "findings": {"critical": 0, "high": 1, "medium": 2, "low": 3}},
    "adversarial_review": {"status": "PASSED", "blocking": 0, "issues": {"total": 5, "resolved": 4, "deferred": 1}},
    "change_risk_scoring": {"status": "PASSED", "score": 42, "classification": "MEDIUM"},
    "pr_standards": {"status": "PASSED", "blocking": 0, "violations": {"critical": 0, "warning": 2, "info": 3}}
  },
  "blocking_issues": [],
  "deferred_items": [
    {"source": "adversarial-review", "id": "R3", "tracking": "#456", "description": "..."}
  ],
  "fix_loop_ran": false,
  "verdict": "APPROVED",
  "recommendation": "Proceed to PR creation and Stage 10."
}
```

### 8.3 Verdict Logic

```
IF any check has unresolved BLOCK status:
  verdict = "REJECTED"
ELIF risk_score > threshold + 15:
  verdict = "REJECTED"
ELIF any check has WARN status OR deferred_items > 0 OR risk_score > threshold:
  verdict = "APPROVED WITH CAVEATS"
ELSE:
  verdict = "APPROVED"
```

---

## STEP 9: PR Creation (Conditional)

This step runs ONLY if:
1. The verdict is APPROVED or APPROVED WITH CAVEATS, AND
2. `--pr` flag is enabled

### 9.1 Create PR with Review Context

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

### 9.2 Record PR URL

```
STEP 9: PR Creation
  PR URL: {url}
  Reviewers assigned: {list}
  Labels: {list}
```

---

## STEP 10: Post-Review Feedback Loop (Conditional)

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

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    /review-gate                                 │
 │                                                                 │
 │  STEP 0: Validate preconditions (branch, commits, tests)       │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 1: /code-quality-gate (skip layer check)                 │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 2: /architecture-fitness (authoritative layer check)     │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 3: /security-audit (via security-auditor agent)          │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 4: /adversarial-review --mode code                       │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 5: /change-risk-scoring                                  │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 6: /pr-standards                                         │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 7: /fix-loop + /auto-verify (if --fix and blocks exist)  │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 8: Consolidated report → test-results/review-gate.json   │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 9: /request-code-review (if --pr and verdict ≠ REJECTED) │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 10: /receive-code-review (when feedback arrives)         │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
```

---

## Parallelization Strategy

Steps 1-6 can be partially parallelized since they analyze the same changeset independently. The recommended grouping:

| Batch | Steps | Rationale |
|-------|-------|-----------|
| Batch A (parallel) | 1 (code-quality-gate), 2 (architecture-fitness) | Both are static analysis, no side effects |
| Batch B (parallel) | 3 (security-audit), 5 (change-risk-scoring) | Both are read-only analysis |
| Sequential | 4 (adversarial-review) | Needs findings from batches A+B as context |
| Sequential | 6 (pr-standards) | Quick check, runs after review fixes |
| Conditional | 7 (fix-loop) | Only if blocks exist |
| Final | 8 (report), 9 (PR), 10 (feedback) | Sequential, depends on all prior results |

When using subagents, launch Batch A and Batch B concurrently:

```
Agent(prompt="Run /code-quality-gate on all changed files, skipping Step 5 layer validation")
Agent(prompt="Run /architecture-fitness on all changed files")
Agent(prompt="Run /security-audit on all changed files")
Agent(prompt="Run /change-risk-scoring")
```

Then run adversarial-review with the collected findings as context, followed by pr-standards.

---

## MUST DO

- Always run ALL six sub-skills unless explicitly skipped via `--skip` — partial reviews create false confidence
- Always produce the consolidated report (Step 8) even if some checks fail — downstream stages need the full picture
- Always write `test-results/review-gate.json` — this is the machine-readable contract with Stage 10
- Always run `architecture-fitness` as the authoritative layer check — skip `code-quality-gate` Step 5 to avoid duplication
- Always aggregate blocking issues from ALL sub-skills before deciding the verdict
- Always apply override rules from `change-risk-scoring` (security files, migrations → minimum MEDIUM)
- Always include deferred items with tracking references in the consolidated report
- Always re-run only failed checks after fix-loop — do not re-run passing checks

## MUST NOT DO

- MUST NOT skip the security audit for any change — security is non-negotiable
- MUST NOT proceed to PR creation (Step 9) when the verdict is REJECTED
- MUST NOT run `code-quality-gate` Step 5 (layer validation) when `architecture-fitness` is also running — it duplicates the check
- MUST NOT auto-fix blocking findings without `--fix` flag — the user must opt into automatic fixes
- MUST NOT report a passing verdict when any critical security finding is unresolved
- MUST NOT silently swallow sub-skill failures — if a sub-skill crashes or times out, report it as UNKNOWN status in the consolidated report
- MUST NOT create the PR without including the review gate summary in the PR description
- MUST NOT re-run the entire pipeline when only specific checks failed — re-run only the failed checks after fixes
- MUST NOT block on warnings from `change-risk-scoring` alone — risk score is advisory, not a hard gate (unless score exceeds threshold + 15)
