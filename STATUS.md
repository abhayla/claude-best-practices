# T-371 STATUS — SKILL.md v0.10 (procedure / incident-log split)

Contract: `D:/Abhay/GetWorkDone/queue/T-371-hub-gwd-skill-v010-rewrite-procedure-incident-split.claimed.20b6c4c6.md`
Worktree: `D:/Abhay/Ventures/claude-best-practices-wt-T-371` · branch `t371-hub-gwd-skill-v010-rewrite-procedure-inc`

## DoD items (contract order)

1. [ ] SKILL.md v0.10 <= 30 KB; dated incident narratives moved VERBATIM to
       `references/incident-log.md` with a one-line back-reference from the rule they justify;
       MUST/NEVER rule-line inventory before vs after in the PR body.
2. [ ] Exactly ONE launch recipe (worker-wrapper.ps1 argv, forward-slash paths, `-StateRoot`);
       STEP 6 documents preflight exits 4,6,7,8,9,10,11,12,13,14 (+ T-363/T-364 codes);
       settings keys `fleet.max_concurrent_workers` + `max_turns_by_deliverable`
       (`soft_concurrency_cap` gone); FAST LANE declared in STEP 3 with its eligibility list;
       dead VibeCoding path + "PORTFOLIO.yml once it exists" corrected.
3. [ ] Three standing worker-mandate lines live in ONE injected file (bus `worker-mandates.txt`,
       coordinated with T-372 which has NOT landed); the skill points at it instead of asking
       dispatchers to hand-copy verbatim text.
4. [ ] `config/gwd-skill-conformance-grandfather.yml` emptied of fixed drift; conformance +
       MUST<->gate tests green with `GWD_ROOT=D:/Abhay/GetWorkDone`; PROSE-ONLY MUST count drops.
5. [ ] Fresh eval `evals/2026-08-27-v010-rewrite.md` (skill-evaluator, output mode minimum);
       global pointer skill updated only if its path list changed.
6. [ ] Full local CI block green; PR opened with `hold` label from this fresh worktree; final
       push carries no skip-ci marker.
7. [ ] Ratchet hole closed: grandfather + `gate:PROSE-ONLY` count compared against
       `git show origin/main:<path>`; tmp-git-repo fixture proves red-then-green. SKILL.md
       documents preflight exit 15 and the reserved T-364 codes.

## Status

STEP 0 (docs first): nothing implemented yet. This commit exists so the PR is open and honest
before any code lands.

## Known environment facts (recorded, not fixed)

- Baseline T-370 ratchet run in this worktree: **16 passed, 1 failed** — the failure is
  `test_preflight_exit_codes_bidirectional` (`exit 15`, the T-363 keeper-liveness gate, is
  undocumented in SKILL.md and not grandfathered). That is DoD item 7's target.
- The hub's local pytest has one PRE-EXISTING failure, `test_fleet_script_health` on
  `kt-backup.cmd` — environment-only (it scans the live fleet on this disk); CI does not see it.
  Not fixed here by contract instruction.
- Hub PR #596 (T-353, `hold`) is OPEN and holds the STEP 3 fast-lane text; this task folds that
  text in rather than rewriting it. Absorption scope is recorded in the PR body.
- T-372 (bus `worker-mandates.txt` + wrapper injection) has NOT landed; per this contract this
  task adds the file and points the skill at it.
