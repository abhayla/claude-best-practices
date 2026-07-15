---
name: review-gate
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Orchestrate all review sub-skills (code-quality-gate, architecture-fitness, security-audit, adversarial-review, change-risk-scoring, pr-standards) into a single autonomous pipeline. Aggregates results
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# review-gate — now ships as a plugin

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

Orchestrate all review sub-skills (code-quality-gate, architecture-fitness, security-audit, adversarial-review, change-risk-scoring, pr-standards) into a single autonomous pipeline. Aggregates results into a consolidated review report with a go/no-go verdict. Use when running the Stage 9 pre-merge review gate before deployment.

After install the skill resolves as `cbp-workflows:review-gate` (invokable as `/review-gate` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Parse Arguments and Gather Context
- 0.1 Argument Parsing
- 0.2 Validate Preconditions
- 0.3 Detect Project Context
- 0.4 Initialize Report Tracking
- Batch A — Code Quality + Architecture (Parallel)
- 1.1 Record Results
- Batch B — Security + Risk Scoring (Parallel)
- Batch C — Adversarial Review → PR Standards (Sequential)
- Fix Loop (Conditional)
- Generate Consolidated Review Report
- 5.1 Consolidated Report Format

Original invocation shape: `[--skip <skill1,skill2>] [--fix] [--pr] [--threshold <0-100>] [--include-test-health]`.
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
