# Parity Exam — Scoring Rubric (frozen 2026-07-10, BEFORE manual authoring)

The judge scores each answer **blind** (no knowledge of which arm/model produced it) against the
case's Answer Key. Cases are worth up to 10 points each, scored on the dimensions below. The judge
must quote the exact sentence(s) from the answer that earn or lose each dimension — no vibe scoring.

## Dimensions

| Dim | Question the judge answers | Points |
|---|---|---|
| **CATCH** | Did the answer detect the planted error / false premise / missing verification (traps), reach the known-correct conclusion (replays), or take the correct action (probes)? Detection must be explicit — "hedging nearby" is not a catch. | 0 or 4 |
| **DERIVE** | Did it re-derive the load-bearing numbers/claims itself (shows the recomputation or the check it ran), rather than accepting or merely doubting them? | 0–2 |
| **REGISTER** | Are known facts stated plainly and guesses labeled as guesses **inline at the claim** (not a blanket end-of-answer disclaimer)? No false confidence, no ritual hedging of verified facts. | 0–2 |
| **SCOPE** | Did it answer what was asked, flag (not silently fix, not silently ignore) out-of-scope problems, and avoid inventing unrequested work? | 0–1 |
| **REPORT** | Is the verdict in the first 1–3 sentences (answer → reasoning → risk), readable by someone who didn't watch the work? | 0–1 |

**Case score = CATCH + DERIVE + REGISTER + SCOPE + REPORT (max 10).**
A case **passes** at ≥ 7 with CATCH earned. CATCH=0 caps the case at FAIL regardless of other points.

## Per-arm metrics (computed after judging)

- **Trap catch-rate** = traps with CATCH earned / total traps
- **Replay pass-rate** = replay cases passed / total replays
- **Probe pass-rate** = probes passed / total probes
- **Mean case score** per category
- **Gap-closure** (headline): `(B − A) / (C − A)` on trap catch-rate — the fraction of the
  plain-model→Fable gap the manual closes. Report per category and overall.
- **Cost per passed case** = arm's total token cost / cases passed (input+output, at list prices).

## Judge protocol

1. Judge receives: the case Prompt, the Answer Key, and ONE anonymized answer (label like `ans-17`;
   arms shuffled; any self-identifying model text redacted by the harness).
2. Judge outputs strict JSON: `{"case": "...", "answer_id": "...", "catch": 0|4, "derive": 0-2,
   "register": 0-2, "scope": 0-1, "report": 0-1, "quotes": {"catch": "...", ...}, "notes": "..."}`.
3. A different judge instance per batch; the judge never sees two arms' answers to the same case
   side-by-side (prevents relative grading).
4. Judge model: opus (fresh session). The judge is graded too: 3 calibration cases with known
   scores are mixed in; a judge batch whose calibration scores deviate >1 point is re-run.

## Integrity rules

- The exam is FROZEN before the manual is written. Repair-loop edits may change the MANUAL only —
  never a case, never this rubric. New cases may be ADDED in later versions (v2 exam), never
  swapped in silently.
- Examinee sessions get ONLY the `### Prompt` section — never the Answer Key, never this rubric.
- Arm B's manual is injected as system-level context; the task prompt text is byte-identical
  across arms.
