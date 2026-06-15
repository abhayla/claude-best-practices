# QA Report: /development-loop workflow (downstream)

**Date:** 2026-06-15  **Tester role:** QA / Test Automation Engineer
**Subject:** merged hardened `/development-loop` (skill v2.1.0) provisioned into a fresh Node+TS downstream sandbox via the real provisioning path.
**Method:** executed the workflow's observable contract behaviors against a real sandbox. Deterministic safety properties → hard evidence; LLM-judgment routing → spec-conformance against SKILL.md STEP 1.

## Results matrix

| # | Test | Type | Verdict | Evidence |
|---|------|------|---------|----------|
| T1 | PREFLIGHT passes when closure present | deterministic | **PASS** | closure files present → proceed |
| T2 | PREFLIGHT BLOCKs on missing worker | deterministic | **PASS** | removed plan-executor-agent → `WORKER_REGISTRY_NOT_LOADED` |
| T3 | Simple complexity → skip IDEATE+PLAN | spec-conformance | **PASS** | STEP 1 heuristic: single-file/"fix"/"just" → EXECUTE→VERIFY→COMMIT |
| T4 | Medium → skip IDEATE, run PLAN | deterministic (e2e) | **PASS** | prior e2e: parseDollars built PLAN→EXECUTE→VERIFY→COMMIT |
| T5 | Complex → all 5 steps | spec-conformance | **PASS** | STEP 1: 6+ files/cross-layer → ideate+plan+execute+verify+commit |
| T6 | **VERIFY gate blocks commit on failing tests** | deterministic | **PASS** | buggy multiply → tests FAIL → commit count unchanged (gate held) |
| T7 | VERIFY pass → commit proceeds (+fix-loop) | deterministic | **PASS** | fix → tests PASS → committed exactly once |
| T8 | `--no-commit` stops after VERIFY | deterministic | **PASS** | green verify, no commit produced |
| T9 | Empty args → ask for feature | spec-conformance | **PASS** | SKILL: "If $ARGUMENTS empty, ask the user" |
| T10 | Trivial task → suggest `/implement` | spec-conformance | **PASS** | SKILL preamble routes trivial → /implement |
| T11 | run_id format + idempotent re-run | deterministic | **PASS** | `{ISO}_{7sha}` regex valid, two runs distinct |
| T12 | REPORT verdict + state schema integrity | deterministic | **PASS** | required keys present; canonical `result` enum PASSED\|FAILED\|BLOCKED |
| T13 | Runtime dirs gitignored | deterministic | **PASS** | `.workflows/`, `test-results/`, `test-evidence/` in sandbox .gitignore |
| T14 | EXECUTE BLOCKED/FAILED → abort to REPORT, skip verify+commit | contract-integrity | **PASS** | abort-path text present in provisioned SKILL |

**14/14 PASS.** Core safety gate (T6) and provisioning closure both hold.

## Findings (defects / risks)

### F1 — VACUOUS-GREEN: no-tests project commits "verified" code (MEDIUM) — tracked: [#50](https://github.com/abhayla/claude-best-practices/issues/50)
- **Repro:** a downstream project whose test command is `node --test` with **zero test files** exits 0 → `/auto-verify` reports `result: PASSED` → `/development-loop` VERIFY gate passes → STEP 6 COMMITs code that was never actually exercised, while the verdict claims "verified".
- **Evidence:** `node --test` on an empty test dir → `exit=0`.
- **Root cause:** the VERIFY gate asserts "tests did not fail", not "≥1 meaningful test ran". A runner that exits 0 on zero tests makes the gate vacuous. This is the shape-vs-substance miss class (`output-plausibility-verification.md`, `dod-verbs.md`).
- **Why missed:** the prior hardening validation only exercised projects that already had passing tests; it never tested the empty-suite path.
- **Sibling audit (Class: vacuous-green verify gate):** stack-dependent. `node --test` → exit 0 (vulnerable). `pytest` → exit 5 "no tests collected" (non-zero; not a clean pass, so less vulnerable). Any workflow whose VERIFY delegates to `/auto-verify` (testing-pipeline, debugging-loop) shares the class. Owner of the robust fix is `/auto-verify` (it should report a distinct verdict when 0 tests executed), with `/development-loop` treating "0 tests on a code-producing run" as not-PASSED.
- **Recommended fix (separate change — out of scope for a TEST pass):** `/auto-verify` emits `result: FAILED` (or a `NO_TESTS` warning that the strict gate treats as fail) when a code change produced 0 executed tests; assert `summary.total >= 1` for a code-producing run.

## Out of scope / not a defect
- Complexity routing exactness (T3/T5) is LLM judgment; the heuristic is well-specified — marked spec-conformance, not deterministically executed.
- `--research` (planner-researcher dispatch) not exercised end-to-end (needs a real research-triggering task); closure presence verified.
