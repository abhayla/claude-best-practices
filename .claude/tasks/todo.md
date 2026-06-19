# Task Tracker

<!-- Claude maintains this file during implementation sessions. -->
<!-- Format: checkable items grouped by task, marked complete as work progresses. -->

## Current Task

### Platform Migration & Futuristic Goal (2026 H2) — 2026-06-19 — ⏳ ACTIVE

**SSOT:** `plans/platform-migration-2026H2.md` · **Tracker:** GitHub epic issue · resurfaced via `.remember/`.
Migrate hand-rolled hub patterns onto native Claude Code primitives (W13–24); close deploy gap;
move governance prose→harness. Test-gated chunk-by-chunk. Fable dependency: none (Opus 4.8).

**Platform Migration 2026 H2 — shipped this session (all merged to main):**
- ✅ **PR #121** — RETIRE 6 deprecated test-pipeline patterns → /test-pipeline + /fix-github-issue
  (total 272→266). Surgical, test-gated, blind-reviewed.
- ✅ **PR #122** — Phase 2.1/2.2: adopt native `/code-review ultra` + `/autofix-pr` as ADDITIVE
  opt-in pointers (no replacement of free local skills); 6 patterns version+hash bumped.
- ✅ **Phase 3.1** — crons→Routines DECLINED (deterministic pipelines, not agentic; negative ROI).
- 🛑 **Withdrawn:** e2e-pipeline.yml RETIRE — re-verify showed it's LIVE config (not orphaned); corrected.

**Phase status (parent initiative):**
- [x] Phase 0 (ledger), Phase 4.2 C1–C4 (PR #120), Phase 5.1a (URLs), Phase 1.3 (KEEP), goal codified (README #4)
- [x] **Phase 2.1 / 2.2** DONE (PR #122) · **Phase 3.1** KEEP-decided
- [ ] **Phase 2.3** (deploy gap) — BLOCKED on owner: Hostinger Linux VPS (SSH+Docker) + a real app to deploy
- [ ] **Phase 3.2** (Auto-mode hard-deny) — planned, approval-gated · **4.2 C5 / 5.1b** — deferred YAGNI
- [ ] Phases 1.1/1.2 — settled "don't churn" (already-adopted/marginal)

**Key lesson filed:** verify CURRENT consumers before calling a pattern orphaned/deletable; feed
independent reviewers raw evidence, not my conclusion.

### loop-engineering — 2026-06-17 — ✅ SHIPPED (merged) + hub-ward monitoring (v1.1.0)

- #75 merged (3636620): the autonomous self-* meta-loop.
- #76 merged (0f19c21): hub-ward monitoring — loop emits hub-linked learnings on every
  terminal signal (preflight_blocked/escalated/healed/shipped) → existing weekly
  aggregate_telemetry cron surfaces downstream defects/effectiveness, no new pipeline.
- Independent review caught + fixed B1 (aggregator dropped learnings-only patterns);
  guarded by an end-to-end test. Lesson filed (aggregation must seed from its key field).
- Remaining: external downstream rollout stays per-repo / owner-gated (unchanged).

### loop-engineering distributable pattern — 2026-06-16 — ✅ BUILT & VERIFIED (push/PR escalated)

User directive: build a fully-autonomous, self-healing / self-verifying /
self-learning / self-feedback **loop-engineering** capability as a distributable
hub pattern, working for THIS hub AND downstream projects, provisioning verified.
Pre-authorized autonomous execution. Compose existing self-* assets (no new
engines) per rule-curation + KISS/DRY → exactly 1 new pattern (the skill).

Self-* → composed-from: healing=/fix-loop·/debugging-loop · verification=maker≠checker
(supervisor-verification + independent-test-verification) · learning=/learn-n-improve ·
feedback=/escalation-report+triage-inbox · autonomy=bounded budgets + /loop·/goal.

- [x] Ground in live schemas (contracts, development-loop SKILL, registry shape, _meta=263)
- [x] Decision: compose; 1 new pattern; escalate only outward downstream PRs/push
- [x] Phase 0 — Spec: docs/specs/loop-engineering-spec.md
- [x] Phase 1 — Skill: core/.claude/skills/loop-engineering/SKILL.md (skill-at-T0)
- [x] Phase 2 — Contract: loop-engineering DAG in BOTH workflow-contracts.yaml copies (identical, test-verified)
- [x] Phase 3 — Registry: entry + closure; _meta 263→264; changelog
- [x] Phase 4 — Tests (TDD): closure coverage + maker≠checker guards (×2)
- [x] Phase 5 — Verify: 4 validators + 1454 pytest green
- [x] Phase 6 — Docs: generate_docs + generate_workflow_docs (new docs/workflows/loop-engineering.md)
- [x] Phase 7 — Downstream guarantee: PREFLIGHT runtime probe + closure test + contract-sync test
- [x] Independent code review (code-reviewer-agent) → PASSED, 0 blocking findings
- [x] Lesson captured (fenced-vs-inline Skill() validator gotcha)
- [x] Committed 10ec04f on feat/loop-engineering
- [ ] ⛔ ESCALATION GATE (awaiting owner OK): push branch to remote + open hub PR (outward/publish)

## Review

- Goal-anchored decision held: composed existing self-* assets (healing/verification/
  learning/feedback) → exactly 1 new pattern, no engine duplication. KISS/DRY/curation clean.
- maker≠checker is enforced at THREE layers: SKILL body (2 distinct subagent_types),
  contract DAG (execute≠verify_review dispatch), and 2 regression tests. Cannot silently collapse.
- Downstream verification is structural, not hopeful: closure test proves workers ship with the
  skill; PREFLIGHT BLOCKs at runtime if they didn't (registry session-pinning aware); contract-sync
  test keeps the distributable copy honest.
- The one real gotcha (inline `Skill("/x")` tripping the cross-ref validator) → fenced blocks; lesson filed.
- Remaining: the actual downstream ROLLOUT (provisioning to external repos) is an outward action —
  escalated, not auto-done.

### Promote firekaro Groups A/B/C → hub (3 PRs, merge to main) — 2026-06-12 — ✅ COMPLETE

User directive: promote all three groups, separate PR each, fully autonomous,
merge everything, nothing left hanging. Overrode the SKIP verdict on
plan-before-coding + engineering-roles in plans/hub-promotion-firekaro.md.

## PR C (#45, Tier 5a) — supporting governance rules — ✅ merged
- [x] core/.claude/rules/plan-before-coding.md (generalized, must-have)
- [x] core/.claude/rules/engineering-roles.md (generalized router, nice-to-have)
- [x] registry (+2, total 258) + changelog
- [x] Local CI green, PR #45 CI green, squash-merged

## PR B (#46, Tier 5b) — governance hooks — ✅ merged
- [x] core/.claude/hooks/no-overask-guard.sh (generalized, incl. per-turn aggregation fix)
- [x] core/.claude/hooks/session-governance-status.sh (explicit-zero telemetry line)
- [x] core settings.json: SessionStart + Stop wiring
- [x] registry (+2, total 260) + changelog; local CI green, PR #46 CI green, squash-merged

## PR A (#47, Tier 5c) — prompt-auto-enhance v3.6.0 — ✅ merged
- [x] core skill 3.2.0→3.6.0 + grading-rubric (de-firekaro'd: dates, persona, rule numbers)
- [x] core rule rewritten compact 97 lines (lean-rule tests honored), registry 3.1.0
- [x] core prompt-enhance-reminder.sh 2.1.0 (governance tail + keepgoing reset)
- [x] Hub .claude/ mirrored (skill/rule/hook) + adopted 5b hooks with settings wiring
- [x] Version-pin tests updated (3.6.0 / 3.1.0); registry + changelog; CI green, squash-merged

## Post
- [x] plans/hub-promotion-firekaro.md: Tier 5 record + SKIP strike-through
- [x] Temp files removed; working tree clean

## Review

- Merge order C→B→A was load-bearing: A's rule/hook reference 5a rules + 5b hooks;
  each PR passed validators independently.
- The hub's lean-rule architecture tests (rule ≤100 lines, <15% of skill, hub rules
  ≤250 total) forced the v3.6 rule to be re-compressed rather than copied verbatim —
  all contracts preserved, detail lives in the skill. This is the correct SSOT shape.
- test_prompt_logger fails locally on Windows (bash hook invocation) on a CLEAN tree
  too — not a regression; passes in Linux CI. Deselect locally, trust CI.
- registry/patterns.json is NOT alphabetical — append entries, never re-sort.
- gh pr create --body with embedded double quotes breaks PS 5.1 arg passing — use
  --body-file.

---

## Archive

### Subagent Dispatch Platform Limit Remediation (2026-04-24) — ✅ COMPLETE
Resolved as Option A (T0-only orchestrator, skill-at-T0). See CLAUDE.md
"Workflow Orchestration (skill-at-T0)" + docs/WORKFLOW-DIAGRAM.md for the
shipped model; lessons captured in .claude/tasks/lessons.md.
