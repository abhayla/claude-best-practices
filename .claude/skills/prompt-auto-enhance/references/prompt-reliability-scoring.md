# Prompt Reliability Scoring

Score any prompt across 5 reliability dimensions before it goes into production.
Use when a user asks to "score", "evaluate", or "audit" a prompt — not during
automatic strengthening (that uses the 9-category diagnosis instead).

## Scoring Workflow

<scoring-protocol>
<step name="collect">
Ask the user to paste their prompt and describe the use case it serves.
The use case is critical — a prompt is scored against its intended context,
not in isolation. A terse prompt may score high for a CLI tool but low for
a customer-facing chatbot.
</step>

<step name="score">
Score the prompt across 5 dimensions, 1-10 each. Every score MUST cite
a specific quote from the prompt as evidence.

### Dimension Definitions

<dimensions>
<dimension name="instruction-clarity" weight="1.0">
  How unambiguously does the prompt communicate what must be done?

  | Score | Criteria |
  |-------|----------|
  | 9-10  | Single interpretation possible. Action verb + object + success criteria explicit. |
  | 7-8   | Clear intent but minor ambiguity in scope or approach. |
  | 5-6   | Multiple reasonable interpretations exist. Key details implied, not stated. |
  | 3-4   | Vague intent. Reader must guess what "done" looks like. |
  | 1-2   | No clear action. Could mean almost anything. |
</dimension>

<dimension name="output-format" weight="1.0">
  How precisely is the expected output defined?

  | Score | Criteria |
  |-------|----------|
  | 9-10  | Locked template with named sections, field types, and length bounds. |
  | 7-8   | Format specified (e.g., "JSON with these fields") but no template. |
  | 5-6   | General format mentioned ("a list", "a summary") without structure. |
  | 3-4   | No format specified. Output shape is entirely up to the model. |
  | 1-2   | Contradictory format signals or "just give me something." |
</dimension>

<dimension name="constraint-strength" weight="1.0">
  How enforceable and measurable are the prompt's constraints?

  | Score | Criteria |
  |-------|----------|
  | 9-10  | All constraints pass the measurability test ("Can a reviewer objectively verify this?"). Uses MUST/MUST NOT with concrete thresholds. |
  | 7-8   | Most constraints are measurable. 1-2 use vague language ("be concise"). |
  | 5-6   | Mix of measurable and unmeasurable. Some constraints are aspirational. |
  | 3-4   | Most constraints are vague ("be thorough", "high quality"). |
  | 1-2   | No constraints, or constraints that contradict each other. |
</dimension>

<dimension name="edge-case-handling" weight="1.0">
  How well does the prompt handle unexpected, missing, or malformed inputs?

  | Score | Criteria |
  |-------|----------|
  | 9-10  | Explicit handling for empty input, malformed data, ambiguous cases. Fallback behavior defined. |
  | 7-8   | Common edge cases addressed. 1-2 plausible failure modes unhandled. |
  | 5-6   | Happy path is clear. Edge cases not mentioned but inferrable. |
  | 3-4   | Only happy path defined. Failure modes would produce garbage output. |
  | 1-2   | No consideration of variability. Assumes perfect input. |
</dimension>

<dimension name="tone-consistency" weight="1.0">
  How clearly is the expected voice, register, and persona maintained?

  | Score | Criteria |
  |-------|----------|
  | 9-10  | Explicit persona with voice attributes (formal/casual, technical depth, audience). Consistent throughout. |
  | 7-8   | Tone is clear from context. Minor inconsistencies between sections. |
  | 5-6   | Tone is implied but not stated. Could shift between invocations. |
  | 3-4   | Mixed signals (formal instructions but casual examples). |
  | 1-2   | No tone guidance. Output voice is unpredictable. |
</dimension>
</dimensions>
</step>

<step name="calculate">
Calculate the overall reliability score:

```
Overall = (instruction_clarity + output_format + constraint_strength
           + edge_case_handling + tone_consistency) / 5
```

Round to one decimal place.
</step>

<step name="flag-risks">
Flag every dimension scoring below 7 as a **launch risk**. Launch risks
are not suggestions — they are defects that will cause inconsistent behavior
in production.

For each launch risk, provide:
1. The specific quote from the prompt that caused the low score
2. A concrete fix that would raise the score to 7+
3. The failure mode that will occur if unfixed
</step>
</scoring-protocol>

## Output Format

MUST use this exact format for the scoring report:

<output-template>
```
## Prompt Reliability Score: <use-case-name>

### Dimension Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Instruction Clarity | N/10 | "<quote from prompt>" — <reasoning> |
| Output Format | N/10 | "<quote from prompt>" — <reasoning> |
| Constraint Strength | N/10 | "<quote from prompt>" — <reasoning> |
| Edge Case Handling | N/10 | "<quote from prompt>" — <reasoning> |
| Tone Consistency | N/10 | "<quote from prompt>" — <reasoning> |

### Overall Reliability Score: N.N / 10

### Launch Risks

[For each dimension < 7:]
**[RISK] <Dimension Name> (N/10)**
- Evidence: "<quote>"
- Failure mode: <what will go wrong in production>
- Fix: <specific change to raise score to 7+>

### Verdict

- **9.0+** — Production ready. Ship it.
- **7.0-8.9** — Viable with minor hardening. Fix launch risks first.
- **5.0-6.9** — Significant rework needed. Multiple failure modes likely.
- **Below 5.0** — Not production ready. Redesign before scoring again.
```
</output-template>

## Mapping to Existing Diagnosis Categories

The 5 scoring dimensions map to the 9-category diagnosis system used in
automatic strengthening. Use this mapping when a scored prompt also needs
rewriting:

<category-mapping>
| Scoring Dimension | Maps to Diagnosis Categories |
|---|---|
| Instruction Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE |
| Output Format | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE |
| Constraint Strength | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS |
| Edge Case Handling | IMPLICIT_ASSUMPTIONS, MISSING_CONTEXT |
| Tone Consistency | (no direct mapping — unique to scoring) |
</category-mapping>

After scoring, if the user asks to fix the prompt, use the category mapping
to feed directly into the strengthening workflow (Steps 1-5 in the main skill).

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Scoring without use case | Scores are meaningless without context | Always ask for the use case first |
| Estimating instead of calculating | "About a 7" undermines credibility | Calculate from dimension scores exactly |
| Scores without evidence | Unjustified scores cannot be actioned | Every score MUST cite a prompt quote |
| Fixing during scoring | Mixing evaluation with rewriting confuses the output | Score first, then offer to fix via strengthening |
| Over-scoring to be encouraging | Inflated scores miss real risks | Score against the criteria, not the user's feelings |

## CRITICAL RULES

- Score against the use case, not in isolation — context changes the standard
- Every score MUST be justified with a specific quote from the prompt
- Dimensions below 7 are launch risks, not suggestions — they will cause production failures
- Overall score MUST be calculated from dimension scores, not estimated
- Do NOT fix the prompt during scoring — score first, offer fixes after
- Use the locked output template — do not improvise the report format
