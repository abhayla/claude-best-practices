# Fable-Window Program — master state & handoff (updated 2026-07-10, item 2+4 DONE)

**What this is:** the owner-approved program to use the free Fable 5 window to fix the factory's
ROOT PROCESSES so improvement continues after Fable leaves. This file is the single resume point —
a cold session reads THIS first, then the linked plans.

## Locked decisions (owner, via grill — do not re-ask)

| Decision | Value |
|---|---|
| Goal scope | Hub/factory processes ONLY (not 5Wealths-wide) |
| Ranking | G5 north-star first (autonomous self-improving machine) |
| Execution model | Present list → owner approves items → build approved items fully autonomously |
| Fable budget | Aggressive — window is the asset; cheapest-sufficient routing still applies |
| Proof bar | EVERY item ships with machine-checkable DoD + CI green + Fable-independence trap-test on a cheap model |

## Item status

**✅ 1. Fable Operating Manual plugin — DONE** (PRs #313 + #315 merged; plan:
`plans/fable-operating-manual-plugin.md`; report: `docs/fable-operating-manual/PARITY-REPORT.md`;
memory: `project_fable_operating_manual_plugin.md`). Proven: Sonnet+manual 33/33 blind exam
(plain Sonnet 4 failures); Opus 4.8 needs no manual; clean-room acceptance validated (v0.1.1
fixed silent hookEventName drop). Still owed someday for full G6 bar: real `/plugin install` in a
second project.

**✅ 2. Real-run trust-score graduation engine — DONE** (PR #317 merged 2026-07-10): zero-manual
merged-PR trust recorder wired into `auto-pr-reconcile.sh` SessionStart; per-skill ledger fields +
`stats_by`; Verified-by evidence gating (85 verified / 60 unverified / hard-gate veto proven by a
planted false-done trap at score 35). First live sweep recorded 15 real PRs, ATLAS ledger 28/30.
PR #317 itself was logged as a false-confidence run (AUTO but needed a checker fix round) — the
program's first honest calibration point.

**✅ 4. Trap-test mode in /skill-evaluator — DONE** (PR #318 merged + round-3 meta-eval, both
2026-07-10): trap mode in `/skill-evaluator` (v2.4.0, dual-home synced) +
`references/trap-test-protocol.md`; proof bar MET on round 3 (NOT-CERTIFIED verdict for a weak
asset carrying non-re-derivable planted falsehoods; round 2's re-derivable-formula miss is
honestly documented as a weak-trap-type lesson now encoded in the protocol). Detail:
`.claude/skills/skill-evaluator/evals/2026-07-10-trap-mode-meta-eval.md` §"Round 3".

**✅ 3, 5–10: ALL DONE (2026-07-10)** — built fully autonomously per the item-1 playbook
(worktree maker ≠ opus checker + cheap-model trap-test before every landing, CI-gated auto-merge):

3. **Standing-goal ledger** ✅ PR #319 — goals/ predicates + daily standing-goals.yml sentinel +
   /end-session STEP 5b enrollment; malformed goals are failures, never skipped; checker caught
   the missing-labels reporting blocker pre-merge.
5. **Governance dormancy** ✅ PR #322 — turn-origin.sh classifier (human|machine, dual-home synced),
   enhance ceremony human-prompts-only (owner decision + owner-approved rule diff applied),
   plugin 0.4.0 full_process_scope, rule-compliance lint, dormancy audit (15 DEMOTE candidates
   await owner case-by-case).
6. **Cost ledger** ✅ PR #323 — cost_ledger.py + config/model-costs.yml + SessionStart tick +
   >$50/day Notifier alert; checker caught the partial-day-freeze blocker on live data; first
   honest measurement: main frontier loop ≈90% of $300–1,000/day API-equivalent.
7. **Refusal→fallback rule** ✅ PR #321 — owner-approved model-routing addition (compact, fits the
   320-line budget) + docs/governance/refusal-fallback-playbook.md; verified vs claude-api ref.
8. **Bilevel self-improvement** ✅ PR #324 — loop-engineering v1.3.0 strategy ledger + mutation
   axes + novelty gate in the FEEDBACK arm; plugin 0.2.0; 3/3 sonnet orchestrators mutated the
   stuck strategy instead of retrying.
9. **Platform loop taxonomy** ✅ PR #326 — spec §3.7/§3.8 (4 native loop types, routing table,
   budget introspection), loop-engineering v1.4.0, plugin 0.3.0; 5/5 routing trap-test; live
   ScheduleWakeup tool-schema citations captured to docs/claude-references/.
10. **Plugin validation pipeline** ✅ PR #325 — validate_plugin_cleanroom.(py|sh) 3-gate pipeline;
    first sweep 4/4 owing plugins PASS at the serve-validation bar (the heavier second-project
    /plugin install G6 bar remains a separate, owner-framed standard); found `claude plugin
    validate` silently accepts hooks-in-manifest.

**PROGRAM COMPLETE.** Open owner decisions: (a) G6 framing — does automated serve-validation
upgrade the 4 swept plugins, or does the second-project install bar stand? (b) the 15
DEMOTE-candidate rule directives in docs/governance/2026-07-10-dormancy-audit.md. Lessons:
.claude/tasks/lessons.md 2026-07-10 entries (rebase-before-push, rules line budget, security-flag
transcript isolation).

## Context sources for a cold session (in order)

1. THIS file. 2. `plans/fable-operating-manual-plugin.md` (how item 1 was run — reuse its
patterns: worktree isolation, conductor/judge orchestration, fingerprint gates, maker≠checker).
3. Auto-memory `project_fable_operating_manual_plugin.md`. 4. `.claude/tasks/lessons.md` (3 fresh
lessons from item 1: batch-misfiling, hookEventName silent drop, SSOT-first). 5.
`docs/process-improvement/INBOX.md` pending queue (verified refusal-fallback facts for item 7).

## Standing constraints for the executor session

- Worktree isolation for every build (shared main checkout + concurrent sessions).
- Plugin work routes through `/plugin-lifecycle` (version bump = propagation; hookEventName trap).
- Rule-file changes need explicit owner approval per his standing rule 5.
- Maker≠checker on everything; conductors save-immediately + content-fingerprint gate before
  trusting fan-out results (item-1 lessons — all three defects were catches by checker layers).
- Report to owner: answer-first, plain English (he asked for simple-English explanations).
