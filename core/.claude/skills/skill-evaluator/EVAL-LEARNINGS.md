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

---

## Skill #2: systematic-debugging (2026-04-02)

**Verdict:** FIX

**What evaluator caught:**
- Trigger coverage gaps: 4/10 realistic queries would miss (crash, broken, investigate, intermittent)
- `debug` trigger too broad: false positives on "debug logging", "debug mode", "remove debug"
- Cross-skill conflict zone with fix-loop: boundary unclear in description
- Steps 3, 5, 6 have zero inline content — completely empty without references

**What evaluator missed (found manually):**
1. **Orphaned code blocks** — Two broken markdown artifacts at lines 74-76 and 390-395 from reference extraction. Opening code fences were in reference files, closing fences remained in SKILL.md. Evaluator's structural checks don't scan for orphaned code fences.
2. **Wrong step cross-reference** — Step 0.3 says "Step 8 will capture it as a new learning" but learning capture is Step 9. Evaluator doesn't validate internal step cross-references.
3. **Nonexistent skill reference** — `/android-emulator-testing` mentioned in Step 9 but doesn't exist in catalog. Evaluator doesn't cross-reference skill names against the installed skill catalog.
4. **Missing preamble constraints** — Per pattern-structure.md, critical constraints should be at TOP and BOTTOM. Only bottom was covered.

**Proposed evaluator improvements (pending batch apply):**
- [ ] Add orphaned code fence detection: scan for closing ``` without matching opening ``` in the same section
- [ ] Add step cross-reference validation: verify "Step N" references point to actual step numbers
- [ ] Add skill name cross-reference check: verify `/skill-name` references exist in installed skills
- [ ] Add preamble constraint check: verify critical constraints appear in both preamble AND MUST DO/CRITICAL RULES sections

**Fixes applied to systematic-debugging:**
- Removed `debug` trigger (too broad), added 4 targeted triggers: `investigate bug`, `find root cause`, `unexpected behavior`, `intermittent failure`
- Fixed 2 orphaned code blocks from reference extraction
- Fixed step reference: "Step 8" → "Step 9"
- Added inline summaries for Steps 3, 5, 6 (were completely empty)
- Added critical constraints preamble (fix-loop escalation boundary)
- Removed nonexistent `/android-emulator-testing` reference
- Synced registry: description, hash, version, dependency, changelog
- Bumped version 1.0.0 → 1.1.0
