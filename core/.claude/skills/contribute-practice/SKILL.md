---
name: contribute-practice
description: Push a pattern from your project to the best practices hub
version: "1.0.0"
allowed-tools: "Bash Read Grep Glob"
---

# Contribute Practice

Submit a pattern from this project to the Best Practices Hub for review.

## Usage
```
/contribute-practice <path-to-pattern>
```

Example: `/contribute-practice .claude/skills/my-skill/`

## Steps

1. Validate the pattern at the given path:
   - Check for YAML frontmatter (name, description, version)
   - Run secret scan (no API keys, passwords)
   - Verify file structure matches expected type (skill/agent/hook/rule)
2. Auto-detect category:
   - If in `core/` patterns -> category: core
   - If stack-specific -> detect from path or ask user
3. Check for duplicates in hub registry:
   ```bash
   gh api repos/{hub_repo}/contents/registry/patterns.json --jq '.content' | base64 -d
   ```
   - Level 1: Hash match (exact duplicate)
   - Level 2: Name/type match (potential update)
4. If duplicate found, ask: "Update existing pattern or create new?"
5. Create a PR to the hub repo:
   ```bash
   # Fork if needed, create branch, push files, create PR
   gh pr create --repo {hub_repo} --title "Add {name} {type}" \
     --body "Contributed from {project_repo}" \
     --label "contribution"
   ```
6. Report PR URL to user

## Notes
- Patterns must have frontmatter to be accepted
- Secret scan is mandatory -- blocks submission if secrets found
- Hub maintainer reviews and merges the PR
