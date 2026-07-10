# Proposed rule-file diffs — 2026-07-10 (fable-window item 5, Part D)

**STATUS: APPLIED (owner-approved 2026-07-10, "Approve as shown").** The diff below was applied to
`.claude/rules/prompt-auto-enhance.md` on this same branch (separate commit) with the approved
wording verbatim. To stay inside the 320-line hub-rules budget (`test_rule_organization.py`), prose
the new text supersedes was compressed in the same file — the hook-gating intro, the slash-command
paragraph, the "unconditional on OUTPUT" paragraph, and the Grade-A "kills prior over-fire"
historical note — semantics unchanged. This file remains the approval record.

## Owner decision being encoded (LOCKED 2026-07-10)

> The FULL visible enhance process (transcript + grade card + independent reviewer + final prompt)
> fires ONLY on human-typed prompts. Autonomous continuations, background task-notifications,
> scheduled wakeups, and skill-execution turns get at most a one-line banner.

This resolves the conflict flagged in `plans/fable-window-program.md` item 5 (owner previously
preferred the FULL visible process vs. his own rule-5 minimalism): the full process stays the
default **for human prompts**, and machine-origin turns are carved out. Part A of this PR already
implements the behavior via the shared `.claude/hooks/turn-origin.sh` predicate; this diff makes the
RULE text match the implemented behavior so the two don't drift.

## Proposed diff — `.claude/rules/prompt-auto-enhance.md`

```diff
--- a/.claude/rules/prompt-auto-enhance.md
+++ b/.claude/rules/prompt-auto-enhance.md
@@ -25,12 +25,20 @@
 multi-step answer, tool edits/commits), self-apply the banner + full process (transcript
 + grade card + final prompt) + `Role:` line + governance tail even with no reminder injected. The Stop hook `no-overask-guard.sh`
 logs substantive turns missing the banner to `.claude/.enhance-misses.log` (telemetry,
-non-blocking). Genuinely trivial turns (`yes`/`go ahead`) and slash-command turns are exempt.
+non-blocking). Genuinely trivial turns (`yes`/`go ahead`), slash-command turns, AND **machine-origin turns**
+are exempt. **Machine-origin (owner decision 2026-07-10, LOCKED — fire-where-it-pays):** the full
+visible process fires ONLY on HUMAN-typed prompts. A task-notification, scheduled-wakeup,
+skill-execution, or system-reminder-only turn is NOT human-typed — it gets at most a one-line banner,
+never the transcript/grade-card/reviewer ceremony (autonomous work still owes the governance tail).
+The classification is deterministic and shared: `.claude/hooks/turn-origin.sh` `classify_turn()` is
+the SSOT, sourced by both `prompt-enhance-reminder.sh` and `no-overask-guard.sh` so they cannot drift.
 
 ## MANDATORY OUTPUT — sampled: full process on WEAK prompts, one-liner on strong ones (#290)
 
-SAMPLED, not blanket-mandatory: the full pipeline (transcript + grade card + independent
-reviewer) is REQUIRED only on a **WEAK prompt** (a dimension scored < 7, or a fix was applied).
+SAMPLED, not blanket-mandatory, and **HUMAN-SCOPED** (owner 2026-07-10): the full pipeline
+(transcript + grade card + independent reviewer) is REQUIRED only on a HUMAN-typed **WEAK prompt**
+(a dimension scored < 7, or a fix was applied). Machine-origin turns (see turn-origin.sh) are exempt
+from the whole ceremony — banner included.
 A **STRONG / Grade-A / zero-fix** prompt just needs the banner + a one-line Grade-A declaration
 — no full table forced. Kills prior over-fire (blocking a plain status answer to strengthen).
```

**Rationale (one paragraph):** The rule currently says the enhance indicator is "unconditional on
substantive OUTPUT — even when the hook stayed silent," which is exactly the wording that caused
autonomous turns to be graded like human prompts (416 entries in `.enhance-misses.log`, largely
machine-origin — see `2026-07-10-dormancy-audit.md`). The edit adds a fourth exemption class
(machine-origin) alongside the existing trivial/slash-command exemptions and points the reader at
the single deterministic classifier (`turn-origin.sh`) so the rule, the reminder hook, and the Stop
guard all reference one SSOT. It is additive and minimal: the human-prompt behavior (full process on
weak prompts, one-liner on strong) is byte-for-byte unchanged; only the machine-turn carve-out is new.

## Other rule files

The Part-C audit's DEMOTE candidates (15 zero-telemetry directives across `claude-behavior.md`,
`claude-docs-cache.md`, `context-management.md`, `model-routing.md`, `product-incubation.md`,
`workflow.md`) are **not** drafted here. Several are load-bearing doctrine worth keeping even when
unmeasured; a DEMOTE pass is a separate, case-by-case owner review, not a mechanical edit. No other
rule file needs a text change to encode the fire-where-it-pays decision — the predicate lives in the
hooks + the one `prompt-auto-enhance.md` edit above.
