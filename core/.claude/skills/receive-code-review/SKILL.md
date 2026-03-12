---
name: receive-code-review
description: >
  Consume, triage, and act on code review feedback systematically. Fetches PR review
  comments, categorizes them by severity, applies fixes in logical batches, responds
  to reviewers, tracks thread resolution, and generates re-review summaries. Pairs
  with /request-code-review to complete the collaboration cycle.
triggers:
  - receive-review
  - address-review
  - review-feedback
  - handle review
  - address comments
  - fix review
  - review response
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<PR-number or PR-url> [--reviewer <name>] [--round <N>]"
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

### 0.3 Identify Reviewers

List all reviewers and their review states:

```
Reviewers:
  @alice — CHANGES_REQUESTED (3 comments)
  @bob   — APPROVED (1 nit)
  @carol — COMMENTED (2 questions)
```

If `--reviewer` flag is provided, filter to only that reviewer's comments. Otherwise, process all reviewers.

---

## STEP 1: Triage Comments

Categorize every review comment into one of four severity levels. This determines processing order and response format.

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

### 1.4 Handle Edge Cases

| Situation | Action |
|-----------|--------|
| Comment is unclear or ambiguous | Classify as Question and ask for clarification |
| Comment references outdated code (file was already changed) | Note as "Potentially stale" and verify before acting |
| Comment on a line you did not change | Classify normally but note "Out of scope — pre-existing issue" |
| Duplicate comments from different reviewers | Group them and address once |
| Comment is a +1 or "looks good" | Skip — not actionable |
| Comment contains both a question and a suggestion | Split into two entries in the triage table |

---

## STEP 2: Address Must-Fix Comments (P0)

Handle all blocking comments first. These prevent merge.

### 2.1 For Each Must-Fix Comment

1. **Read the referenced file and line** — understand the current code
2. **Understand the reviewer's concern** — what is the specific risk or bug?
3. **Determine the fix approach** — what is the minimal change that addresses the concern?
4. **Implement the fix** — make the code change
5. **Verify the fix** — run related tests to confirm the fix works and does not break anything
6. **Write a response** — explain what was done

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
# Reply to a specific review comment thread
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --method POST \
  --field body="Fixed in \`a1b2c3d\`. Switched to parameterized queries." \
  --field in_reply_to=$COMMENT_ID
```

### 2.4 Commit Strategy for Must-Fixes

Group related must-fix items into logical commits:

| Scenario | Commit Strategy |
|----------|----------------|
| Two must-fix comments on the same file, same concern | Single commit |
| Must-fix comments on different files, same theme (e.g., "add validation") | Single commit with descriptive message |
| Must-fix comments addressing unrelated issues | Separate commits |

**Commit message format:**
```
fix: address review — {concise description}

Addresses review comments #{id1}, #{id2} from @{reviewer}.
{Brief explanation of what changed and why.}
```

---

## STEP 3: Evaluate Suggestions (P1)

Suggestions require a decision: accept, adapt, or decline.

### 3.1 Decision Framework

For each suggestion, evaluate:

| Factor | Question |
|--------|----------|
| **Correctness** | Is the suggested approach more correct than the current one? |
| **Consistency** | Does the suggestion match existing patterns in this codebase? |
| **Complexity** | Does the suggestion simplify or complicate the code? |
| **Scope** | Is the suggestion within the scope of this PR, or should it be a follow-up? |
| **Trade-offs** | What does the suggestion gain and what does it cost? |

### 3.2 Accept a Suggestion

When the suggestion improves the code:

```
Good point — updated to {approach}. See {commit_sha}.

{Optional: brief note on how you adapted the suggestion if it was not applied exactly as proposed.}
```

**Example:**
```
Good point — updated to use a dataclass instead of the raw dict. This also let
me drop the manual validation since dataclass fields handle type checking. See
a1b2c3d.
```

### 3.3 Decline a Suggestion

When you disagree with the suggestion, always explain with evidence:

```
Considered this — keeping the current approach because {reason}.

{Evidence supporting your decision: benchmarks, documentation links, precedent
in the codebase, or constraints the reviewer may not be aware of.}

{If applicable: "Happy to discuss further or try a different approach if you
feel strongly about this."}
```

**Example — declining with benchmarks:**
```
Considered this — keeping the current approach because the HashMap lookup is
O(1) amortized and this function is called ~10K times per request in our hot
path. The BTreeMap suggestion would give us sorted iteration (which we don't
need here) at the cost of O(log n) lookups.

Benchmark results on the target dataset:
  HashMap: 1.2ms avg
  BTreeMap: 3.8ms avg

Happy to discuss further if there is a correctness concern I am missing.
```

**Example — declining with scope:**
```
Agreed this would be a good improvement, but it touches the serialization layer
which is shared with 3 other endpoints. I would prefer to handle this in a
follow-up PR to keep this change focused.

Created issue #456 to track the refactor.
```

### 3.4 Adapt a Suggestion

When the reviewer's direction is right but the specific approach needs adjustment:

```
Agreed with the direction — went with a slightly different approach: {what you
did instead}. The reviewer suggested {their approach}, but {reason for
adaptation}. See {commit_sha}.
```

---

## STEP 4: Answer Questions (P2)

Questions deserve thoughtful, complete answers.

### 4.1 Question Response Guidelines

| Principle | Description |
|-----------|-------------|
| **Be specific** | Reference exact file paths, line numbers, and function names |
| **Show your reasoning** | Explain the trade-off you considered, not just the conclusion |
| **Link to evidence** | Point to docs, tests, or other code that supports your answer |
| **Acknowledge valid concerns** | If the question reveals a gap, say so and address it |
| **Keep it concise** | Answer the question asked, do not over-explain unrelated context |

### 4.2 Question Response Template

```
{Direct answer to the question.}

{Supporting evidence: code reference, documentation link, or architectural
reasoning.}

{If the question reveals a valid concern: "Good catch — I've added
{test/comment/guard} to make this clearer. See {commit_sha}."}
```

**Example — explaining a design decision:**
```
Using a custom serializer here instead of Pydantic because this endpoint
streams large responses (10K+ items) and we need incremental serialization.
Pydantic's `model_dump()` materializes the entire list in memory before
serializing.

See the benchmark in `tests/bench_serialization.py` — the custom serializer
uses ~4MB peak memory vs ~200MB for Pydantic on our production dataset.

Added a comment in the code explaining this trade-off (see a1b2c3d).
```

**Example — question reveals a gap:**
```
On timeout, the current code silently drops the connection. You are right that
this is not great — the caller has no way to distinguish between a timeout and
a successful empty response.

Added a `TimeoutError` exception with a descriptive message and a retry hint.
Also added a test for the timeout path. See a1b2c3d.
```

### 4.3 Reply via GitHub CLI

```bash
# Reply to a question comment
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --method POST \
  --field body="Using a custom serializer because this endpoint streams large responses..." \
  --field in_reply_to=$COMMENT_ID
```

---

## STEP 5: Batch Nits (P3)

Nits are low-severity style comments. Batch them into a single commit to keep history clean.

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

## STEP 6: Handle Disagreements

When you disagree with a reviewer's feedback, follow this protocol.

### 6.1 Disagreement Response Protocol

**Round 1 — Present your reasoning:**

```
I see the concern, but I believe the current approach is better here because:

1. {Reason with evidence — benchmarks, docs, codebase precedent}
2. {Additional supporting point}

{If applicable: "Here is an alternative that might address your concern
differently: {alternative}"}
```

**Round 2 — If the reviewer pushes back:**

```
I understand your perspective. Let me address the specific points:

{Point-by-point response to the reviewer's counter-arguments.}

{Propose a compromise if possible: "What if we {compromise approach}? This
addresses {reviewer's concern} while preserving {your concern}."}
```

**Round 3 — Escalate:**

If disagreement persists after two rounds, do NOT continue arguing in the PR thread.

```
We have different perspectives on this. To avoid blocking the PR, I suggest one
of:
1. Sync offline (call/Slack) to discuss the trade-offs in real-time
2. Bring in a third reviewer (@{suggested_person}) for a tiebreaker
3. Merge with a TODO and revisit in a follow-up PR with more data

@{reviewer} — which option works best for you?
```

### 6.2 Disagreement Anti-Patterns

| Anti-Pattern | Why It Fails | Instead |
|-------------|-------------|---------|
| "I disagree" with no explanation | Dismissive, creates friction | Always provide evidence |
| Silently applying a change you disagree with | Resentment, technical debt | Explain your concern, then comply if overruled |
| "I'll fix it later" without creating a tracking issue | It never gets fixed | Create the issue now, link it in the response |
| Arguing beyond 2 rounds in PR comments | Wastes everyone's time, blocks the PR | Escalate per protocol above |
| Citing authority ("I'm more senior") | Toxic, irrelevant to code quality | Argue with evidence, not credentials |
| Making changes without telling the reviewer | Breaks trust, reviewer cannot track | Always reply before or after making changes |

---

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

### Must-Fix Changes
- Fixed SQL injection in `auth.py` — switched to parameterized queries (a1b2c3d)
- Added rate limiting on login endpoint (e4f5g6h)

### Accepted Suggestions
- Converted raw dict to dataclass in `models.py` (i7j8k9l)

### Declined Suggestions
- Kept HashMap over BTreeMap in `cache.py` — see comment thread for benchmark data

### Questions Answered
- Explained custom serializer choice (streaming performance)
- Addressed timeout handling concern — added TimeoutError (m1n2o3p)

### Nit Fixes
- All nits addressed in single commit (q4r5s6t)

### Commits Since Last Review
1. `a1b2c3d` — fix: parameterized SQL queries in auth
2. `e4f5g6h` — fix: add rate limiting on login
3. `i7j8k9l` — refactor: use dataclass for UserProfile
4. `m1n2o3p` — fix: add timeout error handling
5. `q4r5s6t` — style: address review nits

All threads resolved. CI passing. Ready for re-review.
```

### 9.2 Post the Summary

```bash
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

### Round 1 (2026-03-10)
Reviewers: @alice (CHANGES_REQUESTED), @bob (APPROVED w/ nits)
Comments: 7 total (2 must-fix, 1 suggestion, 2 questions, 2 nits)
Status: All addressed in commits a1b2c3d..q4r5s6t

### Round 2 (2026-03-11)
Reviewers: @alice (COMMENTED)
Comments: 2 total (1 suggestion on new code from round 1, 1 question)
Status: Addressed in commits u7v8w9x, y1z2a3b
New issues introduced: None

### Round 3 (2026-03-12)
Reviewers: @alice (APPROVED)
Comments: 0
Status: Merged
```

### 10.2 Rules for Multi-Round Reviews

| Rule | Description |
|------|-------------|
| **Do not re-address resolved items** | If a comment was resolved in round 1, do not revisit it in round 2 unless the reviewer explicitly reopens it |
| **Distinguish new comments from follow-ups** | New comments on new code (written in response to round 1 feedback) are new items — triage them fresh |
| **Track scope creep** | If round 2+ introduces comments on code that was not changed in this PR, flag it: "This is pre-existing — should I address it here or in a follow-up?" |
| **Detect review fatigue** | If a reviewer is requesting increasingly minor changes across rounds, suggest: "Should we merge and address remaining items in a follow-up?" |
| **Keep a changelog** | Maintain the iteration log above so reviewers can quickly see what changed between rounds |

### 10.3 Stale Comment Detection

When new commits are pushed between review rounds, some comments may reference outdated code:

```bash
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

## Common Scenarios

### Scenario 1: Large Review (20+ Comments)

When a PR receives a large number of comments:

1. **Do not address comments one at a time** — this creates notification noise for reviewers
2. **Triage all comments first** (Step 1)
3. **Batch related fixes** — group by file, by theme, or by reviewer
4. **Post a single summary** at the end rather than replying to each comment individually
5. **Push all fix commits together** so the reviewer sees one update notification

### Scenario 2: Review on Stale PR

When a review arrives on a PR that has been open for a while:

1. **Rebase or merge the base branch** before addressing comments
2. **Re-run CI** to verify the PR still passes
3. **Check if comments are still valid** — some may have been addressed by changes merged to main
4. Address remaining comments normally

```bash
# Update the PR branch
git fetch origin
git rebase origin/main
# or: git merge origin/main

# Force push the rebased branch
git push --force-with-lease

# Re-run CI
gh pr checks $PR_NUMBER --watch
```

### Scenario 3: Reviewer Requests Major Redesign

When a reviewer suggests fundamentally rethinking the approach:

1. **Do not start rewriting immediately** — this may not be the consensus view
2. Ask other reviewers if they agree with the redesign direction
3. If consensus supports redesign:
   - Close the current PR (do not delete the branch)
   - Create a new PR with the redesigned approach
   - Reference the old PR: "Supersedes #N based on review feedback"
4. If opinions are split:
   - Follow the disagreement protocol (Step 6)
   - Escalate if needed

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
