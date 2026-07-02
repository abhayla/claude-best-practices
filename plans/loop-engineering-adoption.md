# Loop-Engineering Adoption Plan (hub + fleet)

**Status:** ACTIVE — Phase 1 not started
**Owner:** Abhay (gates) + Claude (execution)
**Approved direction:** 2026-07-02 session (explain → survey → recommend turn, order: verifiers → pilot → outer rings → success capture → vocabulary/plugin)
**Context:** The hub already ships `/loop-engineering` v1.1.0 (`core/.claude/skills/loop-engineering/SKILL.md`, spec `docs/specs/loop-engineering-spec.md`). This plan does NOT build a loop engine — it closes the five gaps found in the 2026-07-02 research pass (session sources: `docs/process-improvement/sources/` captures + web/X landscape survey) and proves the loop downstream.

**Fleet doctrine (decided 2026-07-02):** one loop per project, anchored INSIDE that project (its session/routine loads its own CLAUDE.md, rules, tests, git hooks). The hub never executes a foreign project's loop in-session; the hub provisions, upgrades, and monitors (telemetry via `aggregate_telemetry.py`). SSOT for the why: spec "out of scope" note + `product-incubation.md` + no-cross-session-entanglement lesson.

---

## Phase 1 — Verifier depth on the loop's critical path

Every source converged on "the verifier is the bottleneck." Scope honestly (KISS): NOT evals for all skills — only the loop's own dispatch chain.

| # | Work item | Owner | Test strategy | DoD (machine-checkable) |
|---|---|---|---|---|
| 1.1 | Eval scenarios for `plan-executor-agent` (MAKER) — dispatch behavior + structured-return contract | Claude | `/agent-evaluator` per scenario, avg ≥4/5 | `core/.claude/agents/plan-executor-agent/evals/scenarios/*.json` exists; evaluator report PASS |
| 1.2 | Eval scenarios for `code-reviewer-agent` (CHECKER) — adversarial-review verdict quality | Claude | `/agent-evaluator`, avg ≥4/5 | scenarios exist + PASS |
| 1.3 | Skill evals for `/loop-engineering` itself (trigger + output + preflight-block path) | Claude | `/skill-evaluator full core/.claude/skills/loop-engineering` — one skill per run, full EVAL-WORKFLOW, no batching | eval artifacts in the skill's `evals/`; report PASS |
| 1.4 | Skill evals for `/fix-loop` + `/auto-verify` (the FEEDBACK/VERIFY arms) | Claude | `/skill-evaluator full`, one per run | eval artifacts + PASS ×2 |

**Documentation:** each eval run's report saved under the pattern's `evals/`; registry hashes resynced; full local CI (`pre-git-merge-checker-agent`) before each PR.

## Phase 2 — Downstream pilot (the test drive)

| # | Work item | Owner | Test strategy | DoD (machine-checkable) |
|---|---|---|---|---|
| 2.1 | Pick pilot project. **Recommended: `../noter-app`** (graduated, 31/31 verified, Notifier-wired — lowest-risk real repo). Swappable by owner in one line. | **Abhay** (or default stands) | — | pilot named in this file |
| 2.2 | Provision loop-engineering + its dependency closure into the pilot | Claude | `/update-practices` diff clean; preflight probe passes in pilot | pilot's `.claude/skills/loop-engineering/` present; PREFLIGHT exits green |
| 2.3 | Author the pilot's first goal contract (one narrow goal, testable finish line) via `/goal-creator` | Claude drafts, **Abhay approves the goal** | contract review: zero open questions | contract file committed in pilot repo |
| 2.4 | Run `/loop-engineering <contract>` IN THE PILOT'S OWN SESSION (fleet doctrine — not from the hub) | **Abhay opens the session**; loop runs autonomously | the loop's own 3 gates (auto-verify strict, independent review, supervisor reproduction) | terminal signal `shipped` (or a clean `escalated`) in pilot's `.claude/learnings.json` with `hub_pattern_link: "loop-engineering"`; shipped PR merged green |
| 2.5 | Telemetry round-trip: confirm the hub sees the pilot run | Claude | run `aggregate_telemetry.py --local` against pilot | pilot's loop signals present in `config/telemetry-aggregates.json` / registry effectiveness fields |

## Phase 3 — Encode the outer rings (Ng) in the spec

| # | Work item | Owner | Test strategy | DoD |
|---|---|---|---|---|
| 3.1 | Add a "Three rings" section to `docs/specs/loop-engineering-spec.md`: Ring 1 machine (existing phases), Ring 2 developer gates (where/why per Ng's context-advantage rule), Ring 3 external feedback (dogfood flywheel + telemetry as the existing implementation) | Claude | `workflow_quality_gate_validate_patterns.py` + `test_workflow_closure_consistency.py` + dual-home sync test | spec section exists; CI green |
| 3.2 | Sync the SKILL.md pointer to the new section (both `.claude/` and `core/.claude/` copies per `config/dual-home-resources.yml` classification) | Claude | `test_dual_home_sync.py` | CI green; registry hash resynced |

## Phase 4 — Success-pattern capture (memory of wins)

| # | Work item | Owner | Test strategy | DoD |
|---|---|---|---|---|
| 4.1 | Extend `/learn-n-improve` to write a success-pattern entry (what worked + reuse trigger) alongside failure lessons — pattern #9 of the 20-pattern taxonomy | Claude | `/skill-evaluator full` on the updated skill; full local CI | skill updated + eval PASS; registry hash resynced; CI green |

## Phase 5 — Shared vocabulary + (gated) plugin

| # | Work item | Owner | Test strategy | DoD |
|---|---|---|---|---|
| 5.1 | `docs/loop-vocabulary.md`: map Ng's 3 rings, Karpathy's 9 rules, Ralph, Willison's brakes, and the 20 patterns → the hub asset implementing each (or an honest "not covered — YAGNI") | Claude | `dedup_check.py --validate-all` (link integrity) | file exists; referenced from the spec; CI green |
| 5.2 | Package loop-engineering as a G6 plugin via `/plugin-lifecycle` | **Abhay — strategic G6 build, requires explicit approval BEFORE building** | plugin-lifecycle's own create+validate flow | DO NOT START until approved; blocked marker here flips on approval |

---

## How "properly implemented" is verified (the meta-answer)

1. **Every item's DoD is machine-checkable** (file-exists / eval-PASS / CI-green / telemetry-signal) — same doctrine as `goals.yml`. No item is "done" by claim.
2. **Maker ≠ checker at the plan level too:** each phase lands via CI-gated PR; `pre-git-merge-checker-agent` runs the full local gate in isolation before push; the `validate` required check gates the merge. The PR numbers get recorded next to each item below as evidence.
3. **The pilot IS the end-to-end test** of everything explained: if Phase 2.4 produces a `shipped` signal through the loop's three independent gates, the explained design (pick→contract→build→check→ship/learn, bounded, escalating) is proven working, not just described.
4. **Documentation artifacts:** this plan file (progress ledger), the spec's new rings section, per-eval reports, the vocabulary doc, and `registry/changelog.md` entries. `.claude/tasks/todo.md` mirrors the active phase per rule 14.

## Progress ledger

- [ ] 1.1 — PR #___
- [ ] 1.2 — PR #___
- [ ] 1.3 — PR #___
- [ ] 1.4 — PR #___
- [ ] 2.1 — pilot confirmed: ______ (default noter-app)
- [ ] 2.2 — PR/commit: ___
- [ ] 2.3 — contract: ___
- [ ] 2.4 — pilot run signal: ___
- [ ] 2.5 — telemetry confirmed: ___
- [ ] 3.1 / 3.2 — PR #___
- [ ] 4.1 — PR #___
- [ ] 5.1 — PR #___
- [ ] 5.2 — BLOCKED on owner approval (G6 gate)
