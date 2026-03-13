---
name: change-risk-scoring
description: >
  Compute a quantified risk score (0-100) for code changes based on files changed,
  complexity delta, inverse test coverage, churn frequency, and author familiarity.
  Produces a classification (low/medium/high/critical) with per-factor breakdown
  and a deploy recommendation (auto-deploy / human review / extra testing / hold).
triggers:
  - change risk
  - risk score
  - deploy risk
  - risk assessment
  - go no-go
  - change risk score
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<branch, commit range, or 'staged'> [--threshold 50] [--format json|markdown]"
---

# Change Risk Scoring — Quantified Deploy Go/No-Go

Compute a composite risk score for a set of code changes. The score drives deploy decisions: low-risk changes auto-deploy, high-risk changes require human review or extra testing.

**Target:** $ARGUMENTS

---

## STEP 1: Identify Changed Files

Determine the changeset to analyze based on the provided arguments:

```bash
# Branch diff against main
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff --name-only "$BASE_BRANCH"...HEAD

# Or staged changes
git diff --cached --name-only

# Or specific commit range
git diff --name-only <commit1>..<commit2>
```

Collect per-file stats:

```bash
# Lines added/removed per file
git diff --numstat "$BASE_BRANCH"...HEAD

# Total file count
git diff --name-only "$BASE_BRANCH"...HEAD | wc -l
```

Exclude files that do not carry production risk:
```
EXCLUDE: *.md, *.txt, *.lock, *.json (config only), *.yml (CI only),
         **/test*/**, **/spec/**, **/__mocks__/**, **/fixtures/**,
         generated/**, migrations/** (flag separately)
```

Record the production file count as `FILE_COUNT`.

---

## STEP 2: Compute Risk Factors

### 2.1 File Count Factor (F)

Raw count of production files changed, normalized to 0-100:

| Files Changed | Score | Rationale |
|--------------|-------|-----------|
| 1-3 | 10 | Surgical change, easy to review |
| 4-7 | 25 | Moderate scope |
| 8-15 | 50 | Wide-reaching, cross-cutting concern |
| 16-30 | 75 | Large change, high coordination risk |
| >30 | 100 | Extremely broad, likely needs splitting |

### 2.2 Complexity Delta Factor (C)

Measure whether the change increases or decreases code complexity.

```bash
# Python — radon
radon cc <changed_files> -s -a -j 2>/dev/null

# JavaScript/TypeScript — eslint complexity rule or cr tool
npx eslint --rule '{"complexity": ["warn", 1]}' <changed_files> 2>/dev/null

# Generic fallback — count decision points added
git diff "$BASE_BRANCH"...HEAD | grep -cE '^\+.*(if |else |elif |case |catch |for |while |&&|\|\||\?)'
```

Score the complexity delta:

| Complexity Change | Score | Rationale |
|------------------|-------|-----------|
| Net decrease | 0 | Simplification reduces risk |
| No change | 10 | Neutral |
| +1 to +5 decision points | 30 | Mild increase |
| +6 to +15 decision points | 60 | Significant increase |
| +16 or more | 90 | Major complexity injection |
| Any function exceeds CC 20 | 100 | Single-function complexity bomb |

### 2.3 Coverage Delta Factor (V)

Determine whether test coverage improved or degraded for changed files.

```bash
# Python — pytest-cov
pytest --cov=src --cov-report=json -q 2>/dev/null
# Parse coverage.json for changed files

# JavaScript/TypeScript — jest/vitest
npx jest --coverage --coverageReporters=json-summary --silent 2>/dev/null
# Parse coverage-summary.json for changed files

# Generic fallback — check if test files exist for changed files
for f in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  test_file=$(echo "$f" | sed 's/src/tests/' | sed 's/\.py/_test.py/')
  [ -f "$test_file" ] && echo "COVERED: $f" || echo "UNCOVERED: $f"
done
```

Score the coverage delta:

| Coverage Situation | Score | Rationale |
|-------------------|-------|-----------|
| Coverage increased or stayed >80% | 0 | Well-tested changes |
| Coverage stayed 60-80% | 20 | Adequate but not strong |
| Coverage stayed 40-60% | 50 | Weak coverage, gaps likely |
| Coverage decreased | 70 | Regression in safety net |
| No tests exist for changed files | 100 | Flying blind |

### 2.4 Churn Frequency Factor (H — Hotspot)

Files changed frequently in the past are fragile. High churn + high complexity = hotspot.

```bash
# Count commits touching each changed file in the last 90 days
for f in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  count=$(git log --oneline --since="90 days ago" -- "$f" | wc -l)
  echo "$count $f"
done | sort -rn
```

Score per file, then take the maximum:

| Commits in 90 Days | Score | Rationale |
|--------------------|-------|-----------|
| 1-5 | 10 | Stable file, low churn |
| 6-15 | 30 | Moderate activity |
| 16-30 | 60 | Frequently changing, possible design issue |
| >30 | 90 | Hotspot — strong signal of instability |

If any file has both churn >15 AND complexity CC >10, flag it as a **hotspot** and set this factor to max(score, 80).

### 2.5 Author Familiarity Factor (A)

Authors who rarely touch a file are more likely to introduce bugs there.

```bash
# For each changed file, check how many prior commits the current author has
AUTHOR=$(git config user.email)
for f in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  author_commits=$(git log --author="$AUTHOR" --oneline -- "$f" | wc -l)
  total_commits=$(git log --oneline -- "$f" | wc -l)
  echo "$author_commits/$total_commits $f"
done
```

Score based on the author's share of commits to the changed files:

| Author Familiarity | Score | Rationale |
|--------------------|-------|-----------|
| >50% of commits are author's | 0 | Primary owner, deep familiarity |
| 20-50% of commits | 20 | Regular contributor |
| 5-20% of commits | 50 | Occasional contributor |
| <5% of commits or new file | 70 | Unfamiliar territory |

---

## STEP 3: Calculate Composite Risk Score

### 3.1 Weighted Formula

```
RISK = (W_f * F) + (W_c * C) + (W_v * V) + (W_h * H) + (W_a * A)
```

Default weights (must sum to 1.0):

| Factor | Weight | Rationale |
|--------|--------|-----------|
| File Count (F) | 0.15 | Scope matters but less than quality signals |
| Complexity Delta (C) | 0.25 | Complexity is the strongest predictor of defects |
| Coverage Delta (V) | 0.25 | Untested code is the primary risk vector |
| Churn Frequency (H) | 0.20 | Hotspots predict where bugs cluster |
| Author Familiarity (A) | 0.15 | Unfamiliar code gets more mistakes |

### 3.2 Classification

| Score | Classification | Color |
|-------|---------------|-------|
| 0-25 | LOW | Green |
| 26-50 | MEDIUM | Yellow |
| 51-75 | HIGH | Orange |
| 76-100 | CRITICAL | Red |

### 3.3 Override Rules

Certain conditions force an escalation regardless of the computed score:

| Condition | Override |
|-----------|----------|
| Any file in `auth/`, `security/`, `crypto/`, `payment/` | Minimum MEDIUM |
| Database migration files changed | Minimum MEDIUM |
| Public API contract changed (OpenAPI, GraphQL schema) | Minimum MEDIUM |
| >50 files changed | Minimum HIGH |
| Any deleted public function/method | Minimum MEDIUM |
| `coverage decreased` AND `complexity increased` | Add +20 to score |

---

## STEP 4: Hotspot Analysis

Produce a focused report on hotspot files — those with both high churn and high complexity.

```bash
# Cross-reference churn and complexity
for f in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  churn=$(git log --oneline --since="90 days ago" -- "$f" | wc -l)
  # Get complexity (language-appropriate tool)
  echo "CHURN=$churn FILE=$f"
done
```

### 4.1 Hotspot Report Format

```
HOTSPOTS (high churn + high complexity):

  src/services/payment_processor.py
    Churn: 28 commits in 90 days
    Complexity: CC 18 (max function: process_refund)
    Risk: This file is a defect magnet — consider refactoring before adding more logic

  src/api/routes/orders.py
    Churn: 22 commits in 90 days
    Complexity: CC 14 (max function: create_order)
    Risk: Frequent changes to complex code — add integration tests
```

If no hotspots are found, state: `No hotspots detected — churn and complexity are within normal ranges.`

---

## STEP 5: Generate Risk Report

### 5.1 Report Format

```
CHANGE RISK ASSESSMENT
========================

Risk Score: 62 / 100
Classification: HIGH
Recommendation: HUMAN REVIEW REQUIRED

Target: feature/payment-refunds (vs main)
Files analyzed: 14 production files (8 test files excluded)
Date: <date>

---

Factor Breakdown:

| Factor | Raw Score | Weight | Weighted |
|--------|----------|--------|----------|
| File Count | 50 | 0.15 | 7.5 |
| Complexity Delta | 60 | 0.25 | 15.0 |
| Coverage Delta | 70 | 0.25 | 17.5 |
| Churn Frequency | 60 | 0.20 | 12.0 |
| Author Familiarity | 50 | 0.15 | 7.5 |
| **Override adjustment** | | | +2.5 |
| **TOTAL** | | | **62.0** |

Override applied: auth/ files changed — floor raised to MEDIUM

---

Hotspots:
  - src/services/payment_processor.py (churn: 28, CC: 18)

---

Top Risk Files:
  1. src/services/payment_processor.py — uncovered, high churn, CC 18
  2. src/api/routes/orders.py — complexity increased by 6
  3. src/auth/token_service.py — author has 1 prior commit

---

Recommendation:
  HUMAN REVIEW REQUIRED
  - Add tests for payment_processor.py before deploying
  - Have a payment domain expert review token_service.py changes
  - Consider splitting this PR: auth changes vs order logic
```

### 5.2 Recommendation Matrix

| Classification | Recommendation | Action |
|---------------|----------------|--------|
| LOW (0-25) | AUTO-DEPLOY | Safe to deploy with standard CI checks |
| MEDIUM (26-50) | HUMAN REVIEW | Request code review, deploy after approval |
| HIGH (51-75) | EXTRA TESTING | Add targeted tests for flagged files, then human review |
| CRITICAL (76-100) | HOLD | Do not deploy — reduce scope, add tests, or refactor first |

---

## STEP 6: JSON Output (Optional)

If `--format json` is specified, output machine-readable results:

```json
{
  "risk_score": 62,
  "classification": "HIGH",
  "recommendation": "HUMAN_REVIEW",
  "factors": {
    "file_count": {"raw": 50, "weight": 0.15, "weighted": 7.5},
    "complexity_delta": {"raw": 60, "weight": 0.25, "weighted": 15.0},
    "coverage_delta": {"raw": 70, "weight": 0.25, "weighted": 17.5},
    "churn_frequency": {"raw": 60, "weight": 0.20, "weighted": 12.0},
    "author_familiarity": {"raw": 50, "weight": 0.15, "weighted": 7.5}
  },
  "overrides": ["auth_files_changed"],
  "hotspots": ["src/services/payment_processor.py"],
  "top_risk_files": [
    {"file": "src/services/payment_processor.py", "reasons": ["uncovered", "high_churn", "cc_18"]},
    {"file": "src/api/routes/orders.py", "reasons": ["complexity_increase_6"]}
  ]
}
```

---

## MUST DO

- Always exclude test files and generated code from production risk scoring
- Always compute all five factors — do not skip any factor even if data is partial
- Always apply override rules after computing the base score
- Always report per-factor breakdown so the user understands what drives the score
- Always flag hotspot files (high churn + high complexity) explicitly
- Always provide an actionable recommendation, not just a number
- Always list the top 3-5 riskiest files with specific reasons
- Always use git log data from the actual repository — do not estimate churn
- Always note when a factor could not be measured (e.g., no coverage tool) and use fallback heuristics

## MUST NOT DO

- MUST NOT score test files as production risk — test changes reduce risk, not increase it
- MUST NOT use the risk score to block deploys silently — always surface the score and let a human decide
- MUST NOT ignore override rules — security and migration files MUST escalate regardless of computed score
- MUST NOT report a score without the factor breakdown — a bare number without explanation is useless
- MUST NOT hard-fail when coverage tools are unavailable — fall back to file-existence heuristics
- MUST NOT count documentation, config-only, or lock file changes toward the file count factor
- MUST NOT present the score as absolute truth — state that it is a heuristic and recommend human judgment for borderline cases
- MUST NOT run destructive git commands (reset, clean, checkout) — this skill is read-only analysis
