# Skill Evaluation Report v2 — loop-engineering v1.2.0 (2026-07-02, re-run)

Re-evaluation AFTER the v1.2.0 eval-driven fixes (PR branch `fix/loop-engineering-eval-defects`),
per `.claude/skills/skill-evaluator/SKILL.md` v2.3.0 (full mode) + `EVAL-WORKFLOW.md` Step 3.5
(mandatory re-evaluate gate), executing plans/loop-engineering-adoption.md item 1.3 re-run.
**Scope honesty:** as in v1, no live autonomous loop was executed (Phase 2's pilot). Method:
(1) every prior finding F1–F13 re-verified against the v1.2.0 TEXT directly (never the
changelog), with supporting-file checks (spec, registry, contracts YAML both copies, guard
tests); (2) an independent context-blind adversarial executability review (fresh subagent, no
prior findings shown, hostile literal-executor walk of all paths) — every one of its findings
re-verified against the text by the supervisor before scoring; (3) reduced honest trigger set
(5 should-trigger + 10 should-not incl. confusable neighbors) × 3 context-blind routing runs
(sonnet ×2 + haiku ×1).

```
SKILL EVALUATION REPORT: loop-engineering (v1.2.0)
=====================================
Mode: full (text-executability adaptation — no live loop run)
Iteration: 2 (re-run after v1.2.0 fixes)

SKILL NECESSITY
  Unchanged from v1: adds clear value (maker/checker split, budgets, preflight
  closure gate, hub-ward telemetry — none exist in an ad-hoc autonomous session).

PRE-FLIGHT (STEP 0)
  0.1 Registry sync:   PASS — hash MATCH (normalized 167d0406…), version 1.2.0
                       consistent (frontmatter = registry = changelog v1.2.0
                       entry present and accurate). All dispatched deps listed.
                       Advisory refs /update-practices, /code-review-workflow
                       still not in deps (not dispatched — accepted in v1).
  0.2 Frontmatter:     PASS — 6 triggers (now inside the 3–6 band; was 7);
                       /goal → /goal-creator (exists in core skills); desc
                       third-person, verb-first, <1024 chars; SemVer OK.
  0.3 Structural:      PASS — 473 lines (<500), 16 fences (balanced), STEPs
                       1→8 contiguous, no dead skill/agent refs (worker agents
                       plan-executor-agent + code-reviewer-agent on disk).
  0.4 Self-update:     N/A — no references/ directory.

TRIGGER EVALUATION (reduced honest set, 15 queries × 3 blind runs)
  Should-trigger:    5/5 activated (15/15 runs, 100%)
  Should-not:        10/10 correctly ignored (0/30 misfires) — incl. neighbors
                     /development-loop, /debugging-loop, /fix-loop,
                     /systematic-debugging, /loop (interval), ralph-loop,
                     /writing-plans, /code-review-workflow, and 2 plain
                     "loop"-keyword coding questions (routed NONE)
  Cross-skill:       0 conflicts; description/trigger changes (7→6 triggers,
                     /goal→/goal-creator) caused no regression
  Trigger verdict:   PASS (sonnet ×2 + haiku ×1, identical routings)

OUTPUT EVALUATION (text executability vs spec)
  Prior findings:    13/13 FIXED in the v1.2.0 text (table below) — including
                     CRITICAL F1 on the default path
  New defects:       0 CRITICAL, 3 MAJOR (N1–N3), 12 MINOR (N4–N15) — all on
                     non-default paths or wording; the success spine
                     (INIT→PREFLIGHT→DISCOVER→PLAN→EXECUTE→4b merge→VERIFY→
                     SHIP→LEARN→loop/REPORT) is coherent end-to-end
  Stress test:       70% unchanged (same 3 v1 MINORs persist — --max-cycles 0
                     undefined, state.json overwritten on re-invocation,
                     unfetchable issue-URL unhandled; none were in F1–F13 scope)
  Output verdict:    FIX (was FAIL) — no CRITICAL remains; the FEEDBACK arm's
                     two non-merge paths need definition before PASS

MODEL COVERAGE
  Tested on:         text-eval; triggers sonnet ×2 + haiku ×1 (identical);
                     adversarial review on default model
  Divergent results: none

OVERALL VERDICT: FIX
Blocking issues: none CRITICAL. Gate to PASS: N1–N3 (three MAJORs, all
introduced or exposed by the F1/F7 fixes — targeted text edits, not a redesign).
```

## Per-prior-finding verification (checked against the v1.2.0 TEXT, not the changelog)

| Prior | Severity | Status in v1.2.0 | Evidence in text |
|---|---|---|---|
| F1 worktree never integrated | CRITICAL | **FIXED (default path)** | New STEP 4b: `pre_merge_sha` recorded, `git merge --no-ff <worktree_branch>`, changed_files recomputed from merged diff ("the maker's self-reported list is a claim; the merged diff is proof"), operative-tree rule 4b.4 binds STEPs 5–6 to the post-merge T0 tree; matching CRITICAL RULE added. **Caveat:** the fix does not cover the two non-success exits from STEP 4 → new N1/N2 below. |
| F2 shipped double-emit | MAJOR | **FIXED** | STEP 7 is the SINGLE `shipped` emit site; STEP 6 SHIP text contains no emit; Monitoring emit-points + CRITICAL RULES agree ("STEP 6 SHIP emits nothing"). |
| F3 $ARGUMENTS unit re-selected forever | MAJOR | **FIXED** | `argument_unit_consumed: false` in the STEP 1 state template; STEP 2 rule 1 gated on it; STEP 7 sets it true; explicit sentence that a single-issue run "terminates PASSED via the nothing-actionable exit". |
| F4 heal reviews stale diff | MAJOR | **FIXED (merge path)** | STEP 6 FAIL: recompute changed_files before re-VERIFY (`git diff <pre_merge_sha>..HEAD` + `git status --porcelain`); CRITICAL RULE "again after every heal". **Caveat:** references `pre_merge_sha`, undefined on the no-merge paths (N2). |
| F5 preflight probe not actionable | MAJOR | **FIXED** | Ordered probe: (a) assert both names in the session's available-agent-types listing (zero-dispatch); (b) fallback file-check + RESIDUAL RISK recorded + dispatch-time "agent type not found" treated as retroactive PREFLIGHT BLOCK (never inline); probes don't count against dispatches_used. Independent reviewer confirmed both branches executable, non-stalling. |
| F6 --no-ship undefined terminal | MAJOR | **FIXED** | STEP 6 "PASS with --no-ship (TERMINAL branch)": skip /post-fix-pipeline, `commit_sha = "SKIPPED"`, LEARN still runs, `clean_exit` emitted INSTEAD of `shipped`, → STEP 8 `result: "PASSED"`, `Commits: SKIPPED`, no loop-back. Minor residual wording clash with STEP 7's parenthetical (N8). |
| F7 spec "blind test verify" absent | MAJOR | **FIXED** | Skill STEP 5.2 + spec §3 VERIFY row both reconciled: blind reviewer on the RAW merged diff + T0 supervisor reproduction TOGETHER realize the layer (KISS, no 4th dispatch). **Caveat:** the dispatch prompt does not actually pass a diff (N3). |
| F8 FAILED enum unreachable | MINOR | **FIXED** | STEP 8 enum + dashboard both now `PASSED \| ESCALATED \| BLOCKED`. |
| F9 inline-DAG dangling ref + hardcoded budgets | MINOR | **FIXED** | STEP 1.2 "execute the numbered STEPs 1–8 of this skill as the DAG"; STEP 1.4 documents template values as DEFAULTS with flag/config override precedence. |
| F10 maker≠checker assert source | MINOR | **FIXED** | STEP 1.5.3 resolves from the contracts DAG `dispatch:` fields of `execute`/`verify_review` (verified present in BOTH `config/workflow-contracts.yaml` and `core/.claude/config/workflow-contracts.yaml`), defined fallback when config absent, asserts the RESOLVED values differ. |
| F11 clean exit invisible to hub | MINOR | **FIXED** | New `clean_exit` signal: STEP 2 emit + PASSED verdict; in the signal enum, Monitoring emit-points, CRITICAL RULES, and spec §5.1 table. Guard test not extended to pin it (N15, test-side). |
| F12 BLOCKED verdict shape | MINOR | **FIXED** | STEP 1.5.4: verdict written with STEP 8 schema + `reason`, `missing`, `cycles_run: 0`, `units_shipped: 0`, `finalized_at`. |
| F13 small drifts (6 items) | MINOR | **FIXED** | max_retries_per_step + wall-clock surfaced (STEP 1.4; but see N9 — unenforced); spec DISCOVER row now says `triage-inbox.md`; checker dispatch counted in dispatches_used (STEP 5.2); /goal → /goal-creator (exists); triggers 7→6; registry advisory-ref omission accepted as in v1. |

## NEW defects (fresh executability pass; independently found by the context-blind reviewer and supervisor-verified against the text)

### MAJOR

- **N1 — Merge-CONFLICT path strands the maker's work; the heal arm's premises are false there.**
  STEP 4b.2: conflict → `git merge --abort` → FAILED gate → STEP 6 FEEDBACK. After the abort,
  HEAD == `pre_merge_sha` and the maker's commits exist only on the unmerged worktree branch.
  STEP 6 FAIL then asserts "The heal runs inline at T0 and edits the SAME post-merge tree" —
  false on this branch — and the prescribed recompute `git diff <pre_merge_sha>..HEAD` is empty.
  No step ever re-attempts the merge after healing, so VERIFY/SHIP can proceed on a tree that
  never contained the maker's work — the precise failure 4b's own rationale describes. Fix:
  define the conflict recovery (heal = resolve conflicts + complete the merge, then re-VERIFY;
  or discard the branch and state the redo explicitly).
- **N2 — Maker `gate: FAILED|BLOCKED` path skips 4b: `pre_merge_sha` undefined, changed_files
  never recomputed, heal premises false.** STEP 4's "go to STEP 6 FEEDBACK (do not VERIFY a
  non-result)" jumps over 4b, yet STEP 6's heal instructions unconditionally reference
  "the SAME post-merge tree" and `<pre_merge_sha>`. A literal executor stalls on the undefined
  sha; the STEP 5 re-entry reviewer gets the maker's self-reported changed_files naming files
  that are unchanged in the T0 tree; any heal-authored pass ships a tree missing the maker's
  worktree commits (branch dangles). Fix: state that on a no-merge entry to FEEDBACK the heal
  starts from the pre-merge tree, set `pre_merge_sha = HEAD` at FEEDBACK entry, and derive
  changed_files from the heal's own diff.
- **N3 — The checker never receives the "RAW merged diff" the independence claim (and the F7
  spec reconciliation) rests on.** STEP 5.2 prose promises the reviewer is "given the maker's
  RAW diff (not its self-assessment)" / "given only the RAW merged diff", but the literal
  dispatch prompt passes `changed_files=<paths>` (+ DoD + plan path) — paths, not a diff, and
  `pre_merge_sha` is not passed, so the reviewer cannot reconstruct the change boundary and
  cannot distinguish the maker's change from pre-existing code. Fix: pass the diff (or
  `pre_merge_sha..HEAD` range) in the prompt, or amend the prose/spec claim.

### MINOR

- **N4 —** "each signal has exactly ONE emit site" is literally false twice: `clean_exit` has
  two sites (STEP 2 / STEP 6 no-ship) and `preflight_blocked` has two (STEP 1.5.4 / the
  retroactive dispatch-time block). Sites are mutually exclusive at runtime, so no double-count
  — the stated invariant just needs rewording ("at most one entry per run per signal").
- **N5 —** `--discover-only` terminal path ("REPORT the triage and STOP") emits no signal and
  writes no verdict, while CRITICAL RULES mandate an emit on "every terminal outcome"; behavior
  also differs depending on whether triage found work (nothing-actionable fires clean_exit
  first). Same class as v1's F11.
- **N6 —** ESCALATE arm ends "then STOP with `result: "ESCALATED"`" without the explicit
  "write verdict, REPORT" routing the STEP 2 clean exit spells out; STEP 8's handoff clearly
  expects ESCALATED to reach REPORT — make the routing explicit.
- **N7 —** Cycle-cap escalation after a fully-clean capped run (ships max_cycles units, then
  discovers one more): the mandated `escalated` emit's "<unresolved unit + what was tried>" has
  vacuous referents (nothing was tried). Define the message for the not-yet-attempted case.
- **N8 —** STEP 6 "still run STEP 7 LEARN" vs STEP 7 "(`--no-ship` runs already terminated at
  STEP 6)" literally disagree about whether STEP 7 executes under --no-ship; also the `healed`
  emit is specified as a future-conditional in the FAIL arm ("When a heal subsequently PASSES
  VERIFY") with no reminder at the PASS arm where the condition is actually known.
- **N9 —** `max_retries_per_step: 3` and the optional wall-clock cap are read (STEP 1.4) but
  never enforced — no per-step counter in state, no check at any step (F13 surfaced them;
  enforcement is still absent).
- **N10 —** State/verdict field gaps: singular `state.artifacts.commit_sha` (overwritten per
  cycle) vs STEP 8 `"commits": [...]`; dashboard `Heals:`/`Units shipped:` counters untracked
  in state; retroactive preflight block reuses the `cycles_run: 0` recipe, false at STEP 4/5;
  `units_shipped` under --no-ship undefined (0 or 1).
- **N11 —** `/status` is invoked in STEP 2 triage but missing from STEP 1.5's required
  sub-skills list — a project without it passes PREFLIGHT and stalls at DISCOVER (the exact
  class PREFLIGHT exists to catch). It IS in the registry deps; add it to the preflight list.
- **N12 —** "Probes and failed dispatches do NOT count against `dispatches_used`" (STEP 1.5)
  vs "the STEP 8 dashboard counts every `Agent()` call" (STEP 5.2) — literal contradiction.
- **N13 —** STEP 1.5 fallback says "record the RESIDUAL RISK in the run log" — "run log" is
  undefined (presumably `events.jsonl`); name it.
- **N14 —** `docs/specs/loop-engineering-spec.md` content was updated for F7/F11/F13 but its
  header still reads `version: 1.1.0` — bump the spec version.
- **N15 —** Guard test `test_loop_engineering_emits_hub_linked_telemetry` still pins only the
  original four signals and its docstring says "all four terminal signals" — `clean_exit` can
  be silently dropped without failing CI (test-side, not skill text).

## What was checked and found CLEAN (per EVAL-WORKFLOW critical rule 8)

- Registry: normalized hash matches (`dedup_check.hash_pattern` → 167d0406…), version 1.2.0
  consistent across frontmatter/registry/changelog; changelog v1.2.0 entry accurately describes
  the fixes; dependency closure on disk (both worker agents + all dispatched skills).
- Contracts: `dispatch: plan-executor-agent` (execute) and `dispatch: code-reviewer-agent`
  (verify_review) present in BOTH the root and core copies — F10's referenced source exists.
- Spec: §3 VERIFY row reconciled, DISCOVER row uses `triage-inbox.md` + clean_exit, §5.1
  signal table includes clean_exit with both emit locations, §4 budgets match.
- Happy path end-to-end: INIT → PREFLIGHT (both probe branches executable) → DISCOVER →
  PLAN → EXECUTE → 4b merge-success → recomputed changed_files → VERIFY (3 gates) → SHIP on
  the post-merge tree → LEARN single shipped emit → loop. Coherent; operative-tree rule
  unambiguous on this path.
- Bounded termination: every looping path increments `cycle` or `retries_used`; caps
  reachable; `argument_unit_consumed` prevents re-execution; --no-ship does not loop; no
  unbounded path found (independent reviewer concurs).
- Verdict enum: all three values (PASSED/ESCALATED/BLOCKED) reachable; no dead value.
- `shipped` single-emit honesty: STEP 6 emits nothing; --no-ship substitutes clean_exit —
  no double-count path exists.
- Trigger surface: description/trigger changes caused zero regression; 0 misfires against 8
  confusable neighbors across 3 blind runs on 2 model tiers.

## Trigger query set (reduced honest set, embedded for reproducibility)

Should-trigger (5 — all routed to loop-engineering 3/3): (1) "Run autonomously until done:
DoD = every lint error fixed + suite green, don't stop to ask"; (2) "set up a self-healing
loop that works through our issue backlog unattended, escalates only on budget exhaustion";
(3) "maker/checker loop — one agent implements, a separate agent reviews before it ships";
(4) issue-URL driven end-to-end "discover, plan, execute, verify, ship, no babysitting";
(5) casual "kick off the autonomous meta-loop on the triage inbox pls".
Should-not (10 — all routed elsewhere/NONE 3/3): feature build → development-loop; Safari
login bug end-to-end → debugging-loop; failing tests w/ retest cmd → fix-loop; "/status every
15 min" → loop (interval); "ralph loop on PROMPT.md" → ralph-loop; migration plan →
writing-plans; diff review + PR → code-review-workflow; for-loop off-by-one question → NONE;
retry-loop-with-backoff coding task → NONE; "debug methodically, not guessing" →
systematic-debugging.

## Recommended fixes (prioritized, mapped)

1. **N1 + N2 (artifact-flow, gate to PASS):** define the two non-merge entries into STEP 6
   FEEDBACK — conflict recovery (heal resolves + completes the merge, then re-VERIFY) and
   maker-FAILED entry (set `pre_merge_sha = HEAD` at FEEDBACK entry; changed_files from the
   heal's own diff; state what happens to the dangling worktree branch).
2. **N3 (verification integrity, gate to PASS):** pass the actual merged diff (or the
   `pre_merge_sha..HEAD` range) to the checker prompt, or soften the "RAW diff" claim in
   skill + spec.
3. **N5 + N6 + N7 (terminal-path polish):** give --discover-only a defined verdict/emit (or
   an explicit exemption in CRITICAL RULES); make ESCALATE route through STEP 8 explicitly;
   define the capped-clean-run escalation message.
4. **N4 + N8 + N12 + N13 (wording consistency):** reword the one-emit-site invariant; resolve
   the STEP 6/7 --no-ship parenthetical; reconcile the dispatch-count sentences; name the
   "run log".
5. **N9 + N10 + N11 (state completeness):** add /status to PREFLIGHT; either enforce
   max_retries_per_step/wall-clock or drop them from STEP 1.4; add heals/units_shipped/commits[]
   tracking and fix the retroactive-block cycles_run.
6. **N14 + N15 (side files):** bump the spec header version; extend the guard test to pin
   clean_exit (and fix its "four signals" docstring).

**Bottom line:** v1.2.0 genuinely fixed all 13 prior findings — the prior CRITICAL default-path
defect is gone and the success spine is executable end-to-end — but the F1 fix left the
FEEDBACK arm's two no-merge entry paths incoherent (N1/N2) and the F7 reconciliation claims a
diff the checker never receives (N3). Verdict **FIX**, not FAIL: three targeted MAJORs stand
between this and PASS; no redesign needed.
