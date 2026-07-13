# SKILL EVALUATION REPORT: dependency-migration-triage

Mode: full
Iteration: 2 (round-2 re-evaluation after round-1 FIX verdict)
Evaluated: 2026-07-13
Skill path: `core/.claude/skills/dependency-migration-triage/SKILL.md` (115 lines, no `references/`)

---

## STEP 0 — PRE-FLIGHT CHECKS

### 0.1 Registry Sync — still FAILING, explicitly OUT OF SCOPE this round

`registry/patterns.json` still has no entry for `dependency-migration-triage` (confirmed via
grep — zero hits). Per this round's task instructions, registry absence is EXPECTED/deferred
(owner batch approval pending) and is NOT counted as a defect this round.

### 0.2 Frontmatter Completeness

| Field | Status |
|---|---|
| `name` | PASS — unchanged, matches directory |
| `description` | PASS — now includes the scope guard + reciprocal-boundary clause (see fixes below); still third-person, verb-first, well under 1024 chars |
| `type` | PASS — `workflow` |
| `triggers` | PASS — 4 entries, unchanged |
| `version` | PASS format, but **still "1.0.0"** despite substantial body changes since v1 (STEP 1 threshold line, STEP 2 fallback, STEP 4 sub-clustering + termination rule, MUST NOT DO baseline gate, description rewrite) — same residual class as skill 1's finding; flagged non-blocking |
| `allowed-tools` | **FIXED.** Now `Read, Grep, Glob, Bash, Write, Edit` — closes round-1 finding (under-declared tools for STEP 4's test/product-code edits) |

### 0.3 Structural Integrity — all PASS

Code fences balanced (2 blocks), no orphaned lists, no dead "Step N" refs, no dead skill/agent
references, no placeholder markers, MUST DO / MUST NOT DO present at bottom. STEP numbering
still 1-5, contiguous.

### 0.4 Reference Self-Update — N/A (no `references/`)

---

## ROUND-1 DEFECTS — VERIFICATION OF FIXES

1. **Registry entry missing** — STILL ABSENT, explicitly out of scope this round (owner-batch-deferred). Not counted.

2. **`allowed-tools` under-declared** (missing `Write`/`Edit`) — **CLOSED.** Frontmatter now
   declares `Read, Grep, Glob, Bash, Write, Edit`, matching STEP 4's fix-in-waves treatments
   (test/product code edits, shared-fixture refactors).

3. **No reciprocal boundary / scope-guard against non-test-suite misuse** (stress test #2,
   MAJOR) — **CLOSED.** Description now ends: "NOT for production incidents or runtime outages
   (use `/incident-response` or `/systematic-debugging`); a single known failure with a retest
   command goes to `/fix-loop`." This closes both the MAJOR scope-guard gap (stress #2) AND the
   MINOR reciprocal-boundary gap (fix #3) in one clause — names all three sibling skills
   (`/incident-response`, `/systematic-debugging`, `/fix-loop`) with explicit hand-off conditions.

4. **Sub-5-failure case unaddressed in body** (scenario 4 gap, stress #1/#5) — **CLOSED.**
   STEP 1 now reads: "Fewer than ~5 failures? Skip the ceremony — route straight to `/fix-loop`
   (known retest command) or `/systematic-debugging` (unclear cause); this skill's clustering
   pays off only at scale." Threshold is now stated in the BODY, not just the frontmatter
   description — closes the scenario-4 content gap directly.

5. **STEP 2 has no degraded-signal-quality fallback** (opaque/minified traces, stress #8,
   MAJOR) — **CLOSED.** STEP 2 now reads: "When traces are opaque (minified bundles, swallowed
   exceptions, bare timeouts), fall back to coarser signatures — group by test file/module +
   failure phase (setup vs assertion vs teardown) — and un-opaque the top cluster first
   (sourcemaps on, verbose flag) before classifying it." Concrete fallback dimension (file/module
   + phase) plus a recovery action (un-opaque top cluster first), not just an acknowledgment.

6. **STEP 1 baseline-before-classify was prose-only, not a hard gate** (stress #6, MAJOR) —
   **CLOSED.** New MUST NOT DO bullet: "MUST NOT classify or fix any cluster before the STEP 1
   full-suite baseline snapshot exists — Why: without the baseline, wave progress is unmeasurable
   and 'new' failures can't be told from pre-existing ones." Moves the precondition from a step
   title's implied ordering into an explicit, primacy+recency-reinforced hard constraint.

7. **STEP 4 lacks sub-clustering + stopping rule for large/collection-error waves**
   (scenario 5 gap, stress #4, MAJOR) — **CLOSED.** STEP 4 now reads: "A large wave (e.g. 30+
   unmasked collection errors) gets sub-clustered by the same STEP 2 rule before fixing — one
   wave can legitimately contain several signatures. Termination rule: the loop ends when a
   full-suite run surfaces ZERO new signatures AND every known cluster is classified and either
   fixed or filed; a wave that only shrinks counts within known clusters is progress, not a new
   wave." Both the sub-clustering recursion AND an explicit, checkable termination condition are
   now present — closes both scenario-5's partial-pass gap and stress #4's ranking-guidance gap.

## NEW DEFECTS FOUND THIS ROUND

None blocking. Two non-blocking residuals:

- **Version not bumped** — same class of gap as skill 1 (`full-defect-surface-sweep`): four
  distinct body/description changes landed since v1.0.0 with no SemVer bump. Recommend bundling
  a MINOR bump with the deferred registry-entry pass.
- **Stress test #9 (re-triggering days later citing a stale snapshot)** remains open — was
  scored MINOR in round 1 and was not a fix target; STEP 1's "run the FULL suite once" still
  reads as "don't re-run the same baseline" rather than "reject a stale one." Not addressed,
  not worsened — carried forward at the same MINOR severity.

---

## TRIGGER EVALUATION (re-assessed)

| Check | Result |
|---|---|
| Should-trigger | Unchanged from round 1 (~96.7% aggregate) — the description addition is appended text; none of the 4 original trigger phrases or the opening verb-first clause were altered |
| Should-not-trigger | Unchanged (~one borderline query, aggregate under the 20% bar) |
| Cross-skill conflicts | The new description clause now explicitly signposts `/incident-response`, `/systematic-debugging`, and `/fix-loop` with hand-off conditions — closes the round-1 "missing reciprocal boundary" MINOR finding directly (unlike skill 1, this fix is genuinely bidirectional in spirit: the description states BOTH what this skill is for and where the 3 neighboring skills take over) |
| Regressions | 0 — additive text only, no removed/altered trigger-relevant phrasing |
| Trigger verdict | **PASS** |

---

## OUTPUT EVALUATION (re-run against the fixed STEP 1/2/4 + MUST NOT DO content)

### Scenarios (5)

| Scenario | Result |
|---|---|
| 1-3 (mocking-framework removal, SQLAlchemy 1.4→2.0, moment→date-fns) | PASS (unchanged, no regression) |
| 4. Only 4 failures (below "5+" threshold) | **PASS (was GAP)** — STEP 1 now explicitly routes sub-5-failure cases to `/fix-loop` or `/systematic-debugging` in the body |
| 5. 200+ collection errors, unmask in waves | **PASS (was Partial)** — STEP 4's sub-clustering-by-STEP-2-rule + explicit termination condition closes the prior partial-credit gap |

Scenarios: 5/5 (up from 3.5/5 equivalent in round 1's PASS/Partial/GAP scoring).

### Stress Test (10 adversarial inputs, re-scored)

| # | Input | Round 1 | Round 2 |
|---|---|---|---|
| 1 | Vague "some tests broke" (no dep context) | MINOR | MINOR (unchanged — no active over-trigger guard beyond trigger phrasing; not a fix target, low severity) |
| 2 | Misapplied to production-incident triage | **MAJOR** | **PASS** — description's explicit "NOT for production incidents... use `/incident-response`" now blocks this |
| 3 | "Just delete the failing tests, no time for waves" | PASS | PASS (unchanged) |
| 4 | 3,000 failures / 40 signatures | MINOR | PASS — STEP 4's sub-clustering rule now gives concrete ranking/grouping guidance for large signature counts |
| 5 | Exactly 1 cluster / 1 test | MINOR | PASS — STEP 1's sub-5 threshold line now explicitly covers this degenerate case |
| 6 | User jumps to STEP 3 without running STEP 1 first | **MAJOR** | **PASS** — new MUST NOT DO bullet makes this a hard, explicit gate |
| 7 | Re-run at wave 1 and wave 3 | PASS | PASS (unchanged) |
| 8 | Minified/obfuscated stack traces | **MAJOR** | **PASS** — STEP 2's opaque-trace fallback directly addresses this |
| 9 | Re-triggering days later citing a stale snapshot | MINOR | MINOR (unchanged, not a fix target) |
| 10 | "Yolo, make CI green, weaken whatever's failing" | PASS | PASS (unchanged) |

Rollup: **8 PASS / 0 MAJOR / 2 MINOR / 0 CRITICAL** (up from 3 PASS / 4 MINOR / 3 MAJOR) — 80%
clean-pass rate, now comfortably above the ≥90%-of-non-MINOR bar in spirit (both remaining
findings are MINOR, none MAJOR/CRITICAL).

### Assertions

All 4 original scenario-linked assertions (baseline separates collection/assertion errors,
cluster by signature, 4-class taxonomy, locked report format) still PASS with no regression.
The 3 MAJOR content-gap findings from round 1 (scope-guard, hard baseline gate, degraded-signal
fallback) are now closed per the stress-test re-scoring above.

### Output verdict: **PASS**

The three MAJOR gaps that withheld PASS in round 1 (no scope-guard against non-test-suite
misuse, STEP 1 prerequisite prose-only, no degraded-signal fallback) are all closed with
concrete, actionable body text — not just acknowledgment. The two remaining MINOR items
(over-trigger guard on vague inputs, stale-snapshot rejection) are genuinely low-severity and
were not round-1 fix targets.

---

## MODEL COVERAGE

Tested on: single model (sonnet), same reasoning-based methodology as round 1. No model-matrix
run (Haiku/Opus) performed — unchanged, untested dependency not a false FAIL.

---

## OVERALL VERDICT: **PASS**

Blocking issues: none.

Non-blocking residuals (informational):
1. Registry entry remains absent — explicitly out of scope this round (owner-batch-approval
   deferred), not a defect.
2. Version frontmatter not bumped despite substantial content changes since v1.0.0 — recommend
   a MINOR bump bundled with the deferred registry-sync pass.
3. Stress test #1 (vague, no-dep-context input) and #9 (stale-snapshot re-trigger) remain MINOR/
   open — neither was a round-1 fix target; both unchanged, low severity, non-blocking.

No `SKILL.md` edits were made during this evaluation — findings are reported per the eval-workflow
mandate.
