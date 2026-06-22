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

**Set it once, globally — it applies to every project.** Config precedence (highest wins):
1. `ENHANCE_SETTINGS_FILE` env var (power users / tests)
2. **Project** `<project>/.claude/enhance-settings.json` (optional per-project override)
3. **Global** `~/.claude/enhance-settings.json` — your one config for **all projects**
4. Plugin default (everything ON)

- Run `/enhance-config` to view all switches, or `/enhance-config <setting> <value>` to flip one
  (e.g. `/enhance-config after_improving let_me_review_first`,
  `/enhance-config display.show.second_opinion_review off`,
  `/enhance-config display.show_when only_weak_prompts`). Presets: `/enhance-config render all` / `render none`.
  These write your **global** config by default, so the change follows you into every project.
- Or copy `enhance-settings.default.json` to `~/.claude/enhance-settings.json` (global) and edit it
  directly — every setting has a one-line explanation in its `_help` section. Drop a copy in a
  project's `.claude/` only when you want that project to differ. Both are re-read every turn.
- Inline shortcuts in any prompt: `enhance off` / `enhance on` (master), `enhance mode auto|ask|off`,
  bare `enhance` — these update your global config.

### What each switch controls
Every setting has a plain-English name, and the settings file carries a `_help` section that
explains each one in one line. Quick reference:

| Setting | Plain meaning |
|---|---|
| `enabled` | Master on/off for the whole prompt-improver |
| `when_to_run` = `automatic` \| `ask_first` \| `off` | Improve every prompt / only when you reply `enhance` / never |
| `after_improving` = `run_immediately` \| `let_me_review_first` | Run the improved prompt right away, or show it and **wait for you** to approve/edit/trigger |
| `when_to_enhance.skip_short_prompts` (count_by, minimum) | Don't bother improving tiny prompts |
| `when_to_enhance.skip_these_phrases` / `skip_phrases_starting_with` | Don't improve continuations like "yes" / "now do …" |
| `display.show_the_process` | `false` = improve silently and just answer |
| `display.show_when` = `every_time` \| `only_weak_prompts` (+ `weak_prompt_score_below`) | Always show the steps, or only when the prompt scored poorly |
| `display.show.{summary_line, step_by_step_log, whats_wrong, score_table, second_opinion_review, list_of_fixes, improved_prompt, assigned_role}` | **Checkboxes** for what you SEE. `second_opinion_review` fires AND shows the blind re-grade. Presets: `/enhance-config render all` / `render none` |
| `improving.{skip_if_already_grade, add_role_when_score_below}` | When to leave a good prompt alone / add a persona |
| `scoring_criteria[]` (weights sum to 1.0) | The rubric used to score a prompt |
| `ask_clarifying_questions.{enabled, ask_until_confidence, max_questions}` | Whether/how much to ask when the request is ambiguous |
| `quality_checks.{require_review_table, require_fix_details}` = block\|warn\|off, `log_misses` | The improver's own self-checks |
| `context_levels` | Which background-context levels to gather |

**Enforced where:** the hooks deterministically enforce `enabled`, `when_to_run`, `after_improving`,
`when_to_enhance.*`, `display.*`, and `quality_checks.*`. The rest (`improving.*`,
`scoring_criteria[]` weights, `ask_clarifying_questions.ask_until_confidence`/`max_questions`,
`context_levels`) are **model-directed** — read by the skill, not the hooks.

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
