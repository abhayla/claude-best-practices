# prompt-auto-enhance (Claude Code plugin)

Diagnose → strengthen → (optionally) show the process, before your prompt runs. **Every entry
criterion, every output component, the independent reviewer, the clarification gate, and the
workflow's own self-enforcement are individual on/off switches** — a master switch plus a
per-criterion toggle, **all default ON**. Settings live in `enhance-settings.json` and are
re-read every turn, so changes auto-adjust with **no reinstall**.

## Install

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install prompt-auto-enhance@claude-best-practices
```

A fresh install reproduces the full enhancement behavior (all switches ON). Switch OFF whatever you don't want.

## Customize

- Run `/enhance-config` to view all switches, or `/enhance-config <key> <value>` to flip one
  (e.g. `/enhance-config run_mode silent`, `/enhance-config show.reviewer_column off`).
- Or copy `settings.json` to `<project>/.claude/enhance-settings.json` and edit it directly — the
  override file wins over the plugin default and is re-read every turn.
- Inline shortcuts in any prompt: `enhance off` / `enhance on` (master), `enhance mode auto|ask|silent|off`,
  bare `enhance` (one-shot re-run of the previous prompt through the full pipeline).

### What each switch controls
| Group | Keys | Effect |
|---|---|---|
| Master | `enabled` | Whole plugin on/off |
| Triggers | `triggers.length_gate` (unit chars\|words, min), `continuation_phrases`, `continuation_prefixes`, `substantive_output_chars` | Which prompts/turns get enhanced |
| Run mode | `run_mode` = `auto` \| `ask` \| `silent` \| `off` | `silent` = strengthen internally + answer, render nothing |
| Verbosity | `show.{banner,transcript,diagnosis,grade_card,reviewer_column,changes_applied,final_prompt,role_line}` | What you SEE of the process |
| Reviewer | `run.independent_reviewer`, `run.reviewer_min_gap` | The blind re-grade (biggest token cost) |
| Strengthen | `strengthen.skip_at_grade`, `strengthen.role_threshold` | When to strengthen / inject a persona |
| Grade | `grade.dimensions[]` (weights sum to 1.0) | Rubric dimensions + weights |
| Clarify | `clarify.{on,confidence_threshold,max_questions}` | The clarification/confidence gate |
| Enforce | `enforce.{reviewer_card,diagnosis_substance}` = block\|telemetry\|off, `enforce.telemetry` | The workflow's own self-enforcement |
| Context | `context.tiers` | Which context tiers to gather |

**Enforced where:** the hooks deterministically enforce `enabled`, `triggers.*`, `run_mode`,
`show.*`, `run.independent_reviewer`, and `enforce.*`. The remaining keys (`strengthen.*`,
`grade.dimensions[]` weights, `clarify.confidence_threshold`/`max_questions`,
`run.reviewer_min_gap`, `context.tiers`) are **model-directed** — read by the skill, not the
hooks — so changing them steers the model but isn't deterministically gated.

## Scope (important)

This plugin ships **only prompt-auto-enhance's own governance** — the rules that make the
enhancement feature work (rendering the full process, the clarification gate). It deliberately
does **NOT** include hub-wide engineering governance (decide-don't-ask, plan-before-coding, role
routing, narrate-and-stop); those are separate concerns and are not part of this plugin.

## Note on the auto-loaded rule

Claude Code plugins cannot ship auto-loaded `rules/` (no plugin-native rules concept — see hub
issue #187). The rule's behavior is delivered at runtime by the hooks (which inject the directive
each turn). If you also want the static rule text, copy `prompt-auto-enhance-rule.md` into your
project's `.claude/rules/` manually.

## Components
- `skills/prompt-auto-enhance/` — the pipeline procedure (Grade → Diagnose → Fix).
- `hooks/prompt-enhance-reminder.sh` (UserPromptSubmit) — settings-driven trigger + verbosity.
- `hooks/enhance-process-guard.sh` (Stop) — settings-driven self-enforcement (reviewer-card + diagnosis-substance + telemetry).
- `commands/enhance-config.md` — the `/enhance-config` toggle interface.
- `settings.json` — default switches (all ON).
