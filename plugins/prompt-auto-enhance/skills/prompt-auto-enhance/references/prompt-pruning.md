# Prompt Pruning Reference

Source: Community pattern — "Remove Every Word That Weakens Your Prompt"

## Original XML-Structured Prompt

This is the source pattern in its native XML-tagged form. It demonstrates
effective use of `<role>`, `<task>`, `<steps>`, `<rules>`, and `<output>` tags
for structured prompt engineering (see XML Tag Reference in SKILL.md).

```xml
<role>
Act as a Claude prompt editor who strips every word that reduces output
reliability without adding precision.
</role>

<task>
Take my existing prompt and cut every phrase, qualifier, and filler instruction
that introduces ambiguity or inconsistency.
</task>

<steps>
1. Ask me to paste my current prompt
2. Flag every word or phrase that is vague, redundant, or weakens instruction clarity
3. Remove or replace each flagged element with tighter language
4. Show a word count reduction alongside the clarity improvement
5. Test the edited prompt against 5 inputs and compare output quality to original
</steps>

<rules>
- Every cut must improve precision, not just reduce length
- Qualifiers like "try to" and "if possible" are automatic flags
- Redundant instructions must be collapsed into one
- Never remove a word without showing what problem it solved
</rules>

<output>
Flag List → Edited Prompt → Word Count Delta → Output Quality Comparison
</output>
```

## Core Principles (extracted)

1. **Every cut must improve precision, not just reduce length** — pruning is
   not about brevity, it's about eliminating ambiguity
2. **Qualifiers are automatic flags** — "try to", "if possible", "maybe" give
   the model permission to underperform
3. **Redundant instructions collapse into one** — repeated constraints waste
   tokens and can contradict each other across phrasings
4. **Every removal must be justified** — show what problem the removed word
   was causing (ambiguity, hedging, scope creep)

## Weakening Language Taxonomy

| Category | Examples | Why It Weakens |
|----------|----------|----------------|
| **Permission hedges** | "try to", "attempt to", "if possible" | Permits failure as an acceptable outcome |
| **Uncertainty markers** | "maybe", "perhaps", "might", "could" | Introduces ambiguity into deterministic instructions |
| **Authority weakeners** | "I think", "I believe", "in my opinion" | Undermines the instruction's authority |
| **Politeness filler** | "please", "kindly", "would you mind" | Adds tokens without adding information in technical prompts |
| **Unbounded scope** | "etc.", "and so on", "and more", "among others" | Leaves the model to guess what else is included |
| **False minimizers** | "simple", "just", "easily", "quickly" | Sets false expectations about task complexity |
| **Delegation without criteria** | "as needed", "as appropriate", "when relevant" | Delegates a decision without specifying the criteria |
| **Redundant emphasis** | "very important", "absolutely must", "critical that you" | If the instruction is well-placed, emphasis is unnecessary |

## Pruning Audit Output Format

```
Pruning Audit:
  Words Flagged: N
  Words Removed: N
  Word Count: X → Y (−Z words, −P%)

  [1] FLAGGED: "<phrase>"
      CATEGORY: <weakening category>
      ACTION: REMOVED | REPLACED → "<replacement>"
      WHY: <what ambiguity or inconsistency this elimination prevents>

  [2] ...

  Validation: Tested against N sample inputs
  Clarity Score: X/10 (before) → Y/10 (after)
```

## Integration with Strengthening Workflow

Prompt pruning is one pass within the broader strengthening workflow (Steps 1-5
in SKILL.md). It runs after category diagnosis and before the rewrite:

1. **Step 1** diagnoses structural weaknesses (9 categories)
2. **Step 1 (Weakening Language Flags)** flags word-level precision issues
3. **Step 2** maps all findings (both categories and flags) to fixes
4. **Step 3** applies fixes — including pruning flagged language
5. **Step 4** shows before/after with word count delta

Pruning and structural fixes are applied together in a single rewrite pass —
not as separate sequential operations.
