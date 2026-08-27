---
name: provisioned-rule-drift-tick
description: "The weekly provisioned-rule drift detector stays wired into the SessionStart reconcile sweep and still classifies a retired hub rule as RETIRED."
enrolled: "2026-08-28"
source: "T-401 / PR #607; plans/capability-advisor.md step 0-1"
last_verified: "2026-08-28"
predicates:
  - kind: file
    path: scripts/check_provisioned_rule_drift.py
  - kind: command
    cmd: "grep -q check_provisioned_rule_drift .claude/hooks/auto-pr-reconcile.sh"
  - kind: command
    cmd: "python -m pytest scripts/tests/test_check_provisioned_rule_drift.py -q -x"
on_failure: "scripts/check_provisioned_rule_drift.py or its step-1d call site in auto-pr-reconcile.sh was removed/renamed, or its classifier regressed — re-wire the weekly tick or update this goal if the detector moved."
---

T-401 added `scripts/check_provisioned_rule_drift.py`: for every repo in the fleet registry it
classifies each `.claude/rules/*.md` copy against hub git history (CURRENT / STALE / MODIFIED /
RETIRED / PROJECT-ONLY / UNKNOWN) and flags contradiction candidates. Its first run found 86 stale
copies across 6 repos — including a `workflow.md` that had contradicted `claude-behavior.md` rule 15
for four months, and `prompt-auto-enhance-rule.md` still enforced everywhere after the hub retired it.
The `--weekly` tick is called from `.claude/hooks/auto-pr-reconcile.sh` step 1d. If that call site is
dropped, provisioned copies go back to drifting silently — the exact failure this detector exists to
catch — with no symptom until a contradiction is found by hand again.
