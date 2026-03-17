# Implementation Plan: Test Pipeline Overhaul + Screenshot-as-Proof

**Created:** 2026-03-17
**Estimated total time:** ~126m (buffered)
**Critical path:** Plan 1 → Plan 2 → Plan 3 (T12) → Plan 4 (T15-16) → Plan 5 (T24-25)

## Decisions

1. **Scope:** UI/E2E tests only (non-UI already has evidence capture via Pact, traces, k6)
2. **Storage:** Local-only (`test-evidence/` gitignored), CI upload via optional hook
3. **Review rate:** 100% of all screenshots (pass and fail)
4. **Timing:** Implemented together with P0 pipeline fixes
5. **Code-quality-gate split:** Non-breaking `references/` extraction (preserves step numbers, JSON paths, cross-references)
6. **Gate behavior:** Fail-closed with `--strict-gates` (orchestrator), warn-and-proceed without (standalone)

## Issues Addressed

| # | Type | Issue | Fix |
|---|------|-------|-----|
| 1 | Redundancy | `/auto-verify` ≈ `/regression-test` | Delegate Steps 1-2 to `/regression-test` |
| 2 | Redundancy | `/auto-verify` reimplements `/fix-loop` | Remove inline fix logic, verify-only |
| 3 | Redundancy | `/post-fix-pipeline` re-runs tests | Remove Steps 1-2, trust upstream |
| 4 | Orphan | `tester-agent` never called | Wire as execution engine in `/auto-verify` |
| 5 | Gap | No orchestrator | Create `test-pipeline-agent` |
| 6 | Orphan | `test-failure-analyzer-agent` disconnected | Wire into `/fix-loop` Step 1 |
| 7 | Violation | `/code-quality-gate` 876 lines | Extract to `references/` directory |
| 8 | Gap | No terminal aggregator | Orchestrator runs aggregation as final step |
| 9 | Gap | Stale artifacts between runs | Orchestrator wipes `test-results/` at start |
| 10 | Bug | Gates bypass on missing files | `--strict-gates` = fail-closed |
| NEW | Feature | Screenshot-as-proof | `--capture-proof` toggle, visual review step |

---

## Atomic Plan 1: Orchestrator + Config + Evidence Infrastructure

- [x] **Task 1:** Create `config/test-pipeline.yml` — Pipeline DAG definition
  - Files: `config/test-pipeline.yml` (create)
  - Verify: `PYTHONPATH=. python -c "import yaml; d=yaml.safe_load(open('config/test-pipeline.yml')); assert len(d['pipeline']['stages'])==3; assert d['global_retry_budget']==15; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 2:** Create `core/.claude/templates/test-evidence-config.json` — Evidence config template
  - Files: `core/.claude/templates/test-evidence-config.json` (create)
  - Verify: `python -c "import json; d=json.load(open('core/.claude/templates/test-evidence-config.json')); assert 'capture_proof' in d; assert 'platforms' in d; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 3:** Create `core/.claude/agents/test-pipeline-agent.md` — Pipeline orchestrator
  - Files: `core/.claude/agents/test-pipeline-agent.md` (create)
  - Verify: `python -c "content = open('core/.claude/agents/test-pipeline-agent.md').read(); assert 'name: test-pipeline-agent' in content; assert 'Core Responsibilities' in content; assert 'Output Format' in content; assert 'config/test-pipeline.yml' in content; assert 'test-evidence' in content; assert 'capture_proof' in content; assert 'strict-gates' in content; assert 'MUST NOT' in content; print('OK')"`
  - Time: ~8m
  - Depends on: Task 1, Task 2

**Dependency graph:** T1 → T3, T2 → T3
**Critical path estimate:** ~14m | Buffered: ~17m

---

## Atomic Plan 2: Pipeline Deduplication & Gate Fixes

- [x] **Task 4:** Add `--strict-gates` and `--capture-proof` parameters to `/auto-verify`
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — frontmatter + parameters)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert '--strict-gates' in c; assert '--capture-proof' in c; assert 'Parameters' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 5:** Rewrite `/auto-verify` Step 0 — Fail-closed gates
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — lines 22-44)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert 'BLOCKED: fix-loop output missing' in c; assert 'WARN: No fix-loop results' in c; print('OK')"`
  - Time: ~3m
  - Depends on: Task 4

- [x] **Task 6:** Rewrite `/auto-verify` Steps 1-2 — Delegate to `/regression-test`
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — lines 48-86)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert '/regression-test' in c; assert 'regression-test.json' in c; assert 'Import-Based Mapping' not in c; print('OK')"`
  - Time: ~5m
  - Depends on: Task 5

- [x] **Task 7:** Remove `/auto-verify` Steps 4-5 — Eliminate inline fix logic
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — lines 114-165)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert 'Do NOT attempt fixes' in c; print('OK')"`
  - Time: ~5m
  - Depends on: Task 6

- [x] **Task 8:** Rewrite `/post-fix-pipeline` — Remove redundant test re-runs, add strict gates
  - Files: `core/.claude/skills/post-fix-pipeline/SKILL.md` (modify — lines 1-75)
  - Verify: `python -c "c = open('core/.claude/skills/post-fix-pipeline/SKILL.md').read(); assert 'version: \"2.0.0\"' in c; assert 'Regression Testing' not in c; assert 'visual-review.json' in c; assert 'Does NOT re-run tests' in c; print('OK')"`
  - Time: ~7m
  - Depends on: Task 5

- [x] **Task 9:** Update `/regression-test` — Add integration note for `/auto-verify` consumers
  - Files: `core/.claude/skills/regression-test/SKILL.md` (modify — after line 21)
  - Verify: `python -c "c = open('core/.claude/skills/regression-test/SKILL.md').read(); assert 'canonical change-to-test mapper' in c; print('OK')"`
  - Time: ~2m
  - Depends on: Task 6

**Dependency graph:** T4 → T5 → T6 → T7 → T9, T8 parallel with T6-T7
**Critical path estimate:** ~23m | Buffered: ~28m

---

## Atomic Plan 3: Wire Disconnected Agents Into Pipeline

- [x] **Task 10:** Wire `test-failure-analyzer-agent` into `/fix-loop` Step 1
  - Files: `core/.claude/skills/fix-loop/SKILL.md` (modify — lines 39-63)
  - Verify: `python -c "c = open('core/.claude/skills/fix-loop/SKILL.md').read(); assert 'test-failure-analyzer-agent' in c; assert 'Agent(' in c; assert 'COMPILE_ERROR' in c; assert 'EMPTY_ASSERTION' in c; print('OK')"`
  - Time: ~5m
  - Depends on: None

- [x] **Task 11:** Add `--strict-gates` and `--capture-proof` to `/fix-loop`
  - Files: `core/.claude/skills/fix-loop/SKILL.md` (modify — frontmatter + parameters + Step 3)
  - Verify: `python -c "c = open('core/.claude/skills/fix-loop/SKILL.md').read(); assert '--capture-proof' in c; assert '--strict-gates' in c; print('OK')"`
  - Time: ~3m
  - Depends on: Task 10

- [x] **Task 12:** Wire `tester-agent` into `/auto-verify` Step 2
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — test execution step)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert 'tester-agent' in c; assert 'Agent(' in c; assert 'ResourceWarning' in c; assert 'manifest.json' in c; print('OK')"`
  - Time: ~5m
  - Depends on: Tasks 6-7 (Plan 2)

- [x] **Task 13:** Update `tester-agent` — Add screenshot capture responsibilities
  - Files: `core/.claude/agents/tester-agent.md` (modify — responsibilities + process)
  - Verify: `python -c "c = open('core/.claude/agents/tester-agent.md').read(); assert 'Evidence Capture' in c; assert 'manifest.json' in c; assert 'Playwright' in c; assert 'Maestro' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 14:** Update `test-failure-analyzer-agent` — Add consumer note
  - Files: `core/.claude/agents/test-failure-analyzer-agent.md` (modify — after frontmatter)
  - Verify: `python -c "c = open('core/.claude/agents/test-failure-analyzer-agent.md').read(); assert 'Pipeline role' in c; assert 'canonical failure classifier' in c; print('OK')"`
  - Time: ~2m
  - Depends on: Task 10

**Dependency graph:** T10 → T11 → T14, T12 (after Plan 2), T13 (parallel)
**Critical path estimate:** ~18m | Buffered: ~22m

---

## Atomic Plan 4: Screenshot-as-Proof — Visual Review Step + Platform Updates

- [x] **Task 15:** Add Step 2.5 to `/auto-verify` — Visual Proof Review
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — insert between Step 2 and Step 3)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert 'STEP 2.5: Visual Proof Review' in c; assert 'visual-review.json' in c; assert 'multimodal Read' in c; assert 'OVERRIDE' in c; assert 'Lorem ipsum' in c; print('OK')"`
  - Time: ~8m
  - Depends on: Task 12

- [x] **Task 16:** Update `/auto-verify` structured output — Add visual review fields
  - Files: `core/.claude/skills/auto-verify/SKILL.md` (modify — structured output JSON)
  - Verify: `python -c "c = open('core/.claude/skills/auto-verify/SKILL.md').read(); assert 'visual_review' in c; assert 'screenshots_reviewed' in c; assert 'evidence_dir' in c; print('OK')"`
  - Time: ~3m
  - Depends on: Task 15

- [x] **Task 17:** Update Playwright skill — Document always-capture mode
  - Files: `core/.claude/skills/playwright/SKILL.md` (modify)
  - Verify: `python -c "c = open('core/.claude/skills/playwright/SKILL.md').read(); assert 'CAPTURE PROOF MODE' in c; assert 'test-evidence' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 18:** Update Android E2E skill — Document always-capture mode
  - Files: `core/.claude/skills/android-run-e2e/SKILL.md` (modify)
  - Verify: `python -c "c = open('core/.claude/skills/android-run-e2e/SKILL.md').read(); assert 'CAPTURE PROOF MODE' in c; assert 'test-evidence' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 19:** Update Flutter E2E skill — Document always-capture mode
  - Files: `core/.claude/skills/flutter-e2e-test/SKILL.md` (modify)
  - Verify: `python -c "c = open('core/.claude/skills/flutter-e2e-test/SKILL.md').read(); assert 'CAPTURE PROOF MODE' in c; assert 'test-evidence' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 20:** Update React Native E2E skill — Document always-capture mode
  - Files: `core/.claude/skills/react-native-e2e/SKILL.md` (modify)
  - Verify: `python -c "c = open('core/.claude/skills/react-native-e2e/SKILL.md').read(); assert 'CAPTURE PROOF MODE' in c; assert 'test-evidence' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

**Dependency graph:** T15 → T16, T17-T20 (all parallel)
**Critical path estimate:** ~23m | Buffered: ~28m

---

## Atomic Plan 5: Rules Update, Code-Quality-Gate Refs, Aggregation, Validation

- [x] **Task 21:** Update `testing.md` rule — Add proof archive format and visual review mandate
  - Files: `core/.claude/rules/testing.md` (modify — add section after line 345)
  - Verify: `python -c "c = open('core/.claude/rules/testing.md').read(); assert 'Screenshot Proof Archive' in c; assert 'manifest.json' in c; assert 'visual-review.json' in c; print('OK')"`
  - Time: ~5m
  - Depends on: None

- [x] **Task 22:** Add `references/` directory to `/code-quality-gate` — Non-breaking split
  - Files: `core/.claude/skills/code-quality-gate/references/error-handling-audit.md` (create), `core/.claude/skills/code-quality-gate/references/mutation-testing.md` (create), `core/.claude/skills/code-quality-gate/references/dead-code-detection.md` (create), `core/.claude/skills/code-quality-gate/SKILL.md` (modify)
  - Verify: `python -c "import os; assert os.path.exists('core/.claude/skills/code-quality-gate/references/error-handling-audit.md'); main = open('core/.claude/skills/code-quality-gate/SKILL.md').read(); lines = len(main.strip().split('\n')); assert lines < 550, f'Still {lines} lines'; assert 'STEP 12' in main; assert 'code-quality-gate.json' in main; print(f'OK — {lines} lines')"`
  - Time: ~8m
  - Depends on: None

- [x] **Task 23:** Update `verify-screenshots` — Add proof-mode integration
  - Files: `core/.claude/skills/verify-screenshots/SKILL.md` (modify — frontmatter + add Step 0.5)
  - Verify: `python -c "c = open('core/.claude/skills/verify-screenshots/SKILL.md').read(); assert '--proof-mode' in c; assert '--run-id' in c; assert 'STEP 0.5' in c; print('OK')"`
  - Time: ~3m
  - Depends on: None

- [x] **Task 24:** Run pattern validation
  - Files: None (validation only)
  - Verify: `PYTHONPATH=. python scripts/validate_patterns.py`
  - Time: ~5m
  - Depends on: Tasks 1-23

- [x] **Task 25:** Update `registry/patterns.json` and regenerate docs
  - Files: `registry/patterns.json` (modify), docs/ (regenerate)
  - Version bumps: `auto-verify` → 2.0.0, `fix-loop` → 1.2.0, `post-fix-pipeline` → 2.0.0, `tester-agent` → 1.2.0, `test-failure-analyzer-agent` → 1.1.1, `verify-screenshots` → 1.1.0
  - New entry: `test-pipeline-agent` v1.0.0
  - Verify: `PYTHONPATH=. python scripts/validate_patterns.py && python scripts/generate_docs.py && echo "OK"`
  - Time: ~5m
  - Depends on: Task 24

**Dependency graph:** T21, T22, T23 (parallel) → T24 → T25
**Critical path estimate:** ~26m | Buffered: ~31m

---

## New Pipeline Flow (after all tasks complete)

```
test-pipeline-agent (orchestrator)
  |
  +-- INIT: rm -rf test-results/ test-evidence/
  |         mkdir -p test-results test-evidence/{run_id}/screenshots
  |         read config/test-pipeline.yml + test-evidence-config.json
  |
  +-- STAGE 1: /fix-loop [--strict-gates] [--capture-proof]
  |    +-- dispatches test-failure-analyzer-agent (Step 1: classify)
  |    +-- applies fix (Step 2)
  |    +-- retests with screenshot capture (Step 3)
  |    +-- writes test-results/fix-loop.json
  |
  +-- STAGE 2: /auto-verify [--strict-gates] [--capture-proof]
  |    +-- STEP 0: gate check (fail-closed, reads fix-loop.json)
  |    +-- STEP 1: delegates to /regression-test (canonical mapper)
  |    +-- STEP 2: dispatches tester-agent (execute + capture screenshots)
  |    +-- STEP 2.5: visual proof review (multimodal Read, 100% review)
  |    +-- STEP 3: evaluate results (verify-only, no fixes)
  |    +-- STEP 4+: quality gate, contract test, perf test
  |    +-- writes test-results/auto-verify.json (includes visual_review field)
  |
  +-- STAGE 3: /post-fix-pipeline [--strict-gates] [--capture-proof]
  |    +-- STEP 0: gate check (reads auto-verify.json + visual-review.json)
  |    +-- STEP 1: documentation updates
  |    +-- STEP 2: git commit (includes evidence summary)
  |    +-- STEP 3: learning capture
  |    +-- writes test-results/post-fix-pipeline.json
  |
  +-- AGGREGATE: read all test-results/*.json
  |    +-- union of failures, contradiction detection
  |    +-- writes test-results/pipeline-verdict.json
  |
  +-- REPORT: summary with evidence location
```
