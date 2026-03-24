# Self-Improving Skill Design

Reference material for Step 5.5 (Inject Active Constraints into Skills).

## Design Philosophy

Skills become self-improving not by embedding feedback logic inside each skill,
but by having a centralized learning pipeline that injects proven constraints
back into skills as active guardrails. This preserves single-responsibility
(each skill does one thing) while closing the feedback loop.

## Source Framework

The following XML-tagged framework informed the design of Step 5.5:

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

1. **Evidence-triggered, not scheduled** — Step 5.5 only activates when
   `reuse_count >= 2`, not on every session. This prevents premature
   constraint injection from one-off errors.

2. **Structured feedback** — Learnings in `learnings.json` use structured
   triples (error → fix → lesson) with tags, not free-form notes. This
   enables precise mapping from learning to target skill.

3. **Feedback enhances, not replaces** — Skills work without any injected
   constraints. Step 5.5 adds constraints that make skills *better* over
   time, but a skill with zero injected constraints is still fully functional.

4. **Centralized, not distributed** — The feedback loop lives in
   `learn-n-improve` (one place), not inside each skill (30+ places).
   This avoids duplication and ensures consistent injection quality.

5. **User-gated** — No skill is modified without explicit user approval.
   The batch approval flow in Step 5.5.3 shows all proposals at once
   for efficient review.
