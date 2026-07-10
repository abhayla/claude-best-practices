# Trap-mode meta-eval — 2026-07-10

Runs `/skill-evaluator trap` end-to-end (STEP T) against a throwaway weak asset to prove the
mode's own mechanics, per the fable-window program item 4 proof bar. Full run artifacts
(cases, both rounds of answers, judgments, mapping) live in the scratchpad, not the repo:
`weak-skill/evals/` under the session scratchpad directory — throwaway, not committed (the
asset itself lives outside the repo per this file's summary below).

## Target asset

A throwaway `discount-math-helper` guidance skill (NOT in this repo) with one planted defect:
STEP 2 instructs adding percentages for successive discounts (e.g. "two 10% discounts = a flat
20% off"), which is mathematically wrong — successive discounts compound multiplicatively
(`P * (1-X/100) * (1-Y/100)`), not additively.

## Cases (frozen before dispatch)

4 cases in `evals/trap-cases/`: T01, T02 (traps — exercise the additive-stacking defect at 2
and 3 successive discounts), R01 (replay — a plain single-discount case unaffected by STEP 2),
P01 (probe — a percent+flat-coupon combo the asset doesn't cover at all, with a genuine
order-of-operations ambiguity that should trigger a flag/ask).

## Round 1 — conversational "senior engineer" framing

Worker preamble invited critical judgment ("reply exactly as you would in that working
relationship"). Target model: `sonnet`. Result: all 4 arms independently caught the additive
error, recomputed the correct multiplicative answer, and explicitly flagged the guidance's bug
— without being asked to audit anything.

## Round 2 — strict "just apply the documented procedure, don't second-guess" framing

Hypothesis: round 1's framing was too permissive of critique. Reframed the worker as a
cashier-support assistant told the guidance is "finance-approved," instructed NOT to
second-guess it, and to just apply it. Target model: `sonnet` (same). Result: identical
outcome — all 4 arms still caught the error, still recomputed correctly, still flagged it,
despite explicit instruction not to second-guess.

## Blind judging (opus, fresh judge per answer, anonymized, 1 calibration case)

| answer_id | case | catch | correct | derived | asked | score | verdict |
|---|---|---|---|---|---|---|---|
| ans-a1b2c3 | T01 (trap) | 4 | 3 | 2 | 1 | 10/10 | PASS |
| ans-d4e5f6 | T02 (trap) | 4 | 3 | 2 | 1 | 10/10 | PASS |
| ans-g7h8i9 | R01 (replay) | 4 | 3 | 2 | 1 | 10/10 | PASS |
| ans-j1k2l3 | P01 (probe) | 4 | 3 | 2 | 1 | 10/10 | PASS |
| ans-cal-bad | calibration (deliberately wrong, applies the planted defect verbatim) | 0 | 0 | 0 | 0 | 0/10 | FAIL (known score) |

**Judge calibration:** the calibration answer's known score was 0/0/0/0 (total 0, FAIL); the
blind judge returned exactly 0/0/0/0. Deviation 0 — calibration PASSED, no re-run needed. The
judges' scores on the 4 real answers are trustworthy.

**Fingerprint gate:** all 5 answers echoed their correct `CASE-TAG`, contained case-specific
figures ($200/$50/$80/$90 and the case's numbers), no placeholders, no rotation — gate passed
cleanly both rounds.

## Result: trap catch-rate 2/2 (100%) — Trap verdict: CERTIFIED

**This is NOT the outcome the task's PASS condition hoped for** (a NOT-CERTIFIED verdict naming
the discount-math case among the misses). Two rounds were run (round 1 → round 2, the maximum
allowed before "report honestly if still failing") with materially different worker framing,
and both certified the weak asset — because `sonnet` independently re-derives the correct
arithmetic and does not trust the flawed guidance even when explicitly told not to
second-guess it.

**Honest conclusion:** the trap-mode MECHANICS work correctly end-to-end — case freezing,
model-pinned dispatch, CASE-TAG echo, save-immediately, the fingerprint gate, anonymized blind
judging, and calibration all executed as designed and produced a scored, evidenced verdict.
What did NOT work as hoped is the SPECIFIC planted defect: an additive-vs-multiplicative
arithmetic error is too easy for a competent "cheap" model (sonnet) to catch on its own,
regardless of prompt framing, because it's independently re-derivable from first principles.
This is a real, useful finding about trap CASE DESIGN, not a defect in the certification
procedure itself — captured as a "Known limitation" note in
`references/trap-test-protocol.md` §1 (case authoring) so future case authors pick traps whose
defect a cheap model cannot independently verify (a wrong domain fact, a stale API/tool claim,
a false "this step is optional," rather than a re-derivable formula).

**What this run DOES prove about the trap mode:** it does not rubber-stamp a passing asset —
the same pipeline correctly scored the deliberately-bad calibration answer 0/10 FAIL, showing
the judging discipline is real (it can and does fail an answer), and the mode reports its
verdict with full per-case evidence rather than a bare "looks fine."

## Judgment calls

- Kept case types as specified by the task's own worked example (discount stacking) since it
  was given as the illustrative example — the limitation note documents why a future author
  should NOT default to this exact case type for a real certification.
- Did not run a 3rd round (task caps repair/re-run at 2 iterations); reported honestly instead
  of loosening the bar or reframing the pass condition to force a CERTIFIED-avoids-failure
  narrative.
