---
name: learning-self-improvement
description: >
  Guide projects to the installable cbp-learning-workflow PLUGIN. The learning
  workflow (capture -> detect-patterns -> knowledge-test, with /learn-n-improve,
  /skill-factory, /test-knowledge and its 2 worker agents) graduated from a copied
  core/ template into the hub marketplace plugin
  `cbp-learning-workflow@claude-best-practices`, which is now its single source of
  truth. Use this pointer when provisioning the learning workflow into a project —
  install the plugin instead of copying the template.
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "3.0.0"
---

# learning-self-improvement — now ships as a plugin

This workflow is **no longer distributed as a copied template**. It graduated to the
`cbp-learning-workflow` plugin (G6-validated 2026-07-12) so there is **one source of
truth** instead of a template copy that drifts. This file is a pointer left in `core/`
so provisioning surfaces the redirect rather than silently dropping the capability
(#346 stage 2; recipe: `plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install cbp-learning-workflow@claude-best-practices
/reload-plugins
```

The plugin ships the FULL closure: this orchestrator plus `/learn-n-improve`,
`/skill-factory`, `/test-knowledge`, and the `session-summarizer-agent` +
`context-reducer-agent` workers. After install the workflow resolves under its own
name (`cbp-learning-workflow:learning-self-improvement`, invokable as
`/learning-self-improvement` when no shadowing copy exists).

## What the plugin workflow does (so provisioning can decide without installing)

The learning workflow is the hub's continuous self-improvement loop, run as a
skill-at-T0 orchestrator in the user's session:

- **capture** — `/learn-n-improve` records error→fix→lesson patterns and verified
  success patterns from the session into `.claude/learnings.json`.
- **detect-patterns** — recurring lessons (3+ evidence occurrences, reactive not
  speculative) are promoted into skill proposals via `/skill-factory`.
- **knowledge-test** — `/test-knowledge` verifies the accumulated knowledge still
  matches the codebase before it is trusted.
- Deep session analysis optionally dispatches `session-summarizer-agent` and
  `context-reducer-agent` workers at T0.

Modes: `session` (end-of-session capture), `detect-patterns`, `full`, or a specific
topic. Projects that only need one-off capture can invoke the plugin's
`/learn-n-improve` directly.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update cbp-learning-workflow`; copied templates drift silently.
- **Closure completeness** — the plugin bundles the sub-skill + agent closure, so an
  install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
