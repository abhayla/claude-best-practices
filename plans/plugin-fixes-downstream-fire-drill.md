# Contract: downstream fire-drill of the 2026-07-15 plugin QA fixes

Executor: a CHEAPER-DRIVEN session (Opus driver, or /loop-engineering sonnet maker + opus
checker) per `model-routing.md` session-level routing — this is written-plan + machine-gate
work. Authored 2026-07-15 after the plugin QA review (PRs #408/#413); zero open questions.

## Why (what this proves that the hub review could not)

The QA review certified all deterministic gates (structural/CLI/serve, 30/30) and fixed all
21 findings — but two fixes are prose-enforced (the `update-practices` STEP 4.5 pointer
guard; the loop-engineering PREFLIGHT gates) and NO end-to-end downstream run has exercised
the fixed versions. Downstream installs still serve OLD cached versions until
`/plugin update`. This drill closes both gaps on one real project.

## Target

`../calculatekaro` (the standard dogfood repo; plugins-first since 2026-07-13). Work in
that repo on a branch per ITS conventions; nothing here touches the hub except the results
note (step 6).

## Steps + gates (each independently checkable)

1. **Update installs**: in calculatekaro run `/plugin update <name>` for every installed
   cbp/hub plugin. GATE: `claude plugin list` (or the cache dir
   `~/.claude/plugins/cache/`) shows the new versions — loop-engineering 0.5.0,
   cbp-workflows ≥0.2.1, cbp-build-test-workflows ≥0.2.2, cbp-learning-workflow ≥0.1.2,
   prompt-auto-enhance 0.4.3, branch-lifecycle 0.1.3, cbp-react-stack 0.1.1. Versions are
   the load-bearing signal (version-pinned cache).
2. **Pointer-guard drill**: run `/update-practices --check-only`. GATE: it reports
   plugin-covered skills as "update via /plugin update", copies ZERO pointer skills into
   `.claude/skills/`, and still offers residual-surface items (path-scoped rules/configs)
   if any are stale. Any pointer file appearing under `.claude/skills/` = FAIL.
3. **PREFLIGHT drill (negative test)**: temporarily rename ONE bundled agent in the
   installed loop-engineering cache copy (e.g. `tester-agent.md` → `.bak`), start a fresh
   session, run `/auto-verify`. GATE: it BLOCKS with `WORKER_REGISTRY_NOT_LOADED` and an
   actionable message — no mid-dispatch crash, no silent inline. Restore the file after.
4. **Closure drill (positive test)**: with installs intact, run `/fix-loop` against a
   deliberately broken trivial test in calculatekaro. GATE: test-failure-analyzer-agent
   dispatches successfully (it now ships in the plugin) and the loop fixes + retests green.
5. **Real-suite regression**: run calculatekaro's own full test suite. GATE: green, same
   count as its last known-good run (its repo docs/PRs #14 record 222 tests).
6. **Report back**: append results (per-gate PASS/FAIL + versions observed) to hub issue
   #346 as a comment, and file any failure as a hub issue tagged `plugin-qa-fire-drill`.

## Budgets / stop conditions

Max 2 fix attempts per failing gate, then file the failure and continue to the next gate
(never silently skip; never weaken a gate to pass). No deploys, no spend, no force-push.
Restoring the step-3 rename is mandatory even on abort.

## DoD

All 6 gates reported PASS on issue #346, or every FAIL filed as its own issue. Nothing
else counts as done.
