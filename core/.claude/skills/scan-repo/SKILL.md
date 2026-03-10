---
name: scan-repo
description: Trigger a project scan for a specific repository
version: "1.0.0"
allowed-tools: "Bash Read"
---

# Scan Repo

Trigger the Best Practices Hub to scan a GitHub repository for patterns.

## Usage
```
/scan-repo <owner/repo>
```

Example: `/scan-repo abhayla/KKB`

## Steps

1. Normalize repo input:
   - Accept `owner/repo`, `https://github.com/owner/repo`, or `github.com/owner/repo`
   - Extract `owner/repo` format

2. Trigger scan workflow:
   ```bash
   gh workflow run scan-projects.yml --repo {hub_repo} -f repo="{owner/repo}"
   ```

3. Ask user: "Add this repo to the tracked list? (config/repos.yml)"
   - If yes, ask which stacks apply
   - Suggest based on repo contents (look for `build.gradle`, `requirements.txt`, etc.)

4. Report: "Scan triggered. Check the hub repo for a new PR with extracted patterns."

## Notes
- Requires `gh` CLI with access to both the hub and target repos
- The scan clones the target repo's `.claude/` directory only (sparse checkout)
- Results appear as a PR on the hub repo
