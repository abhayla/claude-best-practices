---
name: goal-creator
description: >
  POINTER to the installable loop-engineering plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Author a "contract" — a dense, zero-open-questions markdown spec — to hand to an autonomous executor (Claude Code's built-in `/goal`, or `/loop`, a routine, or headless `claude -p`) that runs unattend
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# goal-creator — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
loop-engineering plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install loop-engineering@claude-best-practices
/reload-plugins
```

## What it does (so provisioning can decide without installing)

Author a "contract" — a dense, zero-open-questions markdown spec — to hand to an autonomous executor (Claude Code's built-in `/goal`, or `/loop`, a routine, or headless `claude -p`) that runs unattended until a Definition of Done is met. Use when the user wants to CREATE / DRAFT / WRITE a goal, autonomous contract, or unattended-run spec — "create a goal to…", "draft a contract for /goal", "set up an autonomous run that…". Interview-first: resolve every fork BEFORE the run, because an autonomous run never pauses to ask.

After install the skill resolves as `loop-engineering:goal-creator` (invokable as `/goal-creator` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Cardinal rules (read before anything)
- Load context
- Map the fork inventory
- Interview (Clarification Gate)
- Confirm the output path
- Write the contract
- 5: Self-validate (mechanical zero-open-questions gate)
- Stop — hand off, don't execute
- Mode B: Fold run learnings back (post-run self-improvement)

Original invocation shape: `[one-line description of the goal, optional]`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update loop-engineering`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
