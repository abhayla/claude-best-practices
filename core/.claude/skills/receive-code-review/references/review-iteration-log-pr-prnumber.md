# Review Iteration Log: PR #$PR_NUMBER

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
