---
name: implement
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Implement a feature or fix following a structured workflow: requirements analysis, test creation, implementation, test execution, fix-loop delegation, and verification. Use when user requests new func
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# implement — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
cbp-build-test-workflows plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install cbp-build-test-workflows@claude-best-practices
/reload-plugins
```

## What it does (so provisioning can decide without installing)

Implement a feature or fix following a structured workflow: requirements analysis, test creation, implementation, test execution, fix-loop delegation, and verification. Use when user requests new functionality or structured bug fixes. Use /fix-github-issue for GitHub Issues, /tdd for strict red-green-refactor, /development-loop for full ideation-to-commit orchestration.

After install the skill resolves as `cbp-build-test-workflows:implement` (invokable as `/implement` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Analyze Requirements
- Create/Update Tests
- Implement the Feature
- Run Tests
- Fix Loop (if tests fail)
- Verification (Mandatory Gate)
- 6.1 Multi-Layer Verification Checklist
- 6.2 Partial Failure Protocol
- 6.3 Verification Report
- 6.4 Post-Fix Review
- Post-Implementation (Optional)
- Structured Output

Original invocation shape: `<feature-description>`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update cbp-build-test-workflows`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
