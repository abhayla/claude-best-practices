---
name: get-work-done-scaffold
description: "The GetWorkDone fleet scaffold (settings, owner-questions inbox, ledger, hub dispatcher skill) stays on disk and wired."
enrolled: "2026-07-15"
source: "/get-work-done dispatcher Phase 1 (plan: plans/get-work-done-dispatcher.md); enrolled at Phase-1 exit test 2026-07-15; repointed off dead C:\\Abhay/VibeCoding paths T-152 2026-08-16"
last_verified: "2026-08-16"
predicates:
  - kind: command
    cmd: "python -c \"import os,sys; base=r'D:/Abhay/GetWorkDone'; p=base+'/settings.json'; sys.exit(0 if (not os.path.isdir(base) or os.path.exists(p)) else 1)\""
  - kind: command
    cmd: "python -c \"import os,sys; base=r'D:/Abhay/GetWorkDone'; p=base+'/OWNER-QUESTIONS.md'; sys.exit(0 if (not os.path.isdir(base) or os.path.exists(p)) else 1)\""
  - kind: command
    cmd: "python -c \"import os,sys; base=r'D:/Abhay/GetWorkDone'; p=base+'/LEDGER.md'; sys.exit(0 if (not os.path.isdir(base) or os.path.exists(p)) else 1)\""
  - kind: file
    path: .claude/skills/get-work-done/SKILL.md
on_failure: "The GetWorkDone fleet scaffold (D:\\Abhay\\GetWorkDone\\ settings/inbox/ledger on this PC, or the hub's /get-work-done dispatcher skill) went missing — the dispatcher can no longer run. Restore from plans/get-work-done-dispatcher.md and the Phase 1 skill commit."
---

The `/get-work-done` dispatcher is the mother-hub central task-intake fleet (owner GO
2026-07-15). On this PC its scaffold lives at the local fleet home `D:\Abhay\GetWorkDone\`
(verified on disk T-152 2026-08-16 — the prior `C:\Abhay\GetWorkDone\` VPS path and
`D:\Abhay\VibeCoding\GetWorkDone\` replica path were both dead on this checkout, which is
exactly why this goal fired every day since 2026-07-15 with nobody acting on it: run
31929069050 logged "10 passing, 1 failing" and still reported success because the workflow
piped the sentinel through `tee` without pipefail, discarding its exit code — see the
`.github/workflows/standing-goals.yml` fix from the same PR) — `settings.json`,
`OWNER-QUESTIONS.md`, `LEDGER.md` — plus the in-repo dispatcher skill at
`.claude/skills/get-work-done/SKILL.md`. Silent death of any of these four files breaks
task intake/dispatch with nothing re-checking it — this goal re-verifies the scaffold
stays intact.

**Machine-scoping note (T-152, 2026-08-16):** the three scaffold files are absolute paths
on this PC's local disk and cannot exist on the sentinel's ubuntu CI runner. Per
`goals/README.md`'s predicate discipline, each is a `command` predicate that first checks
whether `D:/Abhay/GetWorkDone` exists at all — on a machine without that directory (the CI
runner, or any other machine) the predicate skip-passes by design (this is a PC-local
signal, never a PR-blocking one); only on this PC does it actually verify the file. This
mirrors the existing skip-pass pattern in `goals/estate-conformance.md`.
