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

## Recommendation (owner-gated next step)

Adopt contract-injection as the DEFAULT dispatch pattern for parallel builds where workers'
outputs must interlock: a foundation/architect step (or wave-1 workers' return contracts)
produces exact interface contracts, and the T0 orchestrator injects them verbatim into every
downstream worker prompt. Concretely this means amending `agent-orchestration.md` §11
(Mandatory Context Passing) to require *interface contracts* — exact signatures/shapes — for
parallel-edit fan-outs, not just artifact paths + summaries, and threading the same requirement
through `/development-loop`/`/implement`'s parallel modes. Those are registered-rule changes →
proposed here, not applied. A second, wider trial (5+ modules, 2 trials per arm) is the cheap
way to firm the evidence first if preferred.
