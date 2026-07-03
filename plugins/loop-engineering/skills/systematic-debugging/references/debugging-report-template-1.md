# Debugging Report Template

## Debugging Report Template

After completing the debugging process, summarize your findings:

```
DEBUGGING REPORT
================

Symptom: {what was observed}
Reproduction: {exact command or steps}

Investigation:
  Hypotheses tested: {count}
  Root cause: {description}
  Causal chain: {symptom} <- {proximate} <- {root cause}

Fix:
  Files changed: {list}
  Approach: {description of the fix}
  Risk: {what could go wrong}

Verification:
  Original reproduction: PASS
  Regression tests: PASS
  Edge cases tested: {count}

Prevention:
  Regression test added: {test name and location}
  Guards added: {description}
  Error messages improved: {yes/no}
```

---

