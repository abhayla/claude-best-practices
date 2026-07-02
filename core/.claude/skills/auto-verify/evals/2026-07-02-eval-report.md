# SKILL EVALUATION REPORT: auto-verify

```
SKILL EVALUATION REPORT: auto-verify
=====================================
Mode: full (trigger + output + conflicts; text-level adaptation — no live
      verification run executed, per eval brief; trigger axis run LIVE via
      3 context-blind routing subagents)
Iteration: 1
Evaluated: 2026-07-02
Skill version: 4.3.0 (core/.claude/skills/auto-verify/SKILL.md, 476 lines
      + references/visual-proof-review.md, 124 lines)
Evaluator: skill-evaluator v2.3.0 procedure + EVAL-WORKFLOW.md steps
      0/0.5/1/2/3(adapted); plan item 1.4b of plans/loop-engineering-adoption.md
      (VERIFY arm of the loop-engineering dispatch chain)

SKILL NECESSITY (qualitative — text-level)
  Adds clear value over baseline: the single canonical post-change gate —
  changed-file→test mapping via /regression-test (import graph + risk), dual
  verdict model (screenshot-authoritative UI / exit-code non-UI), the
  silent-degradation gate, the v4.2.0 NO_TESTS_FOR_CHANGE vacuous-green
  guard, monorepo runner scoping, and the machine-readable
  test-results/auto-verify.json the stage-gate aggregator + /post-fix-pipeline
  + loop-engineering STEP 5 all consume. The JSON contract alone is
  load-bearing for three downstream consumers. Verdict: adds clear value.

TRIGGER EVALUATION (3 context-blind routing subagents x 12 queries;
  2x sonnet + 1x haiku, one sonnet run adversarially prompted; routers saw
  the real frontmatter descriptions of auto-verify + 6 neighbors + NONE and
  were NOT told which skill was under evaluation)
  Should-trigger:    6/6 queries at 100% rate (18/18 runs activated)
  Should-not:        6/6 correctly ignored (0/18 misfires; every neighbor
                     won its own query 3/3)
  Cross-skill:       0 conflicts. Bidirectional signposting VERIFIED in all
                     seven descriptions (auto-verify names /fix-loop +
                     /test-pipeline; test-pipeline, e2e-visual-run,
                     verify-screenshots, post-fix-pipeline each name
                     /auto-verify with boundary language).
  Regressions:       N/A (no --baseline)
  Fresh validation:  N/A (no description optimization needed)
  Trigger verdict:   PASS (36/36 — the strongest trigger surface measured
                     in this eval series)

OUTPUT EVALUATION (executability walk of the text — steps traced as written)
  Gate check (STEP 0):     PASS with 2 minors (F4 dead FLAKY branch,
                           F5 UNKNOWN fall-through does not implement the
                           strict-gates block it claims)
  Test mapping (STEP 1):   PASS — /regression-test mapping-only contract,
                           fallback, zero-test classification (code vs
                           docs-only, strict vs non-strict), monorepo
                           scoping all coherent
  Execution (STEP 2):      PASS with 1 minor (F6 ui_verdict/code_verdict
                           fields not in tester-agent's return contract)
  Routing 2→2.5→3→4:       FAIL (F1 MAJOR) — STEP 2's routing arrows
                           contradict STEP 2.5/STEP 3 and bypass the
                           silent-degradation gate on the literal PASS path
  Committed-change caller: FAIL (F2 MAJOR) — no commit-range input; default
                           change detection + git-stash pre-existing check
                           both assume UNCOMMITTED changes, the opposite of
                           the loop-engineering STEP 5 calling context
  JSON contract (STEP 6):  PASS — `result` (never status/verdict/outcome),
                           PASSED|FAILED enum defensible for a non-fixing
                           skill (FIXED is fix-loop's to emit), visual_review
                           embed + failures[] shape match testing.md; one
                           minor reference-schema drift (F7)
  Does-NOT-fix boundary:   PASS — STEP 3 "Do NOT attempt fixes — fixing
                           belongs in /fix-loop upstream" + CRITICAL RULES;
                           the body genuinely refrains and reports FAILED
                           for the caller to route (correct: auto-verify is
                           the gate, the caller owns the heal edge)
  Stress test (10 adversarial categories, text-level):
                     7 PASS, 0 CRITICAL, 1 MAJOR (F2 surfaces under
                     "stale context"), 2 MINOR (F5 malformed-format,
                     F8 undeclared --strict-quality under conflicting
                     constraints)
  Output verdict:    FIX (two MAJORs; everything else minor)

REFERENCE SELF-UPDATE
  N/A — references/ exists but holds extracted step detail
  (visual-proof-review.md), not a knowledge base; no self-update protocol
  is expected for an extraction-only references/ dir (pre-flight 0.4
  applies to self-updating reference knowledge bases). Recorded as
  not-applicable, with one INFO (F10: no TOC at 124 lines).

MODEL COVERAGE
  Routing tested on: sonnet x2 (one adversarial), haiku x1. Divergences:
  none — 36/36 unanimous. No live execution — output axis is a text walk.

OVERALL VERDICT: FIX
Blocking issues: none CRITICAL. F1 and F2 (both MAJOR) are the substantive
  fixes; F3–F9 are one-line text/metadata edits.
```

## Trigger matrix (3 blind runs x 12 queries — raw data)

Should-trigger set (expected auto-verify): Q1–Q6. Should-NOT set: Q7 (fix-loop),
Q8 (test-pipeline), Q9 (e2e-visual-run), Q10 (regression-test),
Q11 (verify-screenshots), Q12 (post-fix-pipeline).

| Q | Query (verbatim) | Expected | run1 (sonnet) | run2 (haiku) | run3 (sonnet, adversarial) | Verdict |
|---|---|---|---|---|---|---|
| Q1 | "verify my changes" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q2 | "I just refactored the payment service — run verification before I commit" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q3 | "post-change check on these files please: src/api/routes.py and src/models/user.py" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q4 | "did my edits break anything? check it but don't fix anything yet" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q5 | "run the tests covering what I changed and give me a structured pass/fail json, with screenshot proof for the UI parts" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q6 | "quick verification pass w/ quality gates b4 i open the PR" | auto-verify | auto-verify | auto-verify | auto-verify | PASS 3/3 |
| Q7 | "tests are failing, fix them and rerun until green" | fix-loop | fix-loop | fix-loop | fix-loop | PASS 0/3 misfire |
| Q8 | "run the whole test → fix → verify → commit chain end to end" | test-pipeline | test-pipeline | test-pipeline | test-pipeline | PASS 0/3 misfire |
| Q9 | "run the full Playwright suite with visual verification and auto-healing" | e2e-visual-run | e2e-visual-run | e2e-visual-run | e2e-visual-run | PASS 0/3 misfire |
| Q10 | "which tests are affected by this diff? just impact analysis and run the affected ones" | regression-test | regression-test | regression-test | regression-test | PASS 0/3 misfire |
| Q11 | "compare these new screenshots against the stored baselines" | verify-screenshots | verify-screenshots | verify-screenshots | verify-screenshots | PASS 0/3 misfire |
| Q12 | "auto-verify already passed — now update the docs and commit the change" | post-fix-pipeline | post-fix-pipeline | post-fix-pipeline | post-fix-pipeline | PASS 0/3 misfire |

**Trigger matrix: 12/12 cases pass (36/36 runs).** Notable near-miss designs that
did NOT misfire: Q4 ("check but don't fix") is the exact fix-loop/auto-verify
boundary — the description's "Does NOT fix — use /fix-loop for fixes" sentence
carried it 3/3; Q10 shares auto-verify's own mapping machinery (regression-test)
and still routed to the mapper 3/3.

## Findings table (severity-ordered)

| # | Sev | Finding — literal quoted text + concrete failure path |
|---|---|---|
| **F1** | **MAJOR** | **STEP 2's routing arrows contradict STEP 2.5 / STEP 3 and bypass the silent-degradation gate on the literal PASS path.** STEP 2 (after tester-agent returns): "1. If EITHER verdict is **FAILED** → proceed to STEP 3 … 2. If BOTH verdicts are **PASSED** → proceed to STEP 2.5 (confirmation review) then STEP 4". But STEP 2.5 declares "For UI tests: This step is MANDATORY and ALWAYS runs", its sub-step 2.5.4 says "FAILED overrides add to STEP 3's main failure list", the reference's 2.5.1 says "proceed to STEP 3", and STEP 3 hosts BOTH the "Silent-degradation gate (MANDATORY for UI tests): Before declaring PASSED, verify that UI tests actually underwent screenshot verification" AND the flag mechanism for FAILED-exit-code/PASSED-screenshot tests. Concrete failure paths for a literal executor: (a) **PASS path** — 2 → 2.5 → 4 skips STEP 3 entirely, so the silent-degradation gate never runs on exactly the path it guards (declaring PASSED); a tester-agent fallback that silently degraded UI tests to exit-code-only sails to PASSED — the precise "green tests, broken UI" mode CRITICAL RULES says MUST be blocked; the 2.5.4 promise "overrides add to STEP 3's failure list" also lands in a step the routing never visits. (b) **FAIL path** — 2 → 3 skips the "MANDATORY and ALWAYS runs" 2.5, so STEP 3's "Gate signal: STEP 3 reads `visual-review.json`" reads a file that was never written, and the FAILED+looks-correct FLAG mechanism (defined in 2.5.2's verdict tables and testing.md's `flags[]`) is dead on the only path that can populate it. Mitigation (why not CRITICAL): CRITICAL RULES restates the silent-degradation MUST, so a model-layer executor honoring CRITICAL RULES would still apply the gate; the FAIL-path bypass cannot flip a verdict (FAILED stays FAILED). Fix: reroute STEP 2 to the linear "2 → 2.5 → 3 → (4 if PASS)" flow the sub-steps already assume — e.g. "1. Record the manifest. 2. ALWAYS proceed to STEP 2.5, then STEP 3 (which routes to STEP 4 on pass, report on fail)." |
| **F2** | **MAJOR** | **Committed-change blindspot: both change detection and pre-existing-failure detection assume UNCOMMITTED working-tree changes — the opposite of the loop-engineering STEP 5 calling context, defeating the skill's own vacuous-green guard.** Surfaces of the one root cause: (a) Parameters: "`--files` \| git diff \| Specific files to verify" and STEP 1 fallback "Use `git diff --name-only` to identify changed files" — bare `git diff` compares working tree to index, which is EMPTY after loop-engineering's STEP 4b merge commit + heal checkpoint commits ("every heal is COMMITTED … before VERIFY re-entry"). loop-engineering STEP 5 invokes `Skill("/auto-verify", args="--strict-gates")` with no files and no range, and auto-verify exposes NO commit-range parameter to receive the loop's `<pre_merge_sha>..HEAD`. Literal path: zero changed files detected → STEP 1's zero-test classification's "No code changed (docs/config/fixtures-only, **or no changed files**): write `result: "PASSED"`, `summary.total: 0`" → the mechanical gate vacuously greens the exact merged diff it was dispatched to verify. Note the NO_TESTS_FOR_CHANGE strict-gates guard (v4.2.0) cannot fire — it requires "Changed files include source", and zero files were detected at all. (b) STEP 3 Pre-Existing Failure Detection: "`git stash && <test_runner> <failing_test> && git stash pop`" — with all changes committed, `git stash` stashes nothing, so "clean state" IS our state; a genuine regression fails in both runs and the table row "FAILS \| FAILS \| Pre-existing \| Note it, do not block" waves the regression through as non-blocking. Mitigations (why not CRITICAL): loop-engineering's gate needs all three of mechanical + independent reviewer + supervisor reproduction, and a model-layer executor may infer the range from context; but the mechanical leg — the only deterministic one — is structurally hollow for this caller class. Fix: add a `--range <base>..<head>` (or `--base <sha>`) parameter, default the detection ladder to `git diff HEAD` → `git diff <merge-base>` when the working tree is clean, thread the range into `/regression-test` (whose argument-hint already accepts `<branch\|commit-range\|staged>`), and replace the stash check with "re-run the failing test at `<base>`" (worktree/`git stash` only when uncommitted changes exist); loop-engineering's STEP 5 invocation should then pass `--range <pre_merge_sha>..HEAD`. |
| F3 | minor | **Registry description stale — missing the boundary sentence.** Registry `description` ends at "…produces structured results for pipeline consumption." and omits the frontmatter's "Does NOT fix — use /fix-loop for fixes, /test-pipeline for the full fix-verify-commit chain." The blind-routing evidence above shows that sentence is load-bearing for Q4-class routing; docs/recommend consumers currently see the weaker text. Fix: resync registry description to the frontmatter (batchable metadata fix, EVAL-WORKFLOW rule 6). |
| F4 | minor | **Dead FLAKY branch in the STEP 0 gate — schema drift vs testing.md/fix-loop.** STEP 0: "If `result` is `FAILED` or `FLAKY` → BLOCK" and CRITICAL RULES "if upstream fix-loop reported FAILED or FLAKY". testing.md: "There is no separate FLAKY result — flaky is a failure category" (canonical enum PASSED\|FAILED\|FIXED + `flaky_detected: true`), and fix-loop v1.6.0 aligned to exactly that. No blocking gap (a flaky run arrives as FAILED and blocks), but the FLAKY literal can never match. Fix: check `flaky_detected` instead, or drop FLAKY. |
| F5 | minor | **STEP 0's UNKNOWN fall-through comment is not implemented — strict-gates bypass on a corrupt upstream file.** The bash prints "WARN: fix-loop.json unreadable — treating as missing" with comment "# Fall through to the missing-file logic below" — but the missing-file logic (including "With `--strict-gates`: BLOCK") lives in the outer `else` (file-does-not-exist) branch, which an existing-but-corrupt file never reaches; the script proceeds to STEP 1. So under `--strict-gates`, a truncated/corrupt fix-loop.json degrades to WARN+proceed instead of the promised BLOCK. Related INFO: `$STRICT_GATES` is referenced but the snippet never shows it being bound from the `--strict-gates` argument. Fix: on UNKNOWN, apply the same `if [ "$STRICT_GATES" = "true" ]; then BLOCK` clause inline. |
| F6 | minor | **`ui_verdict`/`code_verdict` are consumed but never defined in tester-agent's return contract.** STEP 2: "After `tester-agent` returns, the agent provides TWO verdict dimensions: \| `ui_verdict` \| … \| `code_verdict` \|" — but the skill's own dispatch prompt requests "Return: verdict (PASSED/FAILED), test counts, failure details, ui_test_count, screenshot manifest, per-test verdict_source" (a SINGLE verdict), and tester-agent.md v3.0.0 defines no `ui_verdict`/`code_verdict` fields in any mode. Derivable from per-test `verdict_source` data, so minor — but a literal executor waits for fields that never arrive. Fix: either request the two dimensions in the dispatch prompt (and add them to tester-agent's output format) or state "compute ui_verdict/code_verdict from the per-test verdict_source entries". |
| F7 | minor | **references/visual-proof-review.md's visual-review.json example drifts from testing.md's canonical Visual Review Schema.** The reference's `overrides[]`/`flags[]` entries omit the `verdict_source` field that testing.md's schema includes per entry ("original_result": "PASSED", **"verdict_source": "screenshot"**, …). SKILL.md's own embedded `visual_review` summary matches testing.md. Fix: add `verdict_source` to the reference's two example entries. |
| F8 | minor | **Undeclared flag `--strict-quality`.** STEP 4 item 4: "report as QUALITY_GATE warning (non-blocking unless `--strict-quality`)" — the flag appears in neither the Parameters table nor the `argument-hint`, so no caller can discover or pass it. Fix: add it to both, or reword to "(non-blocking; the orchestrator may treat WARNED as blocking)". |
| F9 | minor | **Registry dependencies incomplete vs the delegation closure.** Registry lists `['regression-test', 'tester-agent']`; the body also delegates via Skill()/reference to `/code-quality-gate` (STEP 4 "delegates to `/code-quality-gate`"), `/contract-test` (STEP 4A), `/perf-test` (STEP 4B). Hub convention includes skill deps (cf. fix-loop v1.6.0's registry entry, expanded to "the real delegation closure"). Fix: add the three (metadata-only, batchable). |
| F10 | INFO | **Reference file >100 lines without a TOC.** visual-proof-review.md is 124 lines with 4 `##` sections and no table of contents (EVAL-WORKFLOW 1c wants a TOC >100 lines). Borderline given only 4 sections; record, don't block. |
| F11 | INFO | **`$RUN_ID` generation undefined in the body.** STEP 2's dispatch passes "Run ID: $RUN_ID" and paths use `test-evidence/{run_id}/`, but the skill never says who mints run_id or points at testing.md's `{ISO-8601}_{7-char-sha}` format. A standalone run must infer it. One pointer line fixes it. |

## Ecosystem check (STEP 0.5)

Neighbors compared: fix-loop, test-pipeline, e2e-visual-run, regression-test,
verify-screenshots, post-fix-pipeline (+ development-loop as an outer caller).
- auto-verify → neighbors: PASS — description names /fix-loop and /test-pipeline
  with the does-not-fix boundary.
- Neighbors → auto-verify: PASS — test-pipeline ("For verification without
  fixes, use /auto-verify"), e2e-visual-run ("post-change targeted verification
  (use /auto-verify)"), verify-screenshots ("pipeline-integrated visual review
  as part of auto-verify (invoked automatically by /auto-verify Step 2.5)"),
  post-fix-pipeline ("reading the upstream auto-verify gate … Does NOT re-run
  tests — use /auto-verify for that"). Fully bidirectional; confirmed working
  by the 36/36 blind-routing result.
- Near-duplicate resolution: NOT a duplicate. auto-verify is the pipeline's
  VERIFY stage; /regression-test is its delegated mapper (STEP 1 explicitly
  "MAPPING ONLY … avoids double execution"); /test-pipeline orchestrates it;
  /fix-loop is its upstream healer. Ecosystem role: the mechanical gate. Keep.
- Skill-vs-rule overlap: testing.md owns the JSON schema and auto-verify
  points at it ("This JSON is consumed by stage gates — see `testing.md` for
  the full schema") — correct SSOT layering. workflow.md Step 6 and
  engineering-roles.md route to /auto-verify as pointers, not copies.

## Pre-flight (STEP 0) and structural audit (STEP 1) — checked, mostly clean

- 0.1 Registry sync: Hash PASS — `dedup_check.hash_pattern` computed
  `4596f2f1…` == registry hash (verified live). Version PASS — registry 4.3.0
  == frontmatter 4.3.0; registry `changelog` latest entry is v4.3.0 and
  matches. Description FAIL-minor (F3). Dependencies FAIL-minor (F9).
- 0.2 Frontmatter: PASS — name matches dir; description third-person,
  verb-first, <1024 chars, states what AND when AND the not-this boundary;
  type workflow; 6 triggers; version SemVer; allowed-tools
  "Bash Read Grep Glob Write Skill Agent" all used (Bash: gates/stash; Write:
  JSON; Skill: regression-test/code-quality-gate/contract-test/perf-test;
  Agent: tester-agent), `Edit` correctly ABSENT for a does-not-fix skill —
  least-privilege honored.
- 0.3 Structural integrity: PASS — 14 fence markers = 7 balanced pairs;
  SKILL.md 476 lines (<500); step refs (0/1/2/2.5/3/4/4A/4B/5/6) all resolve;
  skill refs /regression-test /fix-loop /test-pipeline /code-quality-gate
  /contract-test /perf-test /development-loop all exist; agent ref
  tester-agent exists (tester-agent.md v3.0.0); rule refs
  output-plausibility-verification.md / dod-verbs.md / testing.md exist;
  references/visual-proof-review.md exists, depth 1, no onward file chains
  (its /verify-screenshots mention is a pointer); no placeholder markers;
  critical constraints in BOTH preamble ("Does NOT fix") and CRITICAL RULES.
- 1b Content: PASS with notes — steps verb-phrased ("Gate Check", "Map
  Changes", "Execute Tests", "Evaluate Results" — acceptable); conditional
  logic tabled (verdict combinations, pre-existing matrix, dual-verdict
  table); outputs templated (report block + JSON); no vague language; no
  Windows paths. CRITICAL RULES: 10 items, each with "— Why:" (above the 4–8
  checklist band — INFO only; every item is load-bearing).
- Dispatch caveats: tester-agent registry-pinning is handled by design —
  the STEP 2 fallback ("run tests directly … without UI screenshot
  verification") covers both not-provisioned and mid-session-synced agents,
  and the silent-degradation gate then blocks a UI PASSED unless
  `--allow-degraded-ui` — i.e. the degraded path cannot silently green UI
  work **provided F1's routing fix lands so the gate actually runs on the
  PASS path** (as literally routed today, the fallback + F1 combine into
  exactly the silent degradation the gate exists to catch).

## Loop integration (loop-engineering STEP 5, as invoked)

- Invocation: `Skill("/auto-verify", args="--strict-gates")` inline at T0;
  the loop then reads `test-results/auto-verify.json`. File path and the
  `result` field name match exactly; the loop's gate condition "the
  mechanical result is `PASSED`" matches auto-verify's PASSED\|FAILED enum
  (auto-verify never emits FIXED — correct, it never fixes; the loop's SHIP
  arm passes `test-results/auto-verify.json` on to /post-fix-pipeline, which
  reads the same field). Vocabulary: ALIGNED.
- State: auto-verify's "Standalone cleanup: When running outside the pipeline
  (no Pipeline ID), delete stale test-results/auto-verify.json" prevents the
  loop's gate from reading a previous cycle's verdict. ALIGNED.
- STEP 0 gate in loop context: `test-results/fix-loop.json` typically absent
  on a first VERIFY entry → with `--strict-gates` the literal STEP 0 text
  BLOCKS ("BLOCKED: fix-loop output missing — run fix-loop first or use
  orchestrator"). The loop is not the /test-pipeline orchestrator and runs
  VERIFY before any fix-loop — so the strict missing-upstream block is a
  standing friction for this caller; it happens to be moot only because of
  the two committed-change failure surfaces of F2 (a literal executor never
  even reaches a meaningful test run). Fold into the F2 fix: give the loop's
  invocation an explicit "first-verify, no upstream" shape (e.g.
  `--strict-gates --range <pre_merge_sha>..HEAD --no-upstream-gate` or have
  the loop write a synthetic upstream stub) — as written, bare
  `--strict-gates` from loop-engineering either BLOCKs at STEP 0 (literal)
  or vacuous-greens at STEP 1 (F2), depending on which literalism wins.
  This is the single most important integration repair.

## Rubric scores (5 criteria, 1–5)

| Criterion | Score | Basis |
|---|---|---|
| 1. Trigger reliability | 5/5 | 36/36 blind routing, 0 misfires, 0 conflicts, unanimous across sonnet+haiku incl. adversarial run |
| 2. Output contract | 4/5 | `result` canonical, schema matches testing.md, visual_review embed correct; minors F4 (dead FLAKY), F7 (reference schema drift), F11 (run_id) |
| 3. Literal executability | 3/5 | F1 MAJOR routing contradiction bypasses the silent-degradation gate on the PASS path and the mandatory review on the FAIL path; F5, F6, F8 minors |
| 4. Loop integration | 3/5 | F2 MAJOR committed-change blindspot (vacuous PASS + stash misclassification) plus the STEP 0 missing-upstream friction, on the exact loop-engineering STEP 5 default invocation |
| 5. Cross-skill conflicts | 5/5 | Model bidirectional signposting across 6 neighbors; every neighbor won its own query 3/3 |

**Average: 4.0/5 — but two MAJORs stand, so per the PASS bar (≥4/5 avg AND no
CRITICAL/MAJOR) the verdict is FIX.**

## OVERALL VERDICT: FIX

Blocking issues: none CRITICAL. Recommended fixes (prioritized):

1. **F1** — reroute STEP 2 to the linear 2 → 2.5 → 3 → 4 flow the sub-steps,
   the reference, and testing.md already assume; make STEP 3 the single
   verdict-assembly point (silent-degradation gate + override union + flags)
   on BOTH pass and fail paths. (SKILL.md change → MINOR bump to 4.4.0 +
   registry hash resync.)
2. **F2** — add a commit-range input (`--range <base>..<head>`), default the
   change-detection ladder to `git diff HEAD` / merge-base when the working
   tree is clean, thread the range into /regression-test, and replace the
   git-stash pre-existing check with a run-at-base check for committed-change
   callers; then update loop-engineering STEP 5 to pass
   `--range <pre_merge_sha>..HEAD` (companion edit in loop-engineering,
   out of this skill's file but part of the same fix PR).
3. **F4 + F5 + F6 + F8** — one-line text edits in the same PR (flaky_detected
   check; strict-gates block on UNKNOWN; ui/code_verdict derivation note;
   declare or drop --strict-quality).
4. **F3 + F9** — registry resync (description + dependency closure) —
   metadata-only, batchable per EVAL-WORKFLOW rule 6.
5. **F7 + F10 + F11** — reference polish (verdict_source in examples, TOC,
   run_id pointer).

After fixes: re-run the trigger matrix is NOT required (no description change
is mandated — F3 copies the existing description INTO the registry); re-walk
STEP 2→3 routing and the loop-integration path (F1/F2) against the new text.

Method note: full-mode adapted to text-level per the eval brief — trigger axis
run LIVE via 3 context-blind routing subagents over the real frontmatter
descriptions (routers not told which skill was under evaluation); output axis
via step-by-step executability walk of SKILL.md + references/ against
testing.md's canonical contract and loop-engineering STEP 5's literal
invocation; registry hash verified live with dedup_check.hash_pattern (strip +
collapse whitespace normalization), not raw bytes. No live verification
pipeline was executed.
