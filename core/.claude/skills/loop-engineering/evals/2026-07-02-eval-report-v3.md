# Skill Evaluation Report v3 — loop-engineering v1.2.1 (2026-07-02, round 3)

Verification round 3 AFTER the v1.2.1 fixes (branch `fix/loop-engineering-v121`), the final
gate for plans/loop-engineering-adoption.md item 1.3. Per `.claude/skills/skill-evaluator/SKILL.md`
v2.3.0 + `EVAL-WORKFLOW.md`. **Scope honesty:** as in rounds 1–2, no live autonomous loop was
executed. Method: (1) every round-2 finding N1–N15 re-verified against the v1.2.1 TEXT directly
(never the changelog), with side-file checks (spec, registry hash/version/deps, guard test run
live — 20/20 pass); (2) the three-mode FEEDBACK design traced end-to-end by the supervisor
(merged_this_cycle reachability, pre_merge_sha definedness, checker diff content); (3) one
independent context-blind adversarial pass (fresh subagent, no prior findings shown, hostile
literal-executor walk LIMITED to the surfaces v1.2.1 changed) — every claim it returned was
re-verified against the text by the supervisor before scoring, including git-history provenance
checks (introduced-by-v1.2.1 vs pre-existing-in-v1.2.0). **Trigger axis SKIPPED** (honest skip):
the trigger surface (description + 6 triggers) is byte-unchanged since round 2, where it scored
15/15 should-trigger and 0/30 should-not misfires across 2 model tiers — re-running it would
re-test an unchanged surface.

```
SKILL EVALUATION REPORT: loop-engineering (v1.2.1)
=====================================
Mode: full (text-executability adaptation — no live loop run; trigger axis
      carried forward from round 2, unchanged surface)
Iteration: 3 (re-run after v1.2.1 N1–N15 fixes)

SKILL NECESSITY
  Unchanged from v1/v2: adds clear value.

PRE-FLIGHT (STEP 0)
  0.1 Registry sync:   PASS — hash MATCH (dedup_check.hash_pattern → 7cb09ba5…,
                       computed == registry), version 1.2.1 consistent
                       (frontmatter = registry = spec header = changelog v1.2.1
                       entry, which accurately describes the N1–N15 fixes).
                       Deps now include `status` (N11) — all dispatched deps listed.
  0.2 Frontmatter:     PASS — unchanged from v1.2.0 (6 triggers, desc, SemVer).
  0.3 Structural:      PASS — STEPs 1→8 contiguous, fences balanced, no dead
                       skill/agent refs; preamble + CRITICAL RULES both carry
                       the load-bearing constraints (merge-before-VERIFY,
                       maker≠checker, RAW-diff-to-checker, bounded).
  0.4 Self-update:     N/A — no references/ directory.

TRIGGER EVALUATION
  SKIPPED this round — surface unchanged since round 2 (PASS, 15/15 + 0/30,
  sonnet ×2 + haiku ×1). Carried verdict: PASS.

OUTPUT EVALUATION (text executability vs spec)
  Round-2 findings:  15/15 FIXED in the v1.2.1 text (table below) — including
                     all three round-2 MAJORs (N1, N2, N3). The three-mode
                     FEEDBACK design is coherent: NO path reaches VERIFY or
                     SHIP with merged_this_cycle: false; pre_merge_sha is
                     defined on every path (captured at STEP 4 dispatch;
                     conflict-abort restores HEAD to it; redispatch re-records
                     the same value).
  New defects:       1 MAJOR introduced by the N3 fix (V1 — heal-re-entry
                     checker diff excludes uncommitted heal edits), 1 MAJOR
                     pre-existing-in-v1.2.0 newly surfaced (V2 — dispatch
                     sites ignore the 1.5.3-resolved maker/checker names),
                     8 MINOR (V3–V10, mostly pre-existing wording/spec nits).
  Guard test:        20/20 pass live (test_workflow_closure_consistency.py) —
                     the telemetry test now pins all FIVE signals incl.
                     clean_exit (N15 closed at the test level, verified by run).
  Output verdict:    FIX (was FIX) — the 15 gated findings are closed, but the
                     N3 fix introduced one new MAJOR on the exact axis it was
                     meant to close (the checker's diff on heal re-entries).

MODEL COVERAGE
  Tested on:         text-eval on default model; blind adversarial pass on
                     default model. Trigger matrix carried from round 2.
  Divergent results: none observed.

OVERALL VERDICT: FIX
Blocking issues: none CRITICAL. Gate to PASS: V1 (one targeted MAJOR — a
one-clause fix to the STEP 5.2 diff command on heal re-entries) and V2
(one clause at the STEP 4 / 5.2 dispatch sites). No redesign needed.
```

## Per-round-2-finding verification (checked against the v1.2.1 TEXT, not the changelog)

| # | Sev (v2) | Status in v1.2.1 | Evidence in text |
|---|---|---|---|
| N1 merge-CONFLICT path strands maker's work | MAJOR | **FIXED** | STEP 4b.2 routes to "STEP 6 FEEDBACK, **merge-conflict entry**"; STEP 6 mode 2: "The heal IS the integration: re-run `git merge --no-ff <worktree_branch>`, resolve the conflicts inline at T0, commit the resolution — that completes 4b (set `merged_this_cycle: true`; recompute `changed_files`…) — then enter STEP 5 VERIFY"; unresolvable → abandon branch (recorded in `events.jsonl`) + re-dispatch the maker — "NEVER VERIFY a tree that lacks the maker's work". Traced: no path reaches VERIFY/SHIP with `merged_this_cycle: false`. |
| N2 maker FAILED\|BLOCKED path: undefined sha, false heal premises | MAJOR | **FIXED** | STEP 4: `pre_merge_sha` recorded BEFORE dispatch — "defined on EVERY exit from this step"; FAILED/BLOCKED exit discards the maker's self-reported `changed_files` ("an unmerged claim is never handed to a reviewer") → STEP 6 **maker-failed entry** (mode 3): "Nothing is integrated… do NOT run a healer against it. Re-dispatch the maker (STEP 4)…; the failed attempt's worktree branch is abandoned (record it in `events.jsonl`). VERIFY is reached only after the redo's 4b merge succeeds." |
| N3 checker never receives the RAW merged diff | MAJOR | **FIXED (with a new residue — V1)** | STEP 5.2: "capture `git diff <pre_merge_sha>..HEAD` and include the diff text in the prompt (if it exceeds the prompt budget, write it to `.workflows/loop-engineering/cycle-<n>.diff` and pass that path)"; the dispatch prompt carries `diff_range` + a literal `## RAW MERGED DIFF` block. Spec §3 VERIFY row: "the RAW merged diff itself…, passed in the dispatch context — not a path list". CRITICAL RULE added: "MUST hand the checker the RAW merged diff itself, not a path list". Caveat: the fixed command is commit-to-commit — see V1 for the heal-re-entry gap it introduces. |
| N4 "exactly ONE emit site" literally false | MINOR | **FIXED** | Monitoring: "exactly ONE entry per triggering outcome — a single outcome never emits the same signal twice; where a signal lists more than one site, the sites are mutually exclusive at runtime"; CRITICAL RULES mirror it ("one entry per triggering outcome, never two for the same outcome"). |
| N5 `--discover-only` emits nothing / writes no verdict | MINOR | **FIXED** | STEP 2: `--discover-only` (with the explicit ordering note "the nothing-actionable exit above fires first when it wasn't [found]") → `emit_signal("clean_exit", …"discover-only"…)`, `result: "PASSED"` verdict with `cycles_run: 0`, `units_shipped: 0`, REPORT, STOP; "Never emit twice on one exit." Spec §5.1 clean_exit row lists all three sites. |
| N6 ESCALATE arm lacks explicit STEP 8 routing | MINOR | **FIXED** | STEP 6: "Then go to STEP 8 REPORT with `result: "ESCALATED"` (write the verdict + dashboard + handoff — ESCALATED terminates through STEP 8, same as PASSED)." |
| N7 capped-clean-run escalation message vacuous | MINOR | **FIXED** | STEP 6: "When the capped unit was never attempted…, say so explicitly — message `"<unit> — not attempted: max_cycles reached"`, what-was-tried = `"nothing — cycle cap"`." |
| N8 STEP 6/7 --no-ship contradiction + future-conditional healed emit | MINOR | **FIXED** | STEP 6 no-ship: learning capture "inline HERE… the run does NOT enter STEP 7"; STEP 7: "(`--no-ship` runs never reach this step — their learning capture ran inline at STEP 6…)" — now agree. `healed` emit relocated to the PASS arm where the outcome is known ("the FAIL arm's pending emit fires here"), with the FAIL arm pointing at it ("The `healed` emit for any of these fires at the PASS arm") and the no-ship terminal preserving it ("a resolved heal still emits `healed` first"). |
| N9 max_retries_per_step + wall-clock read but never enforced | MINOR | **FIXED** | STEP 1.4: "These caps are ENFORCED, not advisory: every FEEDBACK re-entry increments `budget.step_retries[<failing step>]`… exceeding `max_retries_per_step` triggers the STEP 6 ESCALATE arm even with global budget left; …wall-clock… check elapsed time against `started_at` at every STEP 2 entry and every FEEDBACK re-entry"; state template adds `step_retries: {}`; STEP 6 FAIL increments both counters; the budget-exhausted condition enumerates all four caps. |
| N10 state/verdict field gaps (commit_sha vs commits[], heals/units_shipped untracked, retroactive cycles_run:0, no-ship units_shipped undefined) | MINOR | **FIXED** (one residual sibling → V4) | Template: `"artifacts": { "commits": [] }`, `units_shipped: 0`, `heals: 0`, `merged_this_cycle: false`; PASS arm "APPEND the sha to `state.artifacts.commits`" + "FIRST increment `heals`"; STEP 7 increments `units_shipped`; no-ship "leave `units_shipped` at 0"; STEP 1.5.4 "(a RETROACTIVE block at STEP 4/5 writes the actual current `cycle` and `units_shipped` counts, not 0)". Residual not in N10's enumeration: singular `state.artifacts.plan` vs verdict `plans: [...]` (V4, MINOR). |
| N11 `/status` missing from PREFLIGHT | MINOR | **FIXED** | STEP 1.5.2 conditional sub-skills list now opens with `status`; registry `dependencies` includes it. |
| N12 probe-vs-dashboard dispatch-count contradiction | MINOR | **FIXED** | STEP 5.2: "the STEP 8 dashboard counts every **completed worker** dispatch (maker + checker); preflight probes and failed dispatches stay excluded (STEP 1.5)" — reconciled with STEP 1.5's exclusion. |
| N13 "run log" undefined | MINOR | **FIXED** | STEP 1.5.1: "record the RESIDUAL RISK as an event in `events.jsonl` (the run log)". |
| N14 spec header still 1.1.0 | MINOR | **FIXED** | `docs/specs/loop-engineering-spec.md` header: `version: 1.2.1`. |
| N15 guard test pins only four signals | MINOR | **FIXED (verified by running it)** | `test_loop_engineering_emits_hub_linked_telemetry` iterates `("preflight_blocked", "escalated", "healed", "shipped", "clean_exit")`; docstring says "all five terminal signals". Full file run: 20/20 pass against the v1.2.1 SKILL.md. |

## Adversarial trace of the three-mode FEEDBACK design (the round-2 gate condition)

- **Mode 1 (VERIFY dissent):** merge succeeded → `merged_this_cycle: true` → inline T0 heal →
  recompute `changed_files` → re-enter STEP 5. Guard holds. (But see V1: the re-entry DIFF
  content, as opposed to the path list, can miss the heal.)
- **Mode 2 (merge conflict):** abort → HEAD == `pre_merge_sha`, `merged_this_cycle: false` →
  heal completes the merge (sets the flag true) → VERIFY; unresolvable → abandon + re-dispatch
  maker → fresh 4b required before VERIFY. Guard holds.
- **Mode 3 (maker FAILED/BLOCKED):** 4b skipped, flag false, self-reported changed_files
  discarded → no healer runs → re-dispatch maker (re-records the same `pre_merge_sha`, HEAD
  unmoved) → VERIFY only after the redo's merge. Guard holds.
- **Conclusion:** no path reaches VERIFY or SHIP with `merged_this_cycle: false`;
  `pre_merge_sha` is defined at every read site on every path. The round-2 gate condition is met.

## NEW defects (context-blind adversarial pass, LIMITED to the v1.2.1-changed surfaces; every claim supervisor-verified against the text; provenance checked against the v1.2.0 text at commit 9d7a186)

### MAJOR

- **V1 — On mode-1 heal re-entry, the checker's "RAW merged diff" excludes uncommitted heal
  edits — introduced by the N3 fix.** STEP 5.2 fixes the dispatch diff as
  `git diff <pre_merge_sha>..HEAD` — a commit-to-commit comparison that never includes
  working-tree changes. STEP 6 mode 1 explicitly anticipates uncommitted heal edits ("plus any
  uncommitted heal edits from `git status --porcelain`" — added to the `changed_files`
  recompute), so the skill's own text admits the state in which the dispatch command is wrong.
  A literal executor re-entering STEP 5 after an uncommitted `/fix-loop` heal hands the reviewer
  the PRE-heal diff while the mechanical gate and supervisor reproduction run on the healed
  working tree. Two concrete failure shapes: (a) fail-closed — the reviewer re-dissents on the
  already-fixed defect, burning `step_retries` to escalation; (b) fail-open — when the original
  FAIL was mechanical-only, the reviewer re-passes the pre-heal diff, the mechanical gate now
  passes, and SHIP commits heal edits the independent reviewer never saw — directly violating
  the v1.2.1 CRITICAL RULE "so the reviewer never grades a stale diff". Provenance: the
  diff-passing mechanism did not exist in v1.2.0 (it passed only `changed_files` paths — that
  was N3), so this is NEW in v1.2.1. Fix (one clause): on heal re-entries capture
  `git diff <pre_merge_sha>` (commit-to-worktree) — or require the heal to be committed before
  re-entering STEP 5, making `..HEAD` correct on every entry.
- **V2 — PREFLIGHT validates the CONFIG-resolved maker/checker, but STEPs 4 and 5.2 dispatch
  hardcoded literals — pre-existing in v1.2.0 (the F10 fix), newly surfaced.** STEP 1.5.3
  resolves the `subagent_type`s from the contracts DAG (`dispatch:` of `execute` /
  `verify_review`) precisely because "comparing the literals in STEPs 4/5 cannot detect a
  project remap" — yet STEP 4 dispatches `subagent_type="plan-executor-agent"` and STEP 5.2
  `subagent_type="code-reviewer-agent"` verbatim, with no instruction to substitute the resolved
  values. In a project that remaps the DAG, preflight asserts maker≠checker on agents that never
  run, and the configured maker is dead config (the 1.5.1 dispatchability probe also probes only
  the default names). Default-config projects are unaffected (resolved == literals). Verified in
  the v1.2.0 text (commit 9d7a186, line 264: same hardcoding) — NOT a v1.2.1 regression; round 2
  missed it. Fix (one clause at each dispatch site): "dispatch the RESOLVED maker/checker
  `subagent_type`s from STEP 1.5.3", and probe the resolved names at 1.5.1.

### MINOR

- **V3 —** `--no-ship` is documented "never commit" (CLI table) and its terminal says "nothing
  was committed" / "verified-but-uncommitted work", but STEP 4b's mandatory `git merge --no-ff`
  lands the maker's commits + a merge commit on the run branch before VERIFY (necessarily — the
  merge is what VERIFY verifies). Behavior is correct; the flag doc and terminal/verdict wording
  misdescribe the repo state (`Commits: SKIPPED` means only the SHIP commit was skipped).
  Reword: "--no-ship = no SHIP commit; the 4b integration merge still lands on the run branch."
- **V4 —** STEP 3 stores singular `state.artifacts.plan` (overwritten per cycle) while the
  STEP 8 verdict wants `artifacts.plans: [...]`; the STEP 1.4 template declares neither `plan`
  nor `pre_merge_sha` keys. Multi-unit runs cannot reconstruct earlier plans from state.
  Residual sibling of N10's class.
- **V5 —** `step_status` is initialized (`{"INIT": "done"}`) and never written again by any
  step — a dead state field; crashed-run resume cannot tell which step died. Pre-existing.
- **V6 —** Mode-1 healer selector "2+ failed cycles on the same unit" is unsatisfiable as
  written: `cycle` increments only at STEP 2, and a failing unit loops STEP 5↔6 (or 6→4) within
  one cycle until `step_retries` escalates — the `/debugging-loop` branch can only fire via the
  fuzzy "unclear root cause" clause. Should read "2+ failed heal attempts". Pre-existing.
- **V7 —** `healed` and `shipped` are grouped under "every terminal outcome" in the Monitoring
  intro + CRITICAL RULES and under "Terminal signal" in spec §5.1, but both fire mid-run
  (`shipped` per unit at STEP 7 before looping back; `healed` at the PASS arm). The per-signal
  emit-point definitions resolve it; the label is wrong. Pre-existing framing.
- **V8 —** Spec §3 ASCII diagram routes `FAIL ► FEEDBACK` back to the DISCOVER rail,
  contradicting the same section's (v1.2.1-updated) FEEDBACK table row ("back to VERIFY only
  after a successful 4b merge") and the skill. Pre-existing diagram not updated with the row.
- **V9 —** Spec §5.1 gives `preflight_blocked`'s emit site as "STEP 1.5" only — the skill adds
  "(incl. retroactive at STEP 4/5)". Also the STEP 1.5.4 emit literal's tag slot
  `<missing-name>` is undefined for the maker==checker block variant (nothing is missing).
- **V10 —** STEP 5 gate sentence: "passes only when **both** … AND … AND …" — three conjuncts
  under "both". Cosmetic; the conjunction is unambiguous. Pre-existing.

## What was checked and found CLEAN (per EVAL-WORKFLOW critical rule 8)

- Registry: computed `dedup_check.hash_pattern` == registry hash (7cb09ba5…); version 1.2.1
  consistent across frontmatter/registry/spec/changelog; changelog v1.2.1 entry accurately
  describes the N1–N15 fixes; `status` + all dispatched deps present.
- Guard tests: `scripts/tests/test_workflow_closure_consistency.py` run live — 20/20 pass
  (five-signal telemetry pin, maker≠checker contract, two-distinct-agents body scan,
  aggregator-key match, contract sync).
- The three-mode FEEDBACK reachability + `pre_merge_sha` definedness (trace above) — the blind
  reviewer independently reported the same surfaces clean.
- Signal completeness: every terminal exit (BLOCKED incl. retroactive, both STEP 2 exits,
  no-ship terminal, ESCALATED, nothing-actionable PASSED) emits exactly one signal; no outcome
  double-emits; the delegated `/learn-n-improve` null-link trap is documented.
- Budget boundedness: every FEEDBACK re-entry increments `retries_used` + `step_retries`;
  `max_cycles` checked at STEP 2; wall-clock checked at STEP 2 entries + FEEDBACK re-entries;
  no unbounded path found (blind reviewer concurs).
- STEP 2 argument-unit consume/loop-back logic and the `--discover-only` emit ordering.
- Spec §3 EXECUTE/VERIFY/FEEDBACK rows + §5.1 table reconciled with the skill (except V8/V9 nits).
- Trigger surface: byte-unchanged since round 2 — carried PASS (15/15 + 0/30), honestly skipped.

## Recommended fixes (prioritized, mapped)

1. **V1 (gate to PASS, verification integrity):** in STEP 5.2, make the diff command
   entry-aware — `git diff <pre_merge_sha>` (includes working tree) on mode-1 heal re-entries,
   or mandate committing the heal before re-entering STEP 5 so `..HEAD` is always complete.
2. **V2 (gate to PASS, one clause × 2 sites):** dispatch the STEP 1.5.3-RESOLVED
   `subagent_type`s at STEPs 4 and 5.2 (and probe the resolved names at 1.5.1), so a project
   remap actually takes effect and preflight validates the agents that run.
3. **V3 + V7 + V10 (wording):** reword the `--no-ship` "never commit" contract and the no-ship
   terminal's "nothing was committed"; relabel "terminal outcome" → "defined emit point" for
   `healed`/`shipped`; fix "both" → "all three".
4. **V4 + V5 (state completeness):** `plans[]` array in state (append per cycle) matching the
   verdict schema; either maintain `step_status` per step or drop it from the template.
5. **V6 (healer selector):** "2+ failed heal attempts on the same unit" (readable off
   `step_retries`), not "2+ failed cycles".
6. **V8 + V9 (spec nits):** redraw the §3 diagram's FEEDBACK edge (→ VERIFY/EXECUTE, not
   DISCOVER); add "(incl. retroactive at STEP 4/5)" to §5.1's `preflight_blocked` row; define
   the emit tag for the maker==checker block variant.

**Bottom line:** v1.2.1 genuinely closes all 15 round-2 findings — the FEEDBACK arm's three
entry modes are now coherent end-to-end, no path reaches VERIFY/SHIP unmerged, `pre_merge_sha`
is always defined, and the checker dispatch carries the actual diff on first entry. But the N3
fix introduced exactly one new MAJOR on its own axis (V1: the heal-re-entry diff is
commit-to-commit and misses uncommitted heal edits — the skill's own mode-1 text admits that
state exists), and the blind pass surfaced one pre-existing MAJOR round 2 missed (V2: dispatch
sites ignore the config-resolved maker/checker that PREFLIGHT validates). Verdict **FIX**, not
FAIL: two targeted one-clause fixes stand between this and PASS; the design is sound.
