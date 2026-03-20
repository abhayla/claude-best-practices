# STEP 10: Team Standards Evolution

### 10.1 Violation Logging

After each standards check, log a summary to `.pr-standards-log.json` (gitignored):

```json
{
  "timestamp": "2026-03-12T14:30:00Z",
  "branch": "feature/user-roles",
  "verdict": "FAIL",
  "violations": {
    "critical": 3,
    "warning": 3,
    "info": 2
  },
  "rules_triggered": [
    {"rule": "no-debugger", "count": 1, "severity": "critical"},
    {"rule": "no-hardcoded-secrets", "count": 1, "severity": "critical"},
    {"rule": "rate-limiting-required", "count": 1, "severity": "critical"},
    {"rule": "new-function-needs-test", "count": 1, "severity": "warning"},
    {"rule": "no-swallowed-errors", "count": 1, "severity": "warning"},
    {"rule": "no-todo-without-ticket", "count": 1, "severity": "warning"},
    {"rule": "no-magic-numbers", "count": 1, "severity": "info"},
    {"rule": "docstring-required", "count": 1, "severity": "info"}
  ],
  "auto_fixes_applied": 1,
  "auto_fixes_skipped": 0
}
```

### 10.2 Trend Analysis

When the log file exists and contains 10+ entries, provide trend insights:

```
STANDARDS TREND ANALYSIS
========================

Most triggered rules (last 30 days):
  1. no-todo-without-ticket — 23 violations across 8 PRs
  2. new-function-needs-test — 18 violations across 12 PRs
  3. no-print-debug — 15 violations across 6 PRs
  4. no-swallowed-errors — 12 violations across 5 PRs
  5. no-magic-numbers — 8 violations across 7 PRs

Recommendations:
  - PROMOTE: no-swallowed-errors (warning -> critical)
    Reason: Triggered in 5 PRs, 3 led to production issues
  - RETIRE: no-commented-code
    Reason: 0 violations in last 30 days — rule may be unnecessary
  - NEW RULE CANDIDATE: "require type hints on public functions"
    Reason: Review feedback pattern — reviewers requested type hints in 4 PRs

Never-triggered rules (candidates for removal):
  - no-binding-pry (team does not use Ruby)
  - no-var-dump (team does not use PHP)
```

### 10.3 Rule Lifecycle

| Phase | Criteria | Action |
|-------|----------|--------|
| **Proposed** | Pattern observed in 2+ reviews | Add as `info` severity |
| **Active** | Catches real issues regularly | Promote to `warning` |
| **Critical** | Violations have caused production issues | Promote to `critical` |
| **Retiring** | Zero triggers for 60+ days | Suggest removal |
| **Retired** | Confirmed unused by team | Remove from rule set |

### 10.4 Feeding Insights Back

After trend analysis, suggest actionable improvements:

1. **Frequent warnings -> critical**: If a warning-level rule triggers in 50%+ of PRs and the violations are always fixed, promote it
2. **Frequent info -> warning**: If an info-level rule triggers often and reviewers also flag the same issue, promote it
3. **Never-triggered rules**: Suggest removing rules for languages/frameworks the team does not use
4. **New rule candidates**: When the same manual review comment appears across 3+ PRs, propose a new automated rule

---

