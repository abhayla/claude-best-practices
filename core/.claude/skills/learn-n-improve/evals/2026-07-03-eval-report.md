# Eval Report — learn-n-improve v2.5.0 (success-pattern capture extension)

Date: 2026-07-03
Change under test: plan item 4.1 of `plans/loop-engineering-adoption.md` — extend
`/learn-n-improve` to capture SUCCESS PATTERNS (what worked + when to reuse it) alongside the
existing failure-lesson (error→fix→lesson) capture. Mode: `output`/`trigger` combined mini-eval
(targeted, per eval-coverage touch-trigger) — full `/skill-evaluator full` not run; this report
substitutes a literal trace against the updated `SKILL.md` text for the 6 cases below.

## Method

Each case is traced literally against `core/.claude/skills/learn-n-improve/SKILL.md` v2.5.0 —
citing the exact STEP/section that governs the expected behavior, not a simulated model run.

## Matrix

### 1. Success-capture — GENERIC success pattern (loop-engineering preflight win)

**Scenario:** A loop-engineering pilot run (e.g. noter-app) completes cleanly (1 cycle, 0 heals)
because the run adopted "list the live agent registry before dispatching a named worker" as a
preflight probe, instead of trusting file-existence on disk.

**Expected:** Session-mode capture recognizes this as a Success Pattern signal (STEP 2 new row:
"A verified approach/tool/sequence that clearly outperformed the alternative … Record what
worked + when to reuse it (STEP 3.5)"), records it under `success_patterns` in
`.claude/learnings.json` (STEP 3.5), and types it `GENERIC` — the registry-listing-preflight
technique is a Claude-Code dispatch craft lesson, true regardless of the product (per
`learnings-routing.md`'s GENERIC/PRODUCT-SPECIFIC test: "true regardless of *this* product").

**Traced result:** PASS. STEP 3.5's worked example is literally this scenario (the
`hub_pattern_link: "pattern-structure"` example entry cites the noter-app pilot and types itself
`GENERIC`). STEP 2's new decision-table row and the "Capture triggers" note both route a
clean/zero-heal pilot run into STEP 3.5. The schema table's `type` field definition explicitly
requires classification "per `learnings-routing.md` BEFORE filing."

### 2. Success-capture — PRODUCT-SPECIFIC success pattern (domain-specific win)

**Scenario:** A project discovers that its specific tax-calculation module's ordering of
deduction application (apply Section-80C before HRA) avoids a rounding-cascade bug particular to
that project's schema — a win, but true only for this codebase's domain, not for Claude Code
craft in general.

**Expected:** Captured as a Success Pattern (STEP 3.5) but typed `PRODUCT-SPECIFIC`, and per the
"Typing and routing" subsection, NOT proposed as a `hub_pattern_link` — "PRODUCT-SPECIFIC success
patterns are recorded here for this project's own reuse but MUST NOT be proposed as a hub pattern
link."

**Traced result:** PASS. The schema's `type` field and the "Typing and routing" step 1 explicitly
branch on this: GENERIC entries are eligible for Hub Pattern Linkage suggestion; PRODUCT-SPECIFIC
entries are explicitly excluded from that flow. This mirrors `learnings-routing.md`'s "MUST NOT
write a product-specific learning into a generic/distributable pattern" — the skill routes
correctly rather than defaulting every success into a hub-shareable pattern.

### 3. Success-capture — reuse_count promotion to active constraint (STEP 5.5 extension)

**Scenario:** The same GENERIC success pattern from Case 1 (registry-listing preflight) recurs a
second time in a later session on a different pipeline, so its `reuse_count` increments from 0
to 2.

**Expected:** STEP 5.5's trigger ("Only activates when a learning OR a success pattern has
`reuse_count >= 2`") fires for the success pattern, mapping it to a target skill (e.g.
`test-pipeline` or `loop-engineering`, wherever agent dispatch happens) and drafting a
constraint-injection proposal identical in form to a failure-lesson's, subject to the same
explicit-approval batch gate (STEP 5.5.3) — a proven win becomes a positive constraint
("prefer X because...") only with user sign-off, never auto-applied.

**Traced result:** PASS. STEP 5.5's trigger line and STEP 5.5.1 heading were both updated to
"learning OR a success pattern"; the eligibility bash snippet now scans both `learnings` and
`success_patterns` arrays and reports a combined count. STEP 3.5's "Reuse count feeds STEP 5.5"
paragraph makes the cross-reference explicit rather than leaving it implicit. The approval gate
(STEP 5.5.3, unchanged) still applies without exception — no separate looser path was introduced
for success patterns, consistent with the CRITICAL RULES' unchanged "MUST NOT inject constraints
into skills without explicit user approval."

### 4. Failure-lesson regression — existing error→fix→lesson capture unchanged

**Scenario:** A session hits a `TypeError` on a None ORM result, fixes it with a null guard, and
the test suite goes from FAILED to PASSED.

**Expected:** Unchanged STEP 2 row ("test-results `PASSED` after prior `FAILED`" → **Fix
Success** → STEP 3) and unchanged STEP 3 error→fix→lesson triple recorded under `learnings`
(NOT `success_patterns`) with the pre-existing schema (`error`, `fix`, `lesson`, `tags`,
`reuse_count`, `hub_pattern_link`).

**Traced result:** PASS — no regression. STEP 3's JSON example, field list, and Hub Pattern
Linkage subsection are byte-for-byte unchanged from v2.4.0. The STEP 2 decision table's
pre-existing "Fix Success" row is preserved verbatim (only its label was clarified from
"Success" to "Fix Success" for disambiguation against the new "Success Pattern" row) and still
routes to STEP 3, not STEP 3.5. `.claude/learnings.json`'s existing `learnings` array is
untouched — the change purely ADDS a sibling `success_patterns` array (STEP 4's table shows
`.claude/learnings.json` now covers "Structured error→fix→lesson database (Step 3) +
success-pattern database (Step 3.5)" — additive, not a schema rewrite).

### 5. Failure-lesson regression — reuse_count / dedup discipline unchanged for failures

**Scenario:** A second occurrence of the same `TypeError` (Case 4) happens in a later session.

**Expected:** STEP 3's existing dedup flow — "Search existing learnings for similar errors …
If similar learning exists, increment `reuse_count`" — fires exactly as before, independent of
the new STEP 3.5 success-pattern dedup logic (which operates on a separate array with its own
search).

**Traced result:** PASS — no regression. STEP 3's four-item dedup/tagging procedure is unedited.
STEP 3.5's "Dedup first" instruction explicitly scopes itself to `success_patterns` ("Search
`success_patterns` for a similar `attempted`/`worked` pair … same discipline as STEP 3") —
it describes an analogous but separately-scoped process, not a shared search that could
cross-contaminate the two arrays or double-count reuse.

### 6. Non-trigger neighbor — session close with no learning to capture (vs `/end-session`)

**Scenario:** The user says "wrap up the session" at the end of a turn with no new failures,
fixes, or notable successes — just routine, unremarkable work.

**Expected:** This does NOT trigger `/learn-n-improve` — it triggers `/end-session` instead (a
session save/checkpoint, not a learning-capture pass). Per the frontmatter description ("For
one-off session saves, use `/end-session`") and the triggers list (none of which match "wrap up
the session" — the closest, "session reflection", implies deliberate analysis of what was
learned, not a routine close), this skill should NOT fire.

**Traced result:** PASS — correctly a non-trigger, and unaffected by this change. The
frontmatter's pointer to `/end-session` for "one-off session saves" is unchanged. The new
triggers added in this revision ("capture what worked", "record a success pattern") are
narrowly worded to require an explicit success-capture intent, not a generic session-close
phrase — so the new triggers do not widen the skill's surface into `/end-session`'s territory.
Also confirms STEP 2's new decision-table rows require a **verified** success signal (test
PASSED with no prior failure, or a verified outperforming approach) — a routine, unremarkable
session with nothing to evaluate produces no matching row, so even if the skill were invoked
directly, STEP 2 would correctly find zero signals to capture.

## Verdict

| # | Case | Result |
|---|---|---|
| 1 | Success-capture, GENERIC | PASS |
| 2 | Success-capture, PRODUCT-SPECIFIC | PASS |
| 3 | Success-capture, reuse_count promotion (STEP 5.5) | PASS |
| 4 | Failure-lesson regression, STEP 3 capture unchanged | PASS |
| 5 | Failure-lesson regression, dedup/reuse_count unchanged | PASS |
| 6 | Non-trigger neighbor vs `/end-session` | PASS |

**6/6 PASS.** No regressions to the existing error→fix→lesson pathway; the new success-pattern
pathway is additive, correctly typed per `learnings-routing.md`, correctly scoped to its own
array, and correctly wired into the existing STEP 5.5 constraint-injection and STEP 6 reporting
without loosening the approval gate.

## Notes / limitations

- This is a targeted/literal trace, not a live multi-turn model run against the skill (per the
  "mini-eval, targeted" instruction for this touch-trigger) — it verifies the skill TEXT routes
  each case correctly, not that a live agent invocation produces byte-identical output.
- Full `/skill-evaluator full core/.claude/skills/learn-n-improve` (trigger + output + conflicts,
  with `--baseline`) was not run for this change; recommend running it before the next
  MAJOR/MINOR bump to this skill if drift is suspected.
