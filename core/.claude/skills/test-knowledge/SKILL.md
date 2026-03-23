---
name: test-knowledge
description: >
  Manage a self-improving knowledge base of testing patterns and lessons learned.
  Use when debugging test failures, choosing fixtures, handling platform quirks,
  or recording a resolved test issue. Modes: search, add, review, seed, digest, stats.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode> [query or entry]"
version: "1.0.0"
type: workflow
---

# Test Knowledge — Self-Improving Testing Knowledge Base

A searchable knowledge base of testing patterns and lessons learned.

**Arguments:** $ARGUMENTS

---

## Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| `search <query>` | Find relevant knowledge | Search entries by keyword |
| `add <entry>` | Record new knowledge | Add a new testing insight |
| `review` | Review recent entries | Check for accuracy and relevance |
| `seed` | Initialize knowledge base | Create initial structure |
| `digest` | Generate summary | Produce a digest of key patterns |
| `stats` | Show statistics | Count entries by category |

---

## Knowledge Categories

| Code | Category | Examples |
|------|----------|---------|
| FIX | Fix Patterns | Common fixes for recurring test failures |
| PLT | Platform | OS/environment-specific quirks |
| TMG | Timing | Race conditions, timeouts, async issues |
| FLK | Flaky Tests | Known flaky tests and workarounds |
| DAT | Test Data | Fixtures, factories, seed data patterns |
| ENV | Environment | Setup, teardown, configuration |
| ERR | Error Patterns | Common error messages and solutions |
| INF | Infrastructure | CI/CD, runners, resource limits |
| RUN | Run Patterns | How to run specific test subsets |
| MIG | Migration | Database/schema test migration patterns |

## Storage

Knowledge is stored in `.claude/test-knowledge.md` in the project root's `.claude/` directory (not inside the skill template). This keeps project-specific knowledge separate from the distributed skill definition.

## Entry Format

```markdown
### [CATEGORY] Brief title
- **Context:** When this applies
- **Pattern:** The insight or fix
- **Example:** Code or command example
- **Added:** [date]
```

---

## STEP 1: Detect Mode

Parse `$ARGUMENTS` to determine the mode.

## STEP 2: Execute Mode

### Search Mode
```bash
grep -i "$QUERY" .claude/test-knowledge.md
```
Return matching entries with context.

### Add Mode
Append a new entry in the standard format to `.claude/test-knowledge.md`.

### Seed Mode
Create initial `.claude/test-knowledge.md` with category headers and a few generic entries.

### Review Mode
Read all entries in `.claude/test-knowledge.md`, flag any that are outdated (referenced APIs changed, patterns superseded), and suggest removals or updates.

### Digest Mode
Summarize the knowledge base into a concise digest grouped by category. Output the top 3 most-referenced patterns and any recurring themes.

### Stats Mode
Count entries per category and report.

---

## MUST DO

- Always use the standard entry format (category code, context, pattern, example, date)
- Always store knowledge in `.claude/test-knowledge.md` — never inside the skill template directory
- Always check for duplicate entries before adding (search by title keywords first)
- Always include a concrete code or command example in every entry

## MUST NOT DO

- MUST NOT store project-specific knowledge inside `core/.claude/` — use the project's own `.claude/` directory
- MUST NOT add speculative entries — only record patterns that solved a real problem
- MUST NOT delete entries without review — use review mode to flag candidates first
