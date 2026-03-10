---
name: skill-factory
description: >
  Use when you suspect repeated workflows could become skills, when session logs
  show recurring multi-step patterns, or when the user asks to analyze their
  workflow for automation opportunities. Scans logs, detects patterns, proposes
  and creates new skills.
argument-hint: "[scan|propose <name>|create <name>|list]"
---

# Skill Factory — Pattern Detector & Skill Creator

Analyze session logs for repeated workflows and propose new skills.

**Arguments:** $ARGUMENTS

---

## MODE SELECTION

| Pattern | Mode | Action |
|---------|------|--------|
| (no args) or `scan` | Scan | Analyze logs, detect patterns, rank by impact |
| `propose <name>` | Propose | Generate full SKILL.md preview for a detected pattern |
| `create <name>` | Create | Write skill files after user approval |
| `list` | List | Show all existing skills with descriptions |

---

## MODE: scan

### Step 1: Gather Data

Scan these sources for repeated multi-step patterns:

```
.claude/logs/workflow-sessions.log     — Workflow step sequences
.claude/logs/test-evidence/*.json      — Test run patterns
.claude/logs/fix-loop/*/               — Fix-loop session patterns
.claude/workflow-state.json            — Current session state
```

Also check session transcripts if available:
```
~/.claude/projects/*/sessions/*.jsonl  — Full session logs (large, scan selectively)
```

### Step 2: Pattern Detection

Look for sequences that appear 3+ times:

| Signal | What to Look For |
|--------|-----------------|
| Repeated tool sequences | Same 3+ tools called in order across sessions |
| Repeated commands | Same bash commands run in sequence |
| Repeated file edits | Same files edited together |
| Repeated error→fix cycles | Same error resolved the same way |
| Repeated skill chains | Same skills invoked in sequence |

### Step 3: Classification

For each pattern, classify using the CLAUDE.md taxonomy:

| Category | When |
|----------|------|
| **Skill** | Repeatable multi-step workflow with clear start/end |
| **Agent** | Autonomous sub-task that can run in isolation |
| **Hook** | Automatic trigger on tool events |
| **CLAUDE.md Rule** | Static instruction, no logic |

Focus on **Skill** candidates (this tool creates skills, not agents/hooks).

### Step 4: Conflict Check

Before proposing, check for existing coverage:

```bash
ls .claude/skills/        # Existing skills
ls .claude/agents/        # Existing agents
ls .claude/hooks/         # Existing hooks
```

Compare each candidate against existing skills by:
- Name similarity
- Functional overlap (does an existing skill already do this?)
- Partial coverage (could an existing skill be enhanced instead?)

### Step 5: Output

Present findings as a ranked table:

```
| # | Pattern | Frequency | Category | Priority | Name | Description |
|---|---------|-----------|----------|----------|------|-------------|
| 1 | ... | 5x | Skill | HIGH | /name | What it does |
```

Priority = frequency x steps x novelty (not covered by existing skill).

---

## MODE: propose

Generate a complete SKILL.md preview for the named pattern.

### Step 1: Validate

1. Confirm the pattern was identified in a previous `scan` or is described by the user
2. Check no existing skill with the same name exists
3. If name conflicts, suggest alternative names

### Step 2: Generate SKILL.md

Follow the skill structure from `superpowers:writing-skills`:

```markdown
---
name: <name>
description: >
  Use when <specific triggering conditions>
argument-hint: "<args if any>"
---

# <Name> - <Brief Title>

<Overview>

**Arguments:** $ARGUMENTS

## When to Use
<Bullet list of triggers>

## Steps
<Numbered procedure>

## Common Mistakes
<What goes wrong>
```

### Step 3: Preview

Display the full SKILL.md content and ask for user approval before writing.

---

## MODE: create

Write skill files to disk after user approval.

### Safety Rules

1. **Max 3 skills per invocation** — prevents runaway creation
2. **Always show preview** — never write without user seeing content
3. **No overwrite** — if `.claude/skills/<name>/SKILL.md` exists, STOP and warn
4. **Conflict detection** — check all existing skills for functional overlap
5. **Update CLAUDE.md** — add new skill to the skills list line after creation

### Steps

1. Confirm user has reviewed the `propose` output
2. Create directory: `.claude/skills/<name>/`
3. Write `SKILL.md`
4. Update CLAUDE.md skills list (add to alphabetical position in the list)
5. Confirm creation with file path

---

## MODE: list

Show all existing skills with their descriptions:

1. Glob `.claude/skills/*/SKILL.md`
2. For each, extract `name` and `description` from YAML frontmatter
3. Display as table sorted alphabetically

```
| # | Skill | Description |
|---|-------|-------------|
| 1 | /adb-test | Autonomous Android E2E testing via ADB... |
| 2 | /auto-verify | Post-change verification loop... |
| ... |
```

---

## PATTERN EXAMPLES

Common patterns that might be detected:

| Pattern | Proposed Skill | Description |
|---------|---------------|-------------|
| pytest fail → read error → fix → rerun | `/fix-backend-test` | Single-file backend test fix cycle |
| gradle build → install → adb test | `/quick-device-test` | Fast device test without full E2E |
| seed DB → run test → verify data | `/db-seed-verify` | Database seeding verification |
| read issue → explore code → plan fix | `/investigate-issue` | Issue analysis without implementation |

---

## CONSTRAINTS

- Only propose skills for patterns with 3+ occurrences
- Never propose skills that duplicate existing ones
- Always check `.claude/skills/`, `.claude/agents/`, `.claude/hooks/` for conflicts
- Skill names: lowercase, hyphens only, no special characters
- Max description length: 500 characters
