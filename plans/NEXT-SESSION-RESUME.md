# Next-Session Resume Prompt

Copy-paste the block below to start the next session.

---

Resume the **Platform Migration & Futuristic Goal (2026 H2)** initiative on the claude-best-practices hub.

**First, read these in order (do not skip):**
1. `.remember/remember.md` — current state (auto-surfaced at session start)
2. `plans/platform-migration-2026H2.md` — the SSOT roadmap + Phase 0 migration ledger
3. `plans/skill-at-t0-doctrine-relaxation.md` — the active Phase 4.2 cascade + the C4 KISS decision
4. `.claude/tasks/lessons.md` — the 2026-06-19 lessons (read the top 3 entries)
5. GitHub epic: run `gh issue view 119`

**Where we are:** Last session (branch `chore/platform-migration-2026h2-tracking`, PR #120, 7 commits) we
ratified the futuristic goal (README #4), built drop-proof tracking, completed the Phase 0 audit, resolved
Phase 1.3 no-churn, wired Phase 5.1a self-updating, and shipped **Phase 4.2 C1** — corrected the now-false
"subagents can't nest" claim (nested subagents are **GA in Claude Code v2.1.172, ≤5 levels**). The C4 design
fork is decided: **keep single-level dispatch as a deliberate KISS convention; nesting is available, adopted
only per concrete need (YAGNI).**

**Pick up here — Phase 4.2 C2–C4** (test-gated, one chunk at a time, in this fresh context):
- Reframe the prose in `agent-orchestration.md` §1–§3/§10 + `pattern-structure.md` Tool Grants + CLAUDE.md
  "Workflow Orchestration (skill-at-T0)" rationale: from "single-level is platform-forced" → "single-level is
  our deliberate KISS convention; nested dispatch ≤5 levels is available and adopted per concrete need."
- Keep the validator assertions (`test_orchestrator_tool_grants.py`) AS-IS (they now enforce a convention,
  not a platform limit) — only update their rationale comments. No master-agent / workflow / project-manager
  -agent needs to change.
- Before push: run FULL local CI (the 4 commands in CLAUDE.md) AND resync `registry/patterns.json` hashes for
  any edited rule (bump version + changelog), per the pattern-edit checklist. Confirm the registry diff is
  minimal (round-trips with `json.dumps(d, indent=2, ensure_ascii=False)`).
- Then ask me (Abhay) to sign off on the **6 RETIREs** + any **downstream MIGRATEs** before deleting/changing
  any downstream-shipped pattern.

**Apply these learnings (from lessons.md):**
- Render the FULL prompt-auto-enhance card on EVERY substantive turn, including continuations/background
  completions (the hooks blocked the last session 5+ times for skipping it).
- Verify each MIGRATE against the live pattern + official docs before spending effort — the Phase-0 audit
  over-claimed; several "migrations" were already-adopted or marginal. Don't churn (KISS/YAGNI).
- There is a **pending hook-tweak proposal** in lessons.md (needs my approval): a `*Session-boundary:*`
  exemption for `no-overask-guard.sh`. Remind me to approve/reject it.

Start at Phase 4.2 C2.

---
