---
name: plugin-version-bump-gate
description: "The blocking CI gate that makes plugin version bumps mandatory (propagation contract) stays on disk and wired into validate-pr."
enrolled: "2026-07-13"
source: "owner question 2026-07-13 (process must hold without Fable); PR #349"
last_verified: "2026-07-13"
predicates:
  - kind: file
    path: scripts/check_plugin_version_bump.py
  - kind: command
    cmd: "python -c \"import io; t=io.open('.github/workflows/validate-pr.yml',encoding='utf-8').read(); assert 'check_plugin_version_bump.py' in t\""
on_failure: "The version-bump gate was deleted or unwired from validate-pr.yml — plugin source edits can merge without a version bump and silently never reach installed copies (the version-pinned-cache trap returns, prose-only). Restore scripts/check_plugin_version_bump.py + its validate-pr step from PR #349."
---

`scripts/check_plugin_version_bump.py` runs as a BLOCKING validate-pr step: a changed
`plugins/<name>/` source file fails CI unless that plugin's `plugin.json` version differs
from the base (README/evals + new plugins exempt). This is the deterministic form of the
/plugin-lifecycle propagation rule, so it holds for any model driving a session. Tests:
`scripts/tests/test_check_plugin_version_bump.py` (incl. the wiring pin).
