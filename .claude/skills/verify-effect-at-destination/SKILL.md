---
name: verify-effect-at-destination
description: Verify a change's effect at its CONSUMER's end before claiming done — probe the injected context, served plugin version, delivered message, or written row. Use after wiring or editing any hook, plugin, config, notification, or integration whose value lands somewhere other than the edited file. Accepted/armed/queued/CI-green are promises, not effects.
version: "1.0.0"
type: workflow
triggers:
  - /verify-effect-at-destination
  - "did the hook actually fire"
  - "verify the plugin propagated"
  - "confirm the effect landed"
  - "is it really wired in"
allowed-tools: Read, Bash, Grep, Glob
argument-hint: "<change-description> [consumer-surface]"
---

# Verify Effect at Destination

The artifact is not the effect. This hub's failure record shows the same root cause recurring on
a new surface each time: a change passes syntax checks, direct execution, even CI — and does
NOTHING, because nobody probed the consumer end (a hook whose `additionalContext` was silently
dropped; plugins edited without a version bump so installed copies never changed; a SessionEnd
hook that fires too unreliably to deliver). This skill is the executable checklist that closes
"looks right" → "landed".

## STEP 1: Name the Consumer and the Terminal State

State, in one line each, BEFORE any probing:

1. **Consumer** — who/what receives this change's effect (the model's context window, an installed
   plugin user, a Telegram chat, a DB reader, a CI run on the next PR)?
2. **Terminal state** — the single observable fact that proves delivery (the injected text appears
   in a live session; the served cache copy contains the new line; the message exists in the chat;
   the row reads back; the gate rejects a violating test branch).

Multiple consumers → one verdict block per consumer (a change delivered to one consumer and not
another is a partial delivery, the worst kind to miss). If the request gives too little context
to name the consumer, ask the one clarifying question first; if no observable terminal state can
exist even with full context, the change is not verifiable — redesign it before building further.

Boundary notes: for a change consumed BEFORE it exists (deciding whether a platform event can
carry your payload at all), use `/platform-event-live-probe` — that skill is the before-build
half of this discipline; this one verifies after the change is made. For plugin fixes
specifically, `/plugin-lifecycle` owns the full fix sequence and already embeds this skill's
version-bump + served-cache probe.

## STEP 2: Classify the Delivery Channel

Route to the matching probe. Channels fail silently in channel-specific ways:

| Channel | Silent-failure mode | Destination probe |
|---|---|---|
| Hook output / `additionalContext` | Payload dropped without error; event fires but context never reaches the consumer loop | Trigger the event LIVE in a real session; grep the transcript/consumer context for a unique marker string you planted |
| Installed plugin (skills/hooks/agents) | Claude Code serves a version-keyed cache (`~/.claude/plugins/cache/<mkt>/<plugin>/<version>/`); source edits without a bump serve stale copies forever | Bump version → update/reinstall → `Read` the CACHED copy and confirm it contains the change |
| Notification (Notifier gateway, Wati, Telegram, email) | 200/queued returned, message never delivered (bad template, dead token, filtered) | Fetch the message at the receiving end (chat history, inbox), not the send response |
| DB / config / ledger write | Write goes to the wrong path/env, or a reader uses a different default | Read the row/key back through the CONSUMER's read path, not the writer's handle |
| CI gate / guard hook | Gate wired but pattern never matches, or event never fires at that boundary | Push a deliberately-violating change on a scratch branch; confirm the gate REJECTS it |
| Generated/derived docs | Generator not re-run; stale artifact ships | Regenerate, then diff the derived file — confirm it moved |
| Internal consumer (same process/repo — a function's callers, an imported module) | Callers exercise a path the edit didn't actually change | Here the project's tests ARE the destination probe — run the CONSUMERS' tests, not just the edited unit's. STEP 3's "tests are source checks" applies only to cross-boundary channels above |

## STEP 3: Run the Destination Probe

Execute the probe from STEP 2 before any completion claim.

<constraints>
- `bash -n`, direct script execution, unit tests, and `claude plugin validate` are SOURCE checks,
  not destination probes — every one of them passed on changes that delivered nothing.
- The probe MUST observe the consumer surface itself. If the consumer is a future session or
  another machine, probe the nearest real proxy (the served cache copy, the armed config read
  back through the platform's own API) and say so in the report.
- No environment to run the probe right now (no test channel, no scratch target)? That is a
  legitimate `SOURCE-ONLY-VERIFIED` — report it honestly with a named follow-up; never upgrade
  the verdict because probing was inconvenient.
</constraints>

## STEP 4: Check the Propagation Trigger

Versioned/cached/scheduled paths deliver only on their trigger. Confirm the trigger fired:

- Plugin change → version bumped AND consumer updated/reinstalled
- Cached web asset → purge/redeploy executed
- Cron/scheduled consumer → next run actually executed (check its log), not just scheduled
- `armed` auto-merge / queued job → check the TERMINAL state later or hand off a named follow-up
  ("armed ≠ landed" — record where the confirmation will come from)

## STEP 5: Report With Evidence

Locked output — end the verification with exactly this block:

```
EFFECT VERIFICATION
Change:        <one line>
Consumer:      <who receives the effect>
Terminal state: <the observable fact chosen in STEP 1>
Probe:         <what was executed/observed, with the command or location>
Verdict:       VERIFIED-AT-DESTINATION | SOURCE-ONLY-VERIFIED | NOT-DELIVERED
Follow-up:     <required only for SOURCE-ONLY-VERIFIED: what will confirm the terminal state, when>
```

`SOURCE-ONLY-VERIFIED` is an honest, allowed verdict — claiming VERIFIED without a destination
probe is not.

## MUST DO

- Always plant a unique marker (string/nonce) in the change when probing context/notification
  channels — Why: without a marker you cannot distinguish your delivery from pre-existing content
- Always probe with the CONSUMER's read path, not the writer's handle — Why: writer-side reads
  hid a wrong-path config write until a reader failed in production
- Always re-probe after any subsequent edit to the same surface, AND after environment drift with
  no edit (cache purge, token rotation, platform upgrade) — Why: a later edit or a changed channel
  can silently un-deliver a previously verified effect; the code being untouched proves nothing
  about the channel
- Always record NOT-DELIVERED findings as a platform gap or bug before working around them —
  Why: the SessionStart/SessionEnd reliability gap was only fixed because the failure was recorded

## MUST NOT DO

- MUST NOT claim "done"/"wired"/"live" on a `SOURCE-ONLY-VERIFIED` state — report the honest
  verdict with its follow-up instead — Why: "governance theater" hooks sat wired-but-inert for
  weeks because done was claimed at the source
- MUST NOT treat CI green as a destination probe for runtime channels — run the channel probe
  instead — Why: CI validated a hook whose payload the platform silently dropped
- MUST NOT edit an installed plugin's source and stop — bump the version and verify the served
  cache copy instead — Why: at least 4 hub incidents shipped fixes that no installed copy ever
  received
- MUST NOT skip the probe because the change is small — a one-line hook edit has the same silent
  channels as a rewrite; run STEP 2's probe anyway — Why: the dropped-`additionalContext` change
  was one field
