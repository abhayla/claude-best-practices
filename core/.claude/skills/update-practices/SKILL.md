---
name: update-practices
description: Pull latest best practices from the hub into your project
version: "1.0.0"
allowed-tools: "Bash Read Write Grep Glob"
---

# Update Practices

Sync the latest patterns from the Best Practices Hub into this project.

## Steps

1. Read `.claude/sync-config.yml` to find hub repo and selected stacks
2. Fetch the hub's `registry/patterns.json` via GitHub API:
   ```bash
   gh api repos/{hub_repo}/contents/registry/patterns.json --jq '.content' | base64 -d
   ```
3. Compare each pattern's hash with local files
4. For patterns with changes, show the user:
   - Pattern name, type, and version change
   - Changelog entry
   - Diff preview
5. On user approval, copy updated files from hub
6. Update `sync-config.yml` with new timestamp
7. Suggest: `git add .claude/ && git commit -m "chore: sync best practices from hub"`

## Notes
- Never overwrite without showing the diff first
- Skip patterns listed in `.secretsignore`
- If no `sync-config.yml` exists, suggest running bootstrap first
