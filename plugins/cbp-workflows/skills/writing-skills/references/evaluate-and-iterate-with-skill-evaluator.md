# STEP 6: Evaluate and Iterate with /skill-evaluator

### 6.1 Invoke Evaluation

For new skills:
```
Agent(subagent_type="general-purpose",
  prompt="/skill-evaluator full <skill-path>")
```

For updated skills:
```
Agent(subagent_type="general-purpose",
  prompt="/skill-evaluator full <skill-path> --baseline")
```

### 6.2 Auto-Fix Routing

When skill-evaluator returns FIX or FAIL, apply the mapped fix:

| Eval Failure Type | Automated Fix |
|---|---|
| Should-trigger failing (<80%) | Broaden description: add user-intent phrases, expand scope |
| Should-not-trigger firing (>20%) | Narrow description: add boundary ("do NOT use when...") |
| Cross-skill conflict | Make triggers more specific, add distinguishing context |
| Trigger regression (--baseline) | Restore key phrases from old description |
| Scenario assertion failures | Add/clarify the step that produces the failing output |
| Stress test CRITICAL | Add guardrail to MUST DO, embed prevention in earliest step |
| Stress test MAJOR | Add edge case handling to relevant step's decision table |
| Stress score <90% overall | Re-run failure mode analysis (Step 2.3), add preventions |
| Skill adds no value over baseline | STOP — report to user: "skill not needed" |

### 6.3 Iterate Until PASS

1. Apply fix from routing table
2. Re-invoke `/skill-evaluator full <skill-path>`
3. If FIX/FAIL: apply next fix (each iteration MUST try a different fix)
4. If PASS: proceed to 6.4

**Max 5 iterations.** After 5 without PASS: STOP, present full iteration history, user decides.

### 6.4 Present for Approval

Present to user: final skill draft, eval report, iteration history, skill necessity delta.

**Wait for user approval before proceeding to Step 7.** This is the single human touchpoint.

### 6.5 Failure Prevention Map

Before promoting, produce a failure prevention map that documents every guardrail in the skill. This is the "proof of failure resistance" artifact.

```
