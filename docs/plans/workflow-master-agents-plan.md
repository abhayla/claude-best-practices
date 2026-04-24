# Implementation Plan: Workflow Master Agents

> **⚠️ SUPERSEDED 2026-04-25 (Phase 3).** This plan's goal — build 8 workflow-
> master agents + sub-orchestrators under a federated T0→T1→T2→T3 dispatch
> model — was fully executed originally, then RETIRED across Phases 3.1–3.8
> after the 2026-04-24 platform finding (subagents cannot spawn subagents;
> [Anthropic docs](https://code.claude.com/docs/en/sub-agents)). All 8
> workflow-masters are now deprecated; orchestration lives in skill-at-T0
> bodies under `core/.claude/skills/<workflow>-*/SKILL.md`. For the current
> Phase 3 migration tracker, see `.claude/tasks/todo.md` § "Phase 3 —
> Workflow-master pattern retirement". For the current design, see
> `docs/specs/test-pipeline-three-lane-spec-v2.md` v2.2 (reference
> implementation) and `core/.claude/agents/workflow-master-template.md` v2.0.0.

**Created:** 2026-03-30
**Estimated total time:** ~51m expected | ~61m with buffer
**Critical path:** Task 1 → 4 → 6 → 9 → 11 → 13

## Atomic Plan 1: Foundation (Config + Rules)

- [x] **Task 1:** Create `config/workflow-contracts.yaml` — Full workflow DAG definitions for all 8 workflows
  - Files: `config/workflow-contracts.yaml` (create)
  - Verify: `python -c "import yaml; yaml.safe_load(open('config/workflow-contracts.yaml')); print('VALID')"`
  - Depends on: None

- [x] **Task 2:** Update `agent-orchestration.md` (both copies) — 4-tier model, controlled nesting, per-scope state, new rules #9-11
  - Files: `.claude/rules/agent-orchestration.md`, `core/.claude/rules/agent-orchestration.md` (modify)
  - Verify: `diff` both copies + `workflow_quality_gate_validate_patterns.py`
  - Depends on: None

- [x] **Task 3:** Add `.workflows/` to `.gitignore`
  - Files: `.gitignore` (modify)
  - Verify: `grep ".workflows/" .gitignore`
  - Depends on: None

## Atomic Plan 2: Template + 4 Primary Agents

- [x] **Task 4:** Create `core/.claude/agents/workflow-master-template.md` — 6 protocols
  - Files: `core/.claude/agents/workflow-master-template.md` (create)
  - Verify: Line count > 150, no placeholders
  - Depends on: Task 1

- [x] **Task 5:** Create `development-loop-master-agent.md`
  - Files: `core/.claude/agents/development-loop-master-agent.md` (create)
  - Depends on: Task 4

- [x] **Task 6:** Create `testing-pipeline-master-agent.md`
  - Files: `core/.claude/agents/testing-pipeline-master-agent.md` (create)
  - Depends on: Task 4

- [x] **Task 7:** Create `debugging-loop-master-agent.md`
  - Files: `core/.claude/agents/debugging-loop-master-agent.md` (create)
  - Depends on: Task 4

- [x] **Task 8:** Create `code-review-master-agent.md`
  - Files: `core/.claude/agents/code-review-master-agent.md` (create)
  - Depends on: Task 4

## Atomic Plan 3: Skill Wrappers + Integration + Validation

- [x] **Task 9:** Create 4 thin skill wrappers
  - Files: `core/.claude/skills/{development-loop,testing-pipeline-workflow,debugging-loop,code-review-workflow}/SKILL.md` (create)
  - Depends on: Tasks 5-8

- [x] **Task 10:** Update `project-manager-agent.md` dispatch protocol
  - Files: `core/.claude/agents/project-manager-agent.md` (modify)
  - Depends on: Tasks 1, 2

- [x] **Task 11:** Update `registry/patterns.json` (9 new entries)
  - Files: `registry/patterns.json` (modify)
  - Depends on: Tasks 5-9

- [x] **Task 12:** Update `config/workflow-groups.yml`
  - Files: `config/workflow-groups.yml` (modify)
  - Depends on: Tasks 5-9

- [x] **Task 13:** Regenerate docs + full CI validation
  - Verify: All 4 CI commands pass
  - Depends on: Tasks 11, 12
