---
name: skill-factory
description: >
  Detect repeated workflows in session logs and create new skills from them.
  Modes: scan (detect patterns), propose (suggest skills), create (build skill),
  list (show existing skills).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: scan|propose|create|list> [details]"
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
2. Write `SKILL.md` with proper frontmatter
3. Include: name, description, allowed-tools, argument-hint
4. Add clear step-by-step instructions
5. Add critical rules section

Template:
```markdown
---
name: {name}
description: >
  {description}
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "{args}"
---

# {Title}

{Instructions}
```

## List Mode

```bash
find .claude/skills -name "SKILL.md" -exec head -5 {} \;
```

Show each skill's name and description.
