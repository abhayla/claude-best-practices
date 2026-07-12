---
name: receive-code-review
description: >
  Apply code review feedback by fetching PR comments, categorizing by severity,
  fixing in logical batches, responding to reviewers, tracking thread resolution,
  and generating re-review summaries. Use when addressing review feedback on a
  pull request. Pairs with /request-code-review to complete the collaboration cycle.
triggers:
  - receive-review
  - address-review
  - review-feedback
  - handle review
  - address comments
  - fix review
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<PR-number or PR-url> [--reviewer <name>] [--round <N>]"
version: "1.1.0"
type: workflow
---

# Receive & Address Code Review

Consume review feedback on a pull request, triage comments by severity, apply fixes, respond to reviewers, and prepare for re-review.

**PR:** $ARGUMENTS

---

## STEP 0: Fetch Review Comments

Before anything else, pull down all review data from the PR.

### 0.1 Authenticate and Fetch

```bash
# Verify GitHub CLI auth
gh auth status

# Fetch PR metadata
gh pr view $PR_NUMBER --json title,body,author,reviewDecision,reviews,state,headRefName,baseRefName

# Fetch all review comments (threaded discussions)
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --jq '.[] | {id, path, line: .original_line, body, user: .user.login, created_at, in_reply_to_id, subject_type}'

# Fetch top-level PR review summaries
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews \
  --jq '.[] | {id, user: .user.login, state, body, submitted_at}'
```

### 0.2 Parse Review State

Determine the overall review status:

| Review State | Meaning | Action |
|-------------|---------|--------|
| `APPROVED` | Reviewer approves — may still have minor comments | Address nits, then merge |
| `CHANGES_REQUESTED` | Reviewer blocks merge until changes are made | Must address all blocking comments |
| `COMMENTED` | Reviewer left feedback without formal approval/rejection | Triage and respond to each comment |
| `PENDING` | Review in progress, not yet submitted | Wait or ask reviewer to submit |

## STEP 1: Triage Comments

Categorize every review comment into one of four severity levels. This determines processing order and response format.


**Read:** `references/triage-comments.md` for detailed step 1: triage comments reference material.

## Review Triage: PR #$PR_NUMBER
Total comments: N

| # | Category | Reviewer | File | Line | Summary | Status |
|---|----------|----------|------|------|---------|--------|
| 1 | [BLOCKING] | @alice | src/auth.py | 42 | SQL injection in query builder | PENDING |
| 2 | [BLOCKING] | @alice | src/auth.py | 87 | Missing rate limit on login | PENDING |
| 3 | [SUGGESTION] | @alice | src/models.py | 15 | Use dataclass instead of dict | PENDING |
| 4 | [QUESTION] | @carol | src/api.py | 33 | Why custom serializer vs Pydantic? | PENDING |
| 5 | [QUESTION] | @carol | src/api.py | 91 | What happens on timeout? | PENDING |
| 6 | [NIT] | @bob | src/utils.py | 12 | Rename `x` to `count` | PENDING |
| 7 | [NIT] | @bob | src/utils.py | 45 | Missing trailing comma | PENDING |

Processing order: #1, #2 (must-fix) → #3 (suggestion) → #4, #5 (questions) → #6, #7 (nits)
```

## STEP 2: Address Must-Fix Comments (P0)

Handle all blocking comments first. These prevent merge.


**Read:** `references/address-must-fix-comments-p0.md` for detailed step 2: address must-fix comments (p0) reference material.

# Reply to a specific review comment thread
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --method POST \
  --field body="Fixed in \`a1b2c3d\`. Switched to parameterized queries." \
  --field in_reply_to=$COMMENT_ID
```

## STEP 3: Evaluate Suggestions (P1)

Suggestions require a decision: accept, adapt, or decline.


**Read:** `references/evaluate-suggestions-p1.md` for detailed step 3: evaluate suggestions (p1) reference material.

## STEP 4: Answer Questions (P2)

Questions deserve thoughtful, complete answers.


**Read:** `references/answer-questions-p2.md` for detailed step 4: answer questions (p2) reference material.

# Reply to a question comment
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --method POST \
  --field body="Using a custom serializer because this endpoint streams large responses..." \
  --field in_reply_to=$COMMENT_ID
```

---

## STEP 5: Batch Nits (P3)

Nits are low-severity style comments. Batch them into a single commit to keep history clean.


**Read:** `references/batch-nits-p3.md` for detailed step 5: batch nits (p3) reference material.

## STEP 6: Handle Disagreements

When you disagree with a reviewer's feedback, follow this protocol.


**Read:** `references/handle-disagreements.md` for detailed step 6: handle disagreements reference material.

## STEP 7: Multi-Reviewer Coordination

When multiple reviewers provide feedback, coordinate carefully.

### 7.1 Detect Conflicting Feedback

After triaging all comments, scan for conflicts:

```
## Reviewer Conflicts Detected

Conflict 1:
  @alice (line 42): "Use a factory pattern here"
  @bob (line 42): "Keep it simple — constructor is fine"

Conflict 2:
  @alice (models.py): "Split into separate modules"
  @carol (models.py): "Single module is easier to navigate"
```


**Read:** `references/reviewer-conflicts-detected.md` for detailed reviewer conflicts detected reference material.

## STEP 8: Review Thread Resolution

Track which discussion threads are resolved and which remain open.

### 8.1 Check Thread Status

```bash
# Fetch review threads with resolution status
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            isResolved
            comments(first: 1) {
              nodes {
                body
                author { login }
                path
                line
              }
            }
          }
        }
      }
    }
  }
' -f owner="{owner}" -f repo="{repo}" -F pr=$PR_NUMBER
```

### 8.2 Resolution Tracking Table

```
## Thread Resolution Status

| # | Thread | Reviewer | Status | Action Taken |
|---|--------|----------|--------|-------------|
| 1 | SQL injection in auth.py:42 | @alice | RESOLVED | Fixed in a1b2c3d |
| 2 | Rate limiting on login | @alice | RESOLVED | Fixed in e4f5g6h |
| 3 | Dataclass suggestion | @alice | RESOLVED | Accepted, see i7j8k9l |
| 4 | Serializer question | @carol | RESOLVED | Explained with benchmark |
| 5 | Timeout handling | @carol | RESOLVED | Fixed in m1n2o3p |
| 6 | Variable rename | @bob | RESOLVED | Fixed in q4r5s6t |
| 7 | Trailing comma | @bob | RESOLVED | Fixed in q4r5s6t |

Resolved: 7/7 — All threads addressed.
```

### 8.3 Pre-Re-Review Checklist

Before requesting re-review, verify:

- [ ] All `CHANGES_REQUESTED` comments have been addressed
- [ ] All discussion threads are resolved (or explicitly marked as "will not fix" with explanation)
- [ ] No unresolved conflicts between reviewers remain
- [ ] All new commits since last review are logically organized
- [ ] CI/tests pass on the latest push
- [ ] No unintended file changes (check `git diff --stat` against expected changes)

```bash
# Verify CI status
gh pr checks $PR_NUMBER

# Verify no unresolved threads
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes { isResolved }
        }
      }
    }
  }
' -f owner="{owner}" -f repo="{repo}" -F pr=$PR_NUMBER \
  --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved == false)) | length'
```

If the count is > 0, list the unresolved threads and address them before proceeding.

---

## STEP 9: Generate Re-Review Summary

After addressing all comments, generate a summary for the reviewer(s).

### 9.1 Summary Template

```
## Re-Review Summary: PR #$PR_NUMBER

Addressed **N** comments: **X** must-fix, **Y** suggestions, **Z** questions, **W** nits.


**Read:** `references/re-review-summary-pr-prnumber.md` for detailed re-review summary: pr #$pr_number reference material.

# Post re-review summary as a PR comment
gh pr comment $PR_NUMBER --body "$(cat <<'SUMMARY'
## Re-Review Summary

Addressed **N** comments: ...

[full summary from template above]

Ready for re-review. @alice @bob @carol
SUMMARY
)"

# Request re-review from specific reviewers
gh pr edit $PR_NUMBER --add-reviewer alice,bob,carol
```

---

## STEP 10: Review Iteration Protocol

Handle multi-round reviews by tracking which round each comment belongs to.

### 10.1 Round Tracking

Maintain a running log across review rounds:

```
## Review Iteration Log: PR #$PR_NUMBER


**Read:** `references/review-iteration-log-pr-prnumber.md` for detailed review iteration log: pr #$pr_number reference material.

# Check if a comment's referenced file/line was changed since the comment was posted
git log --since="$COMMENT_DATE" --oneline -- $COMMENT_FILE
```

If the file was modified after the comment was posted:
1. Re-read the comment in the context of the current code
2. If the comment is still relevant, address it
3. If the comment was already addressed by the intervening changes, reply: "This was addressed in {commit} — the code at this line has changed since your comment."

---

## STEP 11: Learning Extraction

After the review cycle is complete, extract patterns to improve future code quality.

### 11.1 Identify Recurring Feedback

After the PR is merged, analyze the review feedback for patterns:

```
## Review Learning Report: PR #$PR_NUMBER


**Read:** `references/review-learning-report-pr-prnumber.md` for detailed review learning report: pr #$pr_number reference material.

## Common Scenarios


**Read:** `references/common-scenarios.md` for detailed common scenarios reference material.

# Update the PR branch
git fetch origin
git rebase origin/main
# or: git merge origin/main

# Force push the rebased branch
git push --force-with-lease

# Re-run CI
gh pr checks $PR_NUMBER --watch
```

### Scenario 4: Bot/Automated Review Comments

When CI tools, linters, or bots leave review comments:

1. **Treat failing checks as must-fix** — CI failures block merge
2. **Fix linter warnings immediately** — these are deterministic and unambiguous
3. **For false positives** — add the appropriate ignore annotation with a justifying comment
4. **Do not argue with bots** — fix the code or configure the rule

### Scenario 5: Review from Unfamiliar Reviewer

When a reviewer who is not familiar with the codebase leaves comments:

1. **Be patient and thorough in explanations** — they lack context you have
2. **Point to existing patterns** — "This follows the convention in `src/services/UserService.ts`"
3. **Do not dismiss their feedback** — fresh eyes often catch real issues that familiarity blinds you to
4. **If their suggestion contradicts established conventions**, explain the convention and point to where it is documented

---

## PR Comment Interaction Reference

### Fetching Comments

```bash
# All review comments (inline code comments)
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments

# Top-level PR comments (conversation tab)
gh api repos/{owner}/{repo}/issues/$PR_NUMBER/comments

# Review summaries
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews

# Specific review's comments
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews/$REVIEW_ID/comments
```

### Replying to Comments

```bash
# Reply to an inline review comment thread
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --method POST \
  -f body="Fixed in \`a1b2c3d\`." \
  -F in_reply_to=$COMMENT_ID

# Post a top-level PR comment
gh pr comment $PR_NUMBER --body "Re-review summary: ..."
```

### Resolving Threads

```bash
# Resolve a review thread (requires thread ID from GraphQL)
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { isResolved }
    }
  }
' -f threadId="$THREAD_ID"
```

### Requesting Re-Review

```bash
# Add reviewers
gh pr edit $PR_NUMBER --add-reviewer alice,bob

# Remove yourself as reviewer (if you were self-reviewing)
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/requested_reviewers \
  --method DELETE -f reviewers='["your-username"]'
```

---

## Failure Modes

| Failure Mode | Prevention |
|-------------|-----------|
| Start fixing before triaging all comments, miss blocking items | Step 1 mandatory triage gate — MUST categorize all comments before any code change |
| Silently follow one reviewer when feedback conflicts | Step 7 conflict detection + explicit escalation protocol |
| Request re-review with open threads, waste reviewer time | Step 8.3 pre-re-review checklist + GraphQL thread count verification |
| One commit per comment clutters git history | Step 5 batches nits into single commit; Step 2 groups related must-fixes |
| PR argument beyond 2 rounds blocks progress | Step 6 escalation protocol caps at 2 reply rounds |

## CRITICAL RULES

- **Triage before fixing** — NEVER start making changes before categorizing all comments. Processing order matters.
- **Fix must-fix items first** — Blocking comments are always the highest priority. Do not address nits while must-fix items remain.
- **Never dismiss without explanation** — Every declined suggestion or disagreement MUST include reasoning with evidence. "I disagree" is not a valid response.
- **Batch nits into one commit** — Do not create a separate commit for each nit. Keep git history clean.
- **Verify all threads are resolved before requesting re-review** — Use the GraphQL API to check thread status. Requesting re-review with open threads wastes the reviewer's time.
- **Surface multi-reviewer conflicts explicitly** — NEVER silently follow one reviewer over another when their feedback conflicts.
- **Do not over-respond** — Match response length to comment severity. Nits get one word ("Fixed"). Questions get a paragraph. Must-fix items get an explanation of the fix.
- **Track rounds, not just comments** — In multi-round reviews, always note which round a comment came from and do not re-address resolved items.
- **CI must pass before re-review** — NEVER request re-review when CI is failing. Fix CI first.
- **Extract learnings** — After every review cycle, identify recurring patterns and propose rules or automation to prevent them in future PRs.

## MUST NOT DO

- MUST NOT start fixing code before completing the triage in Step 1
- MUST NOT create one commit per review comment — group related changes logically
- MUST NOT ignore comments from any reviewer, even if another reviewer approved
- MUST NOT silently pick one reviewer's suggestion when reviewers conflict
- MUST NOT request re-review with unresolved threads or failing CI
- MUST NOT respond to nits with lengthy explanations — keep it proportional
- MUST NOT continue arguing in PR comments beyond 2 rounds — escalate instead
- MUST NOT apply suggestions you disagree with without voicing your concern — silent compliance builds resentment and hides technical debt
- MUST NOT merge with `CHANGES_REQUESTED` status without the requesting reviewer's explicit approval to proceed
