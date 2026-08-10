# Scope: global

# Model Routing — cheapest sufficient model per dispatch (owner directive 2026-07-03)

Set `model` explicitly on EVERY Agent()/workflow dispatch — inheriting the frontier main-loop model is a deliberate choice, never a default (Anthropic practice: the orchestrator reasons; subagents run on the smallest model that fits):

| Tier | Dispatch it for |
|---|---|
| `haiku` | rubric scoring, blind re-grades, classification, extraction, format checks |
| `sonnet` (DEFAULT for execution) | any explicit brief + machine-checkable gate: eval runs, itemized fix workers, code edits per plan, research, docs |
| `opus` | deep debugging, architecture analysis, multi-file work with design freedom |
| omit `model` (inherit frontier) | ONLY frontier judgment: novel unrubriced design, subtle spec reasoning, the final ship-gate adversarial verification |

When torn pick the cheaper tier; escalate ONE tier after 2 supervised failures (record the routing lesson).
Checker MAY differ from maker (model diversity).
Verification rigor NEVER drops with the tier — cheap execution, full supervision.

## Preemptive category routing (owner-approved 2026-07-14 — don't eat the refusal round-trip)
Worker categories KNOWN to trip Fable's safety classifiers route straight to `opus`, never fable:
security scanning / vulnerability analysis / exploit-adjacent audits (security-auditor-agent,
prompt-injection testing, authz-gap hunting) and any dispatch a prior run saw refused with
`category:"cyber"`. Reactive fallback (below) stays as the safety net for everything else —
this rule removes the predictable refusals (and the confusing ~1h sticky-routing tail they
trigger) from workloads we KNOW are classifier-adjacent.

## Refusal→fallback + Fable-exit swap (owner-approved 2026-07-10 — playbook: docs/governance/refusal-fallback-playbook.md)
Fable/Mythos can DECLINE as a SUCCESS (HTTP 200, stop_reason:"refusal"): branch on stop_reason, never exit code; new claude-fable-5 code defaults to server-side fallbacks (betas:["server-side-fallback-2026-06-01"] + fallbacks:[{"model":"claude-opus-5"}]); a HEADLESS flagged run ENDS THE TURN — reroute to opus and continue, don't fail; never ask a Fable dispatch to echo raw chain-of-thought (reasoning_extraction). Fable-window close: only the "omit model" row re-points to opus.

## Effort dial — set per PASS, not per session (verified vs official docs 2026-07-14)
Effort is a first-class COST lever, not just quality (same task measured ~6x cheaper at medium
vs max — practitioner data, Willison 2026-06-09). Official Fable guidance: start `high` (the API
default), `xhigh` ONLY for capability-sensitive work, step down to `medium`/`low` for routine —
low-effort Fable often beats xhigh on prior models. Sequence per pass: first design/build pass
`high` (or `xhigh` when frontier-hard), fix-up/mechanical passes `low`. Knobs: Workflow `agent()`
`effort:` opt; Agent() dispatches inherit session effort; raw API `output_config.effort`. At
high/xhigh set a large max_tokens. "ultracode" = `xhigh` + standing multi-agent permission, not a
6th API level. Task-budget composition + details: docs/governance/refusal-fallback-playbook.md.

## Session-level routing (owner directive 2026-07-13 — supersedes habit, not the dispatch table)
Fable 5 is for FABLE-ONLY work; if Opus or Sonnet can do it with the same effectiveness, THEY do it
— Fable must not burn tokens on work a cheaper tier handles. This applies to the SESSION DRIVER,
not just Agent() dispatch:
- Route to a CHEAPER-DRIVEN session (Opus driver, or /loop-engineering with sonnet maker + opus
  checker): any work with a written plan + machine-checkable gates (planned clusters, migrations,
  test-debt /debugging-loop runs, scout-finding processing, routine loop cycles).
- Reserve FABLE-driven sessions for: novel governance/architecture design with no plan yet,
  adversarial final verification of strategic changes, updating the Operating Manual itself,
  and incident-class problems after a cheaper tier failed twice.
- Fable's standing duty when driving: make this call EXPLICITLY at task intake and hand off
  (plan file + .remember handoff) rather than executing cheap work itself.
