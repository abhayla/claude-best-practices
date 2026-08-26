# T-371 STATUS — SKILL.md v0.10 (procedure / incident-log split) — COMPLETE

Contract: `D:/Abhay/GetWorkDone/queue/T-371-hub-gwd-skill-v010-rewrite-procedure-incident-split.claimed.20b6c4c6.md`
Worktree: `D:/Abhay/Ventures/claude-best-practices-wt-T-371` · branch
`t371-hub-gwd-skill-v010-rewrite-procedure-inc` · PR **#598** (label `hold`, NOT merged by this
worker).

## DoD items — all 7 done

1. **DONE** — SKILL.md v0.10 is **30,663 bytes** (LF). Every dated incident narrative moved
   VERBATIM into `.claude/skills/get-work-done/references/incident-log.md`, anchored `I-01…I-37`
   with the v0.9 line range each block came from; every rule in SKILL.md carries a `[log: I-nn]`
   back-reference. Rule inventory (26 v0.9 bullets → 32 v0.10 bullets, none dropped; 25 narrative
   MUST/NEVER lines byte-for-byte in the log) is in the PR body.
2. **DONE** — one launch recipe (`worker-wrapper.ps1` argv form, forward-slash paths,
   `-StateRoot`); **0** `claude -p … --model` recipes remain. Preflight exits **0–17** documented
   (T-364 landed mid-run, so 16/17 are LIVE, not reserved).
   `settings.fleet.max_concurrent_workers` + `settings.worker_defaults.max_turns_by_deliverable`
   named, `soft_concurrency_cap` gone. FAST LANE declared in STEP 3 with its eligibility list
   (absorbed from open PR #596). Dead VibeCoding path removed; "PORTFOLIO.yml once it exists"
   corrected to "it EXISTS".
3. **DONE** — `D:/Abhay/GetWorkDone/worker-mandates.txt` created (bus commit `06fdc98`), the skill
   points at it and no longer asks dispatchers to hand-copy verbatim text. **T-372 has NOT
   landed**, so the wrapper does not yet append the file — SKILL.md says so plainly rather than
   claiming a working mechanism.
4. **DONE** — `config/gwd-skill-conformance-grandfather.yml` emptied of every fixed drift (only
   the two ceilings the tests require remain, both lowered: `max_bytes` 66296→30720,
   `max_ungated_musts` 26→0). Conformance + MUST↔gate tests: **23 passed** with
   `GWD_ROOT=D:/Abhay/GetWorkDone` (before: 1 failed, 16 passed). Unmechanised MUSTs 26 → 17.
5. **DONE** — `evals/2026-08-27-v010-rewrite.md` (output mode, scenario "intake one trivial docs
   task + one code task"), with an explicit honesty header listing what was NOT run (no
   subagent-isolated runs, no baseline, no model matrix, 5 of 10 stress categories). Global
   pointer `~/.claude/skills/get-work-done/SKILL.md` updated — its path list DID change
   (`references/`, `worker-mandates.txt`) and its RULE ZERO contradicted the fast lane.
6. **DONE** — full local CI block green except one pre-existing environment-only failure (below).
   PR opened from this fresh worktree with `hold` at creation; the final push carries no marker.
7. **DONE** — ratchet hole closed: the grandfather file AND the `gate:PROSE-ONLY` MUST count are
   now compared against `git show origin/main:<path>`; tmp-git-repo fixtures prove red-then-green,
   and a mutation of the comparison function turned 4 fixtures RED (evidence in the PR body).

## Honest notes

- **Byte bar:** 30,663 B = 29.94 KiB, under 30 KB on the 1024-byte reading the ratchet uses; 663
  bytes over a decimal 30,000 reading. Flagged, not hidden. `.gitattributes` pins these files to
  LF so a CRLF checkout can't inflate the measurement by ~430 bytes.
- **Pre-existing failure, untouched (contract instruction):**
  `test_fleet_script_health.py::test_real_fleet_has_no_unknown_silent_failure_findings` — scans
  the live fleet scripts on this machine's disk; invisible to GitHub CI. Final suite:
  **1 failed, 2241 passed, 150 skipped**.
- **12 mid-run failures were FIXED, not waived** — the three rule-decay guards
  (cadence / root-cause / skip-ci) now read their EVIDENCE from the skill package while keeping
  rule placement and the CRITICAL-RULES MUSTs pinned to SKILL.md; three tokens genuinely missing
  from the compressed text were restored to SKILL.md.
- **PR #596 (T-353) is only PARTIALLY absorbed** — its SKILL.md fast-lane text is in; its
  ci-cd-setup reference, plans edits and its own test file are not. It will conflict on SKILL.md;
  the dispatcher should re-cut it against this branch or close it and re-file the three remaining
  pieces.
- **Two pytest runs exceeded the harness's 600s foreground cap** and were auto-moved to a tracked
  background task by the harness (not by this worker); both were waited out and their results read
  before continuing. No command was launched with `&`.
- Eval finding **F1 (MAJOR, deferred)**: `references/` has no `self-update-protocol.md`. The
  incident log is a frozen archive, so there is nothing to self-update; recorded in the eval
  rather than silently skipped.
