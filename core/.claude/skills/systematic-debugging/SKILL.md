---
name: systematic-debugging
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Debug failures methodically using a structured diagnosis workflow: reproduce, isolate, hypothesize, gather evidence, find root cause, apply targeted fix, verify, and prevent recurrence. Use when facin
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# systematic-debugging — now ships as a plugin

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

Debug failures methodically using a structured diagnosis workflow: reproduce, isolate, hypothesize, gather evidence, find root cause, apply targeted fix, verify, and prevent recurrence. Use when facing bugs, test failures, or unexpected behavior instead of making random code changes. For a KNOWN failure with a retest command that just needs iterate-until-green, use /fix-loop instead — /fix-loop escalates back here when the root cause is unclear or 2+ fix attempts fail.

After install the skill resolves as `cbp-build-test-workflows:systematic-debugging` (invokable as `/systematic-debugging` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Search Past Learnings
- 0.1 Search the Learnings Database
- 0.2 If Match Found
- 0.3 If No Match Found
- Reproduce the Failure
- 1.3 Handle Non-Reproducible Failures
- 1.4 Classify the Failure Type
- Isolate the Failure
- 2.1 Read the Error Trace
- 2.2 Narrow the Scope
- Binary Search Through Code
- Minimize the Input

Original invocation shape: `<bug-description, error message, or failing test command>`.
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
