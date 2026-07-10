---
name: trust-recorder-sweep
description: "The zero-manual trust recorder stays wired into the SessionStart reconcile sweep."
enrolled: "2026-07-10"
source: "PR #317"
last_verified: "2026-07-10"
predicates:
  - kind: file
    path: scripts/record_merged_prs.py
  - kind: command
    cmd: "grep -q record_merged_prs .claude/hooks/auto-pr-reconcile.sh"
on_failure: "record_merged_prs.py or its call site in auto-pr-reconcile.sh was removed/renamed — re-wire the sweep or update this goal if the recorder moved."
---

PR #317 added `scripts/record_merged_prs.py` — a zero-manual sweep that accrues real
trust-score signal from every merged PR without a human running a command. It is called
from `.claude/hooks/auto-pr-reconcile.sh` (SessionStart), which is the only reliably-firing
hook in the branch lifecycle (see CLAUDE.md "Autonomous Branch Lifecycle"). If the call
site is quietly dropped during a future edit to `auto-pr-reconcile.sh` — the exact kind of
silent regression this ledger exists to catch — the trust-score calibration ledger stops
accruing real data with nothing visibly broken: merges keep happening, sessions keep
starting, and only a stalled `trust-score/ledgers/atlas.jsonl` would eventually reveal it.
