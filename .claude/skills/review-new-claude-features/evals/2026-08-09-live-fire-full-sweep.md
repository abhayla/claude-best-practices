# Eval — /review-new-claude-features live-fire full sweep (2026-08-09)

**Mode:** output-quality via real invocation (live-fire precedent: get-work-done
`evals/2026-07-15-phase1-live-fire.md`). Not a simulated scenario — this is the actual
owner-facing run of 2026-08-09, session `session_0169yKpHnmNGiPa5414zgLYK`, plus the
headless weekly variant shipped the same day.

## Trigger fidelity

- Owner prompt: "what are the features you recommend to implement… list all the features"
  → skill invoked explicitly at T0. Trigger matched the skill's stated use ("what new
  Claude Code features should this hub adopt?"). PASS.

## Procedure adherence (STEP 1–5)

| Step | Evidence | Verdict |
|---|---|---|
| 1 Doctrine + baseline | Baseline resolved from `plans/platform-migration-2026H2.md` (last audited v2.1.183); doctrine anchors cited per verdict | PASS |
| 2 Fetch since baseline | Changelog fetched from code.claude.com; truncated tail (2.1.184–192) re-fetched from the GitHub CHANGELOG raw — two sources, coverage gap named explicitly (only 2.1.191 carried features) | PASS |
| 3 Judge per doctrine | Every feature bucketed ADOPT / MEASURE-FIRST / KEEP / REJECT with one-line reasons; YAGNI applied (archive source, DirectoryAdded hook rejected for no caller) | PASS |
| 4 Dedupe | Prior decisions honored, not re-litigated (cross-session messaging REJECT-for-now same-day; Routines KEEP; agent teams REJECT; Sonnet/Opus 5 already adopted PR #450) | PASS |
| 5 Report, dry-run | Verdict table rendered; NO issues filed (dry-run default honored); spend/policy items (self-hosted runners, paid routine #153) kept PROPOSE-only | PASS |

## Output value (the point of the skill)

- Produced 4 ADOPT, 3 MEASURE-FIRST, ~15 PASS/REJECT verdicts across v2.1.184–226.
- Caught and corrected a same-session error: `/remote-control` had been mis-declared
  "not a real command"; STEP 2's verify-against-docs surfaced the official Remote Control
  doc (verified requirements, flags, plan support) — the skill's adversarial-fetch rule
  did exactly what it exists for.
- Two verdicts converted to landed work the same day: Remote Control trial (owner-facing
  recommendation) and the weekly headless invocation itself.

## Weakness found (honest)

- The skill has NO automatic cadence — the owner discovered a shipped feature (cross-session
  messaging) via X, two days late. Fixed same day, owner-approved: keeper-driven weekly
  headless run (`GWD\feature-adoption-sweep.ps1`, bus commit `cdcb7a5`), baseline tracked in
  `heartbeats\feature-sweep-baseline.txt`. The cost contract is unchanged — the owner
  scheduled it; the skill still never schedules itself.
- STEP 2 single-page fetch truncates on the long changelog; the working pattern (fall back
  to the raw GitHub CHANGELOG.md) is now encoded in the weekly sweep's prompt.

## Verdict

PASS — trigger, procedure, dedupe, and dry-run contract all held in a real run; output
drove real adoption decisions the same day. Re-eval when the weekly headless variant has
4+ ticks of history (verify baseline advancement + card delivery).
