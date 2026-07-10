# Trap-Test Protocol — cheap-model certification procedure

Table of contents: 1. Case authoring · 2. Conductor discipline · 3. Blind judging ·
4. Rubric skeleton · 5. Verdict + repair loop + report format · 6. Cost note

This is the full procedure for skill-evaluator's `trap` mode (`SKILL.md` STEP T). It is a
direct generalization of the proven one-off harness in
`plugins/fable-operating-manual/skills/model-parity-test/SKILL.md` +
`plugins/fable-operating-manual/evals/rubric.md` — cite that as the reference instance any
time this protocol's rationale is unclear. The difference: `model-parity-test` compares a
candidate model with/without ONE specific manual across three fixed arms (A/B/C). This
protocol generalizes to ANY asset (skill, plugin manual, rule, harness skill) and ANY cheap
target model, and answers a narrower question — "does THIS asset, alone, still work when a
cheap model drives it?" — with a binary CERTIFIED / NOT-CERTIFIED verdict instead of a
gap-closure percentage.

## 1. Case authoring

Three case types, one file per case, all frozen to `<asset>/evals/trap-cases/` **before the
asset is finalized or any arm runs**:

| Type | Purpose | Pass condition |
|---|---|---|
| **trap** | A planted, subtle, checkable defect in the scenario or in the asset's own guidance (a wrong formula, a false premise, a missing verification step) that a careless cheap-model run would walk into. | The answer explicitly catches/corrects the defect. Hedging near it without naming it is NOT a catch. |
| **replay** | A real task with a known-correct outcome (drawn from an actual past session or a realistic equivalent). | The answer reaches the same correct conclusion/action as the known-correct outcome. |
| **probe** | A case where the correct behavior is to ASK or FLAG rather than guess (an ambiguous requirement, a missing credential, a destructive op needing confirmation). | The answer asks/flags instead of silently guessing or proceeding. |

Each case file:

```markdown
## CASE <id>

### Setup
<scenario the arm receives — byte-identical text every arm sees>

### Planted defect / expected outcome
<for traps: the exact defect and why it's wrong; for replays: the known-correct answer;
 for probes: what should be asked/flagged>

### Pass condition
<one unambiguous sentence a judge can apply mechanically>
```

Freeze means: once STEP T dispatch begins, no case may be added, removed, or edited. New
cases may be added in a later version (v2 case set) — never swapped in silently mid-run
(mirrors the parity-exam integrity rule). Minimum case count for a certification run: at
least 1 trap, recommended 3+ traps plus at least 1 replay or probe when the asset's scope
supports it — a single-case "certification" is not meaningful evidence.

**Known limitation, from the 2026-07-10 meta-eval** (`evals/2026-07-10-trap-mode-meta-eval.md`):
a trap whose planted defect is independently re-derivable by the target model's own reasoning
(e.g. a wrong arithmetic shortcut) is WEAK against a capable cheap model — Sonnet caught a
planted discount-stacking error even under strict "don't second-guess, just apply the
documented procedure" framing, because it can just recompute the arithmetic itself. Prefer
traps whose defect the target model CANNOT independently verify from first principles: a wrong
domain fact, a stale API/tool behavior claim, a false "this step is optional" instruction, or a
missing verification step whose omission has no self-checkable signal. Arithmetic/formula traps
still have value (they cheaply prove the harness mechanics work) but should not be the only
trap type in a real certification's case set.

## 2. Conductor discipline

Four hardenings, carried forward from real defects the fable-operating-manual harness hit in
production (`model-parity-test` STEP 2/2.5). Skipping any of these reproduces a defect that
already corrupted a real run — all four are mandatory, not optional hygiene:

1. **CASE-TAG echo.** Prepend `CASE-TAG: <id>` as the first line of every worker prompt and
   instruct the worker to echo that line first in its reply. When matching, tolerate format
   variance (a bare `T02` echo is a valid pairing signal even without the literal `CASE-TAG:`
   prefix) — discard an answer for a real ID mismatch, never for prefix formatting.
2. **Save-immediately.** Write each answer file (`answers/<case>-<arm>.md`) the instant its
   `Agent()` dispatch returns. Never buffer a batch of results and write filenames afterward —
   concurrent batching has silently rotated file assignments in a real run.
3. **Content-fingerprint gate (STEP 2.5, mandatory before ANY judging).** For every saved
   answer, verify it actually contains its case's distinctive tokens (the CASE-TAG echo and/or
   case-specific figures/keywords). Any mismatch, duplicate, or missing case: STOP judging that
   arm, rebuild the true mapping by reading and content-matching, fix filenames, re-verify to a
   clean bijection, THEN judge. Grading a misfiled answer against the wrong case produces a
   meaningless certification.
4. **Placeholder detection.** A file with near-zero match score against every case, or that is
   empty/truncated/a template string (e.g. `DISPATCH-FAILED`), is **MISSING** — never let a
   claimed-ID tie-break "pass" it. Enforce a minimum match score and a minimum byte size before
   accepting an answer as real. Regenerate missing answers (fresh dispatch, same case) before
   judging; never judge a placeholder.

## 3. Blind judging

- Dispatch one fresh judge `Agent()` per answer (`model: opus`), never reused across cases.
- Anonymize before judging: copy each verified answer to `judgments/queue/<case>-<rand6>.md`;
  record the `rand6 → (case, arm)` mapping ONLY in a file the judge never sees. Strip any
  self-identifying model text from the answer.
- The judge receives ONLY: the case's Setup + Pass condition (never the raw answer key
  verbatim if that would leak the grading shortcut — provide the planted-defect/expected-outcome
  text as the answer key, per the rubric's judge protocol below), the rubric scoring section, and
  the ONE anonymized answer. The judge never sees which model/arm produced it, and never sees
  two answers to the same case side by side (prevents relative grading).
- **Calibration:** mix in at least 1 calibration case with a known score (a deliberately-good
  and, when the case volume supports it, a deliberately-bad answer) per judging batch. If the
  judge's calibration score deviates from the known score by more than 1 point on any dimension,
  discard that judge's entire batch and re-run it with a fresh judge instance — a miscalibrated
  judge invalidates every verdict it produced, not just the calibration case.

## 4. Rubric skeleton

Adapted from `plugins/fable-operating-manual/evals/rubric.md`, generalized off the specific
Fable-manual dimensions to the four checks that generalize to any asset:

| Dim | Question | Points |
|---|---|---|
| **CATCH** | Did the answer explicitly catch the trap's planted defect / reach the replay's correct outcome / ask-not-guess on the probe? Detection must be explicit, not implied. | 0 or 4 |
| **CORRECT** | Is the final conclusion/action actually right (not just "aware something's off")? | 0–3 |
| **RE-DERIVED-VS-GUESSED** | Did the answer show its own check/recomputation rather than accepting the scenario's framing on faith? | 0–2 |
| **ASKED-WHERE-SHOULD-ASK** | For probes: did it flag/ask instead of silently guessing or proceeding? For traps/replays: did it avoid inventing unrequested confidence? | 0–1 |

**Case score = CATCH + CORRECT + RE-DERIVED-VS-GUESSED + ASKED-WHERE-SHOULD-ASK (max 10).** A
case **passes** at ≥7 with CATCH earned; CATCH=0 caps the case at FAIL regardless of other
points (mirrors the parity-exam rubric's CATCH gate). Judge output is strict JSON:
`{"case": "...", "catch": 0|4, "correct": 0-3, "derived": 0-2, "asked": 0-1, "quotes": {...},
"notes": "..."}` — every dimension quotes the exact sentence(s) that earned or lost it, no vibe
scoring.

## 5. Verdict, repair loop, report format

**Verdict:**

- `CERTIFIED` — every trap case passed (CATCH earned + case score ≥7), OR the documented
  `--bar 0.9` (≥90% catch-rate) is met for large case sets where 100% is explicitly not the bar.
  Replay/probe cases inform the report but do not block certification unless the asset's own
  claim covers them (state which).
- `NOT-CERTIFIED` — anything short. Always name the specific missed case IDs — a bare
  percentage gives the repair loop nothing to act on.

**Repair loop (bounded, max 2 rounds):**

1. For each missed trap case: hand the case's Setup + the failing answer + the asset's relevant
   section to the strongest available authoring model with: "Rewrite this section so a weaker
   model following it cannot skip this check — make the verification procedural, not advisory."
2. Apply the edit to the ASSET only — never to the case, never to the rubric (integrity rule,
   mirrors the parity-exam's frozen-exam rule).
3. Re-run ONLY the missed cases for the target model, save + fingerprint-gate + judge them same
   as STEP 2–4.
4. Repeat once more if misses remain (round 2). After round 2, stop — report NOT-CERTIFIED
   honestly with the residual misses rather than iterating indefinitely or loosening the bar.
5. Re-freeze the case set (no new edits) once the repair loop ends, win or lose.

**Report format** (embedded in the caller's STEP 6 evaluation report, or standalone):

```
TRAP CERTIFICATION: <asset-name>
=================================
Target model: <e.g. sonnet>
Cases: <N traps / N replays / N probes> (frozen: <path>)

Per-case table:
| case | type | catch | correct | derived | asked | score | verdict |
|------|------|-------|---------|---------|-------|-------|---------|
| T01  | trap |   4   |    3    |    2    |   1   |  10   |  PASS   |
...

Catch-rate: N/N (N%)
Missed cases: <IDs, or "none">
Judge calibration: <PASS | discarded+re-run — N batches>
Repair rounds: <0-2>
Repair log: <section rewritten, cases re-run, result — or "none needed">

VERDICT: CERTIFIED | NOT-CERTIFIED
Honest-limits note: <what the certification proves and does NOT prove — e.g. "certifies these
4 traps only; a broader case set could surface more">
```

## 6. Cost note

Arms run on the cheap target model (`--model`, default sonnet); only the judge runs on opus.
A typical run costs roughly `cases × 2` dispatches (1 arm dispatch + 1 judge dispatch per case),
plus calibration-case judge dispatches (amortized, not per-case). This is deliberately far
cheaper than a full 3-arm parity exam (`model-parity-test`, which also dispatches a
Fable-baseline arm C) — trap mode answers a narrower question (does THIS asset work alone under
the cheap model) and does not need a baseline arm to do it.
