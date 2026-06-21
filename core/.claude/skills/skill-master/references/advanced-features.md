# Skill Master — Advanced Features

Supplementary reference for skill-master's advanced capabilities: keyword search, self-update, and routing examples.

## Keyword Search (Step 9)

When the user's request does not match any skill well, provide a keyword search.

### Full-Text Search

Search across all discovered skill descriptions, triggers, and step content:

```bash
# Search all SKILL.md files for the user's keywords
grep -r -l "{keyword}" core/.claude/skills/*/SKILL.md
```

Use `Grep` to search all SKILL.md files for the user's keywords. Report matches with the relevant context line.

### Present Search Results

```
SEARCH RESULTS for "database migration":

  1. /fastapi-db-migrate (3 matches)
     - Description: "...database migration..."
     - Step 2: "Run alembic to generate migration..."
     - Trigger: "migrate database"

  2. /pg-query (1 match)
     - Description: "...PostgreSQL query patterns..."

  No exact match? Consider:
    - /writing-skills to create a custom skill for this workflow
    - /brainstorm to explore the problem before choosing a skill
```

### Fuzzy Matching

When exact keyword search yields no results, try partial matches:

1. Split multi-word keywords and search each word independently
2. Search for synonyms: "test" also matches "verify", "check", "validate"
3. Search skill names (not just descriptions) for partial prefix matches

---

## Self-Update and Re-Scan (Step 10)

Ensure the catalog is always fresh.

### Re-Scan on Every Invocation

Every time skill-master is invoked, re-run Step 1 in full. Do NOT cache or reuse a previous catalog. Skills may have been added, removed, or modified since the last invocation.

### Detect Changes

If session state exists from a previous invocation, compare the new catalog against the stored snapshot:

```
CATALOG CHANGES SINCE LAST SCAN:
  + /new-skill-name (added — description: "...")
  - /removed-skill (no longer found on disk)
  ~ /modified-skill (description changed)
  = {N} skills unchanged
```

### Handle Missing Skills in Active Workflows

If a skill that is part of an active workflow has been removed from disk:

1. Alert the user: "Skill `/removed-skill` is no longer available on disk."
2. Suggest a replacement by searching the catalog for similar descriptions
3. Offer to skip the removed skill and continue the workflow

---

## Routing Decision Examples

These examples show how the scoring algorithm routes requests. The specific skills mentioned are illustrative — actual routing always uses the live catalog from Step 1.

### Example 1: Direct Trigger Match

```
User: "I need to debug a failing test"
Scan: Found skill with trigger "debug" → /systematic-debugging (score: 100)
Route: Direct match, high confidence
Action: Invoke /systematic-debugging with args "failing test"
```

### Example 2: Stack-Specific Routing

```
User: "Run my Android unit tests"
Scan: Found skill with prefix "android-" and "test" in name → /android-run-tests (score: 90)
Also matched: /auto-verify (score: 30, generic testing)
Route: Stack-specific match wins
Action: Invoke /android-run-tests
```

### Example 3: Ambiguous Request

```
User: "Help me with this code"
Scan: Multiple low-confidence matches:
  /implement (score: 25) — "code" appears in description
  /request-code-review (score: 25) — "code" appears in description
  /systematic-debugging (score: 20) — general development tool
Route: Ambiguous — ask user to clarify
Action: Present top 3, ask "Are you trying to: build something, review code, or fix a bug?"
```

### Example 4: Workflow Request

```
User: "I want to build a new authentication system"
Scan: "new" + "build" + large scope → Task type: New Feature
Workflow suggestion:
  1. /brainstorm — Explore auth approaches (OAuth, JWT, session-based)
  2. /writing-plans — Break chosen approach into tasks
  3. /executing-plans — Implement each task
  4. /security-audit — Verify auth security
  5. /request-code-review — Get team feedback
  6. /branching — Prepare PR
Action: Present workflow, ask user to confirm or modify
```

### Example 5: No Match with Search Fallback

```
User: "Generate API documentation from my code"
Scan: No skill scores above 40
Closest: /brainstorm (score: 15) — "documentation" is not a trigger
Search: Grep "documentation" across all SKILL.md files → 0 results
Action: Report no match, suggest /writing-skills to create an api-docs skill
```

### Example 6: Conflict Resolution

```
User: "I have a plan, help me build it"
Scan: Two strong matches:
  /implement (score: 65) — "build" trigger
  /executing-plans (score: 60) — "plan" + "execute" in description
Action: Present comparison table, recommend /executing-plans because user said "I have a plan"
```
