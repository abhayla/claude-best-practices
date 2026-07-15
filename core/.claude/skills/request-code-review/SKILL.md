---
name: request-code-review
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Create high-quality, review-optimized pull requests that surface risks, generate intelligent review questions, annotate diffs with intent, and help reviewers focus on what matters. Use when preparing 
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# request-code-review — now ships as a plugin

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

Create high-quality, review-optimized pull requests that surface risks, generate intelligent review questions, annotate diffs with intent, and help reviewers focus on what matters. Use when preparing a PR for review to ensure it gets reviewed faster and more thoroughly.

After install the skill resolves as `cbp-workflows:request-code-review` (invokable as `/request-code-review` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Assess the Change Set
- 1.1 Gather Change Data
- 1.2 PR Size Analysis
- Classify Changes by Risk Level
- 2.2 Security Pattern Scan
- Detect Breaking Changes
- Annotate Diff with Intent
- Generate Review Questions
- Pre-Review Self-Check
- 6.1 Code Hygiene Checklist
- 6.2 Hygiene Violations Response
- 6.3 Branch Hygiene

Original invocation shape: `<branch-name or description of changes to prepare for review>`.
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
