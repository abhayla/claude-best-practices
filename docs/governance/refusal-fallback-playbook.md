# Refusal → fallback + model-swap playbook (owner-approved 2026-07-10)

Full text of the owner-approved model-routing addition (fable-window item 7). The always-on
rule `.claude/rules/model-routing.md` carries the compact directive; this file is the playbook
it points to. Facts verified against the claude-api reference + the cached
`docs/claude-references/model-config.md` — supersedes the unverified INBOX pending items.

## Refusal → fallback

Fable/Mythos safety classifiers can DECLINE a request as a SUCCESS: HTTP 200 with
`stop_reason:"refusal"` (+ `stop_details.category`: cyber|bio|reasoning_extraction|frontier_llm|null).

- API scripts: branch on `stop_reason`, NEVER on exit code or `content[0]`. A pre-output
  refusal has empty content and is unbilled; a mid-stream refusal bills the partial —
  discard it, don't treat it as a complete answer.
- New `claude-fable-5` API code opts into server-side fallbacks BY DEFAULT:
  `betas:["server-side-fallback-2026-06-01"]` + `fallbacks:[{"model":"claude-opus-5"}]`
  (on Bedrock/Vertex/Foundry use the SDK's client-side `BetaRefusalFallbackMiddleware`).
- Claude Code sessions: a flagged request auto-re-runs on default Opus with a transcript
  notice; HEADLESS/autonomous runs instead END THE TURN with a refusal — pipelines must
  treat a refusal-ended turn as "reroute to opus and continue", not as a task failure.
- Never prompt a Fable/Mythos dispatch to echo its raw chain-of-thought — that is the
  `reasoning_extraction` refusal class; decision rationale / process summaries are fine.

## Operational facts (verified 2026-07-14 against platform.claude.com/docs — refusals-and-fallback, adaptive-thinking, migration-guide)

- **Sticky routing:** after a conversation falls back, later `fallbacks`-bearing requests for
  that conversation route STRAIGHT to the fallback model for ~1 hour (org-scoped, content-hash
  of the conversation prefix + serving model; message content not stored; best-effort — the
  requested model may still be retried; non-streaming requests only in the current release).
  A sticky-served turn carries NO `fallback` content block — detect it by the
  `fallback_message` entry in `usage.iterations` plus the response's `model` field. During an
  incident, "everything suddenly serves from Opus for a while" is this feature, not a bug.
- **Fallbacks don't propagate into nested model calls:** the `fallbacks` parameter does NOT
  reach model calls made inside tool execution — every sub-agent/nested call needs its own
  fallback config. Budget refusal handling per REQUEST, not per turn (one turn can produce
  several refusals across an agent + its sub-agents).
- **Refusals are invisible to error-rate monitoring** (they are HTTP 200): emit one event per
  refusal and one per fallback-served response (`fallback_message` in `usage.iterations`),
  and alert on the gap between the two counts.
- **Claude Code native flag:** headless/CLI runs pass `--fallback-model <model>` (or the
  `fallbackModel` setting) instead of hand-rolling the "reroute to opus" step — flag verified
  present in the local CLI (`claude --help`, 2026-07-14). The transcript-notice auto-re-run
  described above covers interactive sessions; the flag covers headless.
- **Thinking summaries default OFF on Fable 5:** `thinking.display` defaults to `"omitted"`
  (prior models defaulted to `"summarized"`) — any tooling that reads thinking summaries gets
  empty text unless `display: "summarized"` is set explicitly.
- **Prompt-cache minimum dropped to 512 tokens** for Fable 5 on the Claude API (still 1,024 on
  Bedrock) — prompt blocks of 512+ tokens now qualify for the ~90%-discount cache read.

## Task budgets + send_to_user (raw-API agentic loops — verified 2026-07-14)

- **Task budgets (beta `task-budgets-2026-03-13`):** `output_config.task_budget:
  {"type":"tokens","total":N[,"remaining":M]}` injects a model-only-visible countdown across
  the whole agentic loop (thinking + tool calls + tool results + output). ADVISORY, not
  enforced — `max_tokens` stays the hard cap. Minimum `total` 20,000; Fable 5 / Mythos 5 /
  Opus 4.8 / Opus 4.7 only (NOT Sonnet 5, NOT Claude Code/Cowork surfaces). A budget too
  small for the task triggers refusal-LIKE behavior (decline, aggressive scope-down, early
  partial stop) — if a budgeted run stops early unexpectedly, RAISE the budget before
  debugging anything else. Don't decrement `remaining` client-side while resending full
  history: it double-counts (the server doesn't re-count resent turns), under-reports the
  budget, and invalidates the prompt-cache prefix. Composes with the loop-domain retry
  budgets in the loop-engineering spec §3.8/§3.9 — token budget ≠ work-retry budget.
- **send_to_user tool:** long async raw-API agents get a client-side `send_to_user` tool
  (input schema: one `message` string; render it verbatim, return a simple ack) so mid-task
  deliverables/progress reach the user without ending the turn. Defining the tool is NOT
  sufficient — Fable rarely calls it unprompted; pair it with system-prompt elicitation
  ("when you have content the user must read verbatim, call send_to_user") and never route
  narration/reasoning through it. The hub's equivalent for Claude-Code-driven loops is the
  Notifier gateway (loop-engineering spec §3.9).

## Model swap when the Fable window closes

The tier table in `.claude/rules/model-routing.md` is unchanged; only the "omit model
(inherit frontier)" row re-points — frontier judgment dispatches then inherit opus (4.8).
No other tier moves.
