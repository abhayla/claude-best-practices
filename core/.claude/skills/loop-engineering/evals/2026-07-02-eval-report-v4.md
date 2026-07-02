# Skill Evaluation Report v4 — loop-engineering v1.2.2 (2026-07-02, round 5: FINAL narrow verification)

Narrow verification round AFTER the v1.2.2 fixes (commit `cd78222`, PR #263). Scope per the
round-5 charter: confirm the ten round-3 findings V1–V10 (see `2026-07-02-eval-report-v3.md`)
are genuinely closed in the v1.2.2 TEXT, and that the v1.2.2 edits introduced no NEW defects —
scoped to the changed surfaces (STEP 1.4/1.5/4/5.2/6 of SKILL.md; spec header/§3/§5.1) plus their
immediate interactions (first-pass, heal re-entry, maker-FAILED, merge-conflict, `--no-ship`,
resume-after-interrupt). NOT a full re-eval: trigger axis, budget boundedness, STEP 2 exits, and
the three-mode FEEDBACK reachability were verified in rounds 2–4 on surfaces v1.2.2 did not
change and are carried forward. Method: every V-finding re-verified against the current text
(never the changelog), each fix adversarially traced as a literal executor; side checks run live
(guard test suite, registry hash, version consistency, orphan-literal sweep, git provenance of
the v1.2.2 commit).

```
SKILL EVALUATION REPORT: loop-engineering (v1.2.2)
=====================================
Mode: narrow verification (round 5 — V1–V10 closure + new-defect sweep on
      the v1.2.2-changed surfaces only)
Iteration: 4 (re-run after v1.2.2 V1–V10 fixes)

PRE-FLIGHT
  Registry sync:   PASS — computed dedup_check.hash_pattern ==
                   registry hash (42c86b8e…); version 1.2.2 consistent
                   (frontmatter = registry = spec header = registry
                   `changelog` field v1.2.2 entry, which accurately
                   describes the V1–V10 fixes). NOTE: per-version history
                   lives in the registry entry's `changelog` field, not
                   registry/changelog.md (same convention as v1.2.0/1.2.1).
  Guard tests:     PASS — scripts/tests/test_workflow_closure_consistency.py
                   run live in this worktree: 20/20 pass (closure, maker≠checker
                   contract, two-distinct-agents body scan — still satisfied
                   after the state.workers indirection — telemetry pins,
                   contract sync).

V1–V10 VERIFICATION
  Closed:          10/10 (table below). Both round-3 MAJORs (V1, V2) are
                   closed by the exact mechanism the v3 report prescribed.
  New defects:     0 CRITICAL, 0 MAJOR, 2 minor (W1–W2 below — both residues
                   of the V1 fix's illustrative text, neither re-opens the
                   V1 failure on the normative reading).

OVERALL VERDICT: PASS
  All ten round-3 findings are closed in the v1.2.2 text; the new-defect
  sweep found no CRITICAL/MAJOR issue. W1–W2 are non-blocking polish items
  for a future PATCH.
```

## Per-finding verdict table (checked against the v1.2.2 TEXT)

| # | Sev (v3) | Verdict | Evidence in the v1.2.2 text (+ break attempts) |
|---|---|---|---|
| **V1** heal re-entry diff excludes uncommitted heal edits | MAJOR | **CLOSED** | STEP 6 mode 1: "Before re-entering STEP 5, COMMIT the heal's edits (a heal checkpoint commit, e.g. `git commit -am "heal: <what>"`) — an uncommitted heal edit is invisible to the commit-to-commit diff the checker receives — then recompute `changed_files` from `git diff --name-only <pre_merge_sha>..HEAD`, which is now complete." STEP 5.2 restates the invariant at the capture site: "complete on EVERY entry to this step, first-pass or heal re-entry, because every heal is COMMITTED (STEP 6 mode 1's heal checkpoint commit) before VERIFY re-entry, so no reviewed state is ever sitting uncommitted in the working tree." CRITICAL RULES: "whose edits MUST be COMMITTED (heal checkpoint commit) BEFORE re-entering VERIFY so `git diff <pre_merge_sha>..HEAD` is complete on every entry." The v1.2.1 porcelain special case is REMOVED (grep: zero `porcelain` hits in SKILL.md). Break attempts: (a) mode-2 re-entry — the merge resolution is itself committed ("commit the resolution — that completes 4b"), so `..HEAD` is complete; (b) mode-3 — no heal runs, redo's 4b merge commits everything; (c) first pass — 4b merge commits everything; (d) repeated mode-1 heals — each committed, diff accumulates correctly; (e) `--no-ship` — terminal text now explicitly accounts for heal checkpoint commits ("the STEP 4b integration merge, and any heal checkpoint commits, still sit on the run branch"), no lost heal, no double-commit with SHIP (heal edits already committed; `/post-fix-pipeline` commits only the docs/SHIP delta). Every one of the four diff-capture sites (4b.3 recompute, 5.2 dispatch diff, mode-1 recompute, mode-2 recompute) now sees committed state. Residues: W1/W2 below (minor). |
| **V2** dispatch sites ignore the config-resolved maker/checker | MAJOR | **CLOSED** | STEP 1.4 template declares `"workers": { "maker": "plan-executor-agent", "checker": "code-reviewer-agent" }` + "`workers` holds the DEFAULT maker/checker names; STEP 1.5.3 overwrites them with the config-resolved values, and STEPs 4/5.2 dispatch from `state.workers`." STEP 1.5.3: "Store the resolved values into `state.workers.maker` / `state.workers.checker` (overwriting the template defaults) — STEPs 4 and 5.2 dispatch THESE, never hardcoded literals." STEP 4 dispatches `Agent(subagent_type=<state.workers.maker>, …)` and STEP 5.2 `Agent(subagent_type=<state.workers.checker>, …)` — the default literals survive ONLY in `#` comments ("# default is subagent_type=\"plan-executor-agent\" only when config is absent"; grep confirms lines 247/318 are the only literal-dispatch strings and both are comments). STEP 1.5.1 probes "the RESOLVED maker and checker from item 3 below … — probe the RESOLVED names, never the default literals." CRITICAL RULES mirror it. Break attempts: (a) remapped project — 1.5.3 resolves from the contracts DAG, stores, 1.5.1 probes the resolved names, 4/5.2 dispatch them → remap takes effect end-to-end; (b) config absent — fallback defaults stored in state, identical behavior to v1.2.1; (c) resume-after-interrupt — `state.workers` persists in state.json, re-read on resume; (d) forward reference 1.5.1→"item 3 below" is explicit and self-aware, not a trap. No orphan literal dispatch remains. |
| **V3** `--no-ship` "never commit" misdescription | minor | **CLOSED** | CLI comment: "skip the SHIP commit # (the 4b integration merge still lands)"; flag table: "skip the SHIP commit (the 4b integration merge still lands on the run branch)"; terminal: "the SHIP commit was skipped (the STEP 4b integration merge, and any heal checkpoint commits, still sit on the run branch)"; dashboard gloss: "`Commits: SKIPPED` (meaning: only the SHIP commit was skipped)". The old "never commit"/"nothing was committed" wording is gone. |
| **V4** singular `state.artifacts.plan` vs verdict `plans: [...]`; template gaps | minor | **CLOSED** | Template: `"artifacts": { "plans": [], "commits": [] }` and `"pre_merge_sha": null` now declared. STEP 3: "APPEND the plan path to `state.artifacts.plans` (one entry per cycle — the STEP 8 verdict's `plans: [...]` is read straight from this array, so multi-unit runs keep every plan)." STEP 4 maker prompt reads "Plan file: <latest entry of state.artifacts.plans>". |
| **V5** dead `step_status` field | minor | **CLOSED** | Field dropped from the STEP 1.4 template (v3's option b); grep: zero `step_status` hits in SKILL.md. |
| **V6** unsatisfiable "2+ failed cycles" healer clause | minor | **CLOSED** | Mode-1 selector: "# unclear root cause OR 2+ failed heal attempts on the same unit — read off # budget.step_retries (does diagnose→fix→verify→learn)". Satisfiable: `step_retries` increments on every FEEDBACK re-entry. |
| **V7** `healed`/`shipped` mislabeled "terminal" | minor | **CLOSED** | Monitoring intro: "every signal-emitting outcome — the terminal exits, plus the mid-run `shipped` (per unit, STEP 7) and `healed` (PASS arm) marks"; CRITICAL RULES: "the terminal `preflight_blocked`, `escalated`, `clean_exit` plus the mid-run `healed` and `shipped`"; spec §5.1 rows now say "STEP 6 PASS arm (mid-run, …)" / "STEP 7 (mid-run, per shipped unit — the single emit site, never STEP 6)" and the table carries no "Terminal signal" label. |
| **V8** spec §3 diagram routes FAIL►FEEDBACK back to DISCOVER | minor | **CLOSED** | Diagram redrawn: FEEDBACK forks to "VERIFY dissent or a resolvable conflict: heal, complete the 4b merge ► re-enter VERIFY" (rail into VERIFY's `◄`) and "maker FAILED\|BLOCKED or unresolvable conflict: re-dispatch the maker ► EXECUTE" (rail into EXECUTE's `◄`); only LEARN's rail returns to DISCOVER, with the explicit caption "(FEEDBACK never returns to DISCOVER — only LEARN advances to the next unit.)". ASCII rails traced column-by-column: the two FEEDBACK branches connect to the VERIFY (col ~42) and EXECUTE (col ~49) verticals respectively; the GATE line crosses them with `┼`. Diagram now agrees with the §3 FEEDBACK row and the skill. |
| **V9** spec §5.1 `preflight_blocked` emit site incomplete; undefined tag slot for maker==checker | minor | **CLOSED** | Spec §5.1 row: "STEP 1.5 (incl. the retroactive block at STEP 4/5 on a dispatch-time \"agent type not found\")". SKILL STEP 1.5.4 emit literal: tags `[…,<missing-name \| "maker-equals-checker">]` with "(tag slot = the missing dependency's name, or the literal `"maker-equals-checker"` for the maker==checker block, where nothing is missing)"; the Monitoring emit-points list mirrors the same slot. |
| **V10** "both" over three conjuncts | minor | **CLOSED** | STEP 5 gate: "GATE passes only when **all three** agree: the mechanical result is `PASSED` AND the independent reviewer returns `PASSED` AND the supervisor reproduction concurs." |

## NEW findings (v1.2.2-introduced surfaces only)

No CRITICAL. No MAJOR. Two minors — both residues of the V1 fix's *illustrative* text; on the
normative reading ("COMMIT the heal's edits") neither re-opens V1:

- **W1 (minor) — the heal-checkpoint example command `git commit -am "heal: <what>"` does not
  stage UNTRACKED files.** STEP 6 mode 1's mandate is complete ("COMMIT the heal's edits"), but
  the `e.g.` command uses `-a`, which stages only tracked-file modifications. A heal that
  CREATES a file (e.g. `/debugging-loop` adding a regression test) and an executor following the
  example verbatim would leave that file uncommitted → absent from `git diff <pre_merge_sha>..HEAD`
  and from the `--name-only` recompute — a narrow recurrence of the V1 class limited to
  file-creating heals. Mitigations that keep this minor: the normative sentence covers all edits;
  the mechanical gate + supervisor reproduction still run on the working tree (which contains the
  file); and most heals modify existing files. Fix (one word-level edit): make the example
  `git add -A && git commit -m "heal: <what>"`.
- **W2 (minor, cosmetic) — mode-1 paragraph ordering.** The commit instruction ("Before
  re-entering STEP 5, COMMIT the heal's edits…") textually PRECEDES the healer-selection block
  ("Pick the healer by root-cause clarity: …"), though at runtime the heal necessarily runs
  first. The timing anchor ("Before re-entering STEP 5") and the object ("the heal's edits",
  which cannot exist pre-heal) make the semantics unambiguous, and STEP 5.2 + CRITICAL RULES
  restate the invariant at the boundary — so no literal execution path commits-then-heals-then-
  re-enters uncommitted. Reorder (heal → commit → recompute → re-enter) in a future PATCH for
  readability.

## What was checked and found CLEAN

- **Registry**: computed `dedup_check.hash_pattern` == registry hash (`42c86b8e…`); version
  1.2.2 consistent across frontmatter / registry / spec header; registry `changelog` field's
  v1.2.2 entry accurately matches the shipped diff (verified against commit `cd78222`, which
  touched exactly SKILL.md, the spec, patterns.json, and the v3 report).
- **Guard tests**: `test_workflow_closure_consistency.py` run live — 20/20 pass; the
  two-distinct-agents body scan still passes after the `<state.workers.*>` indirection.
- **Orphan sweep**: zero `step_status` / `porcelain` remnants; the only
  `subagent_type="plan-executor-agent"` / `"code-reviewer-agent"` literals sit in `#` comments
  at the two dispatch sites (lines 247/318) — exactly the "defaults kept in comments" design.
- **Diff-capture completeness after heal-commit**: all four capture sites (STEP 4b.3, STEP 5.2,
  mode-1 recompute, mode-2 recompute) see committed state on every path (first-pass, heal
  re-entry, conflict-resolution re-entry, maker-redo).
- **Heal-commit × SHIP × `--no-ship` interactions**: no double-commit (heal edits are committed
  before SHIP's `/post-fix-pipeline` commit), no lost heal on `--no-ship` (terminal text names
  the heal checkpoint commits on the run branch; `healed` still emitted before `clean_exit`).
- **`state.workers` lifecycle**: declared in the 1.4 template → written (overwritten) at 1.5.3 →
  probed at 1.5.1 → read at 4/5.2; persists in state.json across an interrupt/resume.
- **pre_merge_sha definedness on the changed paths**: re-recorded at every STEP 4 entry
  (including mode-3 redo and post-abandon redo, HEAD unmoved); new cycle re-records fresh after
  STEP 7's loop-back (`merged_this_cycle` reset at STEP 2 — unchanged surface, re-confirmed at
  the interaction boundary only).
- **Spec §3 table rows** (EXECUTE/VERIFY/FEEDBACK) agree with the skill on the resolved-worker
  dispatch and the heal-checkpoint commit; §3 diagram agrees with the FEEDBACK row (V8) and the
  no-DISCOVER-return caption.
- **Unchanged surfaces deliberately NOT re-litigated** (rounds 2–4 verdicts carried): trigger
  surface, budget boundedness/enforcement, STEP 2 exits + `--discover-only` emit ordering,
  three-mode FEEDBACK reachability (`merged_this_cycle` guard), signal single-emit map.

## Final verdict

**PASS.** V1–V10: 10/10 closed in the v1.2.2 text, verified against the literal wording (not
the changelog), with the two round-3 MAJORs (V1 heal-diff completeness, V2 resolved-worker
dispatch) closed by exactly the prescribed one-clause mechanisms and self-consistent across
every entry path traced. The v1.2.2 edits introduced no CRITICAL or MAJOR defect; the two new
minors (W1 `-am`-example untracked-file gap, W2 mode-1 paragraph ordering) are non-blocking
polish for a future PATCH and do not re-open the V1 failure on the normative reading. Finding
trajectory across rounds: 13 → 15 → 10 → **2 minor** — converged.
