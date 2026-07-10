# Plan: `fable-operating-manual` plugin (approved item 1 of Fable-window program)

**Owner approval:** Abhay approved item 1 only (2026-07-10), explicitly as a PLUGIN, built fully
autonomously. Approval covers the 2 rule additions (distilled-manual rule inside the plugin +
subagent-injection hook). Aggressive Fable spend authorized. Proof bar: full trap-test on a cheap model.

**Goal (plain English):** before the free Fable 5 window closes, extract Fable's reasoning
*procedures* into a portable Operating Manual, package it as an installable plugin, and PROVE with a
blind 3-arm exam that Opus 4.8 running the manual approaches Fable's discipline — so every process
keeps working and improving after Fable is gone.

**Branch/worktree:** `feat/fable-operating-manual-plugin` at `D:/Abhay/VibeCoding/cbp-wt-fable-manual`
(hub checkout stays on `main`; concurrent session shares it — do NOT edit the main checkout).

## Deliverables (all inside `plugins/fable-operating-manual/` unless noted)

- **D1 Manual** — `manual/fable5-operating-manual.md`: self-contained, portable; entries in
  Trigger → Procedure → Example → Prevents form. Sections: read-intent-beneath-words;
  decompose-into-independently-checkable-pieces; effort-by-cost-of-error (incl. dormancy);
  re-derive-everything (no "just editing" exemption); known-vs-guessed registers (inline labels);
  attack-own-conclusion (specific disproof attempt); answer→reasoning→risk reporting;
  failure-modes-that-look-like-competence catalogue; verification-before-done; scope discipline;
  a pre-send self-test checklist (run on every answer; dormant tasks pass automatically) and the
  precedence rule (a correctness flag outranks every format/length instruction) — full coverage of
  the Khairallah Operating Manual structure (owner cross-checked 2026-07-10) EXTENDED with
  Fable-specific + repo-specific procedures the article lacks.
  Grounded in THIS repo's git history + `.claude/tasks/lessons.md` (failure archaeology), not
  self-flattery.
- **D2 Exam** — `evals/`: ~30–40 cases, authored BEFORE D1 is finalized. Three types:
  `traps/` (planted subtle checkable errors: % math, fabricated source, test-that-tests-nothing,
  false premise, false-done claim, agreeable-reversal pushback, scope-creep bait),
  `tasks/` (replayed real repo tasks with known-correct outcomes from git/lessons),
  `probes/` (should-ask-not-guess judgment). Plus `rubric.md` (fixed scoring: caught-trap y/n,
  correct y/n, re-derived y/n, guessed-where-should-ask y/n; weights).
- **D3 Harness** — `skills/model-parity-test/SKILL.md`: one-command exam runner. Dispatches fresh
  isolated Agent() sessions pinned per arm (A=opus plain, B=opus+manual, C=fable), identical inputs,
  anonymize+shuffle answers, separate blind judge grades vs rubric, emits scorecard. Reusable for ANY
  future model (`/model-parity-test <model>`).
- **D4 Injection layer** — (a) `rules/fable-operating-manual.md` distilled rule (≤100 lines,
  auto-loaded when plugin installed); (b) `hooks/hooks.json` + `hooks/manual-inject.sh`
  (SubagentStart: inject distilled core into every dispatched worker). NEVER declare hooks in
  plugin.json (auto-loaded; duplicate = error).
- **D5 Report** — `docs/fable-operating-manual/PARITY-REPORT.md` (hub docs, not plugin): A vs B vs C
  catch-rates, task pass-rates, cost-per-passed-task, repair-loop iterations, honest gap statement.
- Plugin scaffold: `.claude-plugin/plugin.json` (version 0.1.0, NO hooks key), `README.md`,
  marketplace.json entry, CLAUDE.md plugins-bullet update (4 → 5 plugins).

## Phases

1. **Scaffold** plugin dirs + plugin.json + marketplace entry + README stub. ✅ when `claude plugin validate` passes.
2. **Exam first (D2)** — traps/tasks/probes + rubric. Freeze before D1. Mine git log + lessons.md for
   replay tasks. ✅ when ≥30 cases with unambiguous expected outcomes.
3. **Manual (D1)** — I (Fable) author, grounded in repo history; then distill rule (D4a) ≤100 lines.
4. **Harness (D3) + injection (D4)** — skill + hook; `bash -n` hooks; smoke via `--plugin-dir`.
5. **Run arms** — A/B/C on full exam via Agent dispatches (model pinned: opus/opus/fable; B gets
   manual in prompt context). Blind judge (separate agent, shuffled anonymized answers).
6. **Repair loop** — traps B misses ∧ C catches → Fable rewrites that manual section procedurally →
   re-run those traps. Stop when B's misses stop improving (≤2 rounds gain) or parity plateau.
7. **Land** — STEP 5 gate: pre-git-merge-checker-agent (full CI) + `claude plugin validate` +
   `--plugin-dir` smoke → commit `feat(fable-operating-manual): scaffold ... (v0.1.0)` → push →
   PR + auto-merge armed. D5 report to owner. STEP 8: installed-test via `--plugin-dir` acceptance
   run (fresh install validation counts toward G6 later).

## Constraints / conventions

- Component dirs at plugin ROOT; only plugin.json in `.claude-plugin/`.
- Marketplace entry required; NOT in registry/patterns.json.
- Model routing: Fable (me/main loop or model-omitted agents) authors manual + traps + repairs;
  sonnet for mechanical execution; judge = opus (blind, fresh). Arms exactly as specified.
- Secret scan + full local CI before push. `.claude/` gitignored → this plugin is under `plugins/`
  (normal staging); no `.claude/` copies needed (plugin-as-SSOT from day one, per prompt-auto-enhance
  graduation precedent).
- Honest reporting: manual transfers discipline, not intelligence; report the residual Fable gap.

## State log (append as phases complete)

- 2026-07-10: worktree created, plan written. Phase 1 next.
- 2026-07-10 (Phase 5 SONNET RESULT): manual-Sonnet RECOVERED ALL 4 plain-Sonnet failures
  (T01 10/10, T11 10/10, R03 10/10, P07 8/10-pass) — 27/29 judged cases at 10/10. Plain-Sonnet
  baseline: 14/15 traps, 9/10 replays, 7/8 probes, mean 8.8. Outstanding: 5 sonnet-B answers being
  regenerated after over-strict CASE-TAG matching discarded valid replies (P02,P04,P06,P08,T07);
  harness hardened twice (placeholder-detection + tag-format tolerance, committed). Then: judge
  those 5 → final scorecard → land.
- 2026-07-10 (Phase 5 interim): ARM-C CONDUCTOR DEFECT caught by blind judging (24-file +3
  rotation in answers/); fixed deterministically (fingerprint script + rename + purge 14 corrupted
  judgments + re-judge); harness SKILL hardened (CASE-TAG echo + save-immediately + STEP 2.5
  fingerprint gate, committed). INTERIM A-vs-C RESULT: opus plain 33/33 mean 10.0, fable 33/33
  mean 9.6 → NO separable discipline gap at this difficulty inside the governed hub env (ceiling +
  home-field confounds disclosed). EXTENSION: sonnet candidate run launched (arms A/B, results in
  parity-results/20260710-sonnet/) to locate where the discipline gap starts — that's the model
  post-Fable routing actually uses. Opus arm B still completing (for no-harm confirmation).
- 2026-07-10: Phases 1–4 DONE (commits 8146537, +manual, 70931c7): scaffold+marketplace, exam
  frozen (33 cases + rubric + calibration), manual v1.0 + distilled core, hooks (validated live)
  + harness skill. Phase 5 RUNNING: 3 arm conductors dispatched (A=opus, B=opus+manual, C=fable),
  answers land in parity-results/20260710-opus/answers/ (target 99); keys extracted to keys/;
  aggregation script ready in session scratchpad (aggregate_parity.py). Next on arm completion:
  anonymize → 2 judge conductors (opus judges, 1 answer each, calibration mixed in) → aggregate →
  repair loop → land.
