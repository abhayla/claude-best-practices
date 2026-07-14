---
name: skill-authoring-workflow
description: >
  POINTER to the installable cbp-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Author, validate, and register new skills, agents, and rules end-to-end as a skill-at-T0 orchestrator (Phase 3.8 of subagent-dispatch-platform-limit remediation — the final workflow-master retirement)
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# skill-authoring-workflow — now ships as a plugin

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

Author, validate, and register new skills, agents, and rules end-to-end as a skill-at-T0 orchestrator (Phase 3.8 of subagent-dispatch-platform-limit remediation — the final workflow-master retirement). The skill body IS the orchestrator — runs in the user's T0 session and drives: overlap-check → author → validate → register. Invokes sub-skills (/writing-skills, /claude-guardian, /skill-master) via Skill(); optionally dispatches skill-author-agent via Agent() at T0 for richer draft generation.

After install the skill resolves as `cbp-workflows:skill-authoring-workflow` (invokable as `/skill-authoring-workflow` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- INIT + OVERLAP_CHECK
- 5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)
- AUTHOR
- 2a: Optional skill-author-agent dispatch for richer drafts
- Workflow: skill-authoring
- Run ID: <run_id>
- Target type: <workflow|reference|rule|agent>
- Input: <resolved input>
- Overlap findings: <list>
- Project context: <stack + conventions>
- 2b: /writing-skills protocol (always runs)
- VALIDATE (BLOCKING)

Original invocation shape: `<skill name, learning reference, or pattern description>`.
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
