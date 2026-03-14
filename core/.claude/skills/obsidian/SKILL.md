---
name: obsidian
description: >
  Obsidian vault management — create/edit .md, .base, .canvas files with Obsidian-specific
  syntax. Log decisions, capture bug fixes, manage knowledge. CLI integration (130+ commands),
  wikilinks, callouts, properties, bases, canvas, daily notes. Dev brain pattern.
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

### 3.1 Create / Edit Markdown (.md)

#### Obsidian-Specific Syntax Reference

Always use Obsidian syntax, NOT standard Markdown, for these features:

**Wikilinks** (NEVER convert to standard `[text](url)` format):
```markdown
[[Note Name]]                    # Link to note
[[Note Name|Display Text]]      # Aliased link
[[Note Name#Heading]]            # Link to heading
[[Note Name#^block-id]]          # Link to block
```

**Embeds** (transclusion — pulls content inline):
```markdown
![[Note Name]]                   # Embed entire note
![[Note Name#Heading]]           # Embed specific section
![[image.png]]                   # Embed image
![[image.png|300]]               # Embed image with width
![[image.png|300x200]]           # Embed image with dimensions
![[document.pdf#page=3]]         # Embed PDF page
```

**Callouts** (styled admonitions):
```markdown
> [!note] Title
> Content here

> [!warning] Important
> Critical information

> [!tip]+ Collapsible (open by default)
> Expandable content

> [!danger]- Collapsed by default
> Hidden until clicked
```

Callout types: `note`, `abstract`, `info`, `tip`, `success`, `question`, `warning`, `failure`, `danger`, `bug`, `example`, `quote`

**Properties / Frontmatter** (YAML at top of file):
```yaml
---
title: Note Title
tags:
  - project/active
  - type/decision
date: 2026-03-12
aliases:
  - Alternative Name
cssclasses:
  - custom-class
---
```

**Block IDs** (for precise linking):
```markdown
This is a paragraph. ^unique-id

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

^table-id
```

**Other Obsidian syntax:**
```markdown
%%This is a comment — hidden in reading view%%

==Highlighted text==

- [ ] Task item
- [x] Completed task
- [/] In progress
- [-] Cancelled

$$LaTeX math equation$$

```mermaid
graph TD
    A --> B
```​
```

**Footnotes:**
```markdown
Here is a statement[^1] with a footnote.

[^1]: This is the footnote content.
```

#### File Creation Template

```markdown
---
title: {{title}}
tags: {{tags}}
date: {{YYYY-MM-DD}}
type: {{note|decision|bug|snippet|meeting|daily}}
---

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

### 3.3 Canvas Files (.canvas)

Canvas files use the [JSON Canvas Spec 1.0](https://jsoncanvas.org/):

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4e5f67890",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 400,
      "height": 200,
      "text": "# Node Title\n\nMarkdown content here"
    },
    {
      "id": "b2c3d4e5f6789012",
      "type": "file",
      "x": 500,
      "y": 0,
      "width": 400,
      "height": 200,
      "file": "path/to/note.md"
    },
    {
      "id": "c3d4e5f678901234",
      "type": "link",
      "x": 0,
      "y": 300,
      "width": 400,
      "height": 200,
      "url": "https://example.com"
    },
    {
      "id": "d4e5f67890123456",
      "type": "group",
      "x": -50,
      "y": -50,
      "width": 1000,
      "height": 600,
      "label": "Group Label"
    }
  ],
  "edges": [
    {
      "id": "e5f6789012345678",
      "fromNode": "a1b2c3d4e5f67890",
      "toNode": "b2c3d4e5f6789012",
      "fromSide": "right",
      "toSide": "left",
      "label": "relates to"
    }
  ]
}
```

**Canvas rules:**
- Node IDs: 16-character hexadecimal strings (unique)
- Every node requires: `id`, `type`, `x`, `y`, `width`, `height`
- Text nodes: `text` field with Markdown content
- File nodes: `file` field with vault-relative path
- Link nodes: `url` field
- Group nodes: optional `label`, optional `background` (CSS color)
- Edge sides: `top`, `right`, `bottom`, `left`
- Edges can have: `color` (CSS), `label` (text)

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

### File Operations
```bash
obsidian read "$VAULT" "path/to/note.md"
obsidian create "$VAULT" "path/to/note.md" --content "# Title"
obsidian append "$VAULT" "path/to/note.md" --content "New line"
obsidian prepend "$VAULT" "path/to/note.md" --content "Top line"
obsidian move "$VAULT" "old/path.md" "new/path.md"
obsidian rename "$VAULT" "path/to/note.md" "New Name"
obsidian delete "$VAULT" "path/to/note.md" --trash  # Move to .trash
```

### Daily Notes
```bash
obsidian daily-note append "$VAULT" --content "- $(date +%H:%M) Log entry"
obsidian daily-note read "$VAULT"
obsidian daily-note prepend "$VAULT" --content "## Priority Tasks"
```

### Search & Metadata
```bash
obsidian search "$VAULT" --query "search term" --format json
obsidian properties get "$VAULT" "path/to/note.md"
obsidian properties set "$VAULT" "path/to/note.md" --key status --value done
obsidian tags list "$VAULT"
obsidian tasks list "$VAULT" --incomplete
```

### Graph & Links
```bash
obsidian backlinks "$VAULT" "path/to/note.md"
obsidian unresolved-links "$VAULT"       # Find broken wikilinks
obsidian orphans "$VAULT"                 # Find unlinked notes
```

### Fallback (No CLI)

When Obsidian CLI is not available, fall back to direct file manipulation:

```bash
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

After any vault operation:

1. **Verify file exists** and is valid:
   ```bash
   # Check .md file
   test -f "$FILE_PATH" && echo "Created: $FILE_PATH"

   # Check .canvas file (must be valid JSON)
   python3 -c "import json; json.load(open('$FILE_PATH'))" 2>/dev/null && echo "Valid canvas"

   # Check .base file (must be valid YAML)
   python3 -c "import yaml; yaml.safe_load(open('$FILE_PATH'))" 2>/dev/null && echo "Valid base"
   ```

2. **Check wikilinks** resolve:
   ```bash
   # Extract wikilinks and verify targets exist
   grep -oP '\[\[([^\]|]+)' "$FILE_PATH" | sed 's/\[\[//' | while read link; do
     find "$VAULT_ROOT" -name "$link.md" -o -name "$link" | head -1 | \
       grep -q . || echo "Unresolved: [[$link]]"
   done
   ```

3. **Report:**
   ```
   Vault operation complete:
     Action: {{action}}
     File: {{path relative to vault root}}
     Type: {{.md | .canvas | .base}}
     Wikilinks: {{N total, M unresolved}}
     Size: {{line count or node count}}
   ```

---

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
