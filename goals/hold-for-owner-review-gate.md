---
name: hold-for-owner-review-gate
description: Every hub auto-landing path skips PRs carrying the `hold` label or an "owner review required" body — owner-held PRs never self-land
enrolled: "2026-08-13"
source: PR #536 (T-118; incident: PR #535 self-landed pre-approval 2026-08-13)
last_verified: "2026-08-13"
predicates:
  - kind: command
    cmd: "python -c \"import io; t=io.open('.claude/hooks/session-git-landing.sh',encoding='utf-8').read().lower(); assert 'owner review required' in t and 'hold' in t\""
  - kind: command
    cmd: "python -c \"import io; a=io.open('.claude/hooks/auto-pr-reconcile.sh',encoding='utf-8').read(); b=io.open('.claude/hooks/auto-pr.sh',encoding='utf-8').read(); assert 'session-git-landing.sh' in a and 'session-git-landing.sh' in b\""
  - kind: command
    cmd: "python -c \"import io; t=io.open('scripts/tests/test_auto_pr_reconcile.py',encoding='utf-8').read().lower(); assert 'hold' in t\""
on_failure: "The hold-for-owner-review gate was stripped from session-git-landing.sh, a landing hook stopped routing through the SSOT, or the behavioral hold tests were deleted — an owner-held green PR is one SessionStart away from self-landing (the exact PR #535 incident). Restore from PR #536; ledger post-mortem: getworkdone-state LEDGER.md 2026-08-13 16:12."
---

The hold gate lives in `session-git-landing.sh` — the single SSOT all three landing hooks route
through (auto-pr.sh `land`, auto-pr-reconcile.sh `reconcile`, reaper merge-one). Predicates are
pure-python (Windows-cmd-safe, matching the passing goals' style): hold markers present in the
SSOT, both hooks still route through it, hold tests still exist.
