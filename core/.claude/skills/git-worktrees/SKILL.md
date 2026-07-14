---
name: git-worktrees
description: >
  POINTER to the installable loop-engineering plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Manage git worktrees for isolated parallel development. Provides a decision framework for when to use worktrees vs. regular branches, creation patterns, Claude Code's built-in isolation parameter, par
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# git-worktrees — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
loop-engineering plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install loop-engineering@claude-best-practices
/reload-plugins
```

## What it does (so provisioning can decide without installing)

Manage git worktrees for isolated parallel development. Provides a decision framework for when to use worktrees vs. regular branches, creation patterns, Claude Code's built-in isolation parameter, parallel agent workflows, merge strategies, cleanup procedures, and common pitfalls.

After install the skill resolves as `loop-engineering:git-worktrees` (invokable as `/git-worktrees` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- Understand Git Worktrees
- Decide When to Use Worktrees
- Create Worktrees
- 3.1 Basic Creation
- 3.2 Naming Conventions
- 3.3 Branch Strategies
- 3.4 Post-Creation Setup
- Claude Code's Built-in Worktree Isolation
- 5: Background Autonomous-Run Isolation (lock + commit gate)
- Manual Worktree Management
- Merge Strategies
- 6.1 Choosing a Strategy

Original invocation shape: `<task requiring isolated parallel development or worktree management>`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update loop-engineering`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
