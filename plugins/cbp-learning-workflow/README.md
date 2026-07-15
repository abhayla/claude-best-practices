# cbp-learning-workflow

**The hub's learning/self-improvement workflow, installed instead of copied** — cluster 3 of
the #187 distribution pilot (cluster 1: `cbp-workflows`, cluster 2: `cbp-build-test-workflows`).
One `/plugin install cbp-learning-workflow` gives a downstream project the session-learning
loop: capture error→fix→lesson patterns, accumulate them in `.claude/learnings.json`, distill
recurring patterns into skill proposals, and keep the knowledge base pruned.

## Install

```
/plugin install cbp-learning-workflow
```

(from the hub repo's marketplace — `plugins/.claude-plugin/marketplace.json`).

## What's included

| Type | Name | Role |
|---|---|---|
| Skill | `learning-self-improvement` | The workflow orchestrator: capture → accumulate → distill → propose → prune |
| Skill | `learn-n-improve` | Per-session capture: appends structured error→fix→lesson entries to `.claude/learnings.json` |
| Skill | `skill-factory` | Turns recurring learning patterns into draft skill proposals |
| Skill | `test-knowledge` | Validates captured knowledge against reality before it hardens |
| Skill | `update-practices` | Sync helper the workflow dispatches at close-out |
| Agent | `context-reducer-agent` | Compresses long-session context for distillation |
| Agent | `session-summarizer-agent` | Summarizes sessions for the learning record |

## Quickstart

- Capture this session's lessons: `/learn-n-improve session`
- Run the full learning workflow (distill + propose + prune): `/learning-self-improvement`

The workflow is self-contained: where the hub keeps optional config
(`config/workflow-contracts.yaml`), the skill falls back to its inline steps when absent.

## Boundaries

- `skill-factory create` delegates Skill-category creation to `/writing-skills` and Rule-category
  creation to `/claude-guardian` — both ship in the companion `cbp-workflows` plugin, not here.
  `scan`/`propose`/`list` modes are fully standalone. (deliberate, per the #187 tier design)

- **`skill-authoring-workflow`** (the workflow that turns an approved proposal into a real,
  validated skill) ships in the companion **`cbp-workflows`** plugin — install both for the
  full learn → propose → author chain.
- Shared direct-dispatch sub-skills that also appear in other plugins (`learn-n-improve` is
  in `loop-engineering` too) are deliberately included — plugin skills are namespaced, so
  copies cannot collide, and each plugin stays self-contained for what it directly dispatches.
- **Project-owned artifacts** (`.claude/learnings.json`, lesson files) belong to the project —
  the plugin brings the process, not the data.

## Versioning

Installed plugins are version-pinned in Claude Code's cache. Fixes reach you when the hub
bumps `version` in `.claude-plugin/plugin.json` and you run `/plugin update cbp-learning-workflow`.
