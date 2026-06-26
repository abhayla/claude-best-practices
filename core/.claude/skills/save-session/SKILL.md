---
name: save-session
description: >
  DEPRECATED alias — renamed to /end-session. Run /end-session to round up and close a session
  (state the goal, save a resumable checkpoint, land the work CI-gated, confirm closeable). Kept
  temporarily so habit-typing /save-session still routes correctly; removed after 2 version cycles.
type: reference
allowed-tools: "Skill"
argument-hint: "[session-name]"
version: "2.0.0"
deprecated: true
deprecated_by: end-session
---

# save-session — DEPRECATED (use `/end-session`)

`/save-session` has been **renamed to `/end-session`** — the same skill with a clearer name. This
page is a thin alias kept so that typing `/save-session` out of habit still routes you correctly.

## Why the rename

- "Save session" was ambiguous — it sounded like merely writing a checkpoint file.
- The skill actually runs the full **round-up-and-close** ritual, so `/end-session` names it honestly.
- It now pairs naturally with `/start-session` — the lifecycle reads `start ↔ end`.

## Migration — run `/end-session` instead

Run `/end-session`, passing along any session-name argument exactly as before:

```
/end-session [session-name]
```

It does everything `/save-session` did, plus the close-ritual additions:

- States the session **goal** and assesses whether it was met (PARKED external blockers vs PENDING work).
- Saves a **resumable checkpoint** to `.claude/sessions/` — working files, git state, key decisions,
  and task progress — that `/start-session` restores later.
- **Lands the work**: merges the current branch's PR when CI is green, otherwise arms native
  auto-merge. So "session ended" means "merged when green," not a PR left hanging open.
- Purges checkpoints older than 5 days (silent, no confirmation).
- Confirms the session is **closeable**, or states what still remains if the goal is not met.

## What stays the same

- The same trigger phrases still work — "save session", "checkpoint", "wrap up" all reach `/end-session`.
- The session-file format in `.claude/sessions/` is unchanged; old checkpoints still restore.
- The `argument-hint` is identical — pass an optional session name just as before.

## For automation referencing the old name

- Hooks, skills, or scripts that invoked `save-session` should call `end-session` (the registry,
  workflow-contracts, and the session-continuity skill were already updated).
- Until removal, calls to `/save-session` are forwarded here and then to `/end-session`.

## Related session commands

- `/start-session` — restore a saved checkpoint; it now also reconciles + lands any leftover green PRs.
- `/continue` — a lightweight git-state briefing without loading a session file.
- `/handover` — a narrative handoff document for broader context transfer between people or sessions.
- `/session-continuity` — the orchestrator that chains these into a full save → restore lifecycle.

## Quick example (old habit → new)

- Old: you typed `/save-session pre-release` to checkpoint your work before a break.
- New: type `/end-session pre-release` — it saves the checkpoint AND lands your green work to main.
- Next time, `/start-session pre-release` restores it and sweeps up any leftover PRs.

## Removal

This alias is scheduled for removal after **2 version cycles** — switch your habit and any tooling
to `/end-session` before then. After removal, only `/end-session` will resolve.
