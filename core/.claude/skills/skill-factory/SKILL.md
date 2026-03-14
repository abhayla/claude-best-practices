---
name: skill-factory
description: >
  Detect repeated workflows in session logs and create new skills from them.
  Modes: scan (detect patterns), propose (suggest skills), create (build skill),
  list (show existing skills).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: scan|propose|create|list> [details]"
type: workflow
version: "2.0.0"
---

# Skill Factory — Pattern Detector & Skill Creator

Detect repeated workflows and create reusable skills from them.

**Arguments:** $ARGUMENTS

---

## Modes

| Mode | Description |
|------|-------------|
| `scan` | Analyze recent session work for repeated multi-step patterns |
| `propose` | Suggest new skills based on detected patterns |
| `create <name>` | Create a new skill from a description or detected pattern |
| `list` | Show all existing skills with descriptions |

---

## STEP 1: Mode Detection

Parse `$ARGUMENTS` to determine mode.

## Scan Mode

1. Read recent git history for repeated command patterns
2. Look for multi-step sequences that appear 3+ times
3. Identify candidates for automation

Report:
```
Detected Patterns:
  1. [pattern name] — seen N times
     Steps: [brief description]
     Automation potential: High/Medium/Low
```

## Propose Mode

Based on scan results, propose skill definitions:
```
Proposed Skills:
  1. /skill-name — [description]
     Trigger: [when to use]
     Steps: [what it automates]
     Effort: [estimated complexity]
```

## Create Mode

Create a new skill following the SKILL.md format:

1. Create directory: `.claude/skills/{name}/`
2. Write `SKILL.md` with proper frontmatter (all required fields)
3. Determine skill type: `workflow` (multi-step procedure) or `reference` (knowledge base)
4. For workflow skills: add numbered `## STEP N:` sections with verb-phrase titles
5. For reference skills: add organized `##` sections (no step numbering required)
6. Add `## CRITICAL RULES` or `## MUST DO` / `## MUST NOT DO` section at the end
7. Apply least-privilege to `allowed-tools` — only list tools the skill actually uses
8. Validate with `/writing-skills` quality checklist before saving

Template:
```markdown
---
name: {name}
description: >
  {description — start with a verb, 1-3 sentences}
allowed-tools: "{minimal set of tools actually used}"
argument-hint: "<{required}> [{optional}]"
type: {workflow|reference}
version: "1.0.0"
---

# {Title}

{One-sentence purpose.}

**Request:** $ARGUMENTS

---

## STEP 1: {Verb Phrase}

1. {Specific action}
2. {Specific action}

## STEP 2: {Verb Phrase}

1. {Specific action}
2. {Specific action}

## CRITICAL RULES

- {Rule with consequence of violation}
- {Rule with alternative action}
```

## List Mode

```bash
find .claude/skills -name "SKILL.md" -exec head -5 {} \;
```

Show each skill's name and description.
