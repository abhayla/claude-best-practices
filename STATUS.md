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

## Next steps (this run, T-353F2)

1. [x] Rewrite STATUS.md + PR #596 body to this honest state, commit + push `[skip ci]` — DONE (this commit).
2. [ ] `git fetch origin && git merge origin/main` — resolve SKILL.md conflict by taking
   `origin/main`'s version entirely; keep the other 10 files.
3. [ ] Adapt `scripts/tests/test_get_work_done_fast_lane.py` to the v0.10 section text.
4. [ ] Run that test + the 4 gwd ratchet tests (`GWD_ROOT=D:/Abhay/GetWorkDone`) — must stay green.
5. [ ] Full local CI block from CLAUDE.md, once.
6. [ ] Final marker-free push, `gh pr checks 596 --watch --interval 30`, record results here + in PR body.

`hold` label stays on PR #596 throughout — this worker never merges or closes.
