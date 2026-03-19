# Deployment Awareness and Final Summary

## Deployment Awareness

If the project has continuous deployment configured, monitor the deployment after merge.

### Detect CD Configuration

```bash
# Check for common CD configuration files
CD_DETECTED=false

if [ -f .github/workflows/deploy.yml ] || [ -f .github/workflows/cd.yml ]; then
  echo "GitHub Actions CD workflow detected."
  CD_DETECTED=true
fi

if [ -f vercel.json ] || [ -f netlify.toml ]; then
  echo "Platform-managed CD detected (Vercel/Netlify)."
  CD_DETECTED=true
fi

if [ -f Dockerfile ] && [ -f docker-compose.yml ]; then
  echo "Docker-based deployment detected."
  CD_DETECTED=true
fi

if [ -f fly.toml ] || [ -f render.yaml ] || [ -f railway.json ]; then
  echo "PaaS deployment detected."
  CD_DETECTED=true
fi

if [ "$CD_DETECTED" = false ]; then
  echo "No CD configuration detected — skipping deployment monitoring."
fi
```

### Monitor Deployment Status

```bash
if [ "$CD_DETECTED" = true ]; then
  # Check if a deployment workflow was triggered
  echo "Checking for deployment workflow runs..."

  # Wait a moment for the workflow to trigger
  sleep 5

  # List recent workflow runs on the base branch
  gh run list --branch "$BASE_BRANCH" --limit 3 --json name,status,conclusion,databaseId \
    --jq '.[] | "\(.name): \(.status) (\(.conclusion // "in progress"))"'
fi
```

### Watch for Deployment Failures

```bash
if [ "$CD_DETECTED" = true ]; then
  # Get the most recent deployment run
  DEPLOY_RUN_ID=$(gh run list --branch "$BASE_BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId')

  if [ -n "$DEPLOY_RUN_ID" ]; then
    echo "Latest deployment run: $DEPLOY_RUN_ID"
    echo "Monitor with: gh run watch $DEPLOY_RUN_ID"
    echo ""
    echo "If deployment fails:"
    echo "  1. Check logs: gh run view $DEPLOY_RUN_ID --log-failed"
    echo "  2. Revert if needed: git revert -m 1 $MERGE_SHA && git push origin $BASE_BRANCH"
  fi
fi
```

### Manual Deployment Commands

```bash
if [ "$CD_DETECTED" = false ]; then
  echo "If manual deployment is needed, common commands:"
  echo ""
  echo "  # Heroku"
  echo "  git push heroku $BASE_BRANCH:main"
  echo ""
  echo "  # AWS (via CLI)"
  echo "  aws deploy create-deployment --application-name <app> --deployment-group <group>"
  echo ""
  echo "  # Docker"
  echo "  docker build -t <image> . && docker push <image>"
  echo ""
  echo "  # SSH"
  echo "  ssh <server> 'cd /app && git pull && <restart-command>'"
fi
```

---

## Final Summary

Output a comprehensive summary of everything that was done.

### Summary Template

```
=== Branch Finished ===

PR:            #<PR_NUMBER> — <PR_TITLE>
Branch:        <BRANCH> -> <BASE_BRANCH>
Merge commit:  <MERGE_SHA>
Method:        squash / merge / rebase

Pre-merge:
  - Review:    APPROVED
  - CI:        all checks passed
  - Conflicts: none

Commit cleanup:
  - <N> commits squashed into <M>
  - Fixup commits removed: <count>

Changelog:
  - Entry added under [<CATEGORY>] in CHANGELOG.md
  - Or: No CHANGELOG.md found — skipped

Worktree:
  - Cleaned up worktree at <path>
  - Or: No worktree — skipped

Post-merge verification:
  - Tests:  <X> passed, 0 failed
  - Build:  success

Branch cleanup:
  - Local branch deleted
  - Remote branch deleted
  - Stale references pruned

Cross-PR dependencies:
  - Closed issues: #<issue1>, #<issue2>
  - Unblocked PRs: #<pr1>, #<pr2>
  - Or: No dependencies found

Release:
  - Tagged: <NEW_TAG>
  - Or: No release tag needed

Deployment:
  - Auto-deploy triggered — monitor with: gh run watch <ID>
  - Or: No CD configured — manual deployment may be needed

Rollback (if needed):
  git revert -m 1 <MERGE_SHA> && git push origin <BASE_BRANCH>

=== Done ===
```
