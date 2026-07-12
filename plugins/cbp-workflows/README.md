# cbp-workflows

**The hub's quality-trio workflows, installed instead of copied** — the pilot for migrating
distribution from copy-provision to the native plugin model (hub issue #187). One
`/plugin install cbp-workflows` gives a downstream project three orchestrated multi-step
workflows plus every sub-skill and worker agent they dispatch at level 1 — centrally
versioned, upgraded with `/plugin update`, no per-repo copies to drift.

## Install

```
/plugin install cbp-workflows
```

(from the hub repo's marketplace — `plugins/.claude-plugin/marketplace.json`).

## What's included

| Type | Name | Role |
|---|---|---|
| Skill | `code-review-workflow` | Orchestrates multi-dimension code review: review-gate scoring, reviewer + security-auditor agents, fix routing, verdict |
| Skill | `documentation-workflow` | Keeps docs honest: staleness detection, structure enforcement, ADRs, API doc generation |
| Skill | `skill-authoring-workflow` | Authors new Claude Code skills properly: writing-skills procedure, guardian rule placement, quality gates |
| Skill | `review-gate`, `receive-code-review`, `request-code-review`, `fix-loop`, `fix-github-issue`, `update-practices` | code-review dispatch closure |
| Skill | `adr`, `api-docs-generator`, `doc-staleness`, `doc-structure-enforcer` | documentation dispatch closure |
| Skill | `writing-skills`, `skill-master`, `claude-guardian` | skill-authoring dispatch closure |
| Agent | `code-reviewer-agent`, `security-auditor-agent` | review workers |
| Agent | `docs-manager-agent` | documentation worker |
| Agent | `skill-author-agent` | authoring worker |

## Quickstart

- Review the current change set: `/code-review-workflow`
- Audit and fix the project docs: `/documentation-workflow`
- Author a new skill for this project: `/skill-authoring-workflow`

Each workflow is self-contained: where the hub keeps optional config
(`config/workflow-contracts.yaml`), the skill falls back to its inline steps when the file is
absent — no hub files required downstream.

## Boundaries (deliberate, per the #187 tier design)

- **Stack-specific helpers** (pytest-dev, jest-dev, fastapi-*, android-*, …) are NOT here — they
  belong to per-stack packs and remain provisioned by stack detection.
- **The debugging/loop cluster** (`debugging-loop`, `systematic-debugging`, `auto-verify`,
  `loop-engineering`, …) ships in the separate `loop-engineering` plugin — install both for the
  full development loop. `fix-loop` is included here because code-review dispatches it directly;
  plugin skills are namespaced, so the two copies cannot collide.
- **Session lifecycle** (`start-session`, `end-session`, `continue`) ships in the
  `branch-lifecycle` plugin — deliberately not duplicated here.
- **Project-owned files** (CLAUDE.md, goals.yml, project rules) stay copy-provisioned/synthesized —
  plugins distribute identical-across-adopters capability, not files you're meant to edit.

## Versioning

Installed plugins are version-pinned in Claude Code's cache. Fixes reach you when the hub bumps
`version` in `.claude-plugin/plugin.json` and you run `/plugin update cbp-workflows`.
