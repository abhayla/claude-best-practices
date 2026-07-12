# Pipeline Flow Summary

## Pipeline Flow Summary

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                    /review-gate                                 │
 │                                                                 │
 │  STEP 0: Validate preconditions (branch, commits, tests)       │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 1: BATCH A (parallel agents)                             │
 │     ├── /code-quality-gate (skip layer check)                  │
 │     └── /architecture-fitness (authoritative layer check)      │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 2: BATCH B (parallel)                                    │
 │     ├── /security-audit (via agent)                            │
 │     └── /change-risk-scoring                                   │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 3: BATCH C (sequential, uses A+B context)                │
 │     ├── /adversarial-review --mode code                        │
 │     └── /pr-standards                                          │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 4: /fix-loop + /auto-verify (if --fix and blocks exist)  │
 │     │                                                           │
 │     ▼                                                           │
 │  BATCH D: /test-maintenance audit (if --include-test-health)    │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 5: Consolidated report → test-results/review-gate.json   │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 6: /request-code-review (if --pr and verdict ≠ REJECTED) │
 │     │                                                           │
 │     ▼                                                           │
 │  STEP 7: /receive-code-review (when feedback arrives)          │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
```

---

