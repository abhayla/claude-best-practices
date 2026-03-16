---
name: apply-selections
description: >
  Apply user-selected patterns from a nice-to-have PR by parsing checkbox state
  in the PR body and removing unchecked files from the branch. Works with PRs
  created by recommend.py --provision that contain checkbox lists of optional patterns.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<pr-url>"
version: "1.0.0"
---

# Apply Selections from Nice-to-Have PR

Parse a GitHub PR body with checkbox lists, identify which patterns the user checked,
and remove unchecked pattern files from the PR branch. This finalizes a nice-to-have
PR so only desired patterns remain before merge.

**Arguments:** $ARGUMENTS

The PR URL is required. It must point to a PR created by `recommend.py --provision`
with the nice-to-have tier checkbox format.

---

## STEP 1: Fetch PR Details

Fetch the PR body and branch info:

```bash
# Extract owner/repo and PR number from URL
PR_URL="$1"
PR_NUMBER=$(echo "$PR_URL" | grep -oP '\d+$')
REPO=$(echo "$PR_URL" | grep -oP '[\w-]+/[\w-]+(?=/pull)')

# Fetch PR details
gh api repos/$REPO/pulls/$PR_NUMBER --jq '{body: .body, head_ref: .head.ref, head_sha: .head.sha}'
```

Store the PR body, branch name, and HEAD SHA for subsequent steps.

## STEP 2: Parse Checkbox State

Parse the PR body to extract checked and unchecked patterns:

1. Find all lines matching `- [x]` (checked) and `- [ ]` (unchecked)
2. Extract the pattern name from each line (backtick-wrapped name after the checkbox)
3. Determine the pattern type from the section header (`### Skills`, `### Rules`, `### Agents`)

**Expected PR body format:**
```markdown
### Skills
- [x] `security-audit` — description
- [ ] `docker-optimize` — description

### Rules
- [x] `testing` — description
- [ ] `workflow` — description

### Agents
- [ ] `docs-manager` — description
```

Build two lists:
- `keep`: patterns with `[x]` — these stay on the branch
- `remove`: patterns with `[ ]` — these get deleted from the branch

## STEP 3: Map Patterns to File Paths

For each pattern in the `remove` list, determine its file path on the branch:

| Type | Path Pattern |
|------|-------------|
| skill | `.claude/skills/{name}/SKILL.md` (and entire directory) |
| rule | `.claude/rules/{name}.md` |
| agent | `.claude/agents/{name}.md` |

Verify each file exists on the branch before attempting deletion:

```bash
gh api repos/$REPO/contents/.claude/skills/$NAME/SKILL.md?ref=$BRANCH --jq '.sha' 2>/dev/null
```

## STEP 4: Delete Unchecked Files

For each file to remove, delete it via the GitHub Contents API:

```bash
# For each file to delete
FILE_SHA=$(gh api repos/$REPO/contents/$FILE_PATH?ref=$BRANCH --jq '.sha')
gh api repos/$REPO/contents/$FILE_PATH \
  -X DELETE \
  -f message="chore: remove unselected pattern $NAME" \
  -f sha="$FILE_SHA" \
  -f branch="$BRANCH"
```

For skills (which are directories), delete all files in the directory:

```bash
# List all files in the skill directory
gh api repos/$REPO/contents/.claude/skills/$NAME?ref=$BRANCH --jq '.[].path' | while read FILE; do
  FILE_SHA=$(gh api repos/$REPO/contents/$FILE?ref=$BRANCH --jq '.sha')
  gh api repos/$REPO/contents/$FILE \
    -X DELETE \
    -f message="chore: remove unselected skill $NAME" \
    -f sha="$FILE_SHA" \
    -f branch="$BRANCH"
done
```

## STEP 5: Update PR Body

Update the PR body to reflect the final state — replace unchecked items with
a "Removed" note and add a summary of what was kept vs removed:

```bash
# Build updated body
NEW_BODY="## Applied Selections\n\nKept: N patterns\nRemoved: M patterns\n\n### Kept\n..."

gh api repos/$REPO/pulls/$PR_NUMBER \
  -X PATCH \
  -f body="$NEW_BODY"
```

## STEP 6: Summary

Print the results:

```
Applied selections to PR #N on owner/repo:
  Kept:    [N] patterns ([list])
  Removed: [M] patterns ([list])

PR updated: $PR_URL
Ready to merge.
```

---

## CRITICAL RULES

- NEVER delete files that are checked (`[x]`) — only delete unchecked (`[ ]`) patterns
- NEVER modify files that belong to other tiers (must-have, improved) — this skill only operates on the nice-to-have PR branch
- If the PR body does not contain the expected checkbox format, STOP and report the error — do not guess
- Always verify file existence on the branch before attempting deletion — the file may have already been removed
- Use the GitHub Contents API for deletions (not git force-push) to preserve commit history
- If ALL patterns are unchecked, close the PR instead of leaving an empty branch
