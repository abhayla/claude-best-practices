---
name: integration-test
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Apply integration testing patterns across service boundaries covering database, cache, queue, and external API integrations with real dependencies using testcontainers, fixture strategies, and CI conf
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# integration-test — now ships as a plugin

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

Apply integration testing patterns across service boundaries covering database, cache, queue, and external API integrations with real dependencies using testcontainers, fixture strategies, and CI configuration. Use when writing or reviewing tests that cross service boundaries.

After install the skill resolves as `cbp-build-test-workflows:integration-test` (invokable as `/integration-test` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Service-to-Database
- Transaction Rollback Pattern
- In-Memory vs Containers
- Service-to-Cache
- Service-to-Queue
- Service-to-External API
- VCR / Cassette Pattern
- WireMock Pattern
- Database Fixtures
- Seeding Strategies
- Factory-Based Seeding
- Testcontainers

Original invocation shape: `<integration-type> [language: python|typescript]`.
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
