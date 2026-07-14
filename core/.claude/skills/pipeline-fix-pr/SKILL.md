---
name: pipeline-fix-pr
description: >
  POINTER to the installable cbp-build-test-workflows plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Apply pipeline fixer diffs to a NEW branch and open a single PR with all fixes (instead of N commits on the current branch). Use when the team's git workflow requires PR review for any change. Wraps `
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# pipeline-fix-pr — now ships as a plugin

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

Apply pipeline fixer diffs to a NEW branch and open a single PR with all fixes (instead of N commits on the current branch). Use when the team's git workflow requires PR review for any change. Wraps `/serialize-fixes` for the actual diff application; this skill adds branch creation, push, and `gh pr create`.

After install the skill resolves as `cbp-build-test-workflows:pipeline-fix-pr` (invokable as `/pipeline-fix-pr` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Preflight
- Parse arguments + capture context
- Create fix branch
- Apply diffs (delegate to /serialize-fixes)
- Push branch + open PR (skipped if --no-push)
- Summary
- Per-Issue Outcomes
- Test plan
- Return to original branch + return contract
- NON-NEGOTIABLE

Original invocation shape: `<diffs-glob-or-list> [--base <branch>] [--no-push]`.
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
