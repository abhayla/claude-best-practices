# STEP 2: Batch B — Security + Risk Scoring (Parallel)

### 2.1 Record Results

```
BATCH B — Security Audit:
  Status: {PASS / WARN / BLOCK / UNKNOWN}
  Critical findings: {count}
  High findings: {count}
  Medium findings: {count}
  Low findings: {count}
  Blocking issues: {count}

BATCH B — Change Risk Scoring:
  Risk score: {0-100}
  Classification: {LOW / MEDIUM / HIGH / CRITICAL}
  Recommendation: {AUTO-DEPLOY / HUMAN REVIEW / EXTRA TESTING / HOLD}
  Hotspots: {list or "none"}
  Top risk files: {list}
```

If any Critical security findings exist, this step is automatically BLOCK regardless of other results.

### 2.2 Threshold Check

Compare the risk score against the threshold (default: 50):

| Score vs Threshold | Action |
|--------------------|--------|
| Score ≤ threshold | PASS — risk is within acceptable bounds |
| Score > threshold by ≤ 15 | WARN — flag for awareness but do not block |
| Score > threshold by > 15 | BLOCK — risk exceeds acceptable bounds, recommend scope reduction |

---

