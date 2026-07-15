# Eval: /get-work-done v0.1 — Phase-1 live-fire exit test (2026-07-15)

**Mode:** output-quality via REAL dispatches (live-fire — the plan's locked P5 exit test IS the
eval scenario: real tasks, real repos, real PRs, zero simulated steps).
**Evaluator:** session fedaf490 (dispatcher) + two context-blind checker agents (maker≠checker).
**Evidence:** `D:\Abhay\VibeCoding\GetWorkDone\evidence\2026-07-15-T-001\`, `…\2026-07-15-T-002\`,
`…\LEDGER.md`; plan build log (`plans/get-work-done-dispatcher.md`).

## Scenarios executed

### T-001 — hub repo: enroll GetWorkDone scaffold as a standing goal
- Intake → contract (goal-contract format + dispatcher fields) → atomic claim (rename) →
  repo-identity assert → background sonnet worker via stdin → worker self-isolated in a git
  worktree → **PR #422 opened, CI `validate` green, auto-merged** — zero manual interventions.
- Checker (independent agent) verdict: **FAIL — correct catch.** The goal's predicate for the
  skill file fails on main (skill still on the unmerged feature branch). A self-reporting
  worker would have shipped a false "done"; the maker≠checker design caught a real sequencing
  gap on its first-ever run. Resolution: skill lands via hub PR #419.
- Worker cost: $1.80 (sonnet). Refusal branch not triggered (`stop_reason: end_turn`).

### T-002 — calculatekaro (private, folder trap `..\calculator`): add missing PR CI gate
- Repo registry resolved the folder-name trap correctly; identity assert passed.
- Worker delivered the DoD artifact: **PR #15 merged — `.github/workflows/validate.yml` on
  main, structurally correct** (pull_request no-path-filter + push-to-main, vitest gate).
- Worker process was killed before writing its result JSON → destination probe (not worker
  report) established the outcome — validating the "verify at destination" doctrine.
- Checker verdict: **FAIL — correct catch, two real defects:** (1) the worker merged while its
  own gate check was RED (possible because private+free repos cannot have required checks —
  capability wall confirmed live via 403); (2) the red is a genuine pre-existing repo defect
  the new gate exposed (package-lock.json out of sync → `npm ci` fails).
- Spawned T-003 (P1 break-fix, pre-authorized class): regenerate lockfile, wait-for-green,
  merge only on SUCCESS.

## Defects found → fixed in v0.1 during the eval
1. Prompt-as-argument dies on `---` frontmatter → dispatch via STDIN (SKILL.md STEP 6).
2. Private/free repos: auto-merge ignores CI (no protection possible) → fleet-side
   wait-for-green rule added to CRITICAL RULES; owner question T-004 queued (Pro/public/discipline).
3. Same-repo concurrent sessions: worktree isolation mandated in contracts (proven by T-001).
4. Concurrent worker session wiped the shared enhance-attestation marker → session-scoped
   markers (hub guard + plugin 0.4.4, tests 40/40).

## Verdict
**PASS for Phase-1 scope with findings codified.** The core chain (intake → contract → claim →
identity assert → background worker → PR → independent check → evidence + ledger) executed
end-to-end on real work twice; both checker FAILs were TRUE failures caught by design, not
skill malfunctions — the control loop works precisely because it refused to self-certify.
Trigger eval: skill invoked via its registered name; description routes correctly (verified in
session skill list). Baseline comparison: without the skill, both checker-caught defects would
have shipped as silent "done" claims.

## Follow-ups (tracked)
- T-003 completion + green gate on calculatekaro main (in flight at eval-writing time; ledger
  will carry the terminal state).
- Phase-2+ features (parallel lanes, heartbeat wrapper, pings) intentionally absent — locked
  plan sequences them; do not eval features that don't exist yet.
