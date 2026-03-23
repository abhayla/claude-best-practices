---
name: obsidian
description: >
  Manage Obsidian vaults by creating/editing .md, .base, .canvas files with Obsidian-specific
  syntax. Log decisions, capture bug fixes, and organize knowledge with CLI integration,
  wikilinks, callouts, properties, bases, canvas, and daily notes.
  Use when working with Obsidian vaults or personal knowledge bases.
triggers:
  - obsidian
  - vault
  - knowledge base
  - daily note
  - canvas
  - PKM
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<action: create|edit|search|daily|canvas|base|organize|log> <details>"
version: "1.0.0"
type: workflow
---

# Obsidian — Vault Management & Dev Brain

Manage Obsidian vaults with proper Obsidian-specific syntax. Create, edit, search, and organize notes, bases, and canvases.

**Input:** $ARGUMENTS

---

## STEP 1: Detect Action

Parse the input to determine what the user wants:

| Action | Trigger | Description |
|--------|---------|-------------|
| `create` | "create note", "new note" | Create a new .md file |
| `edit` | "edit", "update", "append" | Modify an existing note |
| `search` | "find", "search", "lookup" | Search vault content |
| `daily` | "daily note", "today", "journal" | Create/append to daily note |
| `canvas` | "canvas", "visual", "diagram" | Create/edit .canvas files |
| `base` | "base", "database", "table view" | Create/edit .base files |
| `organize` | "organize", "restructure", "tag" | Reorganize vault structure |
| `log` | "log decision", "capture bug", "save snippet" | Dev brain logging |

---

## STEP 2: Locate Vault

Find the Obsidian vault root:

```bash
# Look for .obsidian directory (vault marker)
find . -name ".obsidian" -type d -maxdepth 3 2>/dev/null | head -5
```

If no vault found, ask the user for the vault path. Store it for the session.

---

## STEP 3: Execute Action


**Read:** `references/execute-action.md` for detailed step 3: execute action reference material.

# {{title}}

{{content}}

## Related
{{wikilinks to related notes}}
```

### 3.2 Daily Notes

Daily notes follow the configured pattern (check `.obsidian/daily-notes.json` if it exists):

```bash
# Default daily note path
DAILY_DIR="Daily Notes"
TODAY=$(date +%Y-%m-%d)
DAILY_FILE="$VAULT_ROOT/$DAILY_DIR/$TODAY.md"
```

**Daily note template:**
```markdown
---
date: {{YYYY-MM-DD}}
type: daily
tags:
  - daily
---

# {{YYYY-MM-DD}} — {{Day of Week}}

## Tasks
- [ ]

## Log
-

## Notes
```

**Append to daily note** (most common operation):
```bash
# Append a log entry to today's daily note
echo "- $(date +%H:%M) — $ENTRY" >> "$DAILY_FILE"
```

### 3.4 Base Files (.base)

Bases are database-like views stored as YAML:

```yaml
# Example: Project tracker base
filter:
  - property: tags
    operator: contains
    value: project/active
  - property: status
    operator: is not
    value: archived

formula:
  - name: days_since
    expression: "now() - prop('date')"
  - name: priority_score
    expression: "if(prop('priority') = 'high', 3, if(prop('priority') = 'medium', 2, 1))"

properties:
  - name: title
    visible: true
    width: 200
  - name: status
    visible: true
    width: 120
  - name: priority
    visible: true
    width: 100
  - name: days_since
    visible: true
    width: 80

sort:
  - property: priority_score
    order: desc

view: table  # table | cards | list | map
```

**Base rules:**
- Filters narrow which notes appear: `contains`, `is`, `is not`, `starts with`, `ends with`, `exists`, `does not exist`
- Formulas create computed properties using expressions
- Date functions: `now()`, `date()`, `duration()`
- Properties control column visibility, order, and width
- Views: `table` (spreadsheet), `cards` (kanban-like), `list`, `map` (requires location data)

### 3.5 Search Vault

```bash
# If Obsidian CLI is available (v1.12+)
obsidian search --vault "$VAULT_ROOT" --query "$SEARCH_TERM" --format json

# Fallback: grep-based search
grep -rl "$SEARCH_TERM" "$VAULT_ROOT" --include="*.md" | head -20
```

### 3.6 Organize Vault

Common organization patterns:

**PARA Method:**
```
vault/
  Projects/          # Active projects with deadlines
  Areas/             # Ongoing responsibilities
  Resources/         # Reference material by topic
  Archive/           # Completed/inactive items
```

**Zettelkasten:**
```
vault/
  Inbox/             # New unprocessed notes
  Permanent/         # Refined atomic notes
  Literature/        # Notes from sources
  Maps/              # MOCs (Maps of Content)
```

**MOC (Map of Content)** template:
```markdown
---
title: "MOC: {{Topic}}"
tags:
  - MOC
date: {{YYYY-MM-DD}}
---

# {{Topic}}

## Core Concepts
- [[Concept 1]]
- [[Concept 2]]

## Key Resources
- [[Resource 1]]
- [[Resource 2]]

## Open Questions
-

## Related MOCs
- [[MOC: Related Topic]]
```

### 3.7 Dev Brain — Decision & Bug Logging

Use the vault as an engineering knowledge base:

**Decision Log:**
```markdown
---
title: "Decision: {{short description}}"
date: {{YYYY-MM-DD}}
type: decision
tags:
  - decision
  - {{project-tag}}
status: accepted  # proposed | accepted | superseded | deprecated
---

# Decision: {{Short Description}}

## Context
{{What is the situation? What forces are at play?}}

## Decision
{{What was decided?}}

## Consequences
- **Positive:** {{benefits}}
- **Negative:** {{trade-offs}}
- **Risks:** {{what could go wrong}}

## Alternatives Considered
1. [[Alternative A]] — rejected because {{reason}}
2. [[Alternative B]] — rejected because {{reason}}

## Related
- Supersedes: [[Decision: Previous Related Decision]]
- Implements: [[Project: Feature Name]]
```

**Bug Fix Log:**
```markdown
---
title: "Bug: {{short description}}"
date: {{YYYY-MM-DD}}
type: bug
tags:
  - bug
  - {{component-tag}}
status: fixed  # investigating | fixed | wont-fix
severity: {{critical|high|medium|low}}
---

# Bug: {{Short Description}}

## Symptoms
{{What was observed?}}

## Root Cause
{{Why did it happen?}}

## Fix
{{What was changed?}}

```diff
- old code
+ new code
```​

## Prevention
{{How to avoid this in the future?}}

## Related
- Fixed in: [[commit hash or PR link]]
- Affected: [[Component Name]]
```

**Code Snippet:**
```markdown
---
title: "Snippet: {{description}}"
date: {{YYYY-MM-DD}}
type: snippet
tags:
  - snippet
  - {{language}}
  - {{use-case}}
---

# {{Description}}

## When to Use
{{Context for when this pattern applies}}

## Code

```{{language}}
{{code here}}
```​

## Notes
{{Gotchas, edge cases, or usage tips}}

## Source
{{Where this came from — docs, Stack Overflow, personal discovery}}
```

---

## STEP 4: Obsidian CLI Integration

If Obsidian v1.12+ is installed with CLI enabled, use these commands:


**Read:** `references/obsidian-cli-integration.md` for detailed step 4: obsidian cli integration reference material.

# Check if CLI is available
if command -v obsidian &>/dev/null; then
  echo "CLI available"
else
  echo "Using direct file access"
fi
```

Direct file access works for all read/write/edit operations. The CLI adds search, metadata queries, graph operations, and daily note awareness.

---

## STEP 5: Automation Hooks

Set up Claude Code hooks for automatic vault updates:

### Auto-Log Commits to Daily Note
```bash
# In .claude/hooks/post-commit.sh
VAULT_ROOT="$HOME/Obsidian/DevVault"
TODAY=$(date +%Y-%m-%d)
COMMIT_MSG=$(git log -1 --pretty=format:"%s")
COMMIT_HASH=$(git log -1 --pretty=format:"%h")
REPO=$(basename $(git rev-parse --show-toplevel))

echo "- $(date +%H:%M) — \`$REPO\` [$COMMIT_HASH] $COMMIT_MSG" >> \
  "$VAULT_ROOT/Daily Notes/$TODAY.md"
```

### Auto-Log Decisions
```bash
# In .claude/hooks/post-decision.sh
# Triggered when ADR-like content is written
VAULT_ROOT="$HOME/Obsidian/DevVault"
DECISION_DIR="$VAULT_ROOT/Decisions"
mkdir -p "$DECISION_DIR"
# Decision file created by the skill in Step 3.7
```

---

## STEP 6: Verify & Report

**Read:** `references/verify-report.md` for detailed step 6: verify & report reference material.

## RULES

- ALWAYS use wikilinks `[[Note]]` — NEVER convert to standard Markdown links `[Note](note.md)`
- ALWAYS preserve existing frontmatter properties when editing — append, don't overwrite
- ALWAYS use Obsidian callout syntax `> [!type]` — never HTML or custom div blocks
- NEVER delete vault files without explicit user confirmation — move to `.trash/` instead
- Canvas node IDs MUST be 16-character hexadecimal strings and MUST be unique
- Base files MUST be valid YAML — validate before writing
- When appending to daily notes, ALWAYS include a timestamp prefix `HH:MM —`
- Respect the user's vault folder structure — don't reorganize without asking
- Use `%%comments%%` for metadata that shouldn't appear in reading view
- Tags in frontmatter use array format with hierarchical paths: `project/active`, `type/decision`
