# STEP 1: Triage Comments

### 1.1 Comment Categories

| Category | Icon | Criteria | Examples | Priority |
|----------|------|----------|----------|----------|
| **Must-Fix** | `[BLOCKING]` | Security vulnerability, correctness bug, broken API contract, data loss risk, missing error handling for critical path | "This SQL query is injectable", "Race condition on shared counter", "This breaks backward compatibility" | P0 — Fix immediately |
| **Suggestion** | `[SUGGESTION]` | Better approach, performance improvement, alternative pattern, code organization | "Consider using a builder pattern here", "This could be O(n) instead of O(n^2)", "Extract this into a helper" | P1 — Evaluate and decide |
| **Question** | `[QUESTION]` | Clarification request, "why did you...", understanding intent, asking about trade-offs | "Why not use the existing UserService?", "Is this intentional?", "What happens if X is null?" | P2 — Respond with explanation |
| **Nit** | `[NIT]` | Naming preference, formatting, typo, minor style, comment wording | "Rename `tmp` to `tempFile`", "Missing period in docstring", "Prefer `const` over `let` here" | P3 — Batch into single commit |

### 1.2 Classification Rules

Apply these rules to classify ambiguous comments:

1. **If a comment mentions security, auth, injection, or data loss** — always classify as Must-Fix, even if the reviewer frames it casually
2. **If a comment says "nit:" or "minor:" explicitly** — classify as Nit regardless of content
3. **If a comment ends with a question mark and does not suggest a change** — classify as Question
4. **If a comment proposes an alternative approach with "consider", "what about", "have you thought about"** — classify as Suggestion
5. **If a comment points out a bug or incorrect behavior** — classify as Must-Fix
6. **If a comment references a broken test or CI failure** — classify as Must-Fix
7. **If a reviewer requests changes (CHANGES_REQUESTED) and only has nit-level comments** — still treat the review as blocking; the reviewer may have standards that treat nits as required

### 1.3 Build the Triage Table

After classifying all comments, output the triage summary:

```
