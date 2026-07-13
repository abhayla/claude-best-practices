---
name: platform-event-live-probe
description: Live-probe a platform event or API surface BEFORE building on it — prove the event fires and its payload reaches the exact consumer you plan to use, with a minimal tracer. Use before wiring a new Claude Code hook event, SDK callback, webhook, or any documented-but-unverified platform behavior. A documented event name is not delivery.
version: "1.0.0"
type: workflow
triggers:
  - /platform-event-live-probe
  - "does this hook event actually work"
  - "verify the event fires before building"
  - "probe the platform behavior first"
allowed-tools: Read, Write, Bash, Grep, Glob
argument-hint: "<event-or-surface> <intended-consumer>"
---

# Platform Event Live Probe

Build the tracer before the feature. The hub wired `SubagentStop` governance on the documented
event, shipped it, and later live-testing proved the event fires but its `additionalContext`
never reaches the parent loop — the whole mechanism was reverted as "governance theater"
(a 3-commit adopt→verify→revert arc). A same-day plugin revert repeated the pattern. Both costs
were avoidable with a 10-minute probe run BEFORE the build.

## STEP 1: State the Load-Bearing Assumption

Write the assumption as one falsifiable sentence:

```
ASSUMPTION: event <X>, when triggered by <Y>, delivers <payload field Z> to <consumer surface>.
```

If the sentence contains "should" or "according to docs", that is exactly why the probe exists —
docs describe intent; versions drift; payload routing is the part docs are most often silent on.

## STEP 2: Build a Minimal Tracer

Create the smallest artifact that can prove or refute the assumption — NOT the real feature:

| Surface | Tracer |
|---|---|
| Hook event | A 3-line hook that appends `PROBE-<nonce> $(date) $PAYLOAD` to a scratch file AND emits the nonce into its output channel (`additionalContext`, stdout) |
| Webhook | An endpoint (or requestbin) that dumps headers+body verbatim |
| SDK callback | A handler that logs the full callback args to a file |
| External API behavior | A one-off script calling the real API with a marker payload |

Wire the tracer exactly where the real implementation would sit (same settings.json event, same
route) — probing a different wiring point proves nothing about yours.

## STEP 3: Trigger Live and Observe at the Consumer

Trigger the event with a REAL action (a real subagent run, a real session start, a real inbound
request) — not a simulated call to the handler. Then check BOTH ends:

1. **Fired?** — the scratch-file line exists (the platform invoked the tracer).
2. **Delivered?** — the nonce is observable at the intended CONSUMER surface (the parent loop's
   context, the downstream system, the next session).

These are independent facts; the hub's failure was exactly a yes-fired/no-delivered split.

## STEP 4: Decide From the Matrix

| Fired | Delivered | Decision |
|---|---|---|
| yes | yes | Build. Cite the probe (nonce, date, platform version) in the implementation PR |
| yes | no | STOP the build. Record a platform gap; keep any prepared artifact on disk UNWIRED with a note naming the re-wire condition |
| no | — | Do not build. Re-check event name/wiring once; if still silent, the surface does not exist for your case |
| flaky | — | Treat as `no` for anything load-bearing; note the observed reliability (e.g. SessionEnd fires only on clean exits — design for the reliable event instead) |

## STEP 5: Record the Probe Result

Append the result where the next builder will look (the project's platform-reference doc or
lessons file), including: event, platform/CLI version probed, fired/delivered verdicts, nonce
evidence, and date. Platform behavior changes across versions — a probe result carries its
vintage, and a `no` from three versions ago is worth re-probing.

## MUST DO

- Always run the probe against the REAL trigger, not a direct invocation of the handler — Why:
  direct execution passed on the hook whose event-path delivery was broken
- Always test delivery to the exact consumer you will build for — Why: payloads can reach the
  event's own subject yet never reach the parent loop that needs them (the SubagentStop case)
- Always include the platform version in the recorded result — Why: results expire; an unversioned
  "doesn't work" blocks future adoption after the platform fixes it
- Always keep a refuted assumption's artifact unwired-with-a-note rather than deleting it — Why:
  the re-wire condition ("when SubagentStop context reaches T0") makes future adoption a
  one-step change

## MUST NOT DO

- MUST NOT ship the real implementation and the probe as one change — probe first, build second —
  Why: the combined path is how two hub mechanisms shipped inert and needed reverts
- MUST NOT extrapolate one event's delivery semantics to a sibling event — probe each — Why:
  SessionStart and SessionEnd have materially different firing reliability in the same platform
- MUST NOT accept "the docs say it works" from anyone (including yourself) as a probe substitute —
  run STEP 3 instead — Why: both recorded incidents were doc-conformant builds
- MUST NOT leave a yes-fired/no-delivered result unrecorded — write the platform gap down —
  Why: unrecorded gaps get rediscovered at full build cost
