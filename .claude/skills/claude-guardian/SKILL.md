---
name: claude-guardian
description: >
  Validate and place rules into the correct CLAUDE.md or config file. Two modes:
  enhance-and-place a rough rule idea, or audit all config files for misplaced rules.
  Use when adding conventions, after editing CLAUDE.md, or when unsure where a rule belongs.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<rough rule text> | audit"
version: "1.0.1"
type: workflow
---

# Claude Guardian — Config Rule Placement & Audit

Enhance rough rule ideas into well-structured rules and place them in the correct config file.
Audit all config files to catch accidental deletions, misplacements, and protected section violations.

**Arguments:** $ARGUMENTS

---

## MODE SELECTION

- `$ARGUMENTS` contains `audit` → **Mode 2: Audit & Guard**
- Otherwise → **Mode 1: Enhance & Place** (treat `$ARGUMENTS` as the rough rule text)

---

## CONFIG FILE LOCATIONS

| File | Scope | Content Type | Examples |
|------|-------|-------------|---------|
| `~/.claude/CLAUDE.md` | ALL projects globally | Generic cross-project rules | "Always use forward slashes in bash" |
| `~/.claude/CLAUDE.local.md` | All projects globally (private) | Personal preferences | "I prefer verbose test output" |
| `CLAUDE.md` (project root) | This project only | Project-specific rules, architecture | Build commands, file structure |
| `CLAUDE.local.md` (project root) | This project only (gitignored) | Local project preferences | Local env paths, personal shortcuts |
| `.claude/rules/*.md` | This project, path-scoped | Detailed technical rules | Framework patterns, testing rules |

---

## STEP 1: Enhance & Place

### Step 1: Analyze the Rule
- Parse the rough rule text
- Determine scope: global, project, or path-specific
- Identify the correct target file

### Step 2: Enhance the Rule
Transform rough text into structured format:
- Clear, actionable statement
- Example (if applicable)
- Rationale (brief)

### Step 3: Place the Rule
- Read the target file
- Find the appropriate section
- Add the rule without disrupting existing content
- Report what was added and where

---

## STEP 2: Audit

### Step 1: Read All Config Files
Read all CLAUDE.md, CLAUDE.local.md, and .claude/rules/*.md files.

### Step 2: Check for Issues
- **Deletions:** Compare against git history for accidentally removed rules
- **Misplacements:** Rules in wrong scope (global rule in project file, etc.)
- **Duplicates:** Same rule in multiple files
- **Conflicts:** Contradictory rules

### Step 3: Report
```
Audit Results:
  Files checked: N
  Issues found: M
  - [issue type]: [description] in [file]
```
