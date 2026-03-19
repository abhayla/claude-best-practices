---
name: scan-repo
description: >
  Trigger a project scan for a specific repository.
  Normalizes repo input and triggers scan workflow.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<owner/repo or repo-url>"
version: "1.0.0"
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

## STEP 3: Verify Trigger

Check that the workflow dispatched successfully:

```bash
gh run list --workflow=scan-projects.yml --limit=1
```

| Status | Action |
|--------|--------|
| `queued` or `in_progress` | Report success, provide run URL |
| Not found | Verify `gh` is authenticated and workflow exists: `gh workflow list` |
| Error | Report the error message and suggest manual trigger via GitHub UI |

## STEP 4: Post-Scan Follow-Up

Report the trigger result:

```
Scan triggered:
  Repo: $OWNER/$REPO
  Workflow: scan-projects.yml
  Monitor: gh run watch <run-id>
```

Optionally ask if the repo should be added to the tracked repos list in `config/repos.yml`.

---

## CRITICAL RULES

- MUST validate the repo format before triggering — reject malformed inputs
- MUST NOT trigger scans for private repos without confirming the user has access
- MUST report the workflow run URL so the user can monitor progress
