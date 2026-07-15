---
name: update-practices
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Pull latest COPY-PROVISIONED practices from the hub into your project's .claude/ directory — the residual surface only: path-scoped rules, stack helpers without a plugin pack, and shipped configs. PLU
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# update-practices — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
cbp-workflows plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install cbp-workflows@claude-best-practices
/reload-plugins
```

Also bundled (same skill, alternate closure) in: `cbp-build-test-workflows`, `cbp-learning-workflow` — installing any one serves it.

## What it does (so provisioning can decide without installing)

Pull latest COPY-PROVISIONED practices from the hub into your project's .claude/ directory — the residual surface only: path-scoped rules, stack helpers without a plugin pack, and shipped configs. PLUGIN-COVERED content (the workflow plugins, their sub-skills/agents, stack packs) is NOT synced here — update those with `/plugin update <name>` (the install-not-copy model, hub #346). Compares local files against hub registry + hub config directory, shows diffs, and copies updates.

After install the skill resolves as `cbp-workflows:update-practices` (invokable as `/update-practices` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Read Sync Config
- Fetch Hub Registry + Hub Config Inventory
- Compare — Patterns
- b: Compare — Configs (NEW in v1.1.0)
- Show Diffs
- Apply Updates
- 5: Restart Warning (when agents_added is non-empty)
- Report

Original invocation shape: `[--check-only] [--force]`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update cbp-workflows`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
