---
name: escalation-report
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Generate `test-results/escalation-report.md` when `/test-pipeline` (skill-at-T0, spec v2.2) hits the global retry budget (default 15), dispatch budget (default 100), or wall-clock budget (default 90 m
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# escalation-report — now ships as a plugin

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

Also bundled (same skill, alternate closure) in: `loop-engineering` — installing any one serves it.

## What it does (so provisioning can decide without installing)

Generate `test-results/escalation-report.md` when `/test-pipeline` (skill-at-T0, spec v2.2) hits the global retry budget (default 15), dispatch budget (default 100), or wall-clock budget (default 90 min) with failures still unresolved. Use when budget exhaustion has stopped further fix attempts and you need to surface what's resolved vs what's open for the next session.

After install the skill resolves as `cbp-build-test-workflows:escalation-report` (invokable as `/escalation-report` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Read inputs
- Categorize Issues
- Generate Markdown report
- Resolved Failures (closed)
- Unresolved Failures (still open)
- Auto-Fix Failed (`pipeline-fix-failed` label applied)
- Issue-Only Categories (no fix attempted)
- Summary
- Next Session
- Optional notifications + reviewer auto-assign (REQ-C002, REQ-C004)
- REQ-C002: Slack notification
- REQ-C004: CODEOWNERS auto-assign

Original invocation shape: `<run-id> <state-json-path>`.
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
