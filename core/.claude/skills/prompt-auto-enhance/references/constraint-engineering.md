# Constraint Engineering Reference

Source: Community pattern — "Write Constraints That Actually Work"

## Original XML-Structured Prompt

This is the source pattern in its native XML-tagged form. It demonstrates
effective use of `<role>`, `<task>`, `<steps>`, `<rules>`, and `<output>` tags
for structured prompt engineering (see XML Tag Reference in SKILL.md).

```xml
<role>
Act as a Claude constraint engineer who turns vague instructions into
specific rules that produce consistent outputs every time.
</role>

<task>
Take my existing prompt and replace every vague instruction with a concrete,
testable constraint.
</task>

<steps>
1. Ask me to paste my current prompt
2. Identify every instruction that is vague, subjective, or open to interpretation
3. Rewrite each vague instruction as a specific, measurable constraint
4. Test the constrained prompt against 5 inputs and compare to original
5. Deliver a constraint audit showing every change and why it reduces failure
</steps>

<rules>
- Vague = failure — every instruction must be specific enough to be tested
- Constraints must be measurable — "be concise" is not a constraint, "under 100 words" is
- Never add constraints that don't solve a real inconsistency
- Show the before/after for every instruction rewritten
</rules>

<output>
Vague Instruction List → Constraint Rewrites → Before/After → Consistency Score
</output>
```

## Core Principles (extracted)

1. **Vague = failure** — every instruction must be specific enough to be tested
2. **Constraints must be measurable** — "be concise" is not a constraint, "under 100 words" is
3. **Never add constraints that don't solve a real inconsistency**
4. **Show the before/after for every instruction rewritten**

## Measurability Test

For each constraint, ask: **"Can a reviewer objectively verify this was followed
by reading the output alone?"**

| Fails Measurability | Passes Measurability |
|---------------------|---------------------|
| "Be concise" | "Under 100 words" |
| "Use a professional tone" | "No contractions, no slang, no first person" |
| "Keep it simple" | "Max 3 levels of nesting, no sentences over 20 words" |
| "Make it fast" | "Response under 200 tokens, no web searches" |
| "Be thorough" | "Cover all 5 checklist items with evidence for each" |
| "Handle edge cases" | "Include null, empty string, and max-length inputs in tests" |

## Constraint Audit Output Format

```
Constraint Audit:
  Vague Instructions Found: N
  Constraints Rewritten: N

  [1] BEFORE: <vague instruction>
      AFTER:  <measurable constraint>
      WHY:    <what inconsistency this prevents>

  [2] ...

  Validation: Tested against N sample inputs
  Consistency Score: X/10 (before) → Y/10 (after)
```
