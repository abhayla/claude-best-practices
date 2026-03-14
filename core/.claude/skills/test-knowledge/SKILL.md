---
name: test-knowledge
description: >
  Use when debugging test failures, choosing fixtures, handling platform quirks,
  or after resolving a tricky test issue worth remembering. Self-improving knowledge
  base of testing facts. Modes: search, add, review, seed, digest, stats.
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

Knowledge is stored in `.claude/skills/test-knowledge/knowledge.md` as a structured markdown file.

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
grep -i "$QUERY" .claude/skills/test-knowledge/knowledge.md
```
Return matching entries with context.

### Add Mode
Append a new entry in the standard format to `knowledge.md`.

### Seed Mode
Create initial `knowledge.md` with category headers and a few generic entries.

### Stats Mode
Count entries per category and report.
