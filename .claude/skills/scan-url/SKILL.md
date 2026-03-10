---
name: scan-url
description: >
  Trigger an internet scan for a specific URL or topic.
  Detects URL vs topic mode and triggers appropriate scan workflow.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<url or topic>"
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

## STEP 3: Confirm

```
Scan triggered:
  Mode: URL/Topic
  Input: $ARGUMENTS
  Workflow: scan-internet.yml
```

Optionally ask if the URL/topic should be added to the permanent watchlist in `config/urls.yml` or `config/topics.yml`.
