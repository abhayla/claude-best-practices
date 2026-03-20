# STEP 7: Generate Review Report

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

