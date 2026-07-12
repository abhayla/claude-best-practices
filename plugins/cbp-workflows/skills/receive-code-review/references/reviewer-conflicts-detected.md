# Reviewer Conflicts Detected

### 7.2 Resolve Conflicts

Do NOT silently pick one reviewer's suggestion over another. Surface the conflict:

```
@alice @bob — You have different suggestions for the initialization pattern
on line 42:
  - @alice suggests factory pattern for extensibility
  - @bob suggests keeping the constructor for simplicity

My take: {your analysis of both perspectives and which you lean toward, with
reasoning}.

Happy to go either way — let me know if you have a preference or want to
discuss.
```

### 7.3 Priority Rules for Conflicting Feedback

When you must move forward without waiting for consensus:

| Rule | Example |
|------|---------|
| Security > Style | If one reviewer says "add auth check" and another says "keep it simple," add the auth check |
| Codebase convention > Personal preference | If the codebase uses pattern X, follow it even if a reviewer prefers pattern Y |
| Correctness > Performance | If one reviewer points out a bug and another suggests an optimization that would mask it, fix the bug |
| Explicit CHANGES_REQUESTED > COMMENTED | A blocking review takes priority over a non-blocking one |

---

