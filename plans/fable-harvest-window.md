# Fable-harvest window plan (owner-approved 2026-07-13)

Owner approved the full plan (Sessions A–C + stretch) after the external scan
(`docs/process-improvement/sources/2026-07-13-fable-window-external-scan-report.md`).
Goal: extract every Fable-required durable asset before paid-only access resumes.
Each session is FABLE-driven (per `model-routing.md` session-level routing); everything
else stays on Opus/Sonnet.

## Session A — rule-stack contradiction audit + prompt-volume audit (scan items #1 + #6)

STATUS: **DONE 2026-07-13** (same session as approval). Deliverable:
`docs/governance/fable-rule-stack-audit-2026-07-13.md` — contradictions, classifications
(KEEP/REWRITE/DEMOTE/DELETE), volume table, proposed diffs. **All rule changes owner-gated**
(claude-behavior rule 5) — nothing applied without explicit approval.

## Session B — failure-archaeology → skill library (scan item #2)

Fable-driven session. Inputs: `git log` (reverted/abandoned/churned commits) + `.claude/tasks/lessons.md`
+ downstream-repo issue history (IPODhan #109, algochanakya #89, KKB, RealFuel, calculatekaro).
Process: 3-phase — (1) discovery: mine the failure record, cluster into failure CLASSES;
(2) 5-question owner interview to resolve forks; (3) author 10–16 `SKILL.md` candidates with
self-review; route through `/writing-skills` + `/skill-evaluator` before any registry entry.
Output: skills cheaper models inherit. Start: `/continue` in a Fable session — this section is the brief.

## Session C — rubric-mining + weakened-test hunter (scan items #3 + #5)

Fable-driven session. Part 1 (rubrics): pull known-good artifacts (clean auto-merged PRs from
`trust-score/ledgers/`) vs known-bad (reverted/CI-red PRs); have Fable derive per-checker scoring
rubrics (code-reviewer-agent, quality-gate-evaluator-agent) from the DIFFERENCE; wire as reference
files the checkers cite. Part 2 (weakened-test hunter): author a verification skill that re-runs
every claimed check, diffs what actually changed, and hunts weakened/deleted assertions
(VERIFIED/CAVEATS/REFUTED verdict) — gap: nothing today catches a fix that passes by gutting its test.
Start: `/continue` in a Fable session — this section is the brief.

## Stretch — trap/eval batteries for top ~10–20 skills (scan item #4)

Only if the window is still open after C. Extend the parity-exam trap technique to per-skill evals
(burns down queue item #8, the 165-skill eval grandfather list). If Fable leaves first, Opus authors
them later from the documented technique (`plugins/fable-operating-manual/evals/`).

## Not-window-sensitive (queued normally, any model)

Scan items #7–#10: full-manual audit-subagent surface; SkillSpector-style pre-install security scan
(+ Graphify evaluation); novelty tracking in self-improvement rounds; doc-level citations.
Tracked in `.claude/tasks/todo.md`.
