# branch-lifecycle

Hands-off git branch lifecycle for **any** repo — installable as a Claude Code plugin. Once
installed, the user never has to touch git for routine work: pick a branch once per session, every
turn's work is committed + pushed off `main`, a PR is opened, and on session close auto-merge is
armed (gated on your CI), merged-branch cleanup happens automatically, and a second session sharing
the working tree gets warned to use a worktree.

It also bundles the session save/restore skills (`/start-session`, `/end-session`, `/continue`) so
one install covers the whole session + branch flow.

**Fully self-contained:** every hook and skill works with **no other hub files present**. There are
zero references to any external rule, skill, or script — the only things it touches are standard
`git`/`gh` and the downstream project's own `.claude/` state.

## What's inside

| Hook (event) | What it does |
|---|---|
| `stale-branch-reaper.sh` (SessionStart) | nudges the once-per-session branch menu; lists branches idle > N h |
| `session-concurrency-guard.sh` (SessionStart) | warns when another live session shares the working tree → recommends a worktree |
| `auto-pr-reconcile.sh` (SessionStart) | prunes merged local branches; arms auto-merge on leftover open PRs (never the current one) |
| `auto-git.sh` (SessionStart + Stop) | secret-scan → commit → push → open PR; refuses to commit on `main` (carries work to a fresh branch) |
| `auto-pr.sh` (SessionEnd) | opens/refreshes the PR and arms CI-gated auto-merge so it squash-merges when green |
| `branch-choice-gate.sh` (PreToolUse: Edit/Write/MultiEdit) | at the first file edit, reminds you to pick a branch; escalates to worktree advice if a 2nd session is live |
| `session-git-landing.sh` | shared SSOT for the land/reconcile/merge-one logic (sourced by the hooks + the skills) |

| Skill | Purpose |
|---|---|
| `/branch-choice` | the once-per-session branch menu (new from main / keep / switch / merge-then-new / stash) |
| `/git-branch-lifecycle` | control layer: `status`, `work <name>` (worktree), `finish`, `cleanup` |
| `/start-session` · `/end-session` · `/continue` | save / restore / resume session working-state checkpoints |

## Install

From this marketplace:

```
/plugin marketplace add <this-repo>
/plugin install branch-lifecycle
```

The hooks wire themselves automatically via `hooks/hooks.json`. No manual settings edit is required —
defaults are everything-ON.

### Prerequisites (for the auto-merge path only)

- `gh` CLI installed + authenticated, and a GitHub remote. Without them, the commit/branch behavior
  still works; only PR/auto-merge is skipped (silently).
- Branch protection on `main` with a **required** status check (e.g. `validate` / `test`). Auto-merge
  is gated on the *required* checks only — a red or pending PR simply stays open; nothing is forced.

## Configure

Everything is toggleable. Copy `branch-lifecycle-settings.default.json` to
`<project>/.claude/branch-lifecycle-settings.json` (or `~/.claude/` for a global default) and edit —
re-read every session, no reinstall. Or run `/branch-config`. Common switches:

- `enabled: false` — master off-switch (all hooks become no-ops)
- `auto_merge: false` — open PRs but don't auto-merge (you click merge)
- `branch_choice_menu: false` — suppress the first-edit menu
- `stale_branch_hours: 48` — change the staleness threshold
- `secret_scan_cmd: "gitleaks protect --staged --no-banner"` — use your own scanner instead of the
  bundled grep scan

A pre-set environment variable always wins for that session (e.g. `AUTO_MERGE=0 claude ...`).

## Safety

- Never commits on `main`/`master` (carries work to a fresh `auto/work-*` branch first).
- Secret-scans staged changes before every commit; a hit **aborts the commit** (fail-closed). Exempt
  a deliberate dummy by ending the line with `secret-scan:allow`.
- Never force-pushes. Auto-merge is always CI-gated. Every hook is fail-safe (a git/`gh` hiccup never
  blocks your session).
