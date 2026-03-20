# Common Scenarios

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
