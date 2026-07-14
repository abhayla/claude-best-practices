---
name: status
description: >
  POINTER to the installable loop-engineering plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Generate a project health snapshot showing git status, test status, and project state in a single report. Use when starting a session or checking project health.
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# status — now ships as a plugin

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

Generate a project health snapshot showing git status, test status, and project state in a single report. Use when starting a session or checking project health.

After install the skill resolves as `loop-engineering:status` (invokable as `/status` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Gather Information
- 1. Git State
- 2. Uncommitted Changes
- 3. Open PRs/Issues (if gh available)
- 4. Recent Test Results
- Health Criteria
- Report
- Project Status
- Git
- Tests
- Open Work
- Health: [GOOD / NEEDS_ATTENTION / BLOCKED]

Original invocation shape: ``.
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
