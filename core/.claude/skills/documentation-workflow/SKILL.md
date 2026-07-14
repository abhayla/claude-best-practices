---
name: documentation-workflow
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Orchestrate project documentation maintenance end-to-end as a skill-at-T0 orchestrator (Phase 3.5 of subagent-dispatch-platform-limit remediation). The skill body IS the orchestrator — runs in the use
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# documentation-workflow — now ships as a plugin

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

Orchestrate project documentation maintenance end-to-end as a skill-at-T0 orchestrator (Phase 3.5 of subagent-dispatch-platform-limit remediation). The skill body IS the orchestrator — runs in the user's T0 session and drives: ADR creation → API docs generation → structure enforcement → staleness audit. Invokes sub-skills (/adr, /api-docs-generator, /doc-structure-enforcer, /doc-staleness) via Skill(); optionally dispatches the docs-drafting worker via Agent() at T0 for bulk content generation when the structure audit reveals substantial missing content.

After install the skill resolves as `cbp-workflows:documentation-workflow` (invokable as `/documentation-workflow` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- INIT
- 5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)
- ADR (skip if scope ∉ {all, adr} OR no architecture decisions detected)
- API_DOCS (skip if scope ∉ {all, api} OR no OpenAPI spec)
- STRUCTURE (skip if scope ∉ {all, structure})
- Optional: docs-manager-agent dispatch (bulk content drafting)
- Workflow: documentation
- Run ID: <run_id>
- Audit report: <structure audit path>
- Scope: <list of missing doc targets>
- Dry-run: <bool>
- STALENESS (skip if scope ∉ {all, staleness} OR --skip-staleness)

Original invocation shape: `[scope: 'all' | 'adr' | 'api' | 'structure' | 'staleness']`.
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
