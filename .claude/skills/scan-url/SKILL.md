---
name: scan-url
description: >
  Trigger an internet scan for a specific URL or topic.
  Detects URL vs topic mode and triggers appropriate scan workflow.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<url or topic>"
version: "1.0.0"
---

# Scan URL — Trigger Internet Pattern Scan

Scan a URL or topic for Claude Code best practices.

**Input:** $ARGUMENTS

---

## STEP 1: Detect Mode

- If `$ARGUMENTS` looks like a URL (starts with http/https) → **URL mode**
- Otherwise → **Topic mode**

## STEP 2: Trigger Scan

### URL Mode
```bash
gh workflow run scan-internet.yml -f url="$URL"
```

### Topic Mode
```bash
gh workflow run scan-internet.yml -f topic="$TOPIC"
```

## STEP 3: Verify Trigger

Check that the workflow dispatched successfully:

```bash
gh run list --workflow=scan-internet.yml --limit=1
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
  Mode: URL/Topic
  Input: $ARGUMENTS
  Workflow: scan-internet.yml
  Monitor: gh run watch <run-id>
```

Optionally ask if the URL/topic should be added to the permanent watchlist in `config/urls.yml` or `config/topics.yml`.

---

## CRITICAL RULES

- MUST validate URL format before triggering — reject obviously malformed URLs
- MUST distinguish URL mode from topic mode correctly — URLs start with `http://` or `https://`
- MUST report the workflow run URL so the user can monitor progress
