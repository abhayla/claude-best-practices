# Routing Decision Examples

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

---

