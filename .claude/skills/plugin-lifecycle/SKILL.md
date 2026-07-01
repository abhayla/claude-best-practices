---
name: plugin-lifecycle
description: Create and maintain plugins in the hub's plugins/ monorepo end-to-end. On CREATE, scaffolds every required file and registers the plugin in the marketplace. On FIX/UPDATE, edits the source, tests locally FIRST, bumps the version so the install cache actually propagates, lands CI-gated, then verifies the installed plugin. Use when the user says "create a plugin", "fix/update a plugin", "maintain a plugin", or reports a plugin defect.
type: workflow
version: 1.0.0
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Skill, Agent
argument-hint: "<create|fix|audit> <plugin-name> [--desc \"...\"]"
---

# Plugin Lifecycle — Create & Maintain Hub Plugins

Owns the full lifecycle of a plugin in the in-tree monorepo (`plugins/`, marketplace at
`plugins/.claude-plugin/marketplace.json`). It exists because a plugin fix is NOT done when the
source is edited — the installed copy is **version-pinned in a cache** and never sees the fix until
the version is bumped and the plugin is updated. This skill makes that (and every other easy-to-miss
step) part of one recipe.

> **Delegate, don't duplicate.** Generic Claude Code plugin authoring/validation is already covered by
> the `plugin-dev:*` marketplace skills (`plugin-dev:create-plugin`, `plugin-dev:plugin-validator`,
> `plugin-dev:hook-development`, …) and `claude plugin validate`. This skill adds only the HUB
> conventions those don't know: the marketplace entry, the version→propagation contract, the
> local-CI-before-land gate, and dual-home rule copies. Reference: cached Anthropic doc
> `docs/claude-references/create-plugins.md` (read it before authoring plugin internals).

## Mode router

| Argument | Mode | Go to |
|---|---|---|
| `create <name>` | Scaffold a new plugin + register it | STEP 1 → 2 → 3 → 5 → 7 → 8 |
| `fix <name>` / `update <name>` / `maintain <name>` | Fix/extend an existing plugin | STEP 1 → 4 → 5 → 6 → 7 → 8 → 9 |
| `audit [name]` | Report lifecycle health (files, version, marketplace, cache) — read-only | STEP 1 only |

## STEP 1: Route + preflight

Determine the mode from the argument and confirm the ground truth before touching anything.

- `ls plugins/` and read `plugins/.claude-plugin/marketplace.json` — is `<name>` a real plugin?
  `create` requires it to NOT exist; `fix`/`audit` require it to exist.
- Read the plugin's `.claude-plugin/plugin.json` — note the current `version` (the propagation anchor).
- Confirm you are on a fresh branch off `main` (not an already-merged branch); the branch-choice /
  auto-git hooks handle this — if the current branch already has a merged PR, branch off `main` first.
- For `audit`: report `{files present, plugin.json version, marketplace entry present?, hooks declared in
  plugin.json? (must be NO), rule copy in sync?}` and STOP — audit is read-only.

## STEP 2: Scaffold the plugin (CREATE)

Create the plugin at `plugins/<name>/` with EVERY required file. Only `plugin.json` goes inside
`.claude-plugin/`; all component dirs sit at the plugin root.

```
plugins/<name>/
  .claude-plugin/plugin.json      # name, version "0.1.0", description, author, keywords, (commands)
  skills/<name>/SKILL.md          # if it ships a skill
  hooks/hooks.json                # if it ships hooks (auto-loaded — see MUST NOT DO)
  agents/*.md                     # if it ships agents
  <settings>.default.json         # if it ships toggleable settings
  README.md                       # install + usage
```

- `plugin.json` MUST set an explicit `version` (start `0.1.0`). Without it, the git SHA is the version
  and every commit counts as an update.
- For skill/hook/agent internals, invoke `Skill("plugin-dev:create-plugin")` or the matching
  `plugin-dev` authoring skill rather than hand-rolling structure.

## STEP 3: Register in the marketplace + docs (CREATE)

- Add an entry to `plugins/.claude-plugin/marketplace.json` `plugins[]`:
  `{ "name": "<name>", "source": "./<name>", "description": "<one-line>" }`.
- Update `CLAUDE.md`'s `plugins/` bullet + the G6 plugin count if this is a new distributable plugin.
- Plugins live under `plugins/` and are NOT registered in `registry/patterns.json` (that indexes
  `core/` distributables, not marketplace plugins) — do not add a registry entry.

## STEP 4: Make the fix in source + sync dual-home copies (FIX)

- Edit the real source under `plugins/<name>/` — never a cached copy.
- If the plugin ships a rule that the HUB also keeps an operational copy of (e.g.
  `prompt-auto-enhance`'s rule ↔ `.claude/rules/prompt-auto-enhance.md`), apply the SAME edit to BOTH
  so the hub's own behavior and the distributed plugin stay in sync.
- Respect any per-file budgets (e.g. a copied-in rule under the ≤100-line budget its test enforces).
- Root-cause the defect; add or update a test that fails before the fix and passes after.

## STEP 5: Test locally FIRST — before any commit or version bump (BOTH)

This is the gate. Nothing proceeds until it is green.

1. **Full hub CI gate**, isolated — dispatch `Agent(subagent_type="pre-git-merge-checker-agent", …)` so
   its output never floods the session. It runs `dedup_check.py --validate-all`, `--secret-scan`,
   `workflow_quality_gate_validate_patterns.py`, and `pytest scripts/tests/`. Act on PASS/FAIL.
2. **Plugin self-validation** — `claude plugin validate ./plugins/<name>` (the same check the review
   pipeline runs). Fix structure errors (dirs wrongly inside `.claude-plugin/`, bad manifest).
3. **Hook syntax** — `bash -n` every `plugins/<name>/hooks/*.sh`; craft a transcript and exercise any
   Stop/PreToolUse guard so a behavior change is proven, not assumed.
4. **Live smoke via `--plugin-dir`** — the source loads directly and takes precedence over the installed
   copy, so you can prove the fix with NO reinstall: `claude --plugin-dir ./plugins/<name>` (or
   `/reload-plugins` in a running session), then invoke the skill/command and confirm the new behavior.

## STEP 6: Bump the version — the propagation trigger (FIX)

The install cache is pinned at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. A source
edit with NO version bump NEVER reaches an installed plugin — this is the #1 "I fixed it but it's still
broken downstream" trap.

- Bump `version` in `plugins/<name>/.claude-plugin/plugin.json` per SemVer: PATCH = fix,
  MINOR = new mandatory output/mode/behavior, MAJOR = breaking change.
- If the marketplace entry or monorepo `metadata.version` also carries a version, decide whether it
  needs bumping too (usually not for a single-plugin fix).

## STEP 7: Land CI-gated (BOTH)

`.claude/` is gitignored, so a hub operational rule copy needs `git add -f`; everything under
`plugins/` and `scripts/tests/` stages normally.

```bash
git add plugins/<name>/ scripts/tests/<changed_test>.py plugins/.claude-plugin/marketplace.json
git add -f .claude/rules/<synced-rule>.md   # only if a dual-home copy changed
git commit -m "fix(<name>): <what> (v<new-version>)"   # or feat(<name>): scaffold ...
git push -u origin <branch>
```

Open the PR and arm CI-gated auto-merge (`gh pr merge <n> --auto --squash`). Do NOT block the turn
waiting on the merge — the fix is already proven live on disk (STEP 5).

## STEP 8: Test the INSTALLED plugin (BOTH)

Source-tested ≠ installed-tested. Close the loop on the actual install:

- `claude plugin update <name>` (pulls the new version from the marketplace), then `claude plugin list`
  MUST show the new version — if it still shows the old one, the update did not take.
- Invoke the skill/command in a project that has the plugin installed and confirm the fix is live.
- This is the step that would have answered "did you fix it on the other session?" — the hub source can
  be fixed while every installed copy is still pinned to the old version until this runs.

## STEP 9: Capture the lesson (FIX)

If the fix exposed a non-obvious trap (a silent propagation gap, a manifest footgun, a budget), record
it: append to `.claude/tasks/lessons.md` and, if cross-session-durable, write an auto-memory. Fold any
newly-discovered convention into this skill's cheat-sheet below.

## Conventions cheat-sheet (the traps this skill exists to prevent)

- **Version bump = propagation.** Installed plugins are version-pinned in the cache; no bump → the fix
  never ships. Set an explicit `version` (never rely on the git SHA for a maintained plugin).
- **Test before land, not after.** `--plugin-dir ./plugins/<name>` loads the source and overrides the
  installed copy — prove the fix locally, then land.
- **`claude plugin validate`** runs the same check as the submission pipeline — run it every time.
- **`/reload-plugins`** hot-reloads skills/agents/hooks/MCP without a restart.
- **Never declare a plugin's hooks in `plugin.json`.** Hooks in `hooks/hooks.json` are auto-loaded;
  declaring them again causes a duplicate-load error (hub lesson, PR #244).
- **Only `plugin.json` lives in `.claude-plugin/`.** Every component dir (`skills/`, `hooks/`, …) sits
  at the plugin ROOT — the most common structural mistake.
- **`.claude/` is gitignored** → `git add -f` any tracked hub operational copy (e.g. a synced rule).
- **Copied-in rules keep their budget** (e.g. the ≤100-line rule the pattern test enforces).
- Plugins are NOT in `registry/patterns.json`; the marketplace entry is their registration.

## MUST DO

- Always run STEP 5 (full local CI + `plugin validate` + `--plugin-dir` smoke) to green BEFORE any
  commit or version bump — Why: a fix that fails the gate or was never exercised is an unverified claim.
- Always bump `plugin.json` `version` on any FIX that must reach installed copies — Why: the cache is
  version-pinned, so an unbumped fix silently never propagates (the exact bug this skill was created for).
- Always add the marketplace `plugins[]` entry when creating a plugin — Why: without it the plugin is
  invisible to `/plugin install` and cannot be distributed or updated centrally.
- Always run STEP 8 (update + `plugin list` version check + real invocation) before declaring a
  maintained plugin done — Why: source-tested is not installed-tested; the two diverge until update runs.
- Always sync a dual-home rule copy in BOTH the plugin and `.claude/` in the same change — Why: letting
  them drift makes the hub behave differently from what it distributes.
- Always delegate generic scaffolding/validation to `plugin-dev:*` and `claude plugin validate` — Why:
  re-implementing plugin structure by hand reintroduces the footguns those tools already prevent.

## MUST NOT DO

- MUST NOT edit a cached copy under `~/.claude/plugins/cache/...` to "fix" a plugin — edit the source in
  `plugins/<name>/` instead — Why: cache edits are overwritten on the next update and never land in git.
- MUST NOT declare a plugin's hooks in `plugin.json` when they already live in `hooks/hooks.json` — put
  them only in `hooks/hooks.json` — Why: double declaration triggers a duplicate-load error.
- MUST NOT place `skills/`, `hooks/`, `agents/`, or `commands/` inside `.claude-plugin/` — keep them at
  the plugin root — Why: Claude Code only reads `plugin.json` from `.claude-plugin/`; misplaced dirs are ignored.
- MUST NOT commit a plugin fix without a version bump — bump first — Why: an unbumped change reaches no
  installed copy, producing "fixed in the hub, still broken everywhere else".
- MUST NOT block the session waiting on merge CI after landing — arm auto-merge and report — Why: the fix
  is already proven live via `--plugin-dir`; blocking wastes the turn.
- MUST NOT add a plugin to `registry/patterns.json` — the marketplace entry is its registration — Why:
  the registry indexes `core/` distributables, and a stray entry breaks the registry-sync gate.
