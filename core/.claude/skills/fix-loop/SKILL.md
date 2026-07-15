---
name: fix-loop
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Analyze failures and iteratively apply minimal fixes, optionally retesting until resolved. Full Loop mode (with retest command) iterates until green. Single Fix mode (no retest) does one pass — the ri
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# fix-loop — now ships as a plugin

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

Also bundled (same skill, alternate closure) in: `cbp-build-test-workflows`, `loop-engineering` — installing any one serves it.

## What it does (so provisioning can decide without installing)

Analyze failures and iteratively apply minimal fixes, optionally retesting until resolved. Full Loop mode (with retest command) iterates until green. Single Fix mode (no retest) does one pass — the right fit for applying a minimal fix to a runtime error with no retest command.

After install the skill resolves as `cbp-workflows:fix-loop` (invokable as `/fix-loop` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Mode Detection
- Parameters
- Analyze Failure (via test-failure-analyzer-agent)
- A: Flaky Test Detection
- Apply Fix
- Retest (Full Loop mode only)
- Report
- Structured Output
- ESCALATION
- AUTO-RECORD LEARNING (MANDATORY)

Original invocation shape: `[failure_output] [retest_command: <cmd>] [max_iterations: N] [--strict-gates] [--capture-proof | --no-capture-proof]`.
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
