# cbp-build-test-workflows

**The hub's build-and-test workflows, installed instead of copied** — cluster 2 of the #187
distribution pilot (cluster 1: `cbp-workflows`). One `/plugin install cbp-build-test-workflows`
gives a downstream project the two core delivery workflows plus every universal sub-skill and
worker agent they dispatch — centrally versioned, upgraded with `/plugin update`.

## Install

```
/plugin install cbp-build-test-workflows
```

(from the hub repo's marketplace — `plugins/.claude-plugin/marketplace.json`).

## What's included

| Type | Name | Role |
|---|---|---|
| Skill | `development-loop` | Full feature loop: requirements → plan → implement → verify → review handoff |
| Skill | `test-pipeline` | The orchestrated three-lane test run: scout → lanes → analyze → fix-loop → verdict. Ships `test-pipeline.default.yml` INSIDE the skill dir — used automatically when the project has no `.claude/config/test-pipeline.yml` (the plugin copy falls back instead of blocking) |
| Skill | `writing-plans`, `implement`, `brainstorm`, `fix-github-issue`, `update-practices` | development-loop dispatch closure |
| Skill | `auto-verify`, `contract-test`, `integration-test`, `fix-loop`, `pipeline-fix-pr`, `post-fix-pipeline`, `serialize-fixes`, `systematic-debugging`, `escalation-report`, `review-gate` | test-pipeline dispatch closure |
| Agent | `plan-executor-agent`, `planner-researcher-agent` | development-loop workers |
| Agent | `test-scout-agent`, `tester-agent`, `test-failure-analyzer-agent`, `visual-inspector-agent`, `github-issue-manager-agent` | test-pipeline workers |

## Quickstart

- Build a feature end-to-end: `/development-loop <feature description>`
- Run the full test pipeline: `/test-pipeline`

## Boundaries (deliberate, per the #187 tier design)

- **Stack-specific helpers are NOT here** (`pytest-dev`, `jest-dev`, `vitest-dev`,
  `fastapi-run-backend-tests`, `fastapi-api-tester-agent`, android-*, …). `test-pipeline`
  detects the stack and uses them when present; without them it degrades to its universal
  path. Get them via the hub's stack provisioning (`recommend.py --provision`).
- **Companion plugins, not duplicates:** `code-review-workflow` (review phase) ships in
  **`cbp-workflows`**; `debugging-loop` / the deep-debugging cluster ships in
  **`loop-engineering`**. Install those alongside for the full delivery chain. Shared
  direct-dispatch sub-skills (e.g. `fix-loop`, `review-gate`) are deliberately included
  here too — plugin skills are namespaced, so copies cannot collide, and each plugin stays
  self-contained for what it directly dispatches.
- **Project-owned files** (CLAUDE.md, goals.yml, project rules, a customized
  `.claude/config/test-pipeline.yml`) stay copy-provisioned — a project config, when
  present, always wins over the bundled default.

## Versioning

Installed plugins are version-pinned in Claude Code's cache. Fixes reach you when the hub
bumps `version` in `.claude-plugin/plugin.json` and you run `/plugin update cbp-build-test-workflows`.
