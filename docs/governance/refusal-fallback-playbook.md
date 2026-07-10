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
  `betas:["server-side-fallback-2026-06-01"]` + `fallbacks:[{"model":"claude-opus-4-8"}]`
  (on Bedrock/Vertex/Foundry use the SDK's client-side `BetaRefusalFallbackMiddleware`).
- Claude Code sessions: a flagged request auto-re-runs on default Opus with a transcript
  notice; HEADLESS/autonomous runs instead END THE TURN with a refusal — pipelines must
  treat a refusal-ended turn as "reroute to opus and continue", not as a task failure.
- Never prompt a Fable/Mythos dispatch to echo its raw chain-of-thought — that is the
  `reasoning_extraction` refusal class; decision rationale / process summaries are fine.

## Model swap when the Fable window closes

The tier table in `.claude/rules/model-routing.md` is unchanged; only the "omit model
(inherit frontier)" row re-points — frontier judgment dispatches then inherit opus (4.8).
No other tier moves.
