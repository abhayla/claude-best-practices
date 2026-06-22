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
| `enhance_slash_commands` | `false` (default) = never improve a `/command` or saved custom prompt (yours or Anthropic's) — run as-is |
| `when_to_enhance.skip_short_prompts` (count_by, minimum) | Don't bother improving tiny prompts |
| `when_to_enhance.skip_these_phrases` / `skip_phrases_starting_with` | Don't improve continuations like "yes" / "now do …" |
| `when_to_enhance.skip_if_just_a_question` | Just answer plain fact-questions; don't rewrite them |
| `when_to_enhance.skip_tip_for_simple_tasks` | Don't add the "better phrasing" tip for obvious tasks |
| `when_to_enhance.also_check_when_short_prompt_makes_big_work` | Even a short prompt gets the full treatment if it triggers big work |
| `display.show_the_process` | `false` = improve silently and just answer |
| `display.how_much_to_show` = `every_time` \| `scale_to_prompt_quality` \| `only_for_weak_prompts` (+ `weak_prompt_score_below`) | Always full / great→short·okay→compact·weak→full / full only for weak prompts. A prompt is "weak" when it scores below the cutoff (default 7/10) |
| `display.show_step_log_only_for_multipart` | Show the step log only when the request has several parts |
| `display.show.{summary_line, step_by_step_log, whats_wrong, score_table, second_opinion_review, list_of_fixes, improved_prompt, assigned_role}` | **Checkboxes** for what you SEE. `second_opinion_review` fires AND shows the blind re-grade. Presets: `/enhance-config render all` / `render none` |
| `improving.dont_rewrite_if_prompt_is_already` = `excellent` \| `good_or_better` \| `never` | Leave an already-good prompt alone |
| `improving.always_add_a_role` | Always add an "Act as …" role, regardless of score |
| `scoring_criteria[]` (weights sum to 1.0) | The rubric used to score a prompt |
| `ask_clarifying_questions.{enabled, method, ask_until_confidence, max_questions}` | Ask via **grill-me** (one question at a time) when the request is ambiguous |
| `make_sure_steps_were_shown` = `strict` \| `relaxed` \| `off`, `keep_a_quiet_log` | The improver's own self-check that it showed its work |
| `background_research` = `light` \| `normal` \| `deep` | How much project context to read first |

**Deterministic vs guided:** the hooks deterministically enforce `enabled`, `when_to_run`,
`enhance_slash_commands`, the `skip_*` length/phrase rules, `display.show_the_process`/`how_much_to_show`/`show.*`,
and `make_sure_steps_were_shown`. The intent-based ones (`skip_if_just_a_question`,
`skip_tip_for_simple_tasks`, `also_check_when_short_prompt_makes_big_work`, `show_step_log_only_for_multipart`,
`always_add_a_role`, `improving.*`, `scoring_criteria`, `ask_clarifying_questions.*`, `background_research`)
are **guided** — the hook injects the instruction and the model follows it (a bash hook can't tell if a
prompt is "just a question" or has "3 parts").

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
