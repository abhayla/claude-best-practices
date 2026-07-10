# Trap-test: platform-native loop taxonomy routing table (fable-window item 9)

version tested: spec §3.7 (loop-engineering-spec.md v1.4.0)
date: 2026-07-10
model: sonnet (fresh `general-purpose` agent, no prior context)

## Method

A fresh sonnet agent was dispatched with ONLY the §3.7 routing table (5 rows,
table text pasted verbatim, no other spec/skill content) and 5 one-paragraph
task-shape scenarios — one per native primitive plus one that genuinely needs
`/loop-engineering` (independent maker≠checker verification, bounded
self-healing, hub-ward telemetry, multi-unit). The agent had no knowledge of
which row was "supposed" to match which scenario; it routed purely off the
table's task-shape descriptions vs the scenario text.

PASS bar: ≥4/5 routed correctly, including the loop-engineering scenario
(the one the routing table exists to gate correctly — routing everything to
a native primitive, or nothing to loop-engineering, would be the failure mode
this test guards against).

## Scenarios

1. Recurring poll on a known cadence (nightly-deploy status check every 10 min) → expected `/loop` fixed interval
2. Self-paced PR babysitting (adaptive backoff, no fixed cadence) → expected `/loop` dynamic (self-paced)
3. Nightly triage that must survive the session/machine closing → expected cloud Routines (`/schedule`)
4. Single well-specified migrate-until-compiles-and-tests-pass task → expected `/goal <condition>`
5. Unattended multi-unit bug sweep needing maker≠checker + bounded healing + telemetry → expected `/loop-engineering`

## Result: 5/5 PASS

| # | Scenario | Agent's routing | Correct? |
|---|---|---|---|
| 1 | Nightly deploy poll | `/loop` fixed interval | Yes |
| 2 | Self-paced PR babysit | `/loop` dynamic (self-paced) | Yes |
| 3 | Nightly triage, session-independent | cloud Routines (`/schedule`) | Yes |
| 4 | Single migrate-until-DoD task | `/goal <condition>` | Yes |
| 5 | Multi-unit sweep w/ maker≠checker + healing + telemetry | `/loop-engineering` | Yes |

**Raw agent output** (verbatim):

```
1. `/loop` fixed interval — deterministic polling cadence against a known-frequency external process, no adaptive judgment required.
2. `/loop` dynamic (self-paced) — the harness's adaptive backoff replaces hand-rolled polling logic for this open-ended, activity-driven PR babysitting task.
3. cloud Routines (`/schedule`) — a nightly cadence that must fire with no open session requires Anthropic-managed infra, not a session-bound loop.
4. `/goal <condition>` — a single well-specified task with a transcript-verifiable end state (clean compile + passing tests) needing no fleet doctrine.
5. `/loop-engineering` — unattended multi-unit work requiring independent maker≠checker verification, bounded self-healing, and shared telemetry is exactly the shape native `/goal` doesn't cover.
```

## Verdict: PASS (5/5 ≥ 4/5 bar)

The routing table text alone (no skill body, no spec prose beyond the table)
was sufficient for a cheap model with zero prior context to correctly route
all 5 task shapes, including the loop-engineering scenario the table exists
to protect against native-primitive over-adoption. No follow-up action
required.
