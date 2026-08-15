---
name: gwd-no-inline-dispatch
description: get-work-done's no-inline invariant (every task = contract + T-id) and the SSOT-artifact classification stay in the skill body — the v0.8/RULE-A prose layer never silently regresses
enrolled: "2026-08-15"
source: PRs #544/#546/#547/#551/#554 (owner-ordered fix + verifier loops, both CLOSABLE 2026-08-15; incident: GoRefer session executed Wati/Zoho work inline, 3x wrong-context template drafts)
last_verified: "2026-08-15"
predicates:
  - kind: command
    cmd: "python -c \"import io; t=io.open('.claude/skills/get-work-done/SKILL.md',encoding='utf-8').read(); assert 'inline-execution path is DELETED' in t and 'no T-id is a defect' in t\""
  - kind: command
    cmd: "python -c \"import io; t=io.open('.claude/skills/get-work-done/SKILL.md',encoding='utf-8').read(); assert 'ssot_artifacts' in t and 'NEVER authors the artifact text' in t\""
  - kind: command
    cmd: "python -c \"import io; t=io.open('plans/get-work-done-dispatcher.md',encoding='utf-8').read(); assert 'RULE A' in t and 'SELF-REPORTED' in t\""
  - kind: command
    cmd: "python -c \"import io; t=io.open('.claude/skills/end-session/SKILL.md',encoding='utf-8').read(); assert 'sync pending' in t\""
on_failure: "The no-inline invariant, the SSOT-artifact classification, the RULE A/B addendum, or the end-session persistence line was edited out of the skill/plan prose — the 2026-08-15 GoRefer inline-execution defect class is one rewrite away from returning. Restore from PRs #544-#554; evidence: getworkdone-state evidence/2026-08-15-T-13*/ folders."
---

The deterministic halves (contract-lint blocks, preflight exit-7, the guard hook) live on the
getworkdone-state bus and are exercised by tests/test_ssot_artifact_gates.py there — not
checkable from this repo's sentinel, so this goal guards the HUB-side prose layer only:
the skill's invariant sentences, the plan addendum, and the end-session persistence line.
Predicates are pure-python string asserts (Windows-cmd-safe, matching the passing goals' style).
