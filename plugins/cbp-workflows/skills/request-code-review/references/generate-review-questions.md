# STEP 5: Generate Review Questions

### 5.1 Question Generation Rules

Good review questions are:
- **Specific** — Reference exact functions, lines, or decisions
- **Bounded** — Ask about one thing, not "is this okay?"
- **Contextual** — Explain what you considered and why you're unsure
- **Actionable** — The reviewer can answer without extensive research

### 5.2 Question Categories

| Category | Template | Example |
|----------|----------|---------|
| **Correctness** | "Is {approach} correct for {scenario}?" | "Is the retry logic in `OrderService.retry()` safe for concurrent requests? I'm concerned about duplicate charges if two retries execute simultaneously." |
| **Edge cases** | "What happens when {edge case}?" | "What happens when a user's session expires mid-payment? I added a check at line 85 but I'm not sure it covers the Stripe webhook race condition." |
| **Architecture** | "Is {pattern} the right approach for {goal}?" | "I used an event-driven approach for notifications instead of direct calls. Does this align with how we handle cross-service communication elsewhere?" |
| **Performance** | "Will {approach} scale for {load}?" | "The new query joins 3 tables. Is this acceptable for the /users endpoint which handles ~500 RPS, or should I denormalize?" |
| **Security** | "Does {change} introduce {risk}?" | "I'm passing the user ID in the JWT payload instead of looking it up. Does this create a privilege escalation risk if someone modifies their token?" |
| **Compatibility** | "Will {change} break {consumer}?" | "I renamed the `getData()` export to `fetchData()`. I found 3 internal consumers — are there external ones I'm missing?" |

### 5.3 Review Questions Output Format

```
REVIEW QUESTIONS
================

For: @security-team (or whoever owns auth)
  1. TokenService.ts#L78: The IP-binding check skips WebSocket connections
     because they don't carry the origin IP reliably. Is this acceptable,
     or should we enforce a different binding for WS connections?

For: @backend-team
  2. OrderService.ts#L142: The retry uses exponential backoff with jitter,
     but I'm not sure if the max retry count (3) is appropriate for payment
     operations. Our Stripe webhook has a 30s timeout — could 3 retries
     with backoff exceed that?

For: @dba / database owner
  3. Migration 0042: I added a `role` column with DEFAULT 'user'. The users
     table has ~2M rows. Will this lock the table during migration in
     Postgres, or does Postgres handle ADD COLUMN with DEFAULT without a
     full table rewrite?
```

---

