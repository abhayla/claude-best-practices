---
name: claude-guardian
description: >
  Validate and place rules into the correct CLAUDE.md or config file. Two modes:
  enhance-and-place a rough rule idea, or audit config files for accidentally deleted
  rules and protected section integrity. Use when adding conventions, after editing
  CLAUDE.md, or when unsure where a rule belongs. NOT for SSOT layer violations
  (use /ssot-audit), writing new skills (use /skill-authoring-workflow),
  or authoring rule files from scratch (use /writing-skills).
triggers:
  - place a rule
  - where does this rule go
  - audit CLAUDE.md placement
  - add convention to config
  - enhance and place rule
  - rule placement audit
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<rough rule text> | audit"
version: "1.2.0"
type: workflow
---

# Claude Guardian — Config Rule Placement & Audit

Enhance rough rule ideas into well-structured rules and place them in the correct
config file. Audit config files for accidentally deleted rules and protected section
integrity. MUST route deterministic enforcement to `/update-config` (hooks), not
CLAUDE.md. MUST check for existing rules before placing new ones.

**Arguments:** $ARGUMENTS

If `$ARGUMENTS` is empty or whitespace, ask: "Provide rough rule text to
enhance-and-place, or `audit` to scan config files for issues."

---

## MODE SELECTION

- `$ARGUMENTS` is EXACTLY `audit` (case-insensitive, trimmed) → **Mode 2: Audit & Guard** (STEP 2)
- Otherwise → **Mode 1: Enhance & Place** (STEP 1)
- Note: "audit" inside a longer sentence (e.g., "audit this rule text") is NOT a mode signal — use Mode 1.

---

## STEP 1: Enhance & Place

### 1.1 Analyze the Rule

Parse the rough rule text and classify it using this decision tree:

| Rule Type | Signal | Target | Action |
|-----------|--------|--------|--------|
| Deterministic enforcement (style, linting, "always run X") | Zero-exception language, automatable | `.claude/settings.json` | Route to `/update-config` — hooks enforce this, not instructions |
| Path-scoped constraint (applies to specific file types) | Mentions file extensions, directories, frameworks | `.claude/rules/*.md` with `globs:` | Create or append to scoped rule file |
| Global behavioral standard | Applies to all files, requires judgment | `.claude/rules/*.md` with `# Scope: global` | Create or append to global rule file |
| Project context (commands, architecture, gotchas) | Build/test commands, project-specific facts | `CLAUDE.md` (project root) | Add to appropriate section |
| Personal preference | Subjective, not team-wide | `CLAUDE.local.md` | Add (gitignored) |
| Cross-project rule | Applies to ALL projects for this user | `~/.claude/CLAUDE.md` | Add to global user config |

Reference `.claude/rules/configuration-ssot.md` for the full placement taxonomy.

### 1.2 Check for Duplicates

Before placing, search all config files for existing rules covering the same concern:
```bash
grep -r "<key phrases from rule>" CLAUDE.md CLAUDE.local.md .claude/rules/ 2>/dev/null
```
If a duplicate or near-duplicate exists, report it and ask whether to update the existing rule or add a new one.

### 1.3 Enhance the Rule

Transform rough text into structured format:
- **Statement:** Clear, actionable directive using MUST/MUST NOT/ALWAYS/NEVER
- **Alternative:** If rule says "don't do X", include "use Y instead"
- **Rationale:** One sentence explaining why (optional but recommended)

### 1.4 Place the Rule

- Read the target file
- Find the appropriate section (or create one)
- Add the rule without disrupting existing content
- Report: what was added, where, and why that location was chosen

---

## STEP 2: Audit & Guard

**Scope:** Detect accidentally deleted rules and protected section integrity.
For SSOT layer violations (duplication across layers, misplaced config), use
`/ssot-audit` instead — it does deeper cross-layer analysis.

### 2.1 Read All Config Files

Read all CLAUDE.md, CLAUDE.local.md, and `.claude/rules/*.md` files in the project.

### 2.2 Check for Accidental Deletions

Compare current config files against recent git history:
```bash
git diff HEAD~5 -- CLAUDE.md .claude/rules/
```
Flag any removed lines that look like intentional rules (contain MUST, NEVER, ALWAYS, or structured constraint language) — these may be accidental deletions.

### 2.3 Check Protected Section Integrity

Verify that key sections in CLAUDE.md still exist:
- Build/test commands section
- Architecture pointers
- Rules reference table (if previously present)

### 2.4 Report

```
Audit Results:
  Files checked: N
  Accidental deletions suspected: M
  Protected section issues: K
  - [issue type]: [description] in [file]
  
  For SSOT layer analysis (duplicates, misplacements, bloat): run /ssot-audit
```

---

## CRITICAL RULES

- MUST route deterministic enforcement (style, linting, "always run X") to `/update-config` for hooks — Why: CLAUDE.md instructions are advisory; hooks are guaranteed
- MUST check for existing rules before placing new ones — Why: duplicate rules across files cause contradictions and waste context tokens
- MUST NOT duplicate the `configuration-ssot.md` placement taxonomy inline — reference it instead — Why: inline copies drift from the authoritative source
- MUST NOT place path-scoped constraints in CLAUDE.md — use `.claude/rules/` with `globs:` — Why: path-scoped rules in CLAUDE.md consume tokens on every prompt regardless of relevance
- MUST NOT modify `.claude/settings.json` directly — route to `/update-config` — Why: settings.json has specific structure requirements that update-config understands
- MUST preserve existing content when adding rules — never overwrite or reorganize without explicit user approval — Why: accidental content loss during rule placement is the primary failure mode
