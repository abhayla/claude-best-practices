# STEP 3: Form Hypotheses

### 3.1 List Candidate Causes

Generate at least 3 hypotheses, ranked by likelihood:

```
Hypotheses for: {symptom_description}

1. [MOST LIKELY] {hypothesis_1}
   Evidence for: {supporting_evidence}
   Evidence against: {contradicting_evidence}
   How to verify: {verification_step}

2. [POSSIBLE] {hypothesis_2}
   Evidence for: {supporting_evidence}
   Evidence against: {contradicting_evidence}
   How to verify: {verification_step}

3. [UNLIKELY BUT CHECK] {hypothesis_3}
   Evidence for: {supporting_evidence}
   Evidence against: {contradicting_evidence}
   How to verify: {verification_step}
```

### 3.2 Prioritization Heuristics

Rank hypotheses using these principles:

| Principle | Description |
|-----------|-------------|
| **Recent changes first** | Code changed in the last few commits is the most likely culprit |
| **Simple before complex** | A typo is more likely than a compiler bug |
| **Data before logic** | Wrong input is more likely than wrong algorithm |
| **Boundary conditions** | Off-by-one, null, empty string, zero, max value |
| **State before code** | Stale cache, wrong env var, missing config is more likely than code logic error |
| **Common over exotic** | NullPointerException > cosmic ray flipping a bit |

### 3.3 Avoid Premature Conclusions

Do NOT jump to a fix after forming the first hypothesis. Common traps:

- **Confirmation bias** — "I bet it's X" and then only looking for evidence that supports X
- **Anchoring** — Fixating on the first thing that looks wrong, even if it's unrelated
- **Correlation vs causation** — Two things changed at the same time, but only one caused the bug

Always test at least your top hypothesis with concrete evidence before attempting a fix.

---

