---
name: plugin-validation-pipeline
description: "The one-command clean-room plugin-validation pipeline (script + docs) stays on disk and importable."
enrolled: "2026-07-10"
source: "fable-window item 10; scripts/validate_plugin_cleanroom.py"
last_verified: "2026-07-10"
predicates:
  - kind: file
    path: scripts/validate_plugin_cleanroom.py
  - kind: file
    path: scripts/validate_plugin_cleanroom.sh
  - kind: file
    path: docs/plugin-validation-pipeline.md
  - kind: command
    cmd: "python -c \"import scripts.validate_plugin_cleanroom as m; assert hasattr(m, 'validate_plugin'); assert hasattr(m, 'check_structural_gate')\""
on_failure: "The clean-room plugin-validation pipeline (script, wrapper, or doc) was deleted or its public API (validate_plugin / check_structural_gate) was renamed without updating callers — a future G6 plugin build/fix loses its repeatable install-serving proof. Restore from scripts/validate_plugin_cleanroom.py's git history or re-run /plugin-lifecycle's validation step."
---

`scripts/validate_plugin_cleanroom.py` (+ the `scripts/validate_plugin_cleanroom.sh`
one-command wrapper) automates the manual clean-room install-serving check that
`loop-engineering` completed by hand (`plans/loop-engineering-adoption.md` STEP 5.2):
structural manifest checks, `claude plugin validate`, and a headless serve probe that
proves a plugin's skills are visible from the plugin alone via `--plugin-dir`. This goal
only re-verifies the pipeline's own files stay in place — it deliberately does NOT
re-run the headless `claude` probe daily (that would spend tokens and touch a live CLI
from a cron sentinel, which `goals/README.md` disallows for standing-goal predicates).
Full contract: `docs/plugin-validation-pipeline.md`.
