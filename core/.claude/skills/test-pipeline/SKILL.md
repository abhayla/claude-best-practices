---
name: test-pipeline
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Run your full test suite end-to-end: find broken tests, diagnose root causes, open GitHub issues, apply targeted auto-fixes, re-verify, and commit. The three-lane pipeline runs functional + API + UI t
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "4.0.0"
---

# test-pipeline — now ships as a plugin

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

Run your full test suite end-to-end: find broken tests, diagnose root causes, open GitHub issues, apply targeted auto-fixes, re-verify, and commit. The three-lane pipeline runs functional + API + UI tests with dual-signal visual verification, then fans out failure triage (analyze → file issues → fix → serialize). Use when you want the complete test→fix→verify→commit chain.

After install the skill resolves as `cbp-build-test-workflows:test-pipeline` (invokable as `/test-pipeline` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- INIT
- SCOUT
- Mode: classify
- Run ID: <run_id>
- State: .workflows/testing-pipeline/state.json
- Config: .claude/config/test-pipeline.yml
- WAVE 1 — Functional + API + UI (parallel runners)
- Parallel topology (default for >= min_test_count tests)
- Lane: functional
- Capture proof: <bool>
- Run ID: <run_id>
- Manifest: test-results/manifest.json

Original invocation shape: `[failure_output] [--capture-proof | --no-capture-proof] [--skip-fix] [--allow-gaps] [--only-issues N,M] [--fix-pr-mode] [--full-suite-before-success] [--update-baselines]`.
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
