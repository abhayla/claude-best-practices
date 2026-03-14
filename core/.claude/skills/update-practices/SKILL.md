---
name: update-practices
description: >
  Pull latest best practices from the hub into your project's .claude/ directory.
  Compares local files against hub registry, shows diffs, and copies updates.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--check-only] [--force]"
version: "1.0.0"
type: workflow
---

# Update Practices — Pull Latest from Hub

Compare local `.claude/` files against the best practices hub and update.

**Arguments:** $ARGUMENTS

---

## STEP 1: Read Sync Config

Read `.claude/sync-config.yml` to find:
- Hub repo URL
- Selected stacks
- Last sync version/timestamp

If no sync config exists, ask user for hub repo details.

## STEP 2: Fetch Hub Registry

```bash
gh api repos/{hub_repo}/contents/registry/patterns.json \
  -H "Accept: application/vnd.github.v3.raw" > /tmp/hub-registry.json
```

## STEP 3: Compare

For each pattern in the hub registry:
- Check if it exists locally
- Compare content hash
- Identify new, updated, or removed patterns

## STEP 4: Show Diffs

For each changed pattern, show:
- Pattern name and type
- What changed (new file, content update, etc.)
- Diff preview (if content update)

If `--check-only`, stop here and report.

## STEP 5: Apply Updates

For each approved update:
1. Download the file from hub
2. Copy to local `.claude/` directory
3. Update sync config timestamp

If `--force`, apply all without prompting.

## Report

```
Update Practices:
  Checked: N patterns
  New: X
  Updated: Y
  Unchanged: Z
  Applied: A
```
