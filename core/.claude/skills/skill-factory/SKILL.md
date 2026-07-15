---
name: skill-factory
description: >
  POINTER to the installable cbp-learning-workflow plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Detect repeated workflows in session logs and classify them into the right automation type (skill, agent, hook, MCP server, or rule). Use when you notice recurring manual steps that should be automate
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "4.0.0"
---

# skill-factory — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
cbp-learning-workflow plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install cbp-learning-workflow@claude-best-practices
/reload-plugins
```

## What it does (so provisioning can decide without installing)

Detect repeated workflows in session logs and classify them into the right automation type (skill, agent, hook, MCP server, or rule). Use when you notice recurring manual steps that should be automated. Modes: scan, propose, create, list.

After install the skill resolves as `cbp-learning-workflow:skill-factory` (invokable as `/skill-factory` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Modes
- Mode Detection
- Scan Mode
- Propose Mode
- Classification Decision Tree
- Conflict Check
- Output Format
- Create Mode
- Skill Creation
- Agent Creation
- Core Responsibilities
- Output Format

Original invocation shape: `<mode: scan|propose|create|list> [details]`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update cbp-learning-workflow`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
