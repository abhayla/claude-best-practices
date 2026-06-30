# Installing the hub's plugins in a downstream project

The hub ships an in-tree plugin marketplace at `plugins/.claude-plugin/marketplace.json`
(marketplace name: **`claude-best-practices`**). It currently distributes three plugins:

| Plugin | Install where |
|--------|---------------|
| `prompt-auto-enhance` | any project (prompt diagnose-and-strengthen pipeline) |
| `branch-lifecycle` | any git repo (auto branch/commit/push/PR/merge lifecycle + session save/restore) |
| `auto-google-analytics` | only web/frontend projects that need GA4 |

> **Plugin commands are session-bound to the target project.** All `/plugin …` steps below
> MUST run inside the *downstream project's own* Claude Code session — they cannot be driven
> from the hub session.

## 1. Register the marketplace (once per project)

Point at the directory that *contains* `.claude-plugin/` — that is `plugins/`, **not** the repo root:

```
/plugin marketplace add D:\Abhay\VibeCoding\claude-best-practices\plugins
```

## 2. Install the plugin(s)

Syntax is `<plugin>@<marketplace-name>`:

```
/plugin install prompt-auto-enhance@claude-best-practices
/plugin install branch-lifecycle@claude-best-practices
/plugin install auto-google-analytics@claude-best-practices
```

Or run `/plugin` and browse the `claude-best-practices` marketplace interactively.

## 3. Verify

`/plugin` lists installed plugins; their skills surface as `/<plugin>:<skill>`. Start a fresh
session if a newly-installed plugin's commands don't appear immediately.

## 4. Update

```
/plugin update <name>
```

A plugin updates when its `plugin.json` `version` field is bumped. If no `version` is set, the
git commit SHA is used and every new commit counts as an update.

## 5. Uninstall

```
/plugin uninstall <name>@claude-best-practices
```

## Automation / non-interactive form

For a setup script (no interactive session):

```
claude plugin marketplace add D:\Abhay\VibeCoding\claude-best-practices\plugins
claude plugin install prompt-auto-enhance@claude-best-practices
```

## Dev/test shortcut (no marketplace)

Loads a single plugin directly, bypassing the marketplace — useful while developing:

```
claude --plugin-dir D:\Abhay\VibeCoding\claude-best-practices\plugins\prompt-auto-enhance
```

## Caveat — installing from another machine

The hub's `marketplace.json` lives under `plugins/`, not the repo root, so the GitHub shorthand
`/plugin marketplace add abhayla/claude-best-practices` will **not** find it (that form expects
`.claude-plugin/marketplace.json` at the repository root). On a different machine, clone the hub
and add the local `plugins/` path, or add a root-level marketplace pointer (a separate hub
enhancement, not yet done).

## Updating a plugin — why a source edit may not take effect (the install cache)

**Installed plugins are NOT loaded live from the marketplace source.** On install, Claude Code
copies each plugin into a *versioned cache*:

```
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
  e.g. C:\Users\<you>\.claude\plugins\cache\claude-best-practices\prompt-auto-enhance\0.1.1\
```

Claude Code parses **that cached `plugin.json`**, not the live file under `plugins/…` — even when
the marketplace is a local `directory` source pointing at the hub working tree. So **editing the
hub source alone does not fix an installed plugin.** To propagate a change:

1. **Bump the plugin's `version`** in `.claude-plugin/plugin.json`, then run `/plugin update <name>`
   in the downstream project. Updates only flow on a **version bump** (or, if no `version` is set,
   a new git commit SHA) — a same-version source edit is ignored by `/plugin update`.
2. **Or reinstall:** `/plugin uninstall <name>@claude-best-practices` then `/plugin install …` —
   this always re-copies the current source regardless of version.
3. **Emergency hotfix:** edit the cached `plugin.json` under `~/.claude/plugins/cache/…` directly
   (it is the file actually loaded). Reinstall/update will later overwrite it from source, so fix
   the source too.

Plugin load errors are evaluated at **session start** — fully restart the downstream session (not
just reopen `/plugin`) for any change to take effect, then check `/plugin` → **Errors**.

## Authoring gotcha — do NOT declare `hooks` in the manifest

A plugin's `plugin.json` MUST NOT set `"hooks": "./hooks/hooks.json"`. Claude Code **auto-loads**
the standard `hooks/hooks.json` from the plugin root; declaring it again in the manifest double-
loads the same file and fails the whole plugin with:

```
Failed to load hooks ... Duplicate hooks file detected: ./hooks/hooks.json resolves to an
already-loaded file ... The standard hooks/hooks.json is loaded automatically, so manifest.hooks
should only reference ADDITIONAL hook files.
```

Only set `manifest.hooks` when pointing at *extra*, non-default hook files. The standard
`hooks/hooks.json` needs no declaration. (All three hub plugins hit this — fixed in PR #244;
regression-guarded by `scripts/tests/test_prompt_enhance_plugin.py::test_plugin_manifest_valid`.)

## See also

- `docs/claude-references/create-plugins.md` — authoring plugins (cached upstream doc)
- `plugins/.claude-plugin/marketplace.json` — the marketplace manifest (source of truth for the plugin list)
- Goal G6 in `goals.yml` / CLAUDE.md — packaging hub capabilities as installable plugins
