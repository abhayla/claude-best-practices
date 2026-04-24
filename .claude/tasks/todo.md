# Task Tracker

<!-- Claude maintains this file during implementation sessions. -->
<!-- Format: checkable items grouped by task, marked complete as work progresses. -->

## Current Task

### REQ-S004 — Make auto-heal matrix config-driven (2026-04-24)

Spec: `docs/specs/test-pipeline-three-lane-spec.md` §3.6 + §5 SHOULD-HAVE S004.
Problem: `test-pipeline.yml:90-106` declares `auto_heal:` but nothing reads it; `test-failure-analyzer-agent` NN#6 defers "per spec §3.6" to LLM recall. S004 wires the config through.

- [x] Update `test-failure-analyzer-agent.md`: NN#6 references config path; new "Recommended Action Matrix (Config-Driven)" section describes read procedure + fallback-to-ISSUE_ONLY on missing/invalid config; JSON output example adds `recommended_action`; bump v2.2.0 → v2.3.0
- [x] Update `core/.claude/config/test-pipeline.yml` comment on `auto_heal:` block to mark it load-bearing (not forward-compat) + spec_ref: REQ-S004
- [x] Add `scripts/tests/test_pipeline_auto_heal_req_s004.py` with 11 tests: config enum validation, §3.6 drift check, agent-body references config path, fallback policy declared, ALLOWED values enumerated — all pass
- [x] Update `registry/patterns.json` analyzer version 2.2.0 → 2.3.0 + changelog entry
- [x] Run 4 CI gates: dedup_check --validate-all ✅, dedup_check --secret-scan ✅, workflow_quality_gate_validate_patterns ✅, pytest (1257 passed, 60 skipped, 1 xfailed) ✅
- [x] Commit REQ-S004 implementation — `8b0cd24`
- [x] Scaffold REQ-S007 + REQ-S008 (null-default config knobs, new tests) — `c13b745`
- [x] Annotate spec §5 with ship status + deferral re-confirmation for S009/S010/C001 — `7b3c2d6`

### Review

3 commits on main, all CI gates green across each step:
- `8b0cd24` — REQ-S004: analyzer v2.3.0, `auto_heal:` config now load-bearing with fail-safe fallback to ISSUE_ONLY, 11 new tests
- `c13b745` — REQ-S007/S008 scaffolds: null-default config keys + 10 new tests pinning "scaffold doesn't change behavior"
- `7b3c2d6` — spec v1.7: ship-status + deferral audit trail for all §5 requirements

Deferred (not implemented, with documented triggers):
- REQ-S009 (merge-aware dedup) — needs ≥30 days prod use or triage-time evidence
- REQ-S010 (feature-flag PR2 switchover) — window past; only revisit on generalization opportunity
- REQ-C001 (worktree-per-fixer) — spec §2 rejected this design; needs ≥3 same-file-conflict runs/week before reopening

What could break:
- A downstream project that relied on the analyzer emitting `recommended_action` from LLM recall will now get config-driven values. If their `.claude/config/test-pipeline.yml` lacks an `auto_heal:` block, they'll see WARN logs and ISSUE_ONLY defaults — intentional fail-safe, but worth flagging in next update-practices pass.
- `registry/patterns.json` hash for analyzer is stale (file changed, hash not regenerated). `dedup_check.py --validate-all` passed, so not currently enforced — but if hash-drift gating lands later, this will surface.

Nothing pushed. `main` is 3 commits ahead of `origin/main`.

## Completed

### Testing Pipeline Overhaul (2026-04-22)
Branch: `feat/testing-pipeline-overhaul` — 9 commits, 40 files, +2237 net lines.

All 8 phases delivered against plan `C:\Users\itsab\.claude\plans\first-of-all-don-t-sparkling-treehouse.md`.

**Phase A — e2e consolidation (skill wraps agent)**
- [x] `e2e-conductor-agent.md` v1.0.0 → v2.0.0 — absorbed section filter, baseline-update mode, first-run artifacts, dev-server discovery, commit guards; dual-mode state path; cleanup guard
- [x] `test-scout-agent.md` v1.0.0 → v2.0.0 — absorbed scout-phase.md; screenshot EVERY test (was fail-only); Constitution at top
- [x] `visual-inspector-agent.md` v1.0.0 → v2.0.0 — absorbed inspection-phase.md; EXPECTED_CHANGE lane; Constitution at top
- [x] `test-healer-agent.md` v1.0.0 → v2.0.0 — absorbed healing-phase.md; Constitution at top
- [x] `e2e-visual-run/SKILL.md` v3.0.0 → v4.0.0 — shrunk to <100 lines, dispatches conductor
- [x] `core/.claude/skills/e2e-visual-run/references/*` — deleted (content in agents)

**Phase B — Healer upgrade (MCP + deterministic classification)**
- [x] `test-healer-agent.md` — Playwright MCP hard dep (browser_snapshot, browser_evaluate, console_messages, network_requests, test_run)
- [x] `test-failure-analyzer-agent.md` v1.1.1 → v2.0.0 — 18 regex rules with `classification_source` provenance
- [x] `core/.claude/config/e2e-pipeline.yml` — `classification_rules[]` array exposed for per-project extension

**Phase C — Architectural gap fixes**
- [x] Dual-mode state-file paths (standalone: `.pipeline/`, dispatched: `.workflows/testing-pipeline/`)
- [x] `schema_version: "1.0.0"` required first field of every state file
- [x] Cleanup-at-init mode-gated (standalone only)
- [x] Retry budget composition (`remaining_budget` in dispatch context)
- [x] Aggregation consolidated at T1
- [x] `contradictions.action: warn | block` config
- [x] `auto-verify` silent-degradation gate with `--allow-degraded-ui` opt-out
- [x] Registry/workflow-contracts paths verified consistent

**Phase D — Issue tracking**
- [x] GitHub Issue creation spec in `testing-pipeline-master-agent.md` — sha256 signature dedup, 30-day window
- [x] `issue_creation.enabled` + `require_gh_auth` config flags in `e2e-pipeline.yml`

**Phase E — Constitution pointer pattern**
- [x] `## NON-NEGOTIABLE` block at top of every rewritten agent (scout, inspector, healer, analyzer, conductor, master, pipeline-agent) — SSOT-respecting pointer to `agent-orchestration.md` / `testing.md`

**Phase F — Standalone CI aggregator**
- [x] `scripts/pipeline_aggregator.py` (290 LOC, pure, typed)
- [x] `scripts/tests/test_pipeline_aggregator.py` — 14 tests
- [~] GitHub Actions job wiring — deferred per plan scope

**Phase G — Synthetic Playwright fixture**
- [x] `scripts/tests/fixtures/playwright-demo/` — package.json + playwright.config.ts + .gitignore + README.md
- [x] `app/server.js` + 3 HTML pages with DEMO_SCENARIO-aware behavior
- [x] 7 spec files (home, dashboard, checkout, visual, logic, flaky, infra)

**Phase H — Verification**
- [x] `scripts/tests/test_pipeline_e2e.py` — 20 tests in 3 classes (structural, aggregator scenarios, optional Node smoke)
- [x] Aggregator regression: stage-FAILED with empty failures[] now correctly fails pipeline (bug found during Phase H)

**Cross-cutting**
- [x] `registry/patterns.json` — 9 version bumps, all `last_updated: 2026-04-22`
- [x] `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` — Applied section maps recommendations + gaps to commits
- [x] `generate_docs.py` re-run — DASHBOARD.md, STACK-CATALOG.md, GETTING-STARTED.md, dashboard.html regenerated
- [x] Local CI replication — 1081 pytest passed, 58 skipped; validator PASSED; dedup PASSED
- [x] `.claude/tasks/lessons.md` updated — 2 entries (aggregator bug, pinned-content test migration)

## Deferred (documented in plan's Non-goals)

- Full Claude-Code-free headless runner (user narrowed Phase F to aggregation-only)
- `.github/workflows/*.yml` CI wiring for the standalone aggregator
- Headless live-pipeline verification (requires Node + Playwright + Claude Code in CI); currently covered by the aggregator-scenario simulation in `test_pipeline_e2e.py` and the opt-in `TestPlaywrightSmoke` test

## Review

**Outcome:** All 5 research recommendations (docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md) and all 10 architectural gaps surfaced during the orchestration review landed in `feat/testing-pipeline-overhaul`. No new skill/agent names — every change updates an existing pattern in-place so downstream projects replace via the same filenames.

**Verification**
- `pytest scripts/tests/` → 1081 passed, 58 skipped (up from 1047; +34 new across Phases F/G/H)
- `workflow_quality_gate_validate_patterns.py` → PASSED (1 informational warning: `auto-verify` 506 lines, within the 500–1000 "warning zone" per pattern-self-containment.md)
- `dedup_check.py --validate-all` → Registry validation passed
- `generate_docs.py` idempotency → diff reduces to a timestamp-only change (pre-existing behavior; generator uses `datetime.now()` not git HEAD commit time)

**Lessons captured** → `.claude/tasks/lessons.md`
