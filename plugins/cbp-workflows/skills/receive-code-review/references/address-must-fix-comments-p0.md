# STEP 2: Address Must-Fix Comments (P0)

### 2.1 For Each Must-Fix Comment

1. **Read the referenced file and line** — understand the current code
2. **Understand the reviewer's concern** — what is the specific risk or bug?
3. **Determine the fix approach** — what is the minimal change that addresses the concern?
4. **Implement the fix** — make the code change
5. **Verify the fix** — invoke `/auto-verify` to run targeted tests on the changed files and confirm no regressions:
   ```
   Skill("auto-verify", args="--files <fixed_files>")
   ```
   If `auto-verify` reports failures, invoke `/fix-loop` to iterate:
   ```
   Skill("fix-loop", args="retest_command: <project_test_cmd> max_iterations: 3")
   ```
6. **Write a response** — explain what was done (include verification status)

### 2.2 Must-Fix Response Template

For each must-fix comment, reply on the PR thread:

```
Fixed in {commit_sha}.

{Brief explanation of the fix — 1-2 sentences.}

{If the fix differs from what the reviewer suggested, explain why.}
```

**Example responses:**

```
Fixed in a1b2c3d.

Switched from string interpolation to parameterized queries for all SQL calls in
`QueryBuilder`. Also added input validation on the `table_name` parameter since
it cannot be parameterized.
```

```
Fixed in e4f5g6h.

Added rate limiting (10 attempts per 15 minutes per IP) on the login endpoint
using the existing RateLimiter middleware. Chose IP-based rather than
account-based limiting to also protect against credential-stuffing across
different accounts.
```

### 2.3 Reply via GitHub CLI

```bash
