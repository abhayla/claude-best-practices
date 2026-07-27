# Eval: model-routing gap hardening (v0.2 → v0.3), 2026-07-27

**Scope:** owner-approved "fix all" on the 12-gap audit of the cheapest-correct delegation
path (audit + approval in-session; design amendment: `plans/get-work-done-dispatcher.md`
"Amendment 2026-07-27").

## What was tested (deterministic fixtures, all green)

### verify-model-tier.py (fix #1) — 5/5
| Case | Expected | Result |
|---|---|---|
| Real T-001 receipt vs sonnet contract | exit 0 TIER-OK | PASS |
| Opus contract, sonnet ran | exit 1 mismatch | PASS |
| Fable model in modelUsage | exit 1 forbidden | PASS |
| result.json without modelUsage | exit 1 (unverified ≠ pass) | PASS |
| Mixed usage, haiku subagent + sonnet dominant | exit 0 (dominant rule) | PASS |

### contract-lint.py additions (fixes #6/#8) — 7/7
| Case | Expected | Result |
|---|---|---|
| `model: opus` bare (no rationale) | BLOCK | PASS |
| `model: sonnet` + rationale, plain task | OK | PASS |
| Security audit on sonnet | BLOCK (preemptive opus) | PASS |
| Security audit on opus + data_source | OK | PASS |
| Opus + "typo" mechanical hint | WARN only, exit 0 | PASS |
| Data-read without data_source (regression) | BLOCK (pre-existing gate) | PASS |
| Pre-existing well-formed contract (regression) | OK | PASS |

### cost-rollup.py (fixes #9/#10) — 4/4
| Case | Expected | Result |
|---|---|---|
| First real rollup over bus heartbeats | 3 tasks recorded (T-001, T-003, T-wati-report-blindspot) | PASS |
| Re-run (idempotency) | 0 new | PASS |
| Today total 1400 vs ceiling 1000 | exit 2 CEILING-EXCEEDED | PASS |
| Non-numeric ceiling | WARN + exit 0 (explicit NO-OP, never silent) | PASS |

### Gate regressions
- `check_fleet_script_health.py <GWD> --caller SKILL.md` → **clean** after all edits
  (keeper-tick.cmd rollup call follows the errorlevel-logging pattern; no detect-then-discard).
- settings.json remains valid JSON; `daily_token_ceiling` numeric; `max_turns_by_tier` present.

## Prose-rule verification (SKILL v0.3)
Scenario traces walked: (a) security task → table routes opus, lint blocks a sonnet slip;
(b) sonnet refusal → contract edited to opus + re-lint + re-preflight → relaunch; opus refusal
→ immediate park, no second reroute; (c) 2× capability failure on haiku → single escalation to
sonnet, then park (max ONE escalation — no tier-chaining); (d) trivial task in a Fable session
→ dispatched to a cheap worker, not executed inline. All references resolve (scripts exist on
the bus; settings keys present).

## Round 2 (same day) — verification-gap hardening (V1–V4)

Owner follow-up audit of WHO verifies non-code deliverables found the checker procedure
code/deploy-shaped only. Fixes: `deliverable:` + checkable `dod:` contract fields
(lint-enforced), STEP 7 deliverable-aware checker table (content → claim→source tracing;
claude-resource → /skill-evaluator or scenario run; data → independent re-pull), and the
re-derivation evidence standard (an opinion verdict with no artifact = no verdict).

### contract-lint.py V-additions — 7/7
| Case | Expected | Result |
|---|---|---|
| Full contract (deliverable: content + dod list) | OK | PASS |
| Missing `deliverable:` | BLOCK | PASS |
| `deliverable: prose` (bad value) | BLOCK | PASS |
| `dod:` key with no items | BLOCK | PASS |
| Inline `dod: <text>` (data task + data_source) | OK | PASS |
| Legacy-style contract (no new fields — T-028 shape) | BLOCK w/ explicit reason (intended ratchet; sweep amends at re-queue) | PASS |
| Security-on-sonnet with new fields present (regression) | BLOCK (fix #8 still fires) | PASS |

`check_fleet_script_health.py --caller SKILL.md` → clean after round 2.

## Round 3 (same day) — LIVE FIRE: T-029, owner-directed end-to-end content task

Real task ("document the new verification & cost tooling in the bus README" + fix the stale
"outside every git repo" header claim), dispatched through the full v0.3 path. Every new
mechanism fired live:

| Leg | Live result |
|---|---|
| Fix #4 Fable-trivial guard | Dispatching session was Fable → task went to a sonnet worker via contract, not inline |
| V2 lint (live BLOCK) | Lint blocked the dispatcher's own first contract — "assume" in a prohibition sentence tripped the assumption marker. False-positive class recorded (negated context); contract reworded; re-lint green. Gate demonstrably enforcing |
| Preflight | PREFLIGHT-OK on the newly registered `getworkdone-bus` repo |
| Worker | sonnet, 27 turns, $1.15, scope respected (README only), pushed 3a8d22da |
| Fix #1 tier receipt | TIER-OK live: contracted=sonnet ran=claude-sonnet-5 |
| V1/V4 checker (content procedure) | Independent sonnet checker re-derived ALL 15 README claims against script source (claim→source table with file:line per row), verified all 4 dod predicates, wrote evidence folder + LEDGER line. Verdict PASS. Supervisor spot-check of the checker's own artifacts: genuine |
| Fleet cost ledger | T-029 receipt visible; VPS keeper separately confirmed live (8 VPS tasks rolled into costs.jsonl at the 12:36 IST tick, incl. opus T-015 $8.25) |

**New defect FOUND by the live fire (and fixed):** the user-level branch-lifecycle plugin's
auto-git hook fired INSIDE the worker session, committing the worker's turn onto an
`auto/work-*` branch — the rebase collision stranded the T-029 contract + the settings.json
registry edit on that branch (recovered via `git checkout <checkpoint> -- <files>`). Fix:
`worker-wrapper.ps1` now launches every worker with `AUTO_GIT_DISABLE=1` + `AUTO_PR_DISABLE=1`
(bus @697cfde) — workers own their git per contract, session hooks must never rotate branches
under them. Residual: workers launched WITHOUT the wrapper (raw `claude -p`, Hostinger
launcher) don't get this env — set it in those launch paths when they next change.

## Not covered (honest gaps)
- No live end-to-end fleet dispatch exercising the new reroute/escalation paths — needs a real
  refusal/failure, which can't be fabricated honestly. First live occurrences will be the proof;
  the deterministic halves (lint/preflight/receipt) are what make those paths auditable.
- VPS keeper pickup of the new tick step verified only by convention (bus pull on tick), not
  observed live yet.
