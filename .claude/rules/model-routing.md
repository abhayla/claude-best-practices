# Scope: global

# Model Routing — cheapest sufficient model per dispatch

version: "1.0.0"

The T0 session runs on the user-selected model; that is not this rule's concern.
This rule governs every dispatch the orchestrator controls — `Agent(model=...)`,
workflow `agent(..., {model})`, and reviewer/scorer calls. Anthropic's documented
multi-agent practice: the orchestrator carries the frontier reasoning; subagents
doing WELL-SCOPED work run on the smallest model that does the job. Top-tier
(Fable/Opus) usage is a budget — spend it only where lesser models measurably fail.

## Routing table (pick the FIRST row that fits; when torn between two tiers, take the cheaper)

| Tier | Model | Dispatch it for |
|---|---|---|
| Small | `haiku` | Rubric scoring / blind re-grades, classification, extraction, format/schema checks, dedup triage, simple lookups, telemetry parsing |
| Mid (DEFAULT for execution) | `sonnet` | Anything with an explicit brief + machine-checkable gate: eval runs against a written rubric, fix workers applying an itemized finding list, code edits per plan, test writing/running, research + summarization, doc generation, report drafting |
| High | `opus` | Multi-file implementation with real design freedom, deep debugging with unclear root cause, architecture analysis, security audit |
| Frontier | omit `model` (inherit) | ONLY when the task needs frontier judgment: novel design with no rubric, subtle spec/contract reasoning, the FINAL adversarial verification gate where a missed defect ships to users |

## Rules

- MUST set `model` explicitly on every `Agent()`/workflow dispatch per the table —
  omitting it (inheriting the top-tier main-loop model) is a deliberate Frontier-tier
  choice, never a default.
- Escalate-on-failure, don't pre-pay: when unsure between tiers, dispatch the cheaper
  one; if its output fails the supervisor gate twice, re-dispatch one tier up and
  record the routing lesson in `.claude/tasks/lessons.md` (miss → signal → tier).
- Maker ≠ checker composes with this: the checker MAY be a different model than the
  maker — model diversity catches failure modes same-model redundancy misses.
- Supervision is NOT downgraded: whatever tier executes, the T0 supervisor still
  reproduces gates and inspects substance (`supervisor-verification.md`). Cheap
  execution + full verification, never the reverse.
- Repeated haiku-scale calls in one session (e.g. per-turn blind re-grades) stay on
  `haiku` unconditionally — they are rubric applications, not judgment calls.

## CRITICAL RULES

- MUST route every dispatch through the table; frontier-tier inheritance requires the
  task to genuinely need frontier judgment.
- MUST prefer the cheaper tier on uncertainty and escalate only on supervised failure.
- MUST NOT lower verification rigor because execution ran on a cheaper model.
