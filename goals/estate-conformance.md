---
name: estate-conformance
description: "The PC runs the same daily estate-conformance detector the VPS keeper already runs — stray project folders, nested .git inside 5Wealths, and unregistered VibeCoding dirs never go unnoticed on either machine."
enrolled: "2026-08-12"
source: "5wealths PORTFOLIO-MIGRATION-PLAN.md Phase 4c (v2 extended) + T-107"
last_verified: "2026-08-12"
predicates:
  - kind: command
    cmd: "python -c \"import os,subprocess,sys; p=r'D:/Abhay/VibeCoding/GetWorkDone/estate-conformance-check.ps1'; sys.exit(0) if not os.path.exists(p) else sys.exit(subprocess.run(['powershell','-File',p,'-EstateRoot','D:/Abhay']).returncode)\""
on_failure: "estate-conformance-check.ps1 found a stray project-shaped folder outside VibeCoding/Ventures, a nested .git inside 5Wealths, or a VibeCoding dir missing its PORTFOLIO.yml row — read its stdout findings and either fix the location/registration or update this goal if the detector itself moved."
---

The migration plan's Phase 4c enforcement layer (the "never again" fix for the exact failure
class this incident already caused — operational code drifting inside 5Wealths, a Claude
session resolving to the wrong repo) shipped as `estate-conformance-check.ps1`, wired into the
VPS keeper tick. This goal gives the PC the same daily detector: the sentinel here runs the
script with `-EstateRoot D:/Abhay` and requires exit 0 (clean) whenever the script exists on
this checkout. On the sentinel's ubuntu CI runner the script path does not exist, so the
predicate skip-passes there by design — it is a PC/VPS-only signal, never a PR-blocking one.
Without this enrollment, a stray folder or a nested `.git` could reappear on the PC and nobody
would notice until it caused the same class of confusion again.
