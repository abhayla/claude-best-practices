# Format Locking Reference

Source: Community pattern — "Lock Your Output Format" by @heyrimsha

## Original XML-Structured Prompt

This is the source pattern in its native XML-tagged form. It demonstrates
effective use of `<role>`, `<task>`, `<steps>`, `<rules>`, and `<output>` tags
for structured prompt engineering (see XML Tag Reference in SKILL.md).

```xml
<role>
Act as a Claude output architect who eliminates format drift by designing
airtight output specifications.
</role>

<task>
Take my existing prompt and build an output format so precise that Claude
produces identical structure every single run.
</task>

<steps>
1. Ask me to paste my current prompt and show me 2-3 examples of the output
   variance I'm seeing
2. Identify every dimension where format is drifting — length, structure,
   tone, order
3. Design an explicit output template with locked sections, labels, and
   length rules
4. Embed the template directly into the prompt
5. Test against 5 inputs and verify format consistency across all runs
</steps>

<rules>
- Format drift is a prompt problem, not a model problem — own it
- Every output section must be named and ordered explicitly
- Length rules must use numbers, not adjectives
- Test until the format is identical across 5 consecutive runs
</rules>

<output>
Drift Diagnosis → Output Template → Embedded Prompt → Consistency Verification
</output>
```

## Problem

Output format drift — Claude produces different structure, section ordering,
length, or labeling across runs of the same prompt. This is a prompt problem,
not a model problem. Unlocked formats let the model improvise structure on
every invocation.

## Core Principles

1. **Every output section MUST be named and ordered explicitly** — unnamed
   sections drift in position and labeling across runs
2. **Length rules MUST use numbers, not adjectives** — "brief" drifts,
   "under 50 words" does not
3. **Section labels MUST be literal strings** — "## Summary" not "a summary
   section"
4. **Field order MUST be specified** — without explicit ordering, fields
   shuffle between runs

## Format Locking Methodology

### Step 1: Identify Drift Dimensions

Analyze 2-3 sample outputs from the current prompt and classify every
dimension where format varies:

| Drift Dimension | Example |
|----------------|---------|
| **Length** | Summary ranges from 1 sentence to 3 paragraphs |
| **Structure** | Sometimes bullet list, sometimes numbered, sometimes prose |
| **Section order** | "Analysis" appears before or after "Recommendation" |
| **Tone** | Formal in one run, casual in the next |
| **Labeling** | "Summary" vs "Overview" vs "Key Points" |
| **Granularity** | 3 items in one run, 12 in another |

### Step 2: Design Locked Template

Build an explicit output template that eliminates every identified drift
dimension. Rules for the template:

- **Name every section** with a literal heading or label
- **Fix the order** — sections appear in the template order, always
- **Set numeric bounds** for variable-length sections (e.g., "3-5 bullets")
- **Specify format type** per section (bullet list, numbered list, table, prose)
- **Lock labels** — use exact strings, not descriptions

Example locked template:
```
## Summary
[1-2 sentences, max 40 words]

## Changes
| File | Change | Reason |
|------|--------|--------|
[one row per changed file, max 10 rows]

## Risk Assessment
- [3-5 bullet points, each under 20 words]

## Next Steps
1. [exactly 3 numbered items]
```

### Step 3: Embed Template in Prompt

Place the template directly in the prompt using `<output_format>` tags
(see XML Tag Reference in SKILL.md):

```xml
<output_format>
[paste the locked template here — the model treats it as a structural contract]
</output_format>
```

Position the template AFTER the task description and constraints, BEFORE
any examples. This placement maximizes adherence.

### Step 4: Verify Consistency

Test the locked prompt against 5 varied inputs. For each output, verify:

| Check | Pass Criteria |
|-------|--------------|
| Section names match template exactly | Zero label drift |
| Section order matches template | Zero reordering |
| Length bounds respected | All sections within numeric limits |
| Format type respected | Bullets stay bullets, tables stay tables |
| No extra sections added | Output contains only template sections |

If any check fails, tighten the constraint — the drift dimension was not
locked precisely enough.

## Common Locking Patterns

### For JSON output
```
Respond with ONLY this JSON structure, no other text:
{
  "result": "PASSED | FAILED",
  "summary": "<string, max 100 chars>",
  "items": ["<string>", ...],  // exactly 3-5 items
  "score": <number 0-100>
}
```

### For tabular output
```
Respond with ONLY this table, no preamble or explanation:
| Column A | Column B | Column C |
|----------|----------|----------|
[one row per item, max 10 rows, no merged cells]
```

### For sectioned reports
```
Use EXACTLY these sections in this order:
## Section Name 1
[constraints for this section]

## Section Name 2
[constraints for this section]

Do not add, remove, rename, or reorder sections.
```

## Anti-Patterns

- **"Use a clear format"** — vague, produces different formats every run.
  Use a locked template instead.
- **"Output as JSON"** — underspecified, field names and nesting will vary.
  Provide the exact schema instead.
- **"Keep it organized"** — subjective, drifts immediately. Name and order
  every section explicitly instead.
- **"Be consistent"** — meta-instruction that the model cannot self-enforce.
  Lock the structure so consistency is guaranteed by design instead.
