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

---

## Skill #6: fix-issue (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Empty registry description (Priority 1 auto-pick signal)
- Missing `triggers:` field
- Registry version mismatch (registry: 2.0.0, file: 1.0.0)
- Empty dependencies despite referencing fix-loop and post-fix-pipeline
- Empty tags in registry
- Weak CRITICAL RULES (no MUST/MUST NOT language)
- Missing preamble constraints

**What evaluator missed:**
- No new evaluator gaps found — Step 0 pre-flight checks caught everything. First skill where v2.0 evaluator had complete coverage on structural issues.

**Proposed evaluator improvements:** None — v2.0 Step 0 was sufficient.

**Fixes applied to fix-issue:**
- Added `triggers:` list (8 entries) targeting "fix issue" intent
- Added preamble constraints (gh CLI requirement, empty args guard, fix-loop delegation)
- Strengthened CRITICAL RULES with MUST/MUST NOT language (7 rules)
- Updated description to differentiate from /implement and /fix-loop
- Synced registry: description, hash, version (1.0.0 → 2.1.0), dependencies, tags, changelog
- Bumped version 1.0.0 → 2.1.0 (aligned with registry 2.0.0 lineage)

---

## Skill #7: learn-n-improve (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Empty registry description
- Hash stale (file changed since last registry update)
- Changelog incomplete (missing v2.2.0 and v2.3.0 entries)
- Missing `triggers:` field
- Missing preamble constraints
- RULES section used weak language ("Never" instead of MUST NOT) for first 4 rules

**What evaluator missed:**
- No new gaps — v2.0 Step 0 complete coverage again (2nd consecutive skill).

**Proposed evaluator improvements:** None.

**Fixes applied to learn-n-improve:**
- Added `triggers:` list (8 entries) for learning capture intent
- Added preamble constraints (no skill injection without approval, test-run read-only, empty args default)
- Renamed RULES to CRITICAL RULES, strengthened all rules to MUST/MUST NOT
- Added empty-args default behavior rule
- Differentiated from /save-session and /handover in description
- Synced registry: description, hash, tags, changelog

---

## Skill #8: development-loop (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Hash stale
- Missing `triggers:` field
- Empty dependencies (6 skills/agents referenced but none declared)

**What evaluator missed:**
- No new gaps — 3rd consecutive skill with zero new evaluator improvements.

**Proposed evaluator improvements:** None — **stopping criteria met** (3 consecutive skills without new learnings).

**Fixes applied to development-loop:**
- Added `triggers:` list (8 entries) for full-cycle development intent
- Differentiated description from /fix-issue, /debugging-loop, /implement
- Synced registry: description, hash, version (1.0.0 → 1.1.0), 6 dependencies, changelog

---

## Skill #9: post-fix-pipeline (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Empty registry description, stale hash, empty deps/tags, changelog gap
- Missing `triggers:`, missing preamble, missing CRITICAL RULES section

**What evaluator missed:** None.

**Fixes applied:**
- Added 6 triggers, preamble constraint, 6 CRITICAL RULES
- Differentiated from /auto-verify and /test-pipeline in description
- Synced registry: description, hash, dependencies (2), tags, changelog

---

## Skill #10: test-pipeline (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Registry missing description, tags, and changelog fields entirely (not just empty — absent)
- Hash stale, dependencies empty
- Missing preamble constraints
- Near-duplicate check flagged testing-pipeline-workflow (different scope — broader TDD chain vs thin agent wrapper)

**What evaluator missed:** None.

**Fixes applied:**
- Added preamble constraint (delegates to agent, differentiate from /testing-pipeline-workflow and /auto-verify)
- Synced registry: description, hash, 4 dependencies, tags, changelog
- Note: triggers already present (6 entries) — no trigger fix needed

---

## Skill #11: code-review-workflow (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Hash stale, missing triggers, empty dependencies

**What evaluator missed:** None.

**Fixes applied:**
- Added 6 triggers for code review intent
- Differentiated from /review-gate and /request-code-review in description
- Synced registry: hash, version 1.0.0→1.1.0, 4 dependencies, changelog

---

## Skill #12: tdd (2026-04-02)

**Verdict:** FIX (registry only)

**What evaluator v2.0 Step 0 caught:**
- Hash stale, version mismatch (registry 1.0.0 vs file 1.0.1), empty tags
- Registry description exists but could be more specific

**What evaluator missed:** None.

**Fixes applied:**
- Registry-only fix: hash, version, description, tags, changelog
- SKILL.md unchanged — already has triggers, preamble, strong MUST DO/MUST NOT DO

---

## Batch Registry Sync (2026-04-02)

**Scope:** All 225 patterns (skills, agents, rules, hooks)

After evaluating 12 skills individually, the remaining 133 skills + 60 agents/rules/hooks had stale registry metadata. Applied automated batch fix:
- Synced hashes from actual file contents
- Populated empty descriptions from SKILL.md frontmatter
- Generated tags from pattern names and types
- Updated last_updated timestamps

This batch fix addresses the mechanical registry drift that was the most common issue across all 12 individually evaluated skills. The structural fixes (triggers, preamble, CRITICAL RULES) still require per-skill evaluation.

---

## Skill #13: continue (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Missing triggers, version mismatch (registry 2.1.0 vs file 1.1.0), weak RULES section, missing preamble

**What evaluator missed:** None.

**Fixes applied:**
- Added 6 triggers for session resumption intent
- Added preamble differentiating from /start-session and /handover
- Strengthened RULES to CRITICAL RULES with MUST/MUST NOT
- Fixed registry version to match file (1.1.0)

---

## Skill #14: save-session (2026-04-02)

**Verdict:** FIX

**What evaluator v2.0 Step 0 caught:**
- Missing triggers, version mismatch (registry 1.0.0 vs file 1.1.0)

**What evaluator missed:** None. CRITICAL RULES already strong (9 rules with MUST/MUST NOT).

**Fixes applied:**
- Added 6 triggers for session save intent
- Fixed registry version to match file (1.1.0)
