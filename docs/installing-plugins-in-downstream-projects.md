# Installing the hub's plugins in a downstream project

> **Compatibility promise:** what plugin updates may and may not break — stable surfaces, SemVer
> rules, deprecation staging — is defined in `docs/plugin-compat-contract.md`. Read it before
> relying on a plugin surface or shipping a plugin change.

The hub ships an in-tree plugin marketplace at `plugins/.claude-plugin/marketplace.json`
(marketplace name: **`claude-best-practices`**). That file is the **only source of truth** for
which plugins exist — the table below is generated from it (verified by a scripted cross-check
run in CI for this doc; see "Keeping this table honest" below), never hand-typed:

| Plugin | Install where | What it bundles |
|--------|---------------|------------------|
| `prompt-auto-enhance` | any project (prompt diagnose-and-strengthen pipeline) | 1 skill — the enhance pipeline itself |
| `branch-lifecycle` | any git repo (auto branch/commit/push/PR/merge lifecycle + session save/restore) | 5 skills (branch-choice, git-branch-lifecycle, start/end-session, continue) |
| `auto-google-analytics` | only web/frontend projects that need GA4 | 2 skills (setup + the GA4 provisioning engine) |
| `fable-operating-manual` | any project wanting Fable 5's reasoning discipline on any model | 1 skill (`/model-parity-test`) + hook-injected Operating Manual |
| `loop-engineering` | any project wanting the autonomous DISCOVER→PLAN→EXECUTE→VERIFY→SHIP meta-loop | 13 skills + 5 agents (fix-loop, debugging-loop, learn-n-improve, writing-plans, …) |
| `cbp-workflows` | any project wanting the quality-trio (code-review, documentation, skill-authoring) | 16 skills + 4 agents |
| `cbp-build-test-workflows` | any project wanting development-loop + the three-lane test-pipeline | 17 skills + 7 agents |
| `cbp-learning-workflow` | any project wanting the learning/self-improvement workflow | 5 skills + 2 agents |
| `cbp-react-stack` | React/Next.js/RN projects (pairs with `cbp-build-test-workflows`) | 6 skills (vitest/jest runners, React/RN test patterns) |
| `cbp-python-stack` | FastAPI/Python projects (pairs with `cbp-build-test-workflows`) | 4 skills + 2 agents (pytest-dev, FastAPI test/migrate/deploy) |

Every project should install `prompt-auto-enhance` + `branch-lifecycle` (universal), plus
whichever workflow/stack plugins match what it's building. `plugins/.claude-plugin/marketplace.json`
carries the authoritative one-line `description` for each — read there for anything this table
compresses.

> **Plugin commands are session-bound to the target project.** All `/plugin …` steps below
> MUST run inside the *downstream project's own* Claude Code session — they cannot be driven
> from the hub session.

## 1. Register the marketplace (once per project)

**Primary path — GitHub URL, works from any machine and survives any local folder move/rename:**

```
/plugin marketplace add https://raw.githubusercontent.com/abhayla/claude-best-practices/main/plugins/.claude-plugin/marketplace.json
```

This registers the marketplace and lets you browse it (`/plugin`, **Discover** tab) from any
machine with no local clone. **Known current limitation (verified 2026-08-16):** every plugin
entry in `marketplace.json` uses a relative `source` (e.g. `"./prompt-auto-enhance"`), and
Claude Code only resolves relative sources against a *local* copy of the marketplace — a
GitHub-URL-registered marketplace has no local copy, so `/plugin install <name>@claude-best-practices`
fails with `Source path does not exist`. Confirmed by running
`claude plugin marketplace add abhayla/claude-best-practices` (owner/repo shorthand — same
failure mode) and `claude plugin install prompt-auto-enhance@claude-best-practices` against a
clean config dir. **Until the hub adds a root-level `.claude-plugin/marketplace.json` pointer
(tracked as a follow-up — not yet done), installing a plugin still requires the local-clone path
below**, even though registering/browsing works fine over the GitHub URL.

## 2. Install the plugin(s) — today's working method (local clone)

```
git clone https://github.com/abhayla/claude-best-practices.git <path-to-your-local-clone>
/plugin marketplace add <path-to-your-local-clone>/claude-best-practices/plugins
```

Then install by name — syntax is `<plugin>@<marketplace-name>`:

```
/plugin install prompt-auto-enhance@claude-best-practices
/plugin install branch-lifecycle@claude-best-practices
/plugin install auto-google-analytics@claude-best-practices
```

(swap in any plugin name from the table above). Or run `/plugin` and browse the
`claude-best-practices` marketplace interactively. `<path-to-your-local-clone>` is **any**
directory you choose — it is not tied to a specific machine or user account, and moving the
clone afterward just means re-running `marketplace add` with the new path.

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
claude plugin marketplace add <path-to-your-local-clone>/claude-best-practices/plugins
claude plugin install prompt-auto-enhance@claude-best-practices
```

## Footnote — developing the hub itself (no marketplace)

Loads a single plugin directly from a hub checkout, bypassing the marketplace entirely —
useful only while developing/debugging a plugin *in this repo*, not for downstream installs:

```
claude --plugin-dir <path-to-your-hub-checkout>/claude-best-practices/plugins/prompt-auto-enhance
```

## Caveat — the GitHub-URL path registers but can't yet install (verified 2026-08-16)

The hub's `marketplace.json` lives under `plugins/`, not the repo root, so:

- `/plugin marketplace add abhayla/claude-best-practices` (GitHub `owner/repo` shorthand) and
- `/plugin marketplace add https://github.com/abhayla/claude-best-practices.git` (full git URL)

both fail outright with `Marketplace file not found` — Claude Code only looks for
`.claude-plugin/marketplace.json` at the repository root for these two source types. The direct
raw-file URL (`.../plugins/.claude-plugin/marketplace.json`, shown in step 1 above) *does*
register successfully, but every plugin entry's `source` is a relative path
(`"./prompt-auto-enhance"`, etc.), and Claude Code can't resolve a relative path against a
marketplace that was fetched as a single remote file with no local copy — so
`/plugin install <name>@claude-best-practices` then fails with `Source path does not exist`.
All three failure modes were reproduced directly against the live GitHub repo with a clean
`CLAUDE_CONFIG_DIR` before writing this section — this is not a theoretical gap.

**Net effect:** today, on any machine (not just the hub owner's), installing a plugin requires
the local-clone method in step 2 above. The fix is a root-level `.claude-plugin/marketplace.json`
pointing into `./plugins/<name>` for each entry — a repo-structure change, not a docs change, so
it's tracked as separate hub follow-up work rather than done here.

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
