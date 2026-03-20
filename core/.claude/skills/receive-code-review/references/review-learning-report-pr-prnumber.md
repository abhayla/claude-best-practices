# Review Learning Report: PR #$PR_NUMBER

### Recurring Patterns Detected
1. Missing error handling — @alice flagged 2 instances of unhandled exceptions
   Action: Propose a `.claude/rules/` rule requiring error handling on all
   external calls

2. Variable naming — @bob flagged 3 instances of single-letter variable names
   Action: Check if linter has a rule for minimum variable name length

3. Missing input validation — @alice flagged SQL injection and missing rate limit
   Action: Propose a security checklist for auth-related endpoints

### One-Time Items (no action needed)
- Dataclass vs dict discussion — specific to this data model
- Serializer choice — architectural decision, documented in code comment

### Proposed Actions
- [ ] Add rule: "All external API/DB calls MUST have error handling"
- [ ] Configure linter: minimum variable name length = 3 characters
- [ ] Create security checklist for auth endpoints
```

### 11.2 Feed Back to Rules

If a pattern appears 2+ times across different PRs, it is a candidate for automation:

| Pattern Frequency | Action |
|------------------|--------|
| Same feedback 2x in one PR | Note it in the learning report |
| Same feedback in 2+ PRs | Propose a `.claude/rules/` rule |
| Same feedback in 3+ PRs | Propose a linter rule or pre-commit hook |
| Same feedback in 5+ PRs | Escalate — the team needs a convention decision |

### 11.3 Invoke Learn & Improve

```
Skill("learn-n-improve", args="session")
```

Feed the review learning report into the learn-and-improve skill to update project conventions.

---

