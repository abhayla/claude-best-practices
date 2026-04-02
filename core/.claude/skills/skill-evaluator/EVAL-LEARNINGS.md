# Skill Evaluator — Learnings Log

Accumulated learnings from evaluating real skills. Each entry records what the evaluator caught, what it missed, and proposed improvements. These learnings are reviewed periodically and batch-applied to the evaluator SKILL.md after sufficient evidence.

---

## Skill #1: fix-loop (2026-04-02)

**Verdict:** FIX

**What evaluator caught:**
- Missing `Agent` in allowed-tools — skill delegates to test-failure-analyzer-agent but can't invoke Agent tool (BLOCKING)
- Minor cross-skill conflict with systematic-debugging on ambiguous failure queries
- Stress test: 3 MINOR issues (oversized input handling, stale context, conflicting constraints)

**What evaluator missed (found manually):**
1. **Registry sync** — File has a 252-char description but registry has empty string. Evaluator has no step to compare file vs registry descriptions. Had to be told about this in the prompt.
2. **Missing `triggers:` field** — Found as "additional finding" but should be part of standard trigger evaluation since it directly affects activation.
3. **Missing dependency declaration** — Skill delegates to `test-failure-analyzer-agent` via Agent() but doesn't list it in registry `dependencies`. Evaluator doesn't audit dependency declarations.
4. **Changelog/version mismatch** — Registry changelog says "v2.0.0" but version field is "1.2.0". Data integrity issue.

**Proposed evaluator improvements (pending batch apply):**
- [ ] Add registry sync check to Step 1: compare file description vs registry description
- [ ] Add allowed-tools audit to Step 1: scan body for Agent()/Skill() calls, verify matching tools listed
- [ ] Add dependency audit to Step 1: scan body for agent/skill references, verify listed in registry dependencies
- [ ] Make missing `triggers:` field a standard check in Step 2 (trigger evaluation), not just an "additional finding"
- [ ] Add registry version/changelog consistency check

**Fixes applied to fix-loop:**
- Added `triggers:` list (6 entries)
- Added `Agent` to allowed-tools
- Bumped version 1.2.0 → 1.3.0
- Synced registry: added description, added dependency on test-failure-analyzer-agent, updated hash/version/changelog
