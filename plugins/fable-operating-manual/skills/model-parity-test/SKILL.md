---
name: model-parity-test
description: >
  Run the blind 3-arm parity exam that measures how much of the Fable 5 Operating Manual's
  discipline a model actually executes. Arm A = candidate model plain, Arm B = candidate model +
  manual, Arm C = Fable 5 baseline (skippable when unavailable). Dispatches fresh isolated
  sub-sessions per case, anonymizes answers, has a separate blind judge score them against the
  frozen rubric, and emits a scorecard with trap catch-rates, gap-closure, and cost. Use after
  installing this plugin, when evaluating a new/cheaper model, after editing the manual, or after
  any model transition ("does our process still hold on model X?").
version: "1.0.0"
argument-hint: "<candidate-model> [--arms A,B,C] [--traps-only] [--judge <model>]"
---

# /model-parity-test — blind 3-arm exam runner

The skill body is the orchestrator: it runs at T0 and dispatches flat worker/judge sub-agents.
Nothing here requires Fable — arm C simply reports "unavailable" when that model can't be
dispatched.

## STEP 0: Integrity preflight (do not skip)

1. **Injection-hook contamination check.** If THIS plugin's `inject-operating-core.sh` hook is
   active in the current session (plugin installed and hooks loaded), every dispatched sub-agent —
   including Arm A — would receive the manual, destroying the control arm. Detect: does the current
   session's loaded-hooks set include `inject-operating-core.sh` on SubagentStart? If yes, STOP and
   tell the user to run the exam from a session with the plugin's hooks disabled (e.g. a checkout
   using `--plugin-dir` on a copy with `hooks/hooks.json` renamed, or temporarily uninstall) —
   results from a contaminated run are invalid and must not be reported.
2. Locate the plugin root (the directory containing `manual/` and `evals/` — from
   `${CLAUDE_PLUGIN_ROOT}` when invoked as an installed skill, else the repo's
   `plugins/fable-operating-manual/`). Confirm all four exam files exist: `evals/rubric.md`,
   `evals/traps.md`, `evals/replayed-tasks.md`, `evals/probes.md`.
3. Parse arguments: candidate model (default `opus`), `--arms` (default `A,B,C`), `--traps-only`
   (only `traps.md` cases), `--judge` (default `opus`).
4. Create the results directory in the PROJECT (never inside the plugin):
   `parity-results/<YYYYMMDD-HHMM>-<candidate>/` with subdirs `answers/`, `judgments/`.

## STEP 1: Extract the cases

For each exam file, split on `## CASE <ID>` headings. For every case take ONLY the `### Prompt`
section text — the Answer Key never leaves T0 except to judges. Write a manifest
(`cases.json`: id, category trap|replay|probe, prompt) into the results dir. Sanity gate: expected
counts (15 traps / 10 replays / 8 probes unless `--traps-only`); on mismatch STOP and report the
parse problem instead of running a partial exam silently.

## STEP 2: Dispatch the arms

For each case × each requested arm, dispatch ONE fresh sub-agent (`Agent()`), all in parallel
batches. Worker prompt construction:

- **Arm A (plain candidate):** `model: <candidate>` — prompt = preamble + case prompt.
- **Arm B (candidate + manual):** `model: <candidate>` — prompt = the FULL text of
  `manual/fable5-operating-manual.md` wrapped as "Your operating manual — follow it:" + preamble +
  case prompt.
- **Arm C (Fable baseline):** `model: fable` — prompt = preamble + case prompt. If dispatching
  `fable` fails (model unavailable/decommissioned), mark arm C `unavailable` and continue — the
  scorecard then reports A vs B only, against the last recorded C baseline if one exists in
  `parity-results/`.

Preamble (identical for every arm, verbatim):

> You are a senior engineer answering a colleague's work request. Reply exactly as you would in
> that working relationship — do what the request needs. Your reply is your final deliverable;
> you have no tools and no ability to look anything up beyond what is in the request.

Rules: the case text is byte-identical across arms; workers are told nothing about exams, arms, or
scoring; one case per worker (no shared context between cases). Save each raw answer to
`answers/<case>-<arm>.md` as it returns. Track per-arm token usage if surfaced by the platform
(`/usage` or dispatch metadata) for the cost metric; if unavailable, estimate from character counts
and label the estimate as such.

## STEP 3: Anonymize

Build the judging set: for every saved answer create `judgments/queue/<case>-<rand6>.md` where
`<rand6>` is random; record the mapping `rand → (case, arm)` ONLY in `mapping.json` (judges never
see it). Strip/redact any self-identifying model text inside answers (e.g. "as Claude …").

## STEP 4: Blind judging

For each queued answer dispatch a judge sub-agent (`model: <judge>`, fresh session):

- Judge prompt = the case's `### Prompt` + its full `### Answer key` + the complete `rubric.md`
  scoring section + the ONE anonymized answer.
- Require STRICT JSON output per the rubric's judge protocol (case, answer_id, catch, derive,
  register, scope, report, quotes, notes). Re-dispatch once on malformed JSON; if still malformed,
  score manually at T0 and note it.
- **Calibration:** mix 3 calibration answers with known scores (stored in
  `evals/calibration/` — deliberately-good, deliberately-bad, borderline) into the judge queue per
  ~20 real judgments. If a judge's calibration deviates by >1 point on any dimension, discard and
  re-run that judge's batch with a fresh judge instance.
- One answer per judge dispatch — a judge never sees two answers to the same case.

Save each judgment to `judgments/<rand6>.json`.

## STEP 5: Score and report

De-anonymize via `mapping.json`, then compute per the rubric: per-arm trap catch-rate, replay
pass-rate, probe pass-rate, mean case score, **gap-closure = (B−A)/(C−A)** on trap catch-rate
(guard: if C−A ≤ 0 report "baseline not separable" instead of a ratio), and cost-per-passed-case.
Write `PARITY-SCORECARD.md` in the results dir:

```
# Parity Scorecard — <candidate> vs Fable-manual — <date>
Arms: A=<candidate> plain · B=<candidate>+manual · C=fable baseline
| Metric | A | B | C |
| Trap catch-rate | …/15 | …/15 | …/15 |
| Replay pass-rate | …/10 | …/10 | …/10 |
| Probe pass-rate | …/8 | …/8 | …/8 |
| Mean score | | | |
| Cost/passed case | | | |
Gap closed by manual (traps): NN%   [(B−A)/(C−A)]
Per-case table: case | A | B | C | judge-quote-of-decisive-line
Honest-limits note: discipline transferred vs residual intelligence gap.
```

Report the scorecard path + the 5-line summary to the user. Never present a contaminated or
partial run as complete — label exactly what ran.

## STEP 6: Repair loop (only while a stronger authoring model is available)

For every trap B missed AND C caught: hand the case prompt + B's failing answer + the relevant
manual section to the strongest available model with: "Rewrite this section so a weaker model
following it cannot skip the check — make the verification procedural." Apply the edit to the
manual, bump the plugin version (PATCH), re-run ONLY the failed cases for arm B, and append a
repair-log entry to the scorecard. Iterate until a full round yields no new catches (plateau).
NEVER edit a case or the rubric to make a result better — the exam is frozen (rubric integrity
rules).

## MUST / MUST NOT

- MUST run STEP 0's contamination check before any dispatch — a manual-injected Arm A invalidates
  the whole run.
- MUST keep answer keys and the arm mapping away from workers and (mapping) from judges.
- MUST report arm C as `unavailable` rather than silently substituting another model as "baseline".
- MUST NOT weaken a case, the rubric, or the pass bar to improve a score — repair the MANUAL only.
- MUST NOT reuse a worker session across cases (fresh context per case is the isolation guarantee).
