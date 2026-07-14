# Contract-injection experiment — pilot results (2026-07-14)

**Verdict: directionally CONFIRMED (pilot, n=1 per arm).** With identical briefs and identical
sonnet workers, the no-contract arm shipped a user-facing integration failure on its flagship
command; the contract-injected arm integrated with zero mismatches. Recommendation at the end;
adopting the pattern into hub orchestration rules stays owner-gated (rule 5).

Owner-approved as "decision E" of the 2026-07-14 Fable-usage scan (scan item #10). Motivating
external claim: a 13-agent build reporting "seven agents consumed one contract with zero
integration mismatches" (single-source). Motivating hub wound: parallel-edit agent teams
measured 1/3 autonomous completion (2026-06-23), failing exactly at integration — the Execute
tier is human-supervised because of it.

## Design

- **Task:** 3-module Python expense-tracker CLI (`storage.py`, `report.py`, `cli.py`), stdlib
  only. The CLI *surface* was pinned in the brief for both arms (so the smoke test is fair);
  the *inter-module* interfaces were the experimental variable.
- **Arm A (control):** 3 sonnet workers in parallel, shared brief only, no coordination — each
  told the others exist and to assume their interfaces.
- **Arm B (treatment):** 1 sonnet architect first produced a minimal interface contract (dict
  shape, exact function signatures, import direction, error behavior); the SAME worker prompts
  then carried the contract verbatim ("implement to this exactly").
- **Isolation:** each worker wrote exactly one file, forbidden from reading siblings; separate
  scratchpad dirs per arm.
- **Measurement:** the orchestrator (not a worker) ran an identical 4-command smoke scenario
  against each arm — `add` ×2, `list`, `report` — counting distinct cross-module integration
  defects observed.

## Results

| | Arm A — no contract | Arm B — contract-injected |
|---|---|---|
| add / add / list | PASS | PASS |
| report | **FAIL** — `AttributeError: module 'report' has no attribute 'generate_report'` | PASS (`Total: 15.50`, per-category correct) |
| Integration defects | **1** (cli assumed `report.generate_report(expenses) -> dict`; report worker built `compute_total`/`compute_by_category`/`format_report`) | **0** |
| Assumed cross-module seams that held | 2 of 3 (storage calls aligned by luck) | 3 of 3 (by construction) |
| Extra cost | — | 1 architect call (~13s sonnet, ~zero marginal tokens vs a worker) + longer worker prompts |

Notable texture: Arm A's CLI worker *itself* flagged the risk in its return ("this contract will
need reconciling at integration") — the worker knew it was guessing; without a contract channel
there was nowhere for that knowledge to go before integration. The seam that broke was the one
the brief constrained least (report's interface), exactly where theory predicts.

## Honest limits

- **n=1 per arm, one task, one model tier.** This is a pilot, not proof; Arm A's 2-of-3 lucky
  alignments show single-trial variance is real. The external "zero mismatches at 13 agents"
  claim remains unreplicated at that scale.
- The task is small (3 modules); contract value should GROW with fan-out width and seam count,
  but that's extrapolation, not measurement here.
- Architect quality is a new single point of failure the control arm doesn't have — a wrong
  contract binds everyone to the same mistake (mitigation: contracts are cheap to review at T0
  before fan-out).

## Wider trial (2026-07-14, owner-approved follow-up) — CONFIRMED, adopted

5-module inventory-manager CLI (storage/validate/filters/report/cli, ~6 interface seams),
2 independent trials per arm, identical sonnet workers, identical 8-command smoke gauntlet
run by the orchestrator (3 valid adds, 1 invalid add, 3 list variants, report):

| Build | Integration defects | Detail |
|---|---|---|
| A1 — no contract | **4** | cli assumed `validate.validate_item(item)` (TypeError — actual takes name/qty/price), `validate.normalize_item` (absent), `filters.filter_items` (absent), `report.summarize` (absent). EVERY command failed, including valid `add` (exit 1). |
| A2 — no contract | **2** | cli assumed validate returns an error string — actual raises (invalid add dies with a raw traceback instead of a clean error); `filters.filter_items` absent (all `list` variants dead). `add`/`report` aligned by luck. |
| B1 — contract | **0** | 8/8 correct, invalid add cleanly rejected (exit 1, proper message) |
| B2 — contract | **0** | 8/8 correct, invalid add cleanly rejected |

**Combined with the pilot: no-contract 3/3 builds defective (7 distinct guessed-interface
defects); contract-injected 3/3 defect-free.** The strongest arm-A failure (A1: 100% of
commands broken) shows defect count GROWS with seam count, as predicted. Architect cost per
trial: one sonnet call, ~18s. The recurring defect shape is exactly the one contracts remove:
a consumer guessing a producer's function name/signature/error convention.

**Adopted:** `agent-orchestration.md` §11 now REQUIRES interface contracts for parallel-edit
fan-outs (owner-approved 2026-07-14, applied same day; registry 1.7.0).

## Original recommendation (pre-trial, retained for the record)

Adopt contract-injection as the DEFAULT dispatch pattern for parallel builds where workers'
outputs must interlock: a foundation/architect step (or wave-1 workers' return contracts)
produces exact interface contracts, and the T0 orchestrator injects them verbatim into every
downstream worker prompt. Concretely this means amending `agent-orchestration.md` §11
(Mandatory Context Passing) to require *interface contracts* — exact signatures/shapes — for
parallel-edit fan-outs, not just artifact paths + summaries, and threading the same requirement
through `/development-loop`/`/implement`'s parallel modes. Those are registered-rule changes →
proposed here, not applied. A second, wider trial (5+ modules, 2 trials per arm) is the cheap
way to firm the evidence first if preferred.
