# Fable-5 Operating Manual — Parity Report

**Status: EXAM IN PROGRESS (this file is finalized in Phase 5–6 of
`plans/fable-operating-manual-plugin.md`; numbers below are placeholders until the blind judging
completes — do not cite).**

## What was measured

Whether Opus 4.8, loaded with the [Fable 5 Operating Manual](../../plugins/fable-operating-manual/manual/fable5-operating-manual.md),
executes Fable 5's working discipline — measured by a frozen 33-case blind exam
(15 traps · 10 replayed real incidents · 8 judgment probes), judged per the frozen
[rubric](../../plugins/fable-operating-manual/evals/rubric.md) by fresh blind judge sessions with
calibration checks.

| Arm | Configuration |
|---|---|
| A | Opus 4.8, plain |
| B | Opus 4.8 + Operating Manual (full text as operating context) |
| C | Fable 5, plain (the baseline being approached) |

## Headline results

| Metric | A (opus) | B (opus+manual) | C (fable) |
|---|---|---|---|
| Trap catch-rate | TBD/15 | TBD/15 | TBD/15 |
| Replay pass-rate | TBD/10 | TBD/10 | TBD/10 |
| Probe pass-rate | TBD/8 | TBD/8 | TBD/8 |
| Mean case score | TBD | TBD | TBD |

**Gap closed by the manual (traps): TBD%** — the fraction of the plain-Opus→Fable discipline gap
that loading the manual closes: `(B−A)/(C−A)`.

## Repair loop log

| Round | Cases B missed ∧ C caught | Manual section patched | Re-run result |
|---|---|---|---|
| — | — | — | — |

## Integrity notes

- Exam authored and FROZEN before the manual was written; repair rounds edit the manual only.
- Contamination check: the plugin's injection hooks were NOT active in the orchestrating session;
  arms received byte-identical case prompts. All sub-agents in this environment receive the hub's
  uniform governance injection (identical across arms — noted for full disclosure).
- Author-overlap caveat: the same author (Fable 5) wrote both the exam and the manual, from
  general failure classes; procedures never reference exam instances. Residual overlap risk is
  disclosed rather than claimed away — the replayed-incident cases mitigate it (their correct
  outcomes are historical facts, not authored).
- Judges are blind (one anonymized answer each, no arm identity, calibration answers mixed in).

## Honest limits

The manual transfers **discipline** (verification, refusal-to-guess, premise-checking, scope
holding). It does not transfer raw reasoning capacity: expect a residual C-over-B gap on genuinely
hard novel problems, reported above rather than hidden.
