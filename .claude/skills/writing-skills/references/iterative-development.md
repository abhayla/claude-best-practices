# Iterative Skill Development

The most effective process: Claude A creates the skill, Claude B tests it.

## The Claude A/B Pattern

- **Claude A** (your authoring session): designs and refines the skill
- **Claude B** (fresh instance with skill loaded): tests it on real tasks
- You observe Claude B's behavior and bring insights back to Claude A

## Creating a New Skill (Recommended Flow)

### 1. Complete a task without a skill first

Work through a real problem with normal prompting. As you work, notice:
- What context you repeatedly provide
- What corrections you make
- What procedural knowledge you share

This is the necessity check done organically — the gaps you discover
are more authentic than auto-generated test cases.

### 2. Ask Claude to create the skill

"Create a skill that captures the pattern we just used. Include [specific
context you provided]."

Claude models understand the Skill format natively. You don't need a
"writing skills" skill for this — simply ask. (The writing-skills skill
adds value for quality assurance, hub conventions, and evaluation
infrastructure, not because Claude can't produce a SKILL.md without it.)

### 3. Review for conciseness

Check Claude A hasn't added unnecessary explanations:
- "Remove the explanation about what X means — Claude already knows that"
- "Cut the section about Y — that's general knowledge"

### 4. Improve information architecture

- "Organize this so the table schema is in a separate reference file"
- "Move the edge cases to a reference — they'll clutter the main flow"

### 5. Test with Claude B

Run the skill in a fresh Claude instance on related but different tasks.
Observe: Does Claude B find the right information? Apply rules correctly?

### 6. Iterate based on observation

"When Claude used this skill, it forgot to filter by date. Should we add
a section about date filtering?" Return to Claude A with specifics.

## Diagnosing Issues from Observation

| What You Observe | Likely Cause | Fix |
|---|---|---|
| Claude B ignores a rule | Rule not prominent enough | Use MUST/MUST NOT, move to earlier step |
| Claude B reads files in unexpected order | Structure not intuitive | Reorganize, make links more explicit |
| Claude B repeatedly reads the same file | Content should be in SKILL.md | Promote to main body |
| Claude B never accesses a reference file | Poorly signaled or unnecessary | Improve pointer or remove |
| Claude B tries multiple approaches | Instructions too vague | Be more specific about which approach |
| Claude B follows irrelevant instructions | Too many instructions, no gating | Add "only if X" conditions |

### Example walkthrough

You build a BigQuery analysis skill that includes a rule: "Always filter
out test accounts." You test with Claude B by asking for a regional sales
report. Claude B writes the query but forgets to filter test accounts —
even though the skill mentions it.

You return to Claude A: "Claude B forgot to filter test accounts when I
asked for a regional report. The skill mentions filtering, but maybe it's
not prominent enough?"

Claude A suggests: use stronger language ("MUST filter" instead of "always
filter"), move the rule into the query-building step rather than a general
guidelines section, and add it to the MUST DO section. You apply the
changes and test again — Claude B now filters correctly because the rule
is in the right place with the right emphasis.

## Gathering Team Feedback

After the skill works for you, share with teammates:
- Does the skill activate when expected?
- Are instructions clear?
- What's missing from their usage patterns?

Teammates reveal blind spots in your own usage patterns. Incorporate
feedback before hub promotion.

## Why This Works

- Claude A understands agent instruction design
- You provide domain expertise
- Claude B reveals gaps through real usage
- Iteration improves skills based on observed behavior, not assumptions
