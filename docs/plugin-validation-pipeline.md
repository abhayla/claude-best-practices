# Plugin clean-room validation pipeline

`scripts/validate_plugin_cleanroom.py` (wrapped by `scripts/validate_plugin_cleanroom.sh`
for a one-command entry point) automates the manual clean-room install-serving check that
`loop-engineering` completed by hand on 2026-07-03 (`plans/loop-engineering-adoption.md`
STEP 5.2, PR #276): prove that a plugin's skills/commands/hooks are actually served when
installed via `--plugin-dir` into a project with no local `.claude/` — not just that the
plugin's files parse.

## Running it

```bash
# From the hub repo root
PYTHONPATH=. scripts/validate_plugin_cleanroom.sh <plugin-name>
# equivalent:
PYTHONPATH=. python scripts/validate_plugin_cleanroom.py <plugin-name>
```

Useful flags:

| Flag | Effect |
|---|---|
| `--skip-serve` | Run only the structural gate + `claude plugin validate` (no headless `claude` call — fast, free, safe to run anywhere) |
| `--model <alias>` | Model for the headless probe (default `haiku` — cheapest sufficient per `.claude/rules/model-routing.md`) |
| `--timeout <seconds>` | Hard subprocess timeout for the headless probe (default 180s) |
| `--strict-cli` | Pass `--strict` to `claude plugin validate` (treat CLI warnings as errors) |
| `--keep-tmp` | Keep the throwaway clean-room project dir for manual inspection |
| `--json` | Print only the machine-readable verdict JSON |
| `--plugins-root` / `--marketplace-path` | Override the plugins root / marketplace.json path (used by the pytest fixtures; not needed for normal use) |

Exit code is `0` iff every gate that ran passed.

## The three gates

1. **Structural gate** (pure Python, no CLI calls — this is what the pytest suite tests):
   - `plugin.json` parses and has a non-empty `name` and `version`.
   - The plugin's `name` is registered in `plugins/.claude-plugin/marketplace.json`.
   - `plugin.json` does NOT declare `"hooks"` — Claude Code auto-loads
     `hooks/hooks.json`; declaring it again in the manifest double-loads it and fails the
     whole plugin at session start (see the "Authoring gotcha" section of
     `docs/installing-plugins-in-downstream-projects.md`). **This defect passes `claude
     plugin validate` silently** (confirmed live during this pipeline's build — see the
     trap-test below) — the structural gate is the only thing that catches it before a
     user hits the runtime failure.
   - Every skill directory under `skills/` has a `SKILL.md`.
   - The manifest's `commands` field (if declared) points to an existing directory.
   - Every hook command referenced in `hooks/hooks.json` resolves to a file that exists
     on disk relative to the plugin root.

2. **`claude plugin validate <path>`** — the CLI's own manifest validator (confirmed to
   exist via `claude plugin validate --help`; `--strict-cli` forwards `--strict`). Always
   run (not skip-with-note) since the CLI supports it on this platform version.

3. **Clean-room serve test** — creates a throwaway project OUTSIDE the hub repo (system
   temp dir via `tempfile.mkdtemp()`, `git init` + a README, no other `.claude/`), then
   runs one headless, capped turn:
   ```
   claude -p "<read-only probe>" --plugin-dir <abs plugin dir> --model haiku \
     --permission-mode bypassPermissions --output-format stream-json --verbose
   ```
   with `AUTO_PR_DISABLE=1` / `AUTO_MERGE=0` set in the subprocess environment (defensive —
   neutralizes any plugin's own auto-PR-style hooks; the throwaway project has no git
   remote anyway, so such a hook has nothing to act on).

   **PASS signal is deterministic, not text-compliance-based.** Claude Code reports its
   resolved session state — including every loaded plugin's `name`/`path`/`source` — in a
   `{"type":"system","subtype":"init"}` line at the very start of `stream-json` output,
   before the model generates any text. The gate parses that line and checks the plugin
   appears with `source: "<name>@inline"` at the expected `--plugin-dir` path. It also
   surfaces (as evidence, not as the pass criterion) any `skills`/`slash_commands` in that
   same event whose names are prefixed `<plugin-name>:`.

   **Why not just read the model's reply?** An earlier version of this probe asked the
   model to list its available skills in free text and grepped the reply for
   `/<plugin>:<skill>`. That failed against `prompt-auto-enhance` specifically — its own
   `UserPromptSubmit` hook deliberately overrides normal turn behavior (it exists to force
   every substantive prompt through the enhancement pipeline), so the model answered with
   enhancement-pipeline boilerplate instead of the literal skill list, even when told to
   ignore other reminders. The `system/init` signal sidesteps this: it is reported by the
   CLI itself, independent of anything the model chooses to say.

## What PASS means — and what it does not

This pipeline proves **automated install-serving validation**: the plugin's manifest is
well-formed, the CLI's own validator accepts it, and `--plugin-dir` actually serves its
skills/commands into a project with zero local `.claude/`. That is a real, repeatable,
one-command proof — and it is what all 5 shipped plugins (see the sweep below) now have.

It is **not** identical to the full G6 graduation bar that `loop-engineering` cleared by
hand: a real `/plugin marketplace add` + `/plugin install <name>@claude-best-practices`
into a genuinely separate second PROJECT, followed by a full maker≠checker session (a
real task executed, a real commit, an independent checker reproduction) using only the
installed plugin. That heavier bar exercises the marketplace/install-cache path
(`~/.claude/plugins/cache/...`) and a live multi-turn agentic session, neither of which
this pipeline drives. `goals.yml`'s G6 DoD language ("validated, multi-project-tested")
still refers to that heavier bar — this pipeline is the fast, repeatable, CI-safe layer
underneath it, not a replacement for it.

**Known environment limitation:** the clean-room serve test isolates the throwaway
project from any local `.claude/` directory, but it does **not** isolate from the
operator machine's global `~/.claude/` config (installed plugins, MCP servers, etc — full
`HOME`/`USERPROFILE` isolation was tried and breaks Claude Code auth, since credentials
live in that same global state). On a machine where a plugin under test is *also*
installed globally (true for `prompt-auto-enhance`, `auto-google-analytics`, and
`loop-engineering` on the hub maintainer's dev machine, from earlier `/plugin-lifecycle`
work), the `init.plugins` list will contain that plugin twice — once as
`<name>@inline` (our `--plugin-dir` load, which is what the pass check requires) and once
as `<name>@claude-best-practices` (the pre-existing global install). The pass check only
requires the `@inline` entry at the expected path, so a pre-existing global install does
not affect the verdict, but it means this run is not proof of isolation from *all*
ambient state — only from the target project's own `.claude/`. For the strongest possible
guarantee, run on a machine/CI runner with no prior global install of the plugin under
test.

## First sweep results (2026-07-10)

All 4 plugins that owed clean-room validation, run via
`PYTHONPATH=. python scripts/validate_plugin_cleanroom.py <name> --model haiku`:

| Plugin | Structural | `claude plugin validate` | Clean-room serve | Overall |
|---|---|---|---|---|
| `prompt-auto-enhance` | PASS | PASS | PASS — `prompt-auto-enhance:enhance-config`, `prompt-auto-enhance:prompt-auto-enhance` visible | **PASS** |
| `auto-google-analytics` | PASS | PASS | PASS — `auto-google-analytics:analytics-setup`, `auto-google-analytics:auto-google-analytics` visible | **PASS** |
| `branch-lifecycle` | PASS | PASS | PASS — all 6 skills visible (`branch-choice`, `branch-config`, `continue`, `end-session`, `git-branch-lifecycle`, `start-session`) | **PASS** |
| `fable-operating-manual` | PASS | PASS | PASS — `fable-operating-manual:model-parity-test` visible | **PASS** |

`loop-engineering` (already cleared the heavier bar by hand) also passes the structural
gate and `claude plugin validate` — verified via the pytest regression suite
(`test_validate_plugin_cleanroom.py::TestRealPlugins`).

**Honest framing:** all 5 shipped plugins now clear the automated install-serving bar
this pipeline checks. Only `loop-engineering` has additionally cleared the heavier
second-project `/plugin install` + maker≠checker bar described above — that remains the
open item for the other 4 toward the full G6 DoD, unchanged by this pipeline landing.

## Planted-defect trap-test (build-time verification)

To prove the pipeline actually catches regressions (not just rubber-stamps everything), a
copy of `prompt-auto-enhance` was broken two ways in a scratch directory outside the repo:
(1) `plugin.json` was edited to declare `"hooks": "./hooks/hooks.json"`, and (2)
`skills/prompt-auto-enhance/SKILL.md` was deleted. Running the pipeline against it:

```
=== broken-plugin: FAIL ===
  [FAIL] Structural gate
          - plugin.json declares 'hooks' — this double-loads hooks/hooks.json and fails
            the whole plugin at session start (do not declare hooks in the manifest;
            they auto-load)
          - skill directory missing SKILL.md: skills\prompt-auto-enhance
  [PASS] claude plugin validate
  [FAIL] Clean-room serve test
          - 'broken-plugin' did not appear in the init event's plugins list at the
            expected path; loaded plugins: [... every OTHER plugin on the machine ...]
```
Exit code: `1`.

Both planted defects were named by the structural gate. `claude plugin validate` passed
the broken manifest silently (confirming the note above — the CLI validator does not
catch the hooks-double-declare authoring gotcha). The clean-room serve test independently
failed for a different, corroborating reason: the plugin never appeared in the live
session's loaded-plugins list at all — Claude Code refused to load it, exactly as
documented in the authoring-gotcha section (a fatal "Duplicate hooks file detected"
error at session start).

## CI / test-suite coverage

`scripts/tests/test_validate_plugin_cleanroom.py` unit-tests `check_structural_gate` and
`resolve_plugin_dir` against fixture plugin dirs (`scripts/tests/fixtures/plugin-cleanroom/`)
covering each defect class above, plus a regression test that all 5 shipped
`plugins/*` pass the structural gate today. **It never invokes the `claude` CLI** — the
`claude plugin validate` and clean-room-serve gates are exercised manually (as documented
in this file), consistent with the existing `integration` pytest marker convention
(`scripts/tests/conftest.py`) for tests that need a live `claude` CLI.

## See also

- `docs/installing-plugins-in-downstream-projects.md` — install mechanics + the
  hooks-double-declare authoring gotcha this pipeline structurally guards against.
- `goals/plugin-validation-pipeline.md` — the standing goal that keeps this pipeline's
  own files (script, wrapper, this doc) from silently disappearing; it does NOT re-run
  the headless `claude` probe daily (that stays a manual/CI-triggered action, never a
  cron sentinel predicate).
- `.claude/skills/plugin-lifecycle/SKILL.md` — the hub's plugin create/fix/update
  lifecycle; run this pipeline's `--skip-serve` mode as a fast pre-land check, and the
  full run (with the serve probe) before declaring a plugin's install-serving validated.
