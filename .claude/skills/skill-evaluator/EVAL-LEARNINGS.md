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

---

## Skill #3: auto-verify (2026-04-02)

**Verdict:** FIX

**What evaluator caught:**
- High cross-skill conflict cluster with regression-test, test-pipeline, testing-pipeline-workflow on generic queries (6 of 10 should-trigger queries had MEDIUM or LOW activation)
- Hard dependency on `/regression-test` and `tester-agent` with no fallback (MAJOR portability risk)
- Missing `## CRITICAL RULES` section — pattern-structure.md violation
- `Edit` in allowed-tools unnecessary (skill only writes new JSON files)

**What evaluator missed (found manually):**
1. **Missing `triggers:` field entirely** — Not just insufficient triggers, but no triggers field at all. Evaluator's trigger eval (Step 2) generates queries but doesn't first check if the frontmatter field exists. Found during Step 0 registry sync.
2. **No handling for zero affected tests** — If `/regression-test` returns no mapped tests, skill had no explicit path. Evaluator's stress test caught "no arguments, no git changes" (PASS) but didn't distinguish "changes exist but no tests map to them."
3. **Stale test-results/ cleanup in standalone mode** — Pipeline mode cleans via test-pipeline-agent, but standalone invocation could read stale results from a previous run. Evaluator didn't check standalone vs pipeline mode differences.
4. **Registry description empty** — Same class of issue as Skills #1-2. Evaluator still doesn't check registry sync (pending batch apply).
5. **Registry changelog stale** — Only listed v2.0.0 but version is 3.0.0. Registry version/changelog consistency is a known gap.

**Proposed evaluator improvements (pending batch apply):**
- [ ] Add frontmatter field existence check: verify `triggers:` field is present before running trigger evaluation (not just testing trigger quality)
- [ ] Add standalone vs pipeline mode analysis: check if skill behaves differently in each mode and validate both paths
- [ ] Add zero-result path analysis: for skills that delegate to other skills, check what happens when the delegate returns empty/zero results

**Fixes applied to auto-verify:**
- Added `triggers:` list (8 entries) designed to minimize cross-skill conflicts
- Added `## CRITICAL RULES` section (7 rules) at end of file
- Added fallback for missing `/regression-test` (file-based test mapping)
- Added fallback for missing `tester-agent` (direct test execution)
- Added zero-test handling (skip Steps 2-3, write PASSED with warning)
- Added standalone cleanup for stale `test-results/auto-verify.json`
- Removed `Edit` from allowed-tools
- Updated description to clarify boundary with `/fix-loop` and `/test-pipeline`
- Synced registry: description, hash, version, dependencies, changelog
- Bumped version 3.0.0 → 3.1.0

---

## Skill #4: implement (2026-04-02)

**Verdict:** FIX

**What evaluator caught:**
- Missing triggers field — no `triggers:` in frontmatter
- High cross-skill conflict with development-loop, fix-issue, tdd on generic queries
- No empty-arguments guard — `$ARGUMENTS` could be empty with no handling
- No graceful degradation for projects without test frameworks
- CRITICAL RULES section existed but lacked MUST/MUST NOT language

**What evaluator missed (found manually):**
1. **Orphaned lines after Step 6.3** — Lines 111-112 were dangling numbered items ("4. If significant changes..." and "5. Summarize...") left over from a restructuring. Evaluator's structural checks don't detect orphaned numbered-list items between sections.
2. **Registry version mismatch** — Registry said v2.1.0 but SKILL.md had v1.0.0. File was edited but version field wasn't bumped. Evaluator still doesn't check registry sync (pending batch apply).
3. **Overlap with workflow.md rule** — The globally-loaded workflow rule describes a near-identical 7-step process. Evaluator doesn't compare skill content against auto-loaded rules for redundancy.

**Proposed evaluator improvements (pending batch apply):**
- [ ] Add orphaned numbered-list detection: scan for numbered items that appear between section headers without belonging to a list
- [ ] Add skill-vs-rule overlap check: compare skill steps against auto-loaded rules for redundancy
- [ ] (Carried from #1-3) Add registry sync, frontmatter field existence, zero-result path checks

**Fixes applied to implement:**
- Added `triggers:` list (8 entries)
- Added empty-arguments guard in preamble and CRITICAL RULES
- Added test-framework detection fallback in Step 2
- Fixed orphaned lines 111-112 → proper ### 6.4 Post-Fix Review sub-section
- Strengthened CRITICAL RULES with MUST/MUST NOT language (4 new rules)
- Added preamble constraints (tests mandatory, fix-loop delegation)
- Updated description to clarify boundary with /fix-issue, /tdd, /development-loop
- Synced registry: description, hash, version, dependencies, changelog
- Bumped version 1.0.0 → 2.2.0 (aligned with registry lineage)

---

## Skill #5: debugging-loop (2026-04-02)

**Verdict:** FIX

**What evaluator caught (would catch):**
- Missing `triggers:` field entirely — skill invisible to natural language invocation
- HIGH cross-skill conflict with systematic-debugging — descriptions nearly identical, both mention "root cause isolation," "verification," and handling unclear bugs
- No CRITICAL RULES section — pattern-structure.md violation

**What evaluator missed (found manually):**
1. **Near-duplicate resolution required architectural judgment** — Evaluator flags overlap but can't determine if a skill is a legitimate orchestrator wrapper vs a true duplicate. debugging-loop chains 4 skills via an agent; systematic-debugging is standalone. This distinction requires reading the agent file and understanding the orchestration architecture — beyond the evaluator's current scope.
2. **Registry dependencies empty** — Skill delegates to debugging-loop-master-agent and chains systematic-debugging, fix-loop, auto-verify, learn-n-improve, but registry had `dependencies: []`. Same class of issue as Skills #1-4 (pending batch apply).
3. **Registry hash stale** — File content changed but hash wasn't updated. Same class as prior skills.
4. **Missing bidirectional signposting** — systematic-debugging's description doesn't mention debugging-loop as the escalation path. Evaluator checks the target skill but not its neighbors' descriptions for reciprocal pointers.

**Proposed evaluator improvements (pending batch apply):**
- [ ] Add near-duplicate resolution guidance: when overlap is flagged, prompt evaluator to check if skill delegates to the neighbor (orchestrator pattern) vs reimplements it (true duplicate)
- [ ] Add bidirectional signposting check: when cross-skill conflict is detected, verify BOTH skills' descriptions mention the other with clear boundary language

**Fixes applied to debugging-loop:**
- Added `triggers:` list (8 entries) designed for full-cycle intent ("debug and fix", "resolve bug end to end") to avoid conflict with systematic-debugging's diagnosis-oriented triggers
- Rewrote description to clearly state orchestrator role and chain composition
- Added preamble constraint: "This is a full-cycle orchestrator, NOT a diagnosis-only tool"
- Added 2 MUST NOT rules: no diagnosis-only use, no skipping chain steps
- Synced registry: description, hash, version (1.0.0 → 1.1.0), dependencies (5 added), changelog
- Bumped version 1.0.0 → 1.1.0
