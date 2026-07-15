---
name: serialize-fixes
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Apply a list of unified-diff files sequentially to the working tree using the three-phase atomic protocol (git apply --check → git apply → git commit). Use when `/test-pipeline` (skill-at-T0, spec v2.
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# serialize-fixes — now ships as a plugin

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

Apply a list of unified-diff files sequentially to the working tree using the three-phase atomic protocol (git apply --check → git apply → git commit). Use when `/test-pipeline` (skill-at-T0, spec v2.2) has collected per-test diffs from parallel fixer agents at STEP 6 TRIAGE Fan-out 3 and needs to land them on a shared branch without conflicts. On `git apply --check` conflict: discard the stale diff and label the Issue.

After install the skill resolves as `cbp-build-test-workflows:serialize-fixes` (invokable as `/serialize-fixes` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Resolve diff list
- Process each diff (three-phase atomic protocol)
- Phase A: Dry-run check (NEVER dirties working tree)
- Phase B: Real apply (only if Phase A passed)
- Phase C: Commit
- 5: Optional autosquash (REQ-S005)
- Return aggregated contract
- NON-NEGOTIABLE

Original invocation shape: `<diffs-glob-or-list> [--autosquash]`.
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
