# Scope — Validate the `prompt-auto-enhance` plugin in a second project (G6)

**Status:** scoped, not yet run. **Owner-gated:** the run installs the plugin into another local
repo — confirm the target before executing. **Goal served:** G6 (package & distribute capabilities
as installable cross-project plugins). **Author:** delivery scope, 2026-06-23.

## Why this run exists (the gap it closes)

`prompt-auto-enhance` is the hub's first plugin (`plugins/prompt-auto-enhance/`, marketplace
`claude-best-practices`, PR #195/#197). Its **logic** is already proven — a 52/52 eval was run
against IPODhan. What is **NOT** yet proven is the thing G6 is actually about: the
**install + central-update distribution model** — i.e. that a *different* project can
`/plugin install` it from the marketplace, run it with **zero dependency on the hub's `.claude/`**,
and pick up a central version bump. This run validates distribution, not logic.

This is the cheapest honest move toward G6: it converts the one existing plugin from
"hub-built+reviewed" to "multi-project-validated" with **no new plugin build**. It does NOT by
itself flip the G6 DoD (which needs ≥9 plugins) — it de-risks the model before investing in volume.

## Target project

| Candidate | Stack | Fit as validation target |
|---|---|---|
| **CalculateKaro** *(recommended)* | React + Vite + TS SPA (dogfood) | Simplest single-stack; local sibling (in-tree local marketplace resolves on the same machine); a *fresh* project with no prior plugin history → cleanest "works in a new project" signal |
| IPODhan | Next.js | Already carries the 52/52 eval → weaker fresh-install signal, but most familiar |
| RealFuelPricesinIndia | Next.js + Supabase | Fresh, but more moving parts than CalculateKaro |

**Recommendation: CalculateKaro.** Reversible (a plugin install is removable); confirm before the run.

## Preconditions

1. Hub and target are local siblings under `D:/Abhay/VibeCoding/` (true today) — required because the
   marketplace source is the **in-tree local path** `plugins/.claude-plugin/marketplace.json`, not a
   remote. (If the target is ever on a different machine, publish the marketplace remotely first —
   out of scope here.)
2. Target repo has a clean git working tree before the run (so plugin-induced changes are isolated).
3. Note the install is **user/Claude-Code level**, not committed into the target repo — the plugin
   lives in the Claude Code plugin store, the target repo stays clean.

## Procedure (the run — executed in a session opened IN the target project)

1. **Add the marketplace** (once per machine):
   `/plugin marketplace add D:/Abhay/VibeCoding/claude-best-practices/plugins`
2. **Install:** `/plugin install prompt-auto-enhance@claude-best-practices`
3. **Restart** the Claude Code session in the target (plugins/hooks load at session start).
4. **Verify it RUNS in the target** (the core proof):
   - the `*Enhanced:* ...` banner appears on a substantive prompt in the target;
   - the `prompt-enhance-reminder` + `enhance-process-guard` hooks fire (UserPromptSubmit / Stop);
   - `enhance-settings.json` is read each turn — toggle one switch OFF (e.g. the grade card),
     confirm behavior changes next turn with **no reinstall**, then restore.
5. **Verify ZERO hub dependency:** the target's own `.claude/` does NOT contain the
   prompt-auto-enhance skill/rule/hook, yet step 4 still works — proving the plugin is
   self-contained, not silently leaning on a copied template.
6. **Verify central update:** bump the plugin `version` in the hub
   (`plugins/prompt-auto-enhance/.claude-plugin/plugin.json` + marketplace), run
   `/plugin update` (or re-install) in the target, confirm the new version is reported.
   Revert the version bump afterward.
7. **Capture evidence** (see below) into this plan's run-log section.

## Definition of Done (all must hold)

- [ ] Plugin installs cleanly into the target from the marketplace (no errors).
- [ ] On a substantive prompt in the target, the enhance banner + full process render.
- [ ] Both hooks fire in the target (evidence: hook output / log line, not assumed).
- [ ] A settings toggle changes behavior next turn with no reinstall.
- [ ] The target's `.claude/` has NO prompt-auto-enhance copy → confirmed self-contained.
- [ ] A central version bump propagates to the target via `/plugin update`.
- [ ] Evidence captured; CLAUDE.md G6 note updated from "not yet installed/validated in a second
      project" → "validated in <target> (install + run + central-update proven)".

## Evidence to capture

- Terminal transcript of `marketplace add` + `install` + `update`.
- A screenshot/transcript of the enhance banner+process firing in the target on a real prompt.
- The hook-fired log lines (UserPromptSubmit reminder + Stop guard).
- A before/after of the settings toggle showing behavior changed.
- `ls .claude/` in the target showing no prompt-auto-enhance copy.

## Risks & honest caveats

- **Local-marketplace-only:** this proves install on the SAME machine. True remote distribution
  (another machine / a teammate) is a stronger bar not covered here — flag it as the next rung.
- **Does not flip G6:** the DoD needs ≥9 plugins; this validates the model for plugin #1 only.
- **Plugin omits hub governance by design:** the plugin ships only prompt-auto-enhance's own
  governance (NOT decide-don't-ask / plan-before-coding / role routing). The target will get the
  enhance pipeline but not the hub-wide engineering tail — expected, not a defect.
- **`/plugin` is an interactive Claude Code command:** the run needs a human-driven (or `!`-prefixed)
  session in the target; it is not a headless script. Hence this is scoped, not auto-executed here.

## Out of scope (this run)

- Building any new plugin (G6 volume work — separate owner-gated decisions, one at a time).
- The core→plugin retirement of prompt-auto-enhance (tracked separately in
  `plans/prompt-auto-enhance-core-retirement.md`).
- Wiring the target into the telemetry/feedback loop (`/bootstrap-dogfood-project` — optional follow-up).

## Run log

_(empty — fill on execution)_
