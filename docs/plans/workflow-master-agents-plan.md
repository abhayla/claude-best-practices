# Implementation Plan: Workflow Master Agents

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
