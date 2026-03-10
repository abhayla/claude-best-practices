---
name: test-knowledge
description: >
  Use when debugging test failures, choosing fixtures, handling platform quirks,
  or after resolving a tricky test issue worth remembering. Searchable knowledge
  base of testing facts accumulated over time. Modes: search, add, review, seed,
  digest, stats.
argument-hint: "<search topic|add \"fact\"|review category|seed|digest|stats>"
---

# Test Knowledge — Self-Improving Testing Knowledge Base

Persistent, searchable knowledge base for testing facts. Grows over time as issues are resolved.

**Arguments:** $ARGUMENTS

**Knowledge file:** `.claude/skills/test-knowledge/knowledge.md` (committed to git)

---

## MODE SELECTION

Parse `$ARGUMENTS` to determine mode:

| Pattern | Mode | Action |
|---------|------|--------|
| `search <topic>` or just `<topic>` | Search | Grep knowledge.md for matching entries |
| `add "<fact>"` | Add | Append new entry with auto-categorization |
| `review <category>` | Review | Show all entries in a category |
| `seed` | Seed | One-time scan of project docs to populate initial entries |
| `digest` | Digest | Analyze recent test evidence for new learnings |
| `stats` | Stats | Show counts per category and recency |
| (no args) | Stats | Default to stats mode |

---

## CATEGORIES

10 categories with 3-letter codes:

| Code | Category | Description |
|------|----------|-------------|
| FIX | Fixtures | Test client selection, setup patterns, conftest gotchas |
| PLT | Platform | SQLite vs PostgreSQL, Windows vs Linux, emulator API level |
| TMG | Timing | Timeouts, delays, race conditions, waitUntil patterns |
| FLK | Flaky | Intermittent failures, retry strategies, test isolation |
| DAT | Data | Test data, seed scripts, factories, Sharma profile |
| ADB | ADB | Emulator commands, screencap issues, display warnings |
| ERR | Errors | Common error messages and their root causes |
| INF | Infrastructure | CI/CD, hooks, workflow state, test runners |
| RUN | Running | How to run specific test subsets, commands, flags |
| MIG | Migration | Room DB versions, Alembic, schema changes |

---

## MODE: search

1. Read `.claude/skills/test-knowledge/knowledge.md`
2. Search for entries matching the topic (case-insensitive)
3. Display matching entries with their full content
4. If no matches, suggest related categories

**Example output:**
```
Found 3 entries matching "fixtures":

[FIX-001] Backend test fixture selection (2026-02-04)
  Source: backend/tests/CLAUDE.md
  Tags: #pytest #client #auth
  Use `client` for most tests (pre-authenticated). Use `unauthenticated_client`
  for 401 tests. Use `authenticated_client` for JWT verification flow.
  Use `db_session` for direct service/repository tests.

[FIX-002] ...
```

---

## MODE: add

1. Parse the fact from arguments (text after `add`)
2. Auto-categorize based on keywords:
   - fixture/client/conftest → FIX
   - sqlite/postgresql/windows/emulator/api level → PLT
   - timeout/delay/race/wait → TMG
   - flaky/intermittent/retry → FLK
   - seed/factory/sharma/test data → DAT
   - adb/screencap/emulator/display → ADB
   - error/exception/stack trace → ERR
   - ci/hook/workflow/runner → INF
   - run/command/gradle/pytest → RUN
   - room/alembic/migration/schema → MIG
3. Determine next ID: scan knowledge.md for highest `[CAT-NNN]`, increment
4. Append entry to knowledge.md in the correct category section
5. Confirm addition with the assigned ID

**Entry format:**
```markdown
### [CAT-NNN] Title (YYYY-MM-DD)
**Source:** where this was learned
**Tags:** #tag1 #tag2
Content of the fact.
```

---

## MODE: review

1. Read knowledge.md
2. Filter entries by the specified category code (e.g., `FIX`, `PLT`)
3. Display all entries in that category
4. Show count and date range

---

## MODE: seed

**One-time operation** to populate knowledge.md from existing project documentation.

1. Check if knowledge.md already has entries beyond the initial seed
2. If already seeded (18+ entries), warn and ask for confirmation
3. Scan these sources for testing facts:
   - `CLAUDE.md` troubleshooting table
   - `backend/tests/CLAUDE.md` fixture guide
   - `.claude/rules/testing.md` test infrastructure
   - Memory files in `~/.claude/projects/*/memory/`
   - `docs/testing/E2E-Testing-Prompt.md` test profiles
4. Extract facts and write to knowledge.md

---

## MODE: digest

Analyze recent test evidence for new learnings:

1. Scan `.claude/logs/test-evidence/` for recent `run-*.json` and `rerun-*.json` files
2. Scan `.claude/logs/fix-loop/` for recent session evidence
3. For each resolved failure, extract:
   - Root cause
   - Fix applied
   - Category
4. Check if the learning already exists in knowledge.md (dedup by keywords)
5. Present new learnings and ask for confirmation before adding
6. Append confirmed entries to knowledge.md

---

## MODE: stats

1. Read knowledge.md
2. Count entries per category
3. Show total count, oldest/newest entry dates
4. Identify categories with 0 entries (gaps)

**Example output:**
```
Test Knowledge Stats:
  Total: 18 entries (oldest: 2026-02-04, newest: 2026-03-09)

  FIX  Fixtures        ███████  3
  PLT  Platform         █████   3
  TMG  Timing           ███     2
  FLK  Flaky            ███     1
  DAT  Data             █████   2
  ADB  ADB              ███     2
  ERR  Errors           █████   2
  INF  Infrastructure   ███     1
  RUN  Running          ███     1
  MIG  Migration        ███     1

  Gaps: none
```

---

## INTEGRATION POINTS

These skills should suggest `/test-knowledge` when relevant:

| Skill | When | Suggestion |
|-------|------|------------|
| `/fix-loop` | On RESOLVED | "Consider: `/test-knowledge add \"<root cause>\"`" |
| `/reflect` | In session mode | "Run `/test-knowledge digest` to capture learnings" |
| `/run-backend-tests` | On failure | "Try `/test-knowledge search <error keyword>`" |
| `/run-e2e` | On failure | "Try `/test-knowledge search <error keyword>`" |

These are suggestions only — the skills themselves are not modified.
