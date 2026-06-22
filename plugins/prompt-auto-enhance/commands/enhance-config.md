---
description: View and toggle prompt-auto-enhance settings (master switch + every per-criterion on/off). Edits the project override so changes auto-adjust next turn.
---

# /enhance-config — customize prompt-auto-enhance

You are the configuration interface for the prompt-auto-enhance plugin. Every criterion is an
individual on/off switch (master switch + per-criterion), all default ON.

## Resolve the effective settings file
1. Project override: `.claude/enhance-settings.json` (this is what you EDIT — it wins and is re-read every turn).
2. Plugin default: `${CLAUDE_PLUGIN_ROOT}/settings.json` (read-only baseline; copy it to the override path on first edit).

## Behavior
- **No argument** → read the effective settings and render the current state as a grouped table:
  `master | triggers (length_gate, continuation_phrases, continuation_prefixes) | run_mode |
  show.* (banner, transcript, diagnosis, grade_card, reviewer_column, changes_applied, final_prompt, role_line) |
  run.independent_reviewer | run.reviewer_min_gap | strengthen.* | grade weights | clarify.* | enforce.* | context.tiers`,
  each with ON/OFF or its value. End with a one-line hint of example edits.
- **An argument** (e.g. `show.reviewer_column off`, `run_mode silent`, `triggers.length_gate.min 6`,
  `enabled off`, `enforce.over_ask ...` → reject: not in this plugin) → apply it:
  1. If `.claude/enhance-settings.json` does not exist, copy the plugin default there first.
  2. Use `jq` to set the requested key, validating the path exists in the schema and the value type matches
     (booleans for `.on`/toggles, string enum for `run_mode` ∈ {auto,ask,silent,off}, number for thresholds).
  3. Grade weights must still sum to 1.0 — reject an edit that breaks that and explain.
  4. Confirm the new value and note it takes effect next turn (hooks re-read the file).

## Guardrails
- This plugin governs ONLY prompt-auto-enhance. It has NO hub-governance keys (decide-don't-ask,
  plan-before-coding, role routing, narrate-and-stop). Reject attempts to toggle those — they live in the hub.
- Never edit the plugin's own `settings.json` default; only the project override.
- Show the resulting JSON diff (before → after) for any change you make.
