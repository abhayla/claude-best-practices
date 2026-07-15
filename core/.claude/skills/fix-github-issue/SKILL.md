---
name: fix-github-issue
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Analyze and implement a fix for a specific GitHub Issue. Fetches issue details via `gh`, explores codebase for root cause, plans minimal fix, implements, verifies with tests, and runs post-fix-pipelin
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "4.0.0"
---

# fix-github-issue — now ships as a plugin

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

Also bundled (same skill, alternate closure) in: `cbp-build-test-workflows` — installing any one serves it.

## What it does (so provisioning can decide without installing)

Analyze and implement a fix for a specific GitHub Issue. Fetches issue details via `gh`, explores codebase for root cause, plans minimal fix, implements, verifies with tests, and runs post-fix-pipeline. Use when user says "fix issue #N" or references a GitHub Issue.

After install the skill resolves as `cbp-workflows:fix-github-issue` (invokable as `/fix-github-issue` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Fetch and Parse Issue
- Explore and Diagnose
- Implement and Test
- Finalize
- Default mode (no flag)
- `--diff-only` mode (NEW in PR2 of test-pipeline-three-lane spec)
- Summarize
- Fix Summary: Issue #N — <title>
- Failure Modes

Original invocation shape: `<issue-number or issue-url> [--diff-only]`.
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
