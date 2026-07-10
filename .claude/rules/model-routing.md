# Scope: global

# Model Routing — cheapest sufficient model per dispatch (owner directive 2026-07-03)

Set `model` explicitly on EVERY Agent()/workflow dispatch — inheriting the frontier main-loop model is a deliberate choice, never a default (Anthropic practice: the orchestrator reasons; subagents run on the smallest model that fits):

| Tier | Dispatch it for |
|---|---|
| `haiku` | rubric scoring, blind re-grades, classification, extraction, format checks |
| `sonnet` (DEFAULT for execution) | any explicit brief + machine-checkable gate: eval runs, itemized fix workers, code edits per plan, research, docs |
| `opus` | deep debugging, architecture analysis, multi-file work with design freedom |
| omit `model` (inherit frontier) | ONLY frontier judgment: novel unrubriced design, subtle spec reasoning, the final ship-gate adversarial verification |

When torn pick the cheaper tier; escalate ONE tier after 2 supervised failures (record the
routing lesson). Checker MAY differ from maker (model diversity). Verification rigor NEVER
drops with the tier — cheap execution, full supervision.

## Refusal → fallback (verified vs claude-api reference, 2026-07-10)

Fable/Mythos safety classifiers can DECLINE a request as a SUCCESS: HTTP 200 with
stop_reason:"refusal" (+ stop_details.category: cyber|bio|reasoning_extraction|frontier_llm|null).

- API scripts: branch on stop_reason, NEVER on exit code or content[0]. A pre-output
  refusal has empty content and is unbilled; a mid-stream refusal bills the partial —
  discard it, don't treat it as a complete answer.
- New claude-fable-5 API code opts into server-side fallbacks BY DEFAULT:
  betas:["server-side-fallback-2026-06-01"] + fallbacks:[{"model":"claude-opus-4-8"}]
  (on Bedrock/Vertex/Foundry use the SDK's client-side BetaRefusalFallbackMiddleware).
- Claude Code sessions: a flagged request auto-re-runs on default Opus with a transcript
  notice; HEADLESS/autonomous runs instead END THE TURN with a refusal — pipelines must
  treat a refusal-ended turn as "reroute to opus and continue", not as a task failure.
- Never prompt a Fable/Mythos dispatch to echo its raw chain-of-thought — that is the
  reasoning_extraction refusal class; decision rationale / process summaries are fine.

## Model swap when the Fable window closes

The tier table is unchanged; only the "omit model (inherit frontier)" row re-points —
frontier judgment dispatches then inherit opus (4.8). No other tier moves.
