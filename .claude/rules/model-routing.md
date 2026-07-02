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
