---
name: outcome-scorecard-live
description: "The outcome scorecard stays wired into telemetry and keeps producing a LIVE, varying trust score — never a constant, never a fabricated rate."
enrolled: "2026-08-16"
source: "T-144 (Fix 5 + Fix 1)"
last_verified: "2026-08-16"
predicates:
  - kind: file
    path: scripts/measure_outcomes.py
  - kind: command
    cmd: "grep -q measure_outcomes .github/workflows/aggregate-telemetry.yml"
  - kind: command
    cmd: "python -c \"import sys; sys.path.insert(0,'.'); from scripts.trust_score import compute_trust_score, DEFAULT_CONFIG as C; base={'tests_pass':1.0,'coverage':None,'regression_clean':1.0,'secret_scan_clean':1.0,'production_health':1.0}; a=compute_trust_score({**base,'independent_verification':1.0},C)['score']; b=compute_trust_score({**base,'independent_verification':0.0},C)['score']; sys.exit(0 if a!=b else 'trust score is CONSTANT across differing evidence — the gauge is dead again')\""
  - kind: command
    cmd: "python -c \"import sys; sys.path.insert(0,'.'); from scripts.measure_outcomes import invocation_adoption; r=invocation_adoption(None,[]); sys.exit(0 if r['value'] is None else 'invocation_adoption fabricated a rate from an empty sample')\""
on_failure: "Either measure_outcomes.py lost its telemetry wiring, or the trust score stopped responding to differing evidence (the constant-60 dead-gauge regression), or a metric started fabricating a rate from no data. Re-read the T-144 notes in config/trust-score.yml and scripts/measure_outcomes.py."
---

**Outward-pointing invariant: does the number still MEAN anything to the people reading it?**

T-144 repaired a gauge that had been silently dead: `record_merged_prs.py` recorded
`coverage=0.0` for evidence that could never exist on that path, subtracting a fixed penalty
from every run until all 133 recorded ATLAS runs scored an identical 60. Nothing looked
broken — runs accrued, the dashboard rendered, N/30 climbed — and the G5 graduation gate was
reading a number that could not move.

That is the precise failure class this ledger exists for, so the repair itself gets enrolled
rather than trusted to stay fixed. The third predicate is the load-bearing one: it feeds the
engine two runs that differ ONLY in independent verification and fails if they score the
same. Any future change that reintroduces a constant — a hardcoded signal, an over-eager
default, a renormalization bug — trips it the next morning instead of after another 133 runs.

The fourth predicate guards the other half of the honesty contract: "no data" must stay a
first-class answer. The metric it checks replaced a file-exists adoption rate that reported
1.0 from a sample of 1 — a tautology dressed as a measurement. If `invocation_adoption` ever
returns a number for an empty sample again, the scorecard has started lying in the same way
the thing it replaced did.

All predicates are hermetic (no network, no `gh`) per `goals/README.md`.
