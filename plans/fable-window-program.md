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

**⏳ 3, 5–10: LISTED, EXPLAINED TO OWNER, NOT YET FULLY APPROVED/LANDED.**

3. **Standing-goal invariant ledger** (P0) — status: BUILT + checker round done (1 blocker fixed:
   sentinel issue-labels self-provisioning; byte-exact timestamps; hermetic seed tests); landing in
   flight on `feat/item3-standing-goals`. Labels `standing-goals`/`maintenance` created in the live
   repo. `goals/<name>.md` per finished deliverable with a cheap read-only predicate + daily
   sentinel; finishing = enrollment ("a goal verified once is an assumption with a timestamp"; the
   GA4-silently-dead incident is the motivating example).
5. **Governance dormancy overhaul** (P1) — status: OWNER DECISION LOCKED 2026-07-10: the full
   visible enhance process fires on HUMAN-TYPED prompts only; machine turns (task-notifications,
   wakeups, skill-execution, autonomous continuations) get a one-liner at most. Build in flight
   (fire-where-it-pays classifier + compliance lint + dormancy audit; rule-file diff goes to owner
   before applying — his own rule 5). This session's stop-hook noise was the live evidence that
   triggered the decision.
6. **Self-enforcing cost ledger** (P1) — daily loop-cost ledger + cadence-is-a-cost-decision
   check + Notifier alerts. Critical the day billing starts.
7. **Refusal→fallback + model-swap playbook in model-routing.md** (P2) — VERIFIED facts ready to
   encode (see `docs/process-improvement/INBOX.md` pending queue + claude-api skill: HTTP 200
   `stop_reason:"refusal"`, server-side `fallbacks` beta to opus-4.8). Rule edit → owner approval.
8. **Bilevel self-improvement upgrade** (P2) — outer loop mutates a stuck loop's SEARCH STRATEGY
   (not just lessons) + novelty tracking + success-pattern capture in lessons flow.
9. **Platform-native loop adoption** (P2) — official 4-type taxonomy into loop-engineering spec;
   measure native /goal vs hand-rolled DoD gating; budget introspection.
10. **Repeatable plugin-validation pipeline** (P2) — one-command clean-room install validation;
    run on the 3 unvalidated plugins (+ fable-operating-manual's owed install test).

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
