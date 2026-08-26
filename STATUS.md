# T-370 status — hub GWD skill<->fleet conformance tests (ratchet)

Fix round 1 (task T-370F). Contract: `D:/Abhay/GetWorkDone/queue/T-370-hub-gwd-skill-conformance-tests-ratchet.claimed.20b6c4c6.md`.

## DoD items (from contract, in order) — honest state as of this fix round

1. `scripts/tests/test_gwd_skill_conformance.py` — commit `ade96697`. **File verified to exist on disk.** 6 assertions against `.claude/skills/get-work-done/SKILL.md` + live fleet at `$GWD_ROOT` (paths, settings keys, preflight exit codes bidirectional, <=1 `claude -p` recipe, `/skill` refs, byte ratchet). Also adds `scripts/gwd_skill_conformance.py` (extraction/diff library).
2. `config/gwd-skill-conformance-grandfather.yml` — commit `ade96697`. **File verified to exist on disk.** Known drifts C2/M1/M3/M10 listed, shrink-only, self-tested (`test_gwd_skill_conformance_grandfather_ratchet.py`).
3. `scripts/tests/test_gwd_skill_musts_have_gates.py` + `config/gwd-gates.yml` — commit `28d1d0a3`. **Both files verified to exist on disk.** Every CRITICAL RULES MUST carries `gate:<id>`; ungated MUSTs grandfathered as `gate:PROSE-ONLY` via `max_ungated_musts` in the shrink-only yml.
4. `scripts/check_eval_coverage.py` freshness check — commit `417a745a`. **File verified to exist and diff confirmed** (`stale_changed_skills()` + wiring into `main()`); `scripts/tests/test_eval_coverage_freshness.py` added. Red-then-green recorded in the commit message.
5. PR hygiene — **NOT DONE going into this fix round.** `hold` label IS present (verified via `gh pr view 597 --json labels`). BUT: the last push (`417a745a`) carried a `[skip ci]` marker in its commit body, so **no CI checks ever ran** — `gh pr checks 597` reports "no checks reported on the 't370-gwd-conformance-tests' branch". Full local CI block from CLAUDE.md has **never been run** in this worktree before this fix round. This is the actual work of T-370F: run full local CI, fix anything red caused by these files, do the final no-marker push, and watch real CI to green.

## This fix round's plan (T-370F)

1. Rewrite STATUS.md + PR body honestly (this commit). ✅ in progress
2. Run FULL local CI block from CLAUDE.md ("Full local CI replication") in this worktree, `$env:PYTHONPATH='.'`, each command foregrounded — record real pass/fail per command below.
3. Run the four new test modules with `GWD_ROOT=D:/Abhay/GetWorkDone` and record N passed / N skipped.
4. Confirm PR body lists every grandfathered drift + every `gate:PROSE-ONLY` MUST count (T-371 punch list).
5. Final push: empty commit, NO skip-ci marker anywhere, `gh pr checks 597 --watch` in the foreground until every check reports. Fix anything red caused by these files, re-push (no marker), re-watch.

## Full local CI (CLAUDE.md "Full local CI replication") — results

Run in this worktree, `$env:PYTHONPATH='.'` (bash `export PYTHONPATH=.`), each command foregrounded.

| # | Command | Result |
|---|---|---|
| 1 | `dedup_check.py --validate-all` | PASS — "Registry validation passed" |
| 2 | `dedup_check.py --secret-scan` | PASS — "No secrets found" |
| 3 | `workflow_quality_gate_validate_patterns.py` | PASS — "PASSED: All patterns valid (47 warning(s))" — all 47 warnings pre-existing (skill line-count/description-verb warnings across the hub), none touch any T-370 file |
| 4 | `pytest scripts/tests/ -v` (quiet: `-q`) | **1 failed, 2229 passed, 156 skipped.** The 1 failure (`test_fleet_script_health.py::test_real_fleet_has_no_unknown_silent_failure_findings`) is a pre-existing, unrelated check: it inspects the LIVE fleet directory `D:/Abhay/GetWorkDone` on disk (kt-backup.cmd, ww-base.ps1, worker-wrapper.ps1, sweep-silent-exit.ps1, pf-backup.ps1) against a known-findings floor — the fleet has drifted new findings since that floor was last updated. None of the flagged files are in this PR's diff; this test does not read anything T-370 touches. Not caused by my files, not fixed here (out of contract scope). |
| 5 | `check_eval_coverage.py --enforce --base origin/main` | PASS — "check_eval_coverage: all changed skills covered and fresh" |
| 6 | `check_plugin_version_bump.py --base origin/main` | PASS — "Plugin version-bump gate: OK" |
| 7 | `generate_root_marketplace.py --check` | PASS — "OK: ...marketplace.json is in sync" |

**6/7 clean, 1 pre-existing unrelated failure** (live-fleet-state check, not a T-370-diff check).

## Four new T-370 test modules (with `GWD_ROOT=D:/Abhay/GetWorkDone`)

Ran directly (not just as part of the full suite above) to confirm none skip when GWD_ROOT is set:

```
scripts/tests/test_gwd_skill_conformance.py                    6 passed
scripts/tests/test_gwd_skill_conformance_grandfather_ratchet.py 7 passed
scripts/tests/test_gwd_skill_musts_have_gates.py                4 passed
scripts/tests/test_eval_coverage_freshness.py                   5 passed
```

**22/22 passed, 0 skipped** with `GWD_ROOT=D:/Abhay/GetWorkDone` set — confirms these tests actually exercise the live fleet checkout, not just the `GWD_ROOT`-unset skip path.

## PR body / T-371 punch list cross-check

Verified `config/gwd-skill-conformance-grandfather.yml` on disk lists exactly: `missing_preflight_exit_codes: [1,2,3,5,9,10,11,12,13,14]` (M1), `plugin_skill_allowlist: [goal-creator]` (M3), `stale_paths: [D:\Abhay\VibeCoding\...]` (M10), `max_claude_p_recipes: 2` (C2), `max_ungated_musts: 26` (all 26 CRITICAL RULES MUSTs are `gate:PROSE-ONLY` today). All of these are named in the PR body as the T-371 punch list — cross-checked line by line, matches.

## Findings this test suite encodes (from the review, verified independently while scoping)

- SKILL.md mentions only preflight exit codes {0,4,6,7,8}; the live header table defines {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14} — 10 codes undocumented (M1).
- Two `claude -p --model ...` launch recipes exist in SKILL.md (line ~372 STDIN-redirect, line ~590 checker launch) — contradicts the wrapper's argv-based launch at ~425 (C2).
- `/goal-creator` (invoked by SKILL.md STEP 5) does not exist under `.claude/skills/` — only under `core/.claude/skills/` (forbidden for hub work per this repo's own CLAUDE.md) and `plugins/loop-engineering/skills/` (M3).
- `D:\Abhay\VibeCoding\claude-best-practices` (SKILL.md:314) no longer exists on disk (M10).
- CRITICAL RULES block has 26 `MUST`/`MUST NOT` bullets, none carry a `gate:<id>` token today — all grandfathered as `gate:PROSE-ONLY`.
- All `GWD\<script>` / absolute paths + `settings.<key>` references currently resolve cleanly (no drift on those two checks).

`check_fleet_script_health.py` run against the fleet dir separately reports 27 findings (not fixed here per contract — out of scope, mentioned only).
