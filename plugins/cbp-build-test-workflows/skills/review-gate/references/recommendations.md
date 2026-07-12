# Recommendations

### 5.2 Machine-Readable Output

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
  "_status_values": "checks.*.status accepts: PASSED | WARNED | BLOCKED | UNKNOWN",
  "blocking_issues": [],
  "deferred_items": [
    {"source": "adversarial-review", "id": "R3", "tracking": "#456", "description": "...", "deferred_date": "2026-03-01T00:00:00Z", "ttl_remaining_days": 14, "auto_promoted": false}
  ],
  "fix_loop_ran": false,
  "verdict": "APPROVED",
  "recommendation": "Proceed to PR creation and Stage 10."
}
```

### 5.3 Verdict Logic

```
IF any check has status UNKNOWN:
  verdict = "REJECTED"   # UNKNOWN is treated as BLOCK — unknowns are unsafe
ELIF any check has unresolved BLOCK status:
  verdict = "REJECTED"
ELIF risk_score > threshold + 15:
  verdict = "REJECTED"
ELIF any check has WARN status OR deferred_items > 0 OR risk_score > threshold:
  verdict = "APPROVED WITH CAVEATS"
ELSE:
  verdict = "APPROVED"
```

---

