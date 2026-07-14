---
name: contract-test
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Implement consumer-driven contract testing with Pact. Write consumer contract tests, generate Pact files, run provider verification, and set up CI gates with can-i-deploy. Use when adding or modifying
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# contract-test — now ships as a plugin

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

Implement consumer-driven contract testing with Pact. Write consumer contract tests, generate Pact files, run provider verification, and set up CI gates with can-i-deploy. Use when adding or modifying cross-service API boundaries.

After install the skill resolves as `cbp-build-test-workflows:contract-test` (invokable as `/contract-test` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Identify Consumers and Providers
- Write Consumer Contract Tests
- Generate Pact Files
- Run Provider Verification
- Set Up Pact Broker (Optional)
- Options
- Publishing Pacts to the Broker
- Verifying from the Broker
- CI Integration
- can-i-deploy Workflow
- 5: Update Downstream Mocks
- 6.5.1 Detect Changed Response Shapes

Original invocation shape: `<consumer-name> <provider-name> [language: js|python|jvm] [broker-url]`.
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
