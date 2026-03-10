---
name: scan-repo
description: >
  Trigger a project scan for a specific repository.
  Normalizes repo input and triggers scan workflow.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<owner/repo or repo-url>"
---

# Scan Repo — Trigger Project Pattern Scan

Scan a GitHub repository for reusable Claude Code patterns.

**Input:** $ARGUMENTS

---

## STEP 1: Normalize Input

Accept various formats:
- `owner/repo` → use directly
- `https://github.com/owner/repo` → extract `owner/repo`
- `repo` → assume current org or ask for owner

## STEP 2: Trigger Scan

```bash
gh workflow run scan-projects.yml -f repo="$OWNER/$REPO"
```

## STEP 3: Confirm

```
Scan triggered:
  Repo: $OWNER/$REPO
  Workflow: scan-projects.yml
```

Optionally ask if the repo should be added to the tracked repos list in `config/repos.yml`.
