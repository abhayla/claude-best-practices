# goals/ — the standing-goal invariant ledger

**"A goal verified once is an assumption with a timestamp."**

A finished deliverable — a wired hook, a scheduled workflow, an installable plugin, a
deployed artifact — is verified once, at the moment it ships. Nothing re-checks it after
that. The motivating failure class (documented in
`core/.claude/rules/web-analytics-instrumentation.md`): a GA4 snippet that rendered
correctly and was verified once at setup, then silently stopped reaching the collector —
nobody noticed because nothing was re-checking.

This directory is the fix: a standing ledger of enrolled invariants, each carrying cheap
read-only predicates that a daily sentinel (`scripts/check_standing_goals.py`, run by
`.github/workflows/standing-goals.yml`) re-verifies every day. When an invariant silently
dies, the sentinel files (or updates) a deduplicated GitHub issue instead of letting the
assumption go stale unnoticed.

## Enrollment rule: finishing = enrollment

Enrollment happens at `/end-session` STEP 5b — for each deliverable a session actually
FINISHED whose continued working matters beyond the session, write or update a
`goals/<slug>.md` file before the session closes. A goal that is never enrolled is a goal
that can silently die with nobody watching.

## File format

Each `goals/<slug>.md` is YAML frontmatter + a short body:

```markdown
---
name: <slug>
description: <one-line invariant statement>
enrolled: "YYYY-MM-DD"
source: <PR or plan reference>
last_verified: "YYYY-MM-DD"   # sentinel rewrites this on pass with --update-timestamps
predicates:                    # SAME vocabulary as goals.yml's dod: (see repo root goals.yml)
  - kind: file
    path: <repo-relative path>
  - kind: command
    cmd: "<read-only shell command, exit 0 = invariant holds>"
on_failure: <one-line hint for the owner>
---
<body: why this invariant matters, what silent death looks like>
```

Predicate kinds:
- `kind: file` — the file at `path` (repo-relative) must exist.
- `kind: command` — `cmd` is run via `subprocess.run(shell=True, cwd=<repo root>)`; exit 0
  means the invariant holds. Keep predicates read-only and cheap (seconds, not minutes).

Predicate discipline:
- **Stay hermetic**: no network, no `gh`, no environment dependence — OR accept that the
  predicate is a **cron-only signal**. Pass/fail verification belongs to the daily
  sentinel, never PR CI: the PR-time test suite checks only that goal files are
  structurally valid (parse + well-formed frontmatter), it never executes predicates.
- **Prefer `python` one-liners** for command predicates — portable across the sentinel's
  ubuntu runner and local Windows/Git Bash runs.
- **Flat by design**: only `goals/*.md` is scanned — subdirectories are not recursed.

A goal passes iff **all** of its predicates pass. A malformed goal file (unparseable
frontmatter, missing `name`/`predicates`, an unknown predicate `kind`, or an empty
`predicates` list) is reported as a **failure**, never silently skipped — a broken
invariant file is itself a signal something drifted.

## Running the sentinel

```bash
PYTHONPATH=. python scripts/check_standing_goals.py                      # report + exit code
PYTHONPATH=. python scripts/check_standing_goals.py --json               # machine-readable
PYTHONPATH=. python scripts/check_standing_goals.py --update-timestamps  # refresh last_verified on passing goals
```

`scripts/check_standing_goals.py` is run daily by `.github/workflows/standing-goals.yml`
(cron + `workflow_dispatch`). It is cron-only by design — an anticipatory or
environment-dependent goal must never block PR CI, so it is intentionally NOT wired into
`validate-pr.yml`. On failure the workflow files (or comments on) a single deduplicated
GitHub issue (label `standing-goals`) carrying the fresh failure report.
