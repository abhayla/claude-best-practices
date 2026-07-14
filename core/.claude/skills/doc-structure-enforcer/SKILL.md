---
name: doc-structure-enforcer
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Enforce a stage-based documentation folder structure via config-driven rules. Two modes: audit (report misplaced files) or enforce (git mv + update path references). Use when documentation files are d
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# doc-structure-enforcer — now ships as a plugin

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

## What it does (so provisioning can decide without installing)

Enforce a stage-based documentation folder structure via config-driven rules. Two modes: audit (report misplaced files) or enforce (git mv + update path references). Use when documentation files are disorganized or when onboarding a project to a structured docs layout.

After install the skill resolves as `cbp-workflows:doc-structure-enforcer` (invokable as `/doc-structure-enforcer` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- MODE SELECTION
- Expected Folder Structure
- Load or Generate Config
- If config exists:
- If config is missing:
- Scan Documentation Files
- File Manifest
- Classify Files
- Tier 1: Filename Pattern Match
- Tier 2: Content Signal Fallback
- Tier 3: Unclassified
- Classification Results

Original invocation shape: `--audit | --enforce [--config <path>]`.
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
