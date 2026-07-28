# Scope: global

# Model-Cost Routing — premium-model sessions dispatch execution via /get-work-done

version: "1.0.0"

**Origin:** owner directive, 2026-07-28 (gorefer main session, running Fable 5): "whenever we
are working on a Fable model, always use the get-work-done skill … always ensure you are using
the cheap and best model for the task … as and when we find any issue, keep fixing and updating
it, so it keeps self-improving iteratively."

## The rule

When the session's own model is a **premium tier (Fable / Mythos / Opus)**, the session acts as
the **decision layer**, and execution work MUST be routed to the cheapest-correct model instead
of being burned on the premium loop:

1. **Dispatchable work → `/get-work-done`.** Any self-contained repo task with a stateable
   Definition of Done — code changes, test-suite runs, refactors, doc updates, migrations,
   hardening sweeps — MUST go through `/get-work-done`, which sizes the task honestly, picks the
   cheapest-correct model, and lands it via PR + CI-gated merge with an independent checker.
   Batch multiple tasks into one dispatch call when they arrive together.
2. **Mechanical in-session subtasks → cheap subagents.** Where dispatch overhead is not
   justified (a quick fan-out search, a bulk mechanical edit inside the current mission), use
   the Agent tool with an explicit cheaper `model` override (haiku/sonnet) rather than
   inheriting the premium model.
3. **What MUST stay in the premium session** (do NOT dispatch): owner-in-the-loop decisioning
   (recommendation → input → approval iterations), secrets/credential handling, live-system
   operations that need this session's authenticated MCP surfaces (Zoho, Wati, artifact SSOT
   edits), and anything the owner has explicitly placed in an interactive operating mode.
4. **Sizing honesty beats reflex-routing.** If wrapping a task in a contract costs more than
   doing it (a one-line config flip, a single read-and-answer), do it in-session — but say so.
   The test: would a checker-verified PR add value, or only latency?

## Self-improvement loop (the rule about the rule)

Every time `/get-work-done` or this routing **misfires** — wrong model picked, a task that
should have been dispatched but wasn't (or vice versa), contract friction, checker gaps, a
setting that fought the owner's intent:

- **In the same session**, write the `mistake → root cause → rule` lesson through the hub
  lessons flow (`continuous-improvement.md` / `learnings-routing.md`).
- **Fix the cause where it lives**: update the get-work-done skill body, its settings, or THIS
  rule — and version-bump this file so drift is visible.
- Never work around a get-work-done defect silently twice: the second occurrence MUST become a
  codified fix.

## Interaction with other rules

- `decision-authority.md` still governs *when to ask*; this rule governs *where execution runs*.
- The get-work-done skill's own gates (upfront question batching, contract per task,
  merge-on-green) are unchanged by this rule — this rule only makes invoking it mandatory-by-
  default on premium-model sessions.
