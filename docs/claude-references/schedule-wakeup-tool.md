Source: live ScheduleWakeup tool schema (Claude Code harness, session-provided)
Fetched: 2026-07-10

# ScheduleWakeup tool schema (snapshot)

> NOTE: this is a TOOL-SCHEMA SNAPSHOT captured from a live Claude Code session
> (conductor session, 2026-07-10), not a fetched web page. It anchors citations in
> `docs/specs/loop-engineering-spec.md` §3.7/§3.8. Refresh by re-capturing the
> schema from a live session, not by WebFetch.

## Purpose (verbatim from the schema description)

> "Schedule when to resume work in /loop dynamic mode — the user invoked /loop
> without an interval, asking you to self-pace iterations of a specific task"

This confirms first-party that the dynamic (self-paced) `/loop` mode is
implemented via the `ScheduleWakeup` tool: the model calls it to pick the next
wakeup delay each iteration.

## Autonomous-loop sentinels (verbatim from the schema)

> "For an autonomous /loop (no user prompt), pass the literal sentinel
> `<<autonomous-loop-dynamic>>` as `prompt` — the runtime resolves it back to
> the autonomous-loop instructions at fire time. (There is a similar
> `<<autonomous-loop>>` sentinel for CronCreate-based autonomous loops; do not
> confuse the two — ScheduleWakeup always uses the `-dynamic` variant.)"

Two distinct sentinels, both first-party confirmed:

| Sentinel | Used by |
|---|---|
| `<<autonomous-loop-dynamic>>` | `ScheduleWakeup` (dynamic self-paced `/loop`) — always the `-dynamic` variant |
| `<<autonomous-loop>>` | `CronCreate`-based autonomous loops (fixed-interval scheduled tasks) |

## Delay guidance / cache-window economics

The schema's delay guidance documents the prompt-cache-window economics for
wakeup delays: wakeups under ~300 seconds land inside the prompt cache window
(cheaper — the cached prefix is still warm), while longer delays fall outside
it and re-pay the full prompt cost on resume. Pick short delays when actively
iterating and the cache saving matters; back off to longer delays when the
task is quiet and cache retention is moot.

## Related cached docs

- `docs/claude-references/scheduled-tasks.md` — `/loop`, `CronCreate`/`CronList`/`CronDelete`, jitter, 7-day expiry
- `docs/claude-references/goal.md` — `/goal` one-shot autonomous contract
- `docs/claude-references/routines.md` — cloud Routines (`/schedule`), the durable session-independent tier
- `docs/claude-references/sub-agents.md` — confirms `ScheduleWakeup` is NOT available to subagents (T0-only)

**Hub relevance:** cited by `docs/specs/loop-engineering-spec.md` §3.7 (platform-native
loop taxonomy — dynamic `/loop` row + sentinel note) and §3.8 (budget introspection).
