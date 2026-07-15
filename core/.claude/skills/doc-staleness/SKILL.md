---
name: doc-staleness
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Detect documentation that has drifted from the codebase by comparing docs against recent code changes to find stale references, outdated examples, and broken links. Use when docs may be outdated after
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# doc-staleness — now ships as a plugin

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

## What it does (so provisioning can decide without installing)

Detect documentation that has drifted from the codebase by comparing docs against recent code changes to find stale references, outdated examples, and broken links. Use when docs may be outdated after significant code changes or before a release.

After install the skill resolves as `cbp-workflows:doc-staleness` (invokable as `/doc-staleness` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Identify Documentation Files
- Determine Change Window
- Extract Documentation References
- 3.1 File Path References
- 3.2 Symbol References
- 3.3 Command References
- 3.4 Internal Links
- Detect Undocumented Changes
- 4.1 New Modules Without Docs
- 4.2 Changed Behavior Without Doc Updates
- Generate Staleness Report
- Documentation Staleness Report

Original invocation shape: `[docs-directory] [--since <commit-or-date>] [--fix]`.
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
