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

## See also

- `docs/claude-references/create-plugins.md` — authoring plugins (cached upstream doc)
- `plugins/.claude-plugin/marketplace.json` — the marketplace manifest (source of truth for the plugin list)
- Goal G6 in `goals.yml` / CLAUDE.md — packaging hub capabilities as installable plugins
