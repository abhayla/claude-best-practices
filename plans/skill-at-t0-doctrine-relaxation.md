# Plan — Skill-at-T0 Doctrine Relaxation (Phase 4.2 of platform-migration)

**Status:** active · **Created:** 2026-06-19 · **Owner:** Abhay (ratified) · **Driver:** Claude
**Parent:** `plans/platform-migration-2026H2.md` Phase 4 · **Tracker:** epic #119
**Trigger:** Phase 4.1 verdict — nested subagents are **GA (v2.1.172, 5-level hard cap)** per official
`code.claude.com/docs/en/sub-agents`. The hub's single-level-dispatch doctrine is now over-conservative.

## Why this is a careful cascade (not a find-replace)

The premise "subagents cannot spawn subagents" is baked into MANY coupled places. Relaxing one without
the others desyncs the framework (a pattern that nests while the validator still forbids `Agent` on
workers = broken). So the order is: correct the FACT first (safe), then relax coherently in tested chunks.

## Blast-radius file map (the coupled surface)

| Surface | Current (single-level) assumption | Relaxation needed |
|---|---|---|
| `agent-orchestration.md` | §1 "orchestrators MUST run at T0"; §2 "one dispatch level is the hard limit"; §3 "workers MUST NOT attempt Agent"; §10 dual-mode | Rewrite to "nested dispatch GA, ≤5 levels"; redefine worker/orchestrator as depth-relative |
| `pattern-structure.md` | "Tool Grants" — workers MUST NOT declare `Agent`; `dispatched_from` invariant | Allow `Agent` on workers at depth <5; update `dispatched_from` semantics |
| `scripts/tests/test_orchestrator_tool_grants.py` | asserts workers don't declare `Agent` | TDD: update the test FIRST to the new invariant, watch it fail, then fix patterns |
| CLAUDE.md (hub root) "Workflow Orchestration (skill-at-T0)" | "Anthropic does not forward Agent to subagents" rationale | Correct the rationale; note nesting GA ≤5 |
| The 8 `*-master-agent.md` (deprecated) + workflow skills | skill-at-T0 because nesting was impossible | Re-evaluate: skill-at-T0 may still be preferred for some; nesting now an OPTION not a forced workaround |
| `project-manager-agent`, `config/pipeline-stages.yaml` | T0-only orchestration | Allow nested orchestration where it simplifies |

## Sequence (each chunk: implement → test → proceed)

- [x] **C1 (2026-06-19, safe):** Correct the FALSE fact — superseded-banner on `agent-orchestration.md`
  top blockquote + pointer in `pattern-structure.md`. Keep single-level invariant text but mark it
  "over-conservative, relaxation pending this plan." Patterns/validator unchanged → all green.
- [ ] **C2 (TDD):** Update `test_orchestrator_tool_grants.py` to the new invariant (workers MAY declare
  `Agent` unless at depth 5). Red first, then it defines the target.
- [ ] **C3:** Rewrite `agent-orchestration.md` §1–§3, §10 + `pattern-structure.md` Tool Grants coherently.
- [ ] **C4:** Correct CLAUDE.md skill-at-T0 rationale; decide which workflows actually benefit from nesting
  (don't nest for nesting's sake — KISS; skill-at-T0 stays where it's already clean).
- [ ] **C5:** Pilot ONE workflow with nested dispatch A/B; prove real nested parallelism; full CI green.

## DECISION (2026-06-19, decided per KISS/YAGNI — resolves the C4 fork)

The relaxation is a **REFRAME, not a sweeping rewrite.** The hub **KEEPS single-level dispatch as its
default convention** — NOT because the platform forces it (it no longer does), but because it's simpler
(KISS) and no concrete hub workflow yet needs nesting (YAGNI, rule 21: adopt extensibility at the second
caller, not the first). Consequences that SHRINK the remaining cascade:
- **C2 (validator):** `test_orchestrator_tool_grants.py` assertions STAY — they now enforce a deliberate
  **hub convention**, not a platform limit. Only the test's rationale comments need a one-line update.
  No red-first rewrite; existing patterns (no `Agent` on workers) remain valid and green.
- **C3 (rule body):** reframe §1–§3/§10 prose from "platform-forced single-level" → "deliberately-chosen
  single-level convention; nesting ≤5 available and adopted per concrete need." Prose-only, no pattern churn.
- **C4 (CLAUDE.md):** correct the skill-at-T0 *rationale* (it's a choice now, not a platform constraint).
- **C5 (pilot):** deferred until a concrete workflow demonstrably benefits from nesting (YAGNI — may never fire).

This means the big-blast-radius fear was overstated: NO master-agent / workflow / `project-manager-agent`
needs to change. The remaining work is a coherent **prose reframe of 2 rules + CLAUDE.md + validator
comments** — still best done together in fresh context (so §1–§3/§10 stay internally consistent), but far
lower risk than "rewire the orchestration model."

## Guard rails
- **Don't nest for nesting's sake** — skill-at-T0 still works and is simpler for many flows. Nesting is
  now an OPTION; adopt it only where it removes a real T0-orchestration wart (`goal-anchored-decisions.md`).
- **5-level hard cap is real** — designs must not assume unlimited depth.
- Each chunk that edits a downstream-shipped pattern runs the FULL local CI before push
  (`feedback_pattern_edit_ci_checklist`).

## Log
- 2026-06-19 — Plan created (Phase 4.2 ratified). C1 done same turn.
