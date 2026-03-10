---
name: scan-url
description: Trigger an internet scan for a specific URL or topic
version: "1.0.0"
allowed-tools: "Bash Read"
---

# Scan URL

Trigger the Best Practices Hub to scan a URL or topic for new patterns.

## Usage
```
/scan-url <url-or-topic>
```

Examples:
- `/scan-url https://example.com/claude-tips`
- `/scan-url "jetpack compose testing patterns"`

## Steps

1. Detect input type:
   - If starts with `http://` or `https://` -> URL mode
   - Otherwise -> topic search mode

2. **URL mode:**
   ```bash
   gh workflow run scan-internet.yml --repo {hub_repo} -f url="{url}"
   ```
   Ask user: "Add this URL to the watchlist? (config/urls.yml)"

3. **Topic mode:**
   ```bash
   gh workflow run scan-internet.yml --repo {hub_repo} -f topic="{topic}"
   ```

4. Report: "Scan triggered. Check the hub repo for a new PR with findings."

## Notes
- Requires `gh` CLI authenticated with access to the hub repo
- Results appear as a PR on the hub repo (not immediate)
- User must review and merge the PR
