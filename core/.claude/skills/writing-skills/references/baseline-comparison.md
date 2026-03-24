# Baseline Comparison Testing

Reference material for Step 6.4 (Baseline Comparison Testing).

## Procedure

### 6.4.1 Select 5 Test Inputs

Choose inputs that cover the skill's operational range:

| Input # | Type | Selection Criteria |
|---|---|---|
| 1-2 | Happy path | Common, straightforward invocations |
| 3 | Edge case | Boundary condition or unusual input |
| 4 | Past failure | An input that previously triggered a known issue |
| 5 | Adversarial | Deliberately tricky input (from Step 6.3 stress test) |

If the skill has entries in `.claude/learnings.json`, use the error contexts
from those learnings as inputs 4 and 5.

### 6.4.2 Run Baseline

Execute the **original** skill (before your changes) against all 5 inputs.
Record output quality on 4 dimensions:

| Dimension | Score (1-5) | What to Assess |
|---|---|---|
| Correctness | | Did it produce the right output? |
| Completeness | | Did it cover all aspects of the input? |
| Constraint adherence | | Did it follow its own MUST DO / MUST NOT DO rules? |
| Failure handling | | Did it degrade gracefully on edge/adversarial inputs? |

### 6.4.3 Run Enhanced Version

Execute the **modified** skill against the same 5 inputs. Score on the same
4 dimensions.

### 6.4.4 Compare and Gate

```
Baseline Comparison: <skill-name>

| Input | Dimension | Baseline | Enhanced | Delta |
|-------|-----------|----------|----------|-------|
| 1     | Correctness | 4 | 5 | +1 |
| 1     | Completeness | 4 | 4 | 0 |
| ...   | ... | ... | ... | ... |

Summary:
  Improvements: N dimensions improved
  Regressions: M dimensions regressed
  Net score: baseline=X enhanced=Y (delta: +/-Z)

Gate: PASS (no regressions) / FAIL (M regressions detected)
```

**Gate rule**: Enhanced version MUST NOT regress on any dimension for any input.
A single regression blocks promotion — fix the enhancement or accept the
trade-off with explicit user approval.

## Design Philosophy

When enhancing a skill with new constraints or feedback-driven improvements,
you need proof that the enhancement actually helps. Running before/after
comparisons against the same inputs provides that proof — and catches
regressions that would otherwise ship silently.

## Source Framework

The following XML-tagged framework informed the design of Step 6.4:

<role>
Act as a Claude skill trainer who designs prompts that get better automatically
with each use through structured feedback loops.
</role>

<task>
Take an existing Claude skill and add a feedback layer that captures failures,
learns from them, and improves output quality over time.
</task>

<steps>
1. Identify the skill and describe the output quality issues observed
2. Design a feedback capture mechanism — what to log, when, and how
3. Build a reflection loop that uses past failures as active constraints
4. Test the feedback-enhanced skill against 5 inputs and compare to baseline
5. Deliver the updated skill with instructions for running the improvement cycle
</steps>

<rules>
- Feedback MUST be structured — free-form notes do not improve prompts
- Every failure logged MUST connect to a specific prompt element
- Improvement cycles MUST be triggered by evidence, not schedule
- The skill MUST work without the feedback loop — it enhances, not replaces
</rules>

<output>
Feedback Layer Design → Enhanced Skill → Improvement Cycle Instructions → Baseline Comparison
</output>

## Key Principles Applied

1. **Baseline before enhancement** — Always measure the original skill's
   output quality before making changes. Without a baseline, you cannot
   distinguish "better" from "different."

2. **Same inputs, same dimensions** — The comparison is only valid when
   both versions are tested against identical inputs scored on identical
   dimensions. Changing either invalidates the comparison.

3. **No-regression gate** — A single regression on any dimension for any
   input blocks promotion. This is strict by design: regressions compound
   silently across sessions if not caught at enhancement time.

4. **Use learnings as test inputs** — Past failures from `learnings.json`
   are the best adversarial inputs because they represent real-world edge
   cases the skill has already struggled with.

5. **Evidence-triggered cycles** — Enhancement happens when evidence
   (recurring failures, `reuse_count >= 2`) demands it, not on a schedule.
   This prevents unnecessary churn on stable skills.
