# Task Tracker

<!-- Claude maintains this file during implementation sessions. -->
<!-- Format: checkable items grouped by task, marked complete as work progresses. -->

## Current Task

### Prompt Logger Hook (2026-04-24)

Goal: persist every `UserPromptSubmit` prompt to `.claude/tasks/prompts.md` as append-only Markdown. Distributable via `core/.claude/hooks/` so downstream projects get the hook on provision.

Approved design (Q1=A gitignore live log, Q2=A Markdown with `~~~text` fence, Q3=A empty seed in `core/`):
- Hook writes to `$(git rev-parse --show-toplevel)/.claude/tasks/prompts.md`; NEVER writes to stdout (stdout on `UserPromptSubmit` is injected into the conversation context).
- Entry format: `## <iso-ts> — branch@shortsha` heading, `- session:` + `- cwd:` bullets, `~~~text` fence around raw prompt (triple-tilde survives prompts containing triple-backtick blocks).
- Non-blocking under every failure mode: malformed stdin, missing `jq`, missing git, empty prompt → exit 0, log unchanged.

Tasks:
- [x] Write failing tests in `scripts/tests/test_prompt_logger.py` (TDD red — 1 failing on missing hook)
- [x] Implement `core/.claude/hooks/prompt-logger.sh`
- [x] Mirror to `.claude/hooks/prompt-logger.sh` (byte-identical; test_hub_hook_exists_and_matches_core_byte_for_byte pins this)
- [x] Create empty seed `core/.claude/tasks/prompts.md` (header only, tracked)
- [x] Create live log `.claude/tasks/prompts.md` (header only, gitignored)
- [x] Wire second `UserPromptSubmit` hook into `.claude/settings.json`
- [x] Gitignore `/.claude/tasks/prompts.md`
- [x] Document in `core/.claude/hooks/README.md` — new "Prompt Logger" section
- [x] Register in `registry/patterns.json` (type=hook, tier=nice-to-have) + bump `_meta.total_patterns` 237→238
- [x] Run pytest (1283 passed, 60 skipped, 1 xfailed)
- [x] Run full CI replication: dedup --validate-all ✅, dedup --secret-scan ✅, workflow_quality_gate_validate_patterns ✅, pytest ✅
- [x] Append review section

### Review (Prompt Logger)

Outcome: 9 files changed, 16 new tests, all 4 CI gates green. Hook is live in this session — `.claude/tasks/prompts.md` already captured a real prompt during implementation, confirming end-to-end.

TDD caught one real bug during the green phase:
- `entry=$(printf ...)` stripped trailing newlines (bash `$(...)` semantics), causing two back-to-back prompts to run together (`~~~## next` with no blank line). Fixed by switching to grouped redirection `{ ...; } >> "$log"`. Test `test_multiple_appends_do_not_clobber` pins this forever.

What could break:
- On systems without `jq`, the hook becomes a no-op silently (by design — no-blocking is a hard requirement). If a user *expects* prompts to be logged and `jq` is missing, they won't notice. Mitigation: `test_settings_json_wires_prompt_logger_hook` confirms wiring, but no runtime "is logging actually working?" signal exists. Acceptable for v1; layer a statusline hint later if needed.
- Concurrent prompts exceeding PIPE_BUF (4 KB on Linux) can interleave — accepted trade-off, documented in the hook preamble.
- Windows path backslashes appear verbatim in the `- cwd:` bullet. Harmless in Markdown.
- `core/.claude/tasks/prompts.md` seed ships via provisioning; downstream projects need to add `/.claude/tasks/prompts.md` to their own `.gitignore` — this is documented in the hooks README section but NOT enforced. A `synthesize-project` hook could auto-append the gitignore line, but that widens scope beyond this task.

Nothing pushed. No commit created — awaiting user approval per default policy.

## Completed

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

### Review (REQ-S004)

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
