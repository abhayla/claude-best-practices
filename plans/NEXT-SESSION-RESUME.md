# Next-Session Resume Prompt — Platform Migration 2026 H2

> Copy everything in the fenced block below into the next session's first message.
> Last updated: 2026-06-19 (after Phase 4.2 C2–C4 + the `*Session-boundary:*` hook tweak shipped).

```
Resume the Platform Migration & Futuristic Goal (2026 H2) initiative on the
claude-best-practices hub.

First, read these in order (do not skip):
1. .remember/remember.md — current state + the RETIRE reference map (auto-surfaced)
2. plans/platform-migration-2026H2.md — SSOT roadmap; read the Phase 0 Ledger
   "RETIRE" section (it carries the deferred-RETIRE surgical plan + reference map)
3. plans/skill-at-t0-doctrine-relaxation.md — Phase 4.2 cascade, now C1–C4 DONE
4. .claude/tasks/lessons.md — read the top entries (2026-06-19), incl. the now-APPLIED
   *Session-boundary:* hook tweak
5. Run: gh issue view 119

Where we are: branch chore/platform-migration-2026h2-tracking, PR #120. Last session
shipped (all green, independent-reviewed):
- Phase 4.2 C2–C4 (commit 9c0619b): reframed single-level subagent dispatch from
  "platform-forced" → deliberate KISS/YAGNI CONVENTION across 6 surfaces. Nested
  dispatch is GA (Claude Code v2.1.172, ≤5 levels); workers don't declare Agent by
  hub CHOICE, not because the runtime strips it (only the depth-5 cap withholds it).
  Validator assertions UNCHANGED. Phase 4.2 is effectively DONE (only the conditional
  C5 pilot remains, YAGNI — may never fire).
- *Session-boundary:* hook tweak (commit faa4c59): no-overask-guard.sh now exempts a
  completed-tested-chunk stop that opens a line with *Session-boundary:* (logs it for
  audit instead of blocking). Use it to close sessions cleanly.

THE PRIMARY NEXT TASK — execute the owner-APPROVED 6-pattern RETIRE (deferred last
session to fresh context because it's a regression-sensitive removal of test coverage).
Abhay already approved deletion on 2026-06-19; do NOT re-ask for approval — just execute
it carefully, test-gated, as one PR on the current branch.

The 6 patterns (all category=deprecated since 2026-04-24; replacements verified):
  - e2e-conductor-agent           → /test-pipeline (+ /e2e-visual-run)
  - test-pipeline-agent           → /test-pipeline
  - failure-triage-agent          → /test-pipeline
  - testing-pipeline-master-agent → /test-pipeline
  - testing-pipeline-workflow     → /test-pipeline
  - fix-issue                     → /fix-github-issue

WHY this needs care (verify-before-delete finding): these are NOT inert. ~10+ test
files _read() the agent files and assert their CONTENT (responsibility counts,
version-vs-registry, schema fields) → naive deletion = FileNotFoundError, not a
graceful skip. The canonical spec docs/specs/test-pipeline-three-lane-spec-v2.md
(v2.2) still defines them as T1/T2A/T2B.

Surgical removal plan (do in this order, test-gated):
1. RE-VERIFY the reference map first (platform/test facts drift; the map below was
   gathered 2026-06-19) — re-grep each of the 6 names across the repo before editing.
2. Test surgery — remove ONLY the assertions/cases that test the DEAD agents; KEEP every
   test that guards the active /test-pipeline workers (tester-agent, test-scout-agent,
   visual-inspector-agent, test-failure-analyzer-agent). Known coupled files:
     - scripts/tests/test_pipeline_three_lane.py (19 refs — T1/T2A/T2B responsibility-cap
       + allowlist assertions on the deleted agents)
     - scripts/tests/test_pipeline_contracts.py (TEST_PIPELINE_AGENT path @ ~line 40;
       verdict-schema test @ ~228; version-matches-registry parametrize @ ~490)
     - scripts/tests/test_tier_dispatch_consistency.py (DISPATCH_CHAIN keys @ ~38–48 —
       remove testing-pipeline-master-agent + e2e-conductor-agent entries)
     - scripts/tests/test_pipeline_integrity.py:487 (testing-pipeline-workflow in a list)
     - Also scan: test_pipeline_three_lane_pr2.py, test_pipeline_three_lane_req_c003.py,
       test_pipeline_three_lane_should_have.py, test_e2e_visual_run_playwright_only.py,
       test_fixture_deps_and_verdicts.py, test_pipeline_aggregator.py, test_pipeline_e2e.py,
       test_test_pipeline_config_shipped.py, test_assign_workflow_groups.py,
       test_state_archive_and_git_remote.py — confirm each ref is dead-agent (remove) vs
       live-worker (keep).
3. Config/code fixes:
     - config/workflow-groups.yml — remove lines 25 (fix-issue), 131 (testing-pipeline-workflow),
       139 (e2e-conductor), 140 (failure-triage), 149 (test-pipeline-agent),
       152 (testing-pipeline-master), 182 (fix-issue). (Re-confirm line numbers.)
     - scripts/recommend.py:442 — remove "test-pipeline-agent" from MUST_HAVE_AGENTS.
     - config/workflow-contracts.yaml + core/.claude/config/workflow-contracts.yaml:78 —
       update the testing-pipeline-master-agent comment to past tense (or remove).
4. Docs:
     - CLAUDE.md:108 — "The 8 legacy ...master-agent.md files" → "7" (deleting
       testing-pipeline-master-agent leaves 7 of the 8).
     - CLAUDE.md workflow-map row (testing-pipeline → testing-pipeline-workflow): repoint
       to test-pipeline (the active skill) OR drop the row's stale target.
     - docs/specs/test-pipeline-three-lane-spec-v2.md — mark the T1/T2A/T2B agent layer as
       retired/historical (don't delete the spec; annotate it).
5. Delete the 6 files; remove their 6 registry/patterns.json entries; decrement
   _meta.total_patterns by 6; add a registry/changelog.md entry.
6. Regenerate docs: python scripts/generate_docs.py and
   PYTHONPATH=. python scripts/generate_workflow_docs.py (do NOT hand-edit docs/workflows/).
7. FULL local CI (all 4) + an independent context-blind review before push:
     PYTHONPATH=. python scripts/dedup_check.py --validate-all
     PYTHONPATH=. python scripts/dedup_check.py --secret-scan
     PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
     PYTHONPATH=. python -m pytest scripts/tests/ -v
   Watch specifically: test_readme_count_drift.py (README must not hardcode a stale count),
   and confirm no remaining dead cross-reference (the validator blocks those).
8. Land as one commit on PR #120; update plans/platform-migration-2026H2.md (RETIRE → DONE)
   + .remember/remember.md.

Apply lessons (.claude/tasks/lessons.md, 2026-06-19):
- Render the FULL enhance card on EVERY substantive turn incl. continuations.
- Verify each claim/MIGRATE before effort — audits over-claim; re-grep the reference map
  before deleting (it may have drifted).
- Coherence sweep when reframing/removing: grep for sibling references that would dangle.
- You MAY close the session with a *Session-boundary:* line once the chunk is tested + committed.

After the RETIRE lands, the remaining (lower-priority) migration backlog in
plans/platform-migration-2026H2.md: Phase 4.2 C5 pilot (deferred YAGNI), Phases 1.1/1.2
(marginal/already-adopted — confirm before any churn), Phase 2.x (deploy gap — needs VPS
creds, escalate at deploy), Phase 3.x (cloud autonomy / Routines), Phase 5.1b (deferred).

Start by reading the 5 sources, re-verifying the reference map, then execute the RETIRE.
```
