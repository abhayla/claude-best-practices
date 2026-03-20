# STEP 5: Batch Nits (P3)

### 5.1 Process All Nits Together

1. Read all nit comments
2. Apply each fix (rename, formatting, typo, etc.)
3. Commit all nit fixes in a single commit

**Commit message format:**
```
style: address review nits

Addresses nit comments from @{reviewer1}, @{reviewer2}.
- Renamed `x` to `count` in utils.py
- Fixed trailing comma in models.py
- Updated docstring wording in api.py
```

### 5.2 Nit Response Template

For each nit, reply with a brief acknowledgment:

```
Fixed.
```

or

```
Updated — good catch.
```

Do NOT write multi-paragraph responses to nit comments. Keep responses proportional to the comment's significance.

### 5.3 When to Push Back on Nits

Occasionally a "nit" is actually a meaningful style decision. Push back if:

- The naming convention is already established in the codebase (reviewer may be unfamiliar)
- The "nit" would require changes across many files for consistency
- The "nit" contradicts the project's linter or formatter configuration

In these cases, respond:

```
This follows the existing convention in the codebase — see {file}:{line} for
the same pattern. Keeping as-is for consistency. Happy to discuss if you think
the convention itself should change (separate PR).
```

---

