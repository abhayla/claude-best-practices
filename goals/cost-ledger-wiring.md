---
name: cost-ledger-wiring
description: "The daily cost-ledger tick stays wired into the SessionStart reconcile sweep."
enrolled: "2026-07-10"
source: "plans/fable-window-program.md item 6"
last_verified: "2026-07-10"
predicates:
  - kind: file
    path: scripts/cost_ledger.py
  - kind: command
    cmd: "grep -q cost_ledger .claude/hooks/auto-pr-reconcile.sh"
on_failure: "scripts/cost_ledger.py or its call site in auto-pr-reconcile.sh was removed/renamed — re-wire the daily tick or update this goal if the ledger moved."
---

Fable-window item 6 added `scripts/cost_ledger.py` and `config/model-costs.yml` — a
self-enforcing cost ledger that streams the hub's real Claude Code transcript usage into a
daily token/USD rollup and alerts the owner (via the Notifier gateway) when a day's spend
crosses `daily_alert_usd`. Its `--daily` tick is called from
`.claude/hooks/auto-pr-reconcile.sh` (SessionStart), the same reliably-firing hook
`record_merged_prs.py` uses (see `goals/trust-recorder-sweep.md` for that sibling
invariant). If the call site is quietly dropped during a future edit to
`auto-pr-reconcile.sh` — the exact kind of silent regression this ledger exists to catch —
the hub goes back to measuring nothing about its own spend, with no visible symptom until
someone manually notices `costs/ledger.jsonl` has stopped growing.
