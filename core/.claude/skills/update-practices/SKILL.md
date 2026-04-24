---
name: update-practices
description: >
  Pull latest best practices from the hub into your project's .claude/ directory.
  Compares local files (agents, skills, rules, hooks, and shipped configs under
  .claude/config/) against hub registry + hub config directory, shows diffs,
  and copies updates.
  Use when your local patterns are outdated or after hub registry changes.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--check-only] [--force]"
version: "1.1.0"
type: workflow
---

# Update Practices — Pull Latest from Hub

Compare local `.claude/` files against the best practices hub and update. Covers
two scopes: **registry-listed patterns** (agents, skills, rules, hooks) AND
**shipped configs** under `core/.claude/config/` on the hub (which are NOT in
the pattern registry but are nevertheless authoritative templates that downstream
projects should sync to get new schema versions or key additions).

**Arguments:** $ARGUMENTS

---

## STEP 1: Read Sync Config

Read `.claude/sync-config.yml` to find:
- Hub repo URL (e.g., `abhayla/claude-best-practices`)
- Selected stacks
- Last sync version/timestamp

If no sync config exists, ask user for hub repo details.

## STEP 2: Fetch Hub Registry + Hub Config Inventory

```bash
# Pattern registry (agents, skills, rules, hooks)
gh api repos/{hub_repo}/contents/registry/patterns.json \
  -H "Accept: application/vnd.github.v3.raw" > /tmp/hub-registry.json

# Hub-shipped configs (NOT in registry — separate distributable set)
gh api repos/{hub_repo}/contents/core/.claude/config \
  -H "Accept: application/vnd.github.v3+json" > /tmp/hub-config-list.json
```

The config listing returns a directory entry array; filter to `.yml`/`.yaml`/`.json`
files, skip `.example` templates.

## STEP 3: Compare — Patterns

For each pattern in the hub registry:
- Check if it exists locally at `.claude/<type-dir>/<name>`
- Compare the hub `hash` field against the local file's normalized SHA256
- Identify new, updated, or removed patterns

## STEP 3b: Compare — Configs (NEW in v1.1.0)

For each config file in the hub's `core/.claude/config/` listing (excluding
`.example` templates):
- Target local path: `.claude/config/<filename>`
- Fetch the hub file content via:
  ```bash
  gh api repos/{hub_repo}/contents/core/.claude/config/<filename> \
    -H "Accept: application/vnd.github.v3.raw" > /tmp/hub-config-<name>
  ```
- Compare hub content to the local file (if present)
  - If local file MISSING → classify as NEW (`schema_version` initialization)
  - If content differs → classify as UPDATED (diff schema_version too, surface
    it prominently in STEP 4 because it means the skill callers expect new keys)
  - If content matches → UNCHANGED

This is the critical fix for the 2026-04-24 downstream gap: skills updated to
new schema versions but config files on disk stayed at old schema, producing
silent key-shape mismatches at runtime.

## STEP 4: Show Diffs

For each changed pattern or config, show:
- Pattern/config name and type
- What changed (new file, content update, schema version bump)
- Diff preview (if content update)
- **Schema-version bump flag**: if a config's `schema_version` changed between
  local and hub, print a prominent warning. Downstream skills that read the
  config may dispatch with wrong key shapes until the update is applied.

If `--check-only`, stop here and report.

## STEP 5: Apply Updates

For each approved update:
1. Download the file from hub (pattern OR config — same `gh api` + raw accept)
2. Copy to local `.claude/` directory (creating `.claude/config/` if missing)
3. Update `.claude/sync-manifest.json` with the new hub_hash + synced_at timestamp
4. Update sync config timestamp

If `--force`, apply all without prompting.

## STEP 6: Report

```
Update Practices:
  Patterns:
    Checked: N
    New: X
    Updated: Y
    Unchanged: Z
  Configs (shipped under core/.claude/config/):
    Checked: M
    New: A
    Updated (incl. schema bumps): B
    Unchanged: C
  Applied: <total applied>
```

If any schema_version changed on a config, print after the table:

```
⚠ Schema version changes detected:
  .claude/config/test-pipeline.yml: <old> → <new>
  (Skills that read this config may now expect new keys. Re-read the hub's
   release notes for the driving PR if unsure.)
```

---

## CRITICAL RULES

- MUST sync configs in addition to registry-listed patterns — skills updated
  to a new schema will silently fail against stale configs otherwise
- MUST write `.claude/sync-manifest.json` entries for every applied update
  (both patterns and configs) so subsequent runs detect drift
- MUST NOT copy `.example` template files — those are user-customizable
  starting points, not canonical hub state
- MUST NOT silently overwrite a config with schema_version changes when
  `--force` is NOT set — the user SHOULD see the schema bump notice
