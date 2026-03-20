# Cross-PR Dependency Resolution

After the merge, check if this PR was blocking other work and unblock it.

## 8.1 Check for Linked Issues

```bash
# Get issues that this PR closes
CLOSING_ISSUES=$(gh pr view "$PR_NUMBER" --json closingIssuesReferences --jq '
  [.closingIssuesReferences[].number] | join(" ")
')

if [ -n "$CLOSING_ISSUES" ]; then
  echo "This PR closes issues: $CLOSING_ISSUES"
  for ISSUE in $CLOSING_ISSUES; do
    # Verify the issue is closed
    STATE=$(gh issue view "$ISSUE" --json state --jq '.state')
    echo "  Issue #$ISSUE: $STATE"

    # If not auto-closed, close it manually
    if [ "$STATE" != "CLOSED" ]; then
      gh issue close "$ISSUE" -c "Closed by PR #$PR_NUMBER"
    fi
  done
else
  echo "No linked issues found."
fi
```

## 8.2 Check for Dependent PRs

```bash
# Search for PRs that mention this PR or its branch as a dependency
DEPENDENT_PRS=$(gh pr list --search "depends on #$PR_NUMBER OR blocked by #$PR_NUMBER" \
  --json number,title --jq '.[] | "#\(.number): \(.title)"')

if [ -n "$DEPENDENT_PRS" ]; then
  echo "Dependent PRs that may now be unblocked:"
  echo "$DEPENDENT_PRS"
  echo ""
  echo "Action: Review these PRs — they may be ready to merge now."
else
  echo "No dependent PRs found."
fi
```

## 8.3 Notify Dependent PRs

```bash
# Comment on dependent PRs to notify them that the blocker is resolved
if [ -n "$DEPENDENT_PRS" ]; then
  echo "$DEPENDENT_PRS" | while IFS= read -r line; do
    DEP_PR=$(echo "$line" | grep -oP '#\K\d+')
    gh pr comment "$DEP_PR" --body "Dependency resolved: PR #$PR_NUMBER has been merged. This PR may now be unblocked."
  done
fi
```
