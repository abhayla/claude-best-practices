# Task Tracker

<!-- Claude maintains this file during implementation sessions. -->
<!-- Format: checkable items grouped by task, marked complete as work progresses. -->

## Current Task

**Testing Pipeline Overhaul** — implementation of the plan at `C:\Users\itsab\.claude\plans\first-of-all-don-t-sparkling-treehouse.md`.
Branch: `feat/testing-pipeline-overhaul`. Started: 2026-04-22.

### Phase A — e2e consolidation (skill wraps agent)
- [x] Read current state of 5 agent files + e2e-visual-run SKILL.md + references/*
- [ ] `e2e-conductor-agent.md` — absorb user-facing behaviors from e2e-visual-run (section filter, baseline-update mode, first-run artifacts, report format, state-file path fix)
- [x] `test-scout-agent.md` — absorb `references/scout-phase.md`
- [x] `visual-inspector-agent.md` — absorb `references/inspection-phase.md`
- [x] `test-healer-agent.md` — absorb `references/healing-phase.md`
- [x] `e2e-conductor-agent.md` — absorb e2e-visual-run user-facing behaviors (sections, baseline-update, first-run artifacts, env discovery, commit guards, return contract); dual-mode state path; cleanup guard
- [x] `e2e-visual-run/SKILL.md` — shrunk to ~80 lines, dispatches agent
- [x] Delete `core/.claude/skills/e2e-visual-run/references/*`
- [x] Commit Phase A

### Phase B — Healer upgrade (MCP + deterministic classification)
- [x] `test-healer-agent.md` — add Playwright MCP server to frontmatter (hard dep)
- [x] `test-failure-analyzer-agent.md` — add deterministic regex pre-classification short-circuit with `classification_source` field
- [ ] `core/.claude/config/e2e-pipeline.yml` — expose regex rules as configurable
- [ ] Commit Phase B

### Phase C — Architectural gap fixes (state, retry, cleanup)
- [x] State-file path: standalone vs dispatched detection in `e2e-conductor-agent.md`
- [x] State schema versioning: add `schema_version: "1.0.0"` to all state file schemas
- [x] Cleanup-at-init guard: wrap `rm -rf` in `if mode == 'standalone'` in `test-pipeline-agent.md` and `e2e-conductor-agent.md`
- [x] Retry-budget composition: T1 master passes `remaining_budget` in dispatch context; T2 uses passed budget
- [x] Aggregation consolidation: T1 aggregates, T2 does not duplicate
- [x] Contradictions-as-blockers config flag in `testing-pipeline-master-agent.md`
- [x] Silent-degradation gate in `auto-verify/SKILL.md` Step 4
- [x] `config/workflow-contracts.yaml` — already matched (e2e path points to `.workflows/testing-pipeline/e2e-state.json`)
- [x] `core/.claude/config/e2e-pipeline.yml` — schema_version, MCP, regex rules, contradictions, issue_creation, decay/probe history
- [ ] Commit Phase C

### Phase D — Issue tracking integration
- [ ] `testing-pipeline-master-agent.md` — aggregation step adds `gh issue create/comment` for LOGIC_BUG/VISUAL_REGRESSION with signature dedup
- [ ] `issue_creation.enabled` config flag in `e2e-pipeline.yml`
- [ ] `gh auth status` fail-closed check at pipeline start
- [ ] Commit Phase D

### Phase E — Constitution pointer pattern
- [ ] Prepend `## NON-NEGOTIABLE` block to `test-scout-agent.md`
- [ ] Prepend `## NON-NEGOTIABLE` block to `visual-inspector-agent.md`
- [ ] Prepend `## NON-NEGOTIABLE` block to `test-healer-agent.md`
- [ ] Prepend `## NON-NEGOTIABLE` block to `test-pipeline-agent.md`
- [ ] Prepend `## NON-NEGOTIABLE` block to `e2e-conductor-agent.md`
- [ ] Commit Phase E

### Phase F — Standalone CI aggregator (narrow scope)
- [x] Create `scripts/pipeline_aggregator.py` — 290 lines, pure read/compute/write, typed, exit 0/1/2
- [x] Tests in `scripts/tests/test_pipeline_aggregator.py` — 13 tests covering all-pass, any-fail, screenshot-authoritative, contradictions (warn/strict), missing dir, malformed JSON, signature dedup, FIXED status, UI summary, CLI entry point, self-loop guard
- [ ] Add GitHub Actions job calling the aggregator (deferred — CI wiring is a separate workflow file concern)
- [ ] Commit Phase F

### Phase G — Synthetic Playwright fixture
- [x] Create `scripts/tests/fixtures/playwright-demo/` with Express app + Playwright config + 7 scenarios
- [x] 7 test scenarios (home/pass, dashboard/broken-locator, checkout/timing, visual/visual-change, logic/LOGIC_BUG, flaky, infra) with `DEMO_SCENARIO` env var seeding
- [x] `playwright.config.ts` — webServer on port 4317, outputDir test-evidence/latest, screenshot: 'on', json reporter
- [x] `package.json` with Playwright 1.49 + express 4.21 + @playwright/mcp dependency (matches test-healer-agent's declared MCP server)
- [x] Tiny Express server (90 LOC, no framework) with DEMO_SCENARIO-aware endpoints (/health, /api/users, /api/orders, /api/metric) and 3 static HTML pages
- [x] README.md documenting the scenario matrix and how to run standalone vs through the pipeline
- [x] .gitignore excluding node_modules, test-results, test-evidence, .pipeline, .workflows, playwright-report
- [x] Commit Phase G

### Phase H — Verification (end-to-end proof)
- [ ] `scripts/tests/test_pipeline_e2e.py` with parametrized scenarios
- [ ] CI job wiring
- [ ] Run all 15 items in plan's verification checklist
- [ ] Commit Phase H

### Cross-cutting
- [ ] `registry/patterns.json` — bump versions for all changed patterns
- [ ] `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` — append "Applied" section
- [ ] Regenerate docs (`PYTHONUTF8=1 PYTHONPATH=. python scripts/generate_docs.py`)
- [ ] Run full CI replication locally (pytest, workflow_quality_gate_validate_patterns, dedup_check)
- [ ] Update `.claude/tasks/lessons.md` with any corrections encountered

## Completed

_None yet in this task._

## Review

_To be filled at end of task._
