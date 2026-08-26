# T-370 status — hub GWD skill<->fleet conformance tests (ratchet)

WIP. Contract: `D:/Abhay/GetWorkDone/queue/T-370-hub-gwd-skill-conformance-tests-ratchet.claimed.20b6c4c6.md`.

## DoD items (from contract, in order)
1. `scripts/tests/test_gwd_skill_conformance.py` — 6 assertions against `.claude/skills/get-work-done/SKILL.md` + live fleet at `$GWD_ROOT` (paths, settings keys, preflight exit codes bidirectional, <=1 `claude -p` recipe, `/skill` refs, byte ratchet). NOT STARTED.
2. `config/gwd-skill-conformance-grandfather.yml` — known drifts C2/C3/M1/M3/M10 listed, shrink-only, self-tested. NOT STARTED.
3. `scripts/tests/test_gwd_skill_musts_have_gates.py` + `config/gwd-gates.yml` — every CRITICAL RULES MUST carries `gate:<id>`; ungated MUSTs grandfathered as `gate:PROSE-ONLY`, count never grows. NOT STARTED.
4. `scripts/check_eval_coverage.py` freshness check (SKILL.md newer than newest eval under `--enforce`) + red-then-green unit test. NOT STARTED.
5. PR hygiene: `hold` label immediately, no skip-ci on final push, PR body lists grandfathered drifts for T-371. IN PROGRESS (this PR).

## Findings this test suite encodes (from the review, verified independently while scoping)
- SKILL.md mentions only preflight exit codes {0,4,6,7,8}; the live header table defines {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14} — 10 codes undocumented (M1).
- Two `claude -p --model ...` launch recipes exist in SKILL.md (line ~372 STDIN-redirect, line ~590 checker launch) — contradicts the wrapper's argv-based launch at ~425 (C2).
- `/goal-creator` (invoked by SKILL.md STEP 5) does not exist under `.claude/skills/` — only under `core/.claude/skills/` (forbidden for hub work per this repo's own CLAUDE.md) and `plugins/loop-engineering/skills/` (M3).
- `D:\Abhay\VibeCoding\claude-best-practices` (SKILL.md:314) no longer exists on disk (M10).
- CRITICAL RULES block has 26 `MUST`/`MUST NOT` bullets, none carry a `gate:<id>` token today.
- All `GWD\<script>` / absolute paths + `settings.<key>` references currently resolve cleanly (no drift on those two checks).

## Full local CI (run before final push, CLAUDE.md "Full local CI replication")
Not yet run — will run and record each command's result before the final push.
