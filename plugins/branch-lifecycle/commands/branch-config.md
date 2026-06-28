---
description: View or change branch-lifecycle plugin settings (on/off switches for auto-commit, auto-merge, the branch menu, stale-branch reporting, concurrency guard, secret scan).
---

# Branch-Lifecycle Config

Show and edit the toggles that control the `branch-lifecycle` plugin. Settings live in
`branch-lifecycle-settings.json` and are re-read every session — no reinstall needed.

## STEP 1: Locate the active settings file

Resolution order (first that exists wins; otherwise the shipped default is used):

1. `<project>/.claude/branch-lifecycle-settings.json` — per-project
2. `~/.claude/branch-lifecycle-settings.json` — per-user global default
3. `<plugin>/branch-lifecycle-settings.default.json` — shipped default (read-only reference)

```bash
proj="$(git rev-parse --show-toplevel 2>/dev/null)/.claude/branch-lifecycle-settings.json"
glob="$HOME/.claude/branch-lifecycle-settings.json"
for f in "$proj" "$glob"; do [ -f "$f" ] && echo "ACTIVE: $f" && cat "$f" && break; done
```

If neither exists, tell the user the shipped defaults are in effect (everything ON) and that
editing begins by copying the default into the project: copy
`<plugin>/branch-lifecycle-settings.default.json` to `<project>/.claude/branch-lifecycle-settings.json`.

## STEP 2: Apply the requested change

Map the user's plain-English request to a key and write it back as valid JSON (preserve the other
keys). Keys and effects:

| Key | When false / value | Effect |
|---|---|---|
| `enabled` | false | master OFF — every hook becomes a no-op |
| `auto_commit_and_push` | false | no auto-commit each turn |
| `auto_push` | false | commit locally but do not push |
| `auto_open_pr` | false | do not open a PR |
| `auto_merge` | false | open the PR but do not arm auto-merge (you click merge) |
| `branch_choice_menu` | false | suppress the first-edit branch menu nudge |
| `stale_branch_report` | false | do not list stale (>N h) branches at session start |
| `stale_branch_hours` | N | staleness threshold in hours (default 24) |
| `concurrency_guard` | false | do not warn when a 2nd session shares the tree |
| `concurrency_stale_minutes` | N | how long a session lock counts as live (default 30) |
| `secret_scan_cmd` | "cmd" | use your own scanner instead of the bundled grep scan |

After writing, confirm the change and remind the user it takes effect on the next session (hooks
re-read the file each session).

## CRITICAL RULES

- MUST write valid JSON and preserve keys the user did not change.
- MUST NOT edit the shipped `branch-lifecycle-settings.default.json` — write the per-project or
  per-user copy instead.
- MUST tell the user a pre-set environment variable (e.g. `AUTO_MERGE=0 claude ...`) always
  overrides the JSON for that session.
