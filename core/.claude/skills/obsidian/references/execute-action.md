# STEP 3: Execute Action

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

