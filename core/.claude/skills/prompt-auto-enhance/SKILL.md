---
name: prompt-auto-enhance
description: >
  Guide projects to the installable prompt-auto-enhance PLUGIN. This capability
  graduated from a copied core/ template into the hub marketplace plugin
  `prompt-auto-enhance@claude-best-practices`, which is now its single source of
  truth. Use this pointer when provisioning prompt-auto-enhance into a project —
  install the plugin instead of copying the template.
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "4.0.0"
---

# prompt-auto-enhance — now ships as a plugin

This capability is **no longer distributed as a copied template**. It graduated to
an installable Claude Code plugin so there is **one source of truth** instead of a
template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability.

## How to get it

Install from the hub's in-tree marketplace:

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install prompt-auto-enhance@claude-best-practices
/reload-plugins
```

The plugin ships the full pipeline: the grade → diagnose → strengthen skill, the
settings-driven `UserPromptSubmit` trigger, and the `Stop` enforcement guard. After
install the skill is available namespaced as `prompt-auto-enhance:prompt-auto-enhance`,
and the in-plugin `enhance-config` command opens the plain-English settings.

## Why it moved

- **Single source of truth.** A copied template in `core/` plus a plugin meant the
  same skill/rule lived in two distributable places and drifted (line-ending and
  content skew were already observed). The plugin is now canonical.
- **Official guidance.** Anthropic's plugin docs are explicit: after migrating a
  capability to a plugin, remove the original files to avoid duplicate, shadowed copies
  (code.claude.com/docs/en/plugins).
- **Richer + configurable.** The plugin adds plain-English settings (master switch,
  when-to-run, per-part display toggles, slash-command skip) the static template never had.

## Configuration

Settings are plain-English JSON resolved fresh each turn (precedence: env var > project
file > global `~/.claude` file > packaged default). To turn the whole capability off in a
project, set `"enabled": false` (or type `enhance off`); flip the trigger cadence with
`enhance mode auto|ask|off`. The packaged `enhance-settings.default.json` documents every key.

## For hub maintainers

The hub keeps its own operational copy under `.claude/` (skill + rule + the full
governance hook the plugin deliberately omits). That copy is hub-only — it is NOT this
distributable template. Edit the plugin (the SSOT) for downstream behavior; edit `.claude/`
only for hub-operational behavior. The retirement plan + rationale live in
`plans/prompt-auto-enhance-core-retirement.md`, and the divergence is registered in
`config/dual-home-resources.yml`.
