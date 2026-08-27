# T-353 / T-353F2 STATUS

Contract: `D:/Abhay/GetWorkDone/queue/T-353F2-hub-recut-pr596-onto-v010.claimed.20b6c4c6.md`
Prior contracts: `T-353-hub-skill-fast-lane-step3-docs-ci-template.claimed.7a53ee86.md`, `T-353F` (fix round 1).

## Current honest state (T-353F2, this run)

Hub PR **#598** (T-371, SKILL.md v0.10 — procedure/incident split, one launch recipe, fast
lane, MUST→gate ids) merged to `main` at `c88f403b` on 2026-08-27. It **already carries** the
STEP 3 FAST LANE subsection this PR's SKILL.md hunk was trying to add — confirmed by grepping
`origin/main:.claude/skills/get-work-done/SKILL.md` for `FAST LANE`:

> ### FAST LANE (owner decision A, 2026-08-26 - T-349/T-351/T-353)
>
> The ONE owner-approved exception to "a session never edits a target repo itself" - not inline:
> still a T-id, a contract, a worktree of the TARGET repo, `context_docs`, and a checker. Those,
> not a ban on session edits, prevent the 2026-08-15 incident [log: I-01].
>
> **ELIGIBILITY** = ALL of: `deliverable: content|mechanical` * <=5 files in `files:` * <=300
> changed lines at PR time * no path matching the sensitive-path denylist in
> `GWD/fast-lane-gate.py` * no unknowns after scout. `code` is NOT eligible in v1; revisit after
> 10 clean runs.
>
> **FLOW:** gate -> stage-stamp -> worktree edit -> PR -> diff gate -> `fast-lane-check.py` -> merge
> on green -> LEDGER line, detailed in `references/fast-lane-runbook.md`. SLO <=20 min
> launched->merged (`settings.fast_lane_slo_minutes`), a miss = `FAST-LANE-SLO-MISS` via
> `lesson.py status`. A `lane: fast` contract at WORKER dispatch is preflight exit 14.

**Conclusion: this PR's own `.claude/skills/get-work-done/SKILL.md` hunk is SUPERSEDED and will
be DROPPED entirely** — v0.10 on main already has the fast-lane text (in more mature form).
Re-cutting this PR onto `origin/main` means resolving the SKILL.md conflict by taking
`origin/main`'s SKILL.md as-is (no hunk from this branch).

The other 10 files in this PR's diff (`gh pr diff 596 --name-only`) are **not** touched by #598
and **stay**:
- `.claude/skills/get-work-done/references/ci-minutes-discipline.md`
- `core/.claude/skills/ci-cd-setup/SKILL.md`
- `core/.claude/skills/ci-cd-setup/references/docs-only-short-circuit.md`
- `docs/DASHBOARD.md`
- `docs/STACK-CATALOG.md`
- `docs/dashboard.html`
- `plans/get-work-done-dispatcher.md`
- `plans/get-work-done-fast-lane.md`
- `registry/patterns.json`
- `scripts/tests/test_get_work_done_fast_lane.py` — needs adapting: it currently asserts against
  v0.9 wording this branch added; will be re-pointed at the v0.10 section text without weakening
  assertions.

## Steps completed (this run, T-353F2)

1. [x] Rewrote STATUS.md + PR #596 body to the honest state, committed + pushed `[skip ci]`
   (`ae25edd3`).
2. [x] `git fetch origin && git merge origin/main` (`371a0bcf`) — SKILL.md conflict resolved by
   taking `origin/main`'s version entirely (`git checkout --theirs`); the other 10 files kept.
   Post-merge `git diff origin/main --stat` shows exactly the 10 expected files + STATUS.md, and
   SKILL.md no longer diffs from `origin/main`.
3. [x] Adapted `scripts/tests/test_get_work_done_fast_lane.py` to the v0.10 section text
   (`61f57748`): v0.10 split the FAST LANE detail into `references/fast-lane-runbook.md`, so the
   `stage-stamp.py` assertion now also checks that reference file (SKILL.md's inline FLOW line
   abbreviates it to `stage-stamp`); the `300 changed lines` regex was loosened to tolerate the
   line-wrapped `<=300\nchanged lines` phrasing. No assertion was weakened — every original check
   still requires the same concrete facts to be true, just located per v0.10's split.
4. [x] `PYTHONPATH=. python -m pytest scripts/tests/test_get_work_done_fast_lane.py -v` →
   **4/4 passed**. `GWD_ROOT=D:/Abhay/GetWorkDone python -m pytest
   scripts/tests/test_gwd_skill_conformance.py scripts/tests/test_gwd_skill_musts_have_gates.py
   scripts/tests/test_gwd_skill_conformance_grandfather_ratchet.py
   scripts/tests/test_eval_coverage_freshness.py -v` → **28/28 passed**.
5. [x] Full local CI block from CLAUDE.md, once:
   1. `dedup_check.py --validate-all` → `Registry validation passed`
   2. `dedup_check.py --secret-scan` → `No secrets found`
   3. `workflow_quality_gate_validate_patterns.py` → `PASSED: All patterns valid (46 warning(s))`
      — all pre-existing across the registry
   4. `pytest scripts/tests/ -q` → **2239 passed, 156 skipped, 1 failed** (332.77s). The 1
      failure (`test_fleet_script_health.py::test_real_fleet_has_no_unknown_silent_failure_findings`)
      is the SAME pre-existing, environment-only failure called out in the contract (line 6:
      "the known pre-existing pytest failure test_fleet_script_health on kt-backup.cmd is not
      yours") — it scans live fleet scripts on `D:/Abhay/GetWorkDone`, a different repo untouched
      by this PR's diff. On GitHub CI that directory does not exist, so the test self-skips.
   5. `check_eval_coverage.py --enforce --base origin/main` → `1 uncovered + 0 stale changed
      skill(s) (grandfathered)`, exit 0 (`ci-cd-setup` is on the shrink-only grandfather
      allowlist)
   6. `check_plugin_version_bump.py --base origin/main` → `Plugin version-bump gate: OK` (no
      plugin source touched)
   7. `generate_root_marketplace.py --check` — SKIPPED per CLAUDE.md ("skip if plugins/
      untouched"); `plugins/` is untouched by this PR's diff.
6. [x] Final marker-free push (no `[skip ci]` anywhere) — real CI runs on it. `gh pr checks 596
   --watch --interval 30` result recorded below once it completes.

## CI result (real GitHub Actions run on the final marker-free push, `53301cdd`)

`gh pr checks 596 --watch --interval 30` → **both required checks PASS**:
- `test` — PASS (41s), https://github.com/abhayla/claude-best-practices/actions/runs/33041550890/job/98416056337
- `validate` — PASS (41s), https://github.com/abhayla/claude-best-practices/actions/runs/33041550855/job/98416056131

Re-cut complete. PR #596 now diffs from `origin/main` on exactly the 10 expected files (no
SKILL.md hunk of its own). `hold` label stays on PR #596 throughout — this worker never merges
or closes; landing is dispatcher/checker-owned.
