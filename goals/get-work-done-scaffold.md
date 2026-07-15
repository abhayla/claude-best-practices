---
name: get-work-done-scaffold
description: "The GetWorkDone fleet scaffold (settings, owner-questions inbox, ledger, hub dispatcher skill) stays on disk and wired."
enrolled: "2026-07-15"
source: "/get-work-done dispatcher Phase 1 (plan: plans/get-work-done-dispatcher.md); enrolled at Phase-1 exit test 2026-07-15"
last_verified: "2026-07-15"
predicates:
  - kind: file
    path: "D:\\Abhay\\VibeCoding\\GetWorkDone\\settings.json"
  - kind: file
    path: "D:\\Abhay\\VibeCoding\\GetWorkDone\\OWNER-QUESTIONS.md"
  - kind: file
    path: "D:\\Abhay\\VibeCoding\\GetWorkDone\\LEDGER.md"
  - kind: file
    path: .claude/skills/get-work-done/SKILL.md
on_failure: "The GetWorkDone fleet scaffold (D:\\Abhay\\VibeCoding\\GetWorkDone\\ settings/inbox/ledger, or the hub's /get-work-done dispatcher skill) went missing — the Phase 1 dispatcher can no longer run. Restore from plans/get-work-done-dispatcher.md and the Phase 1 skill commit."
---

The `/get-work-done` dispatcher is the mother-hub central task-intake fleet (owner GO
2026-07-15). Its scaffold lives outside the repo at `D:\Abhay\VibeCoding\GetWorkDone\`
(`settings.json`, `OWNER-QUESTIONS.md`, `LEDGER.md`) plus the in-repo dispatcher skill at
`.claude/skills/get-work-done/SKILL.md`. Silent death of any of these four files breaks
task intake/dispatch with nothing re-checking it — this goal re-verifies the scaffold
stays intact.
