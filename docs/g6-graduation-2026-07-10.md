# G6 graduation validation — 2026-07-10

This is the **heavier G6 graduation bar** (distinct from the lighter serve-validation pipeline
documented in `docs/plugin-validation-pipeline.md`, which all 5 shipped plugins already
cleared on 2026-07-10). Graduation requires: *"In a clean-room second project, the INSTALLED
plugin ALONE (no provisioned `.claude/` copies, no hub tree) serves its skills/agents/hooks
through a real exercise of its primary capability."*

Four plugins owed this bar going in: `prompt-auto-enhance`, `auto-google-analytics`,
`branch-lifecycle`, `fable-operating-manual`. `loop-engineering` had already cleared it
(2026-07-03, PR #276) and is not re-tested here.

## Method

For each plugin: a throwaway clean-room directory was created OUTSIDE the hub tree
(`D:/Abhay/VibeCoding/cleanroom-<plugin>-20260710`, `git init` + a bare README, no
`.claude/` of its own). The hub's local marketplace (`claude-best-practices`, a `directory`
source pointing at `D:\Abhay\VibeCoding\claude-best-practices\plugins`) was already
registered on this machine. A headless, capped session
(`claude -p "<prompt>" --output-format stream-json --verbose --model sonnet`, wall-clock
timeout 240s) was run from inside each clean-room directory, exercising the plugin's primary
capability. Each transcript was saved as `.jsonl` in its clean-room directory. For every
plugin, the `system/init` event's `plugins` list was checked for the plugin's presence, and
a fresh, context-isolated skeptic subagent (model sonnet) was dispatched into the same
directory afterward with a brief to try to REFUTE graduation (rule out base-model habit,
stray local config, or another globally-installed plugin producing lookalike behavior).

## Verdict table

| Plugin | Verdict | Evidence |
|---|---|---|
| `prompt-auto-enhance` | GRADUATED | `system/init` lists `prompt-auto-enhance` loaded; mid-transcript a `Stop hook feedback` message reading `STOP BLOCKED (prompt-auto-enhance: full process not shown)…` fired from the plugin's own `hooks/enhance-process-guard.sh` (verbatim phrase confirmed to exist in that script and nowhere else on the machine), blocking the turn; the assistant's next turn then rendered the full `*Enhanced: …*` banner + pipeline log + before/after score table (with the mandatory Reviewer-after column and Overall row) exactly per the plugin's documented contract. Version-keyed cache `~/.claude/plugins/cache/claude-best-practices/prompt-auto-enhance/0.4.0/` exists and is byte-identical to the served hub-source copy. **Skeptic verdict: NOT REFUTED** — one correction: the `system/init` `path` resolved to the hub source tree, not the cache path (see Limitations). |
| `branch-lifecycle` | GRADUATED | `system/init` lists `branch-lifecycle` loaded; a trivial `NOTES.md` edit was requested via a headless prompt with no git instructions given, and afterward `git log --oneline --all` in the clean-room repo showed two new commits titled `auto: checkpoint 2026-07-10 20:59 (2 files on auto/work-20260710-205907)` landed on a new branch `auto/work-20260710-205907` (not `master`) — the exact message template traced to `hooks/auto-git.sh` line 134 (`msg="auto: checkpoint $(date '+%Y-%m-%d %H:%M') ($staged files on $branch)"`); the transcript's tool_use stream shows no manual `git commit`/`git checkout -b` call by the model — branch creation and commits happened via the hook, not the model typing git commands. Version-keyed cache `~/.claude/plugins/cache/claude-best-practices/branch-lifecycle/0.1.1/` exists and is byte-identical. **Skeptic verdict: NOT REFUTED** — same path-resolution correction as above. |
| `fable-operating-manual` | GRADUATED | Freshly installed in the clean room (was NOT pre-installed globally); `system/init` for a session inside its own clean-room dir lists `fable-operating-manual` loaded and `fable-operating-manual:model-parity-test` in `slash_commands` (confirmed invocable — steps only, full 33-case exam NOT run per the honesty scope of this task); separately, its SessionStart injection hook was independently observed firing in the sibling `cleanroom-prompt-auto-enhance-20260710` clean room (also installed at user/global scope) — `additionalContext` began `# Fable 5 Operating Core (distilled — full manual: manual/fable5-operating-manual.md)`, confirmed byte-identical to `manual/distilled-core.md` and found nowhere else in the hub tree. Version-keyed cache `~/.claude/plugins/cache/claude-best-practices/fable-operating-manual/0.1.1/` exists and is byte-identical. **Skeptic verdict: NOT REFUTED** — same path-resolution correction. |
| `auto-google-analytics` | GRADUATED (boundary-limited, as anticipated) | `system/init` lists `auto-google-analytics` loaded and both its skills in `slash_commands`; a 14-turn headless run genuinely exercised the skill's documented "STEP 0 — Preflight" (tool calls checked repo contents and the `GA_PROVISION_SA_KEY` credential per the skill's actual SKILL.md), correctly determined no real web project/site exists in the clean room, refused to fabricate a GA4 property ID or tracking URL (the skill's hard "never fabricate IDs" rule), and ended on a `Sync-check:` question asking for a real site — reaching its first REAL gate that needs live site + GCP context, exactly the boundary the task anticipated. A live GA4 property was NOT provisioned (not possible in a clean room, and not required by the task's honesty rule). Version-keyed cache `~/.claude/plugins/cache/claude-best-practices/auto-google-analytics/0.1.2/` exists and is byte-identical. **Skeptic verdict: NOT REFUTED on capability exercise** (flagged one minor synthesis overstatement in the assistant's own closing summary re: SA-key env-var state, immaterial to the outcome) — same path-resolution correction. |

All four independent skeptic subagents reached **NOT REFUTED** on the core claim (genuine
plugin-hook-driven capability execution, not base-model habit, not another plugin's
lookalike output, not a stray local `.claude/` config) and all four independently surfaced
the SAME correction: `system/init`'s `path` field resolves to the hub **source** tree
(`D:\Abhay\VibeCoding\claude-best-practices\plugins\<name>`), not the version-keyed cache
directory. See "Limitations" for what this does and does not undermine.

## Pre-existing-install handling

Pre-install state (`claude plugin list`, run before any action):

| Plugin | Pre-installed? | Action taken |
|---|---|---|
| `prompt-auto-enhance` | Yes, user scope, version 0.3.3 — **older** than hub source (0.4.0) | Updated in place via `claude plugin update prompt-auto-enhance@claude-best-practices` → cache now at 0.4.0, matching hub source. Not uninstalled. |
| `auto-google-analytics` | Yes, user scope, version 0.1.2 — matches hub source | Validated in place, no reinstall/update needed. Not uninstalled. |
| `branch-lifecycle` | Yes, user scope, version 0.1.1 — matches hub source | Validated in place, no reinstall/update needed. Not uninstalled. |
| `fable-operating-manual` | No — not installed globally | Installed fresh (`claude plugin install fable-operating-manual@claude-best-practices`, user scope) for this validation. **Will be uninstalled** in the cleanup step (see below) since it was not pre-existing. |
| `loop-engineering` | Yes, user scope, version 0.1.0 — noted for context only, not re-tested (already G6-validated 2026-07-03) | No action. |

Cleanup after all 4 plugins were processed: `fable-operating-manual@claude-best-practices`
was uninstalled (it was the only fresh install this session made); no marketplace
registration was added or removed (the `claude-best-practices` directory marketplace was
already registered on this machine before this session started). All four throwaway
clean-room directories were deleted after evidence was captured into this file.

## Limitations

- **Path-resolution caveat (the most important honest gap in this run).** For all four
  plugins, the `system/init` event's `path` field resolved to the hub **source** tree
  (`D:\Abhay\VibeCoding\claude-best-practices\plugins\<name>`), not the version-keyed cache
  directory (`~/.claude/plugins/cache/claude-best-practices/<name>/<version>/`), even though
  each plugin was installed via the real `claude plugin install <name>@claude-best-practices`
  mechanism (not `--plugin-dir`) and each version-keyed cache directory does exist on disk.
  Root cause: the `claude-best-practices` marketplace is registered on this machine as a
  local `directory` source pointing straight at the hub working tree, and Claude Code
  apparently resolves directory-source plugins live from that source path rather than
  copying/reading from the cache — a machine-specific characteristic of this dev setup
  (same mechanism `loop-engineering`'s original 2026-07-03 graduation run would have used),
  not evidence of `--plugin-dir`/inline injection or of a provisioned `.claude/` copy sitting
  in the clean-room project (there was none — each clean room's own `.claude/` contained only
  runtime session artifacts, no plugin content). All four independent skeptic subagents
  confirmed this via `grep`: the served content (hook scripts, manual text, skill files) is
  byte-identical between the hub source and the version-keyed cache, so the *executed logic*
  is provably the same either way — what's weaker is the specific claim that the cache path
  (as opposed to the source path) was the one Claude Code read from in this run. On a
  machine/CI runner where the marketplace is added as a git-hosted source instead of a local
  `directory`, plugin loads would necessarily come from the cache, closing this gap. This
  should be treated as an open item for a fully clean second machine, not a disqualifier for
  the verdicts above — the capability-execution evidence (Stop-hook blocks, branch/commit
  creation, manual injection, skill invocation) is independent of which path served it and
  was not weakened by this finding.
- The clean-room directories are isolated from any local project `.claude/`, but — same
  caveat as `docs/plugin-validation-pipeline.md` — NOT isolated from this machine's global
  `~/.claude/` config (other globally-installed plugins, e.g. `remember`, `superpowers`, also
  fire their own SessionStart hooks in the same sessions). This did not confound any of the
  four verdicts above — in each case the specific evidence (a literal blocked-stop message, a
  literal commit-message template, a literal manual header string, a literal skill-name
  match) was traced to that plugin's own script/skill content, not a lookalike from another
  plugin.
- `prompt-auto-enhance`'s UserPromptSubmit hook (`prompt-enhance-reminder.sh`) does **not**
  emit its own `hook_started`/`hook_response` stream-json events the way `SessionStart` hooks
  do (only `SessionStart` hook events appeared in every transcript) — evidence for this
  plugin instead rests on its downstream `Stop` hook firing (which DOES emit as a "Stop hook
  feedback" turn) and the resulting compliant model behavior. This is a real behavioral
  proof, not a weaker substitute, but note the mechanism is inferred from the Stop-hook
  block + compliant response rather than a direct UserPromptSubmit hook-fired log line.
- `auto-google-analytics`'s exercise is intentionally boundary-limited per the task's own
  honesty rule — no live GA4 property was provisioned, and none was required. What was and
  was not exercised is stated precisely in the verdict table above.
- `/model-parity-test`'s full 33-case exam was NOT run for `fable-operating-manual`, per the
  task's explicit instruction to list its steps only.
- No plugin fell short of the graduation bar in this run — all four are recorded GRADUATED.
