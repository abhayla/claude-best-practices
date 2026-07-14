---
name: learn-n-improve
description: >
  POINTER to the installable cbp-learning-workflow plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Analyze session outcomes and update memory topics (testing-lessons, fix-patterns, success-patterns, skill-gaps) for continuous self-improvement. Captures both failure lessons (error→fix→lesson) and su
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# learn-n-improve — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
cbp-learning-workflow plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install cbp-learning-workflow@claude-best-practices
/reload-plugins
```

Also bundled (same skill, alternate closure) in: `loop-engineering` — installing any one serves it.

## What it does (so provisioning can decide without installing)

Analyze session outcomes and update memory topics (testing-lessons, fix-patterns, success-patterns, skill-gaps) for continuous self-improvement. Captures both failure lessons (error→fix→lesson) and success patterns (what worked + when to reuse it). Four modes: session, deep, meta, test-run.

After install the skill resolves as `cbp-learning-workflow:learn-n-improve` (invokable as `/learn-n-improve` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Modes
- Gather Session Evidence
- Analyze Outcomes
- Build Error→Fix→Lesson Database
- Hub Pattern Linkage (Effectiveness Telemetry)
- 5: Build Success-Pattern Database (memory of wins)
- Schema fields
- Typing and routing (do not skip)
- Update Memory Topics
- Pattern Detection (every 10th learning)
- 5: Inject Active Constraints into Skills
- 5.5.1 Map Learnings (and Success Patterns) to Skills

Original invocation shape: `<mode: session|deep|meta|test-run>`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update cbp-learning-workflow`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
