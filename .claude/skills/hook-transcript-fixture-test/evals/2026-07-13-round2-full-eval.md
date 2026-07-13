# Skill Evaluation — hook-transcript-fixture-test (full mode, ROUND 2)

Date: 2026-07-13
Evaluator: /skill-evaluator full (round-2 re-evaluation after D1-D6 fixes; evaluation arm
dispatched as an isolated sonnet subagent, supervised at T0 — the supervisor independently
re-verified the two verdict-driving claims against the SKILL.md text before accepting)
Skill version evaluated: 1.0.0 (post-round-1-fix state; version NOT bumped by the fixes)
Round-1 report: `2026-07-13-full-eval.md` (verdict FIX, defects D1-D6)
Method note: same as round 1 — trigger activation assessed by single-pass blind routing
judgment per query (borderlines flagged), not 3 live trials per query. Output evaluation
grounded in the REAL hook code (`turn-origin.sh` = sourced function taking `$1`;
`no-overask-guard.sh` = stdin-JSON via `input=$(cat)` + `jq`) and a live check that this
repo's actual `~/.claude/projects/` slug (`D--Abhay-VibeCoding-claude-best-practices`)
matches SKILL.md's stated derivation rule.

```
SKILL EVALUATION REPORT: hook-transcript-fixture-test
=====================================
Mode: full (re-evaluation)
Iteration: 2

PRE-FLIGHT (STEP 0)
  0.1 Registry sync:   N/A-PASS — hub-only skill; absence from registry/patterns.json is
                       expected (per round-1 finding and task instruction; not a defect)
  0.2 Frontmatter:     PASS — name/dir match; description now 502 chars (was 327), still
                       third-person verb-first; type workflow; 4 triggers (≥3);
                       version STILL "1.0.0" — six defect fixes landed with no version bump.
                       Noted as a SemVer-hygiene nit; skill is hub-only (outside the
                       registry/SemVer-gated core/ tree), so non-blocking
  0.3 Structure:       PASS — 0 code fences; STEP 1-5 cross-refs resolve; no dead skill/agent
                       refs; no placeholders. ONE internal inconsistency found between
                       STEP 2's documented-gap carve-out and STEP 4's blanket "every row
                       must have at least one passing fixture test" gate (see NEW DEFECTS)
  0.4 Self-update:     N/A — no references/ directory
  Claim spot-check:    ".claude/.enhance-misses.log" has exactly 430 lines (re-verified live
                       this round); preamble stats now carry "(as of 2026-07)" — but the
                       IDENTICAL stat pair is restated in MUST DO WITHOUT the vintage tag
                       (D5 residual)

SKILL NECESSITY
  Verdict: HIGH — carried forward from round 1 unchanged. The repo's own
  test_turn_origin_classifier.py still commits the exact anti-pattern the skill prevents.

TRIGGER EVALUATION
  Should-trigger:    10/10 activated (100%) — incl. 3 NEW D1-probe queries (symptom-shaped
                     hook-misfire prompts: "my stop hook keeps firing on slash commands",
                     "we keep breaking the enhance guard...") which round 1 flagged as the
                     conflict class; all now route here via the new description clause
  Should-not:        9/10 correctly ignored (same single borderline as round 1: webhook-
                     payload fixture-test query — unchanged, non-worsening)
  Cross-skill:       RESOLVED (was the round-1 FIX driver). Description now explicitly
                     names /systematic-debugging and /fix-loop with an ORDERING rule
                     ("use THIS ... not generic debugging; /systematic-debugging and
                     /fix-loop come after the fixture reproduces the misfire") — a concrete
                     tie-break, not vague shape-recitation (D1-EFFECTIVE: PASS)
  Signposting:       Reciprocal boundary in systematic-debugging/fix-loop still ABSENT
                     (verified: core/.claude/skills/systematic-debugging/SKILL.md names
                     /fix-loop but not this skill). Explicitly OPTIONAL per round 1 —
                     status-report only, not a re-open, non-blocking
  Rule overlap:      NONE — unchanged
  Regressions:       NONE — all 4 literal triggers and 9/10 should-nots resolve identically;
                     the added description clause only ADDS scope, no loosened conditions
  Trigger verdict:   PASS (up from FIX)

OUTPUT EVALUATION
  Scenarios:         5/5 PASS (up from 2 PASS / 3 PARTIAL)
    H1 turn-origin.sh slash shape:        PASS (was PARTIAL) — STEP 3 now opens "FIRST
                                          identify the target hook's ACTUAL I/O contract...
                                          Read the hook's own input handling before writing
                                          the harness"; correctly routes a sourced-function
                                          hook like turn-origin.sh (classify_turn "$1")
    H2 no-overask-guard machine-origin:   PASS (unchanged) — stdin-JSON contract guidance
                                          intact; STEP 3 addition is purely additive
    H3 final-submission vs mid-turn text: PASS (unchanged) — matrix row + MUST NOT DO rule
                                          both intact verbatim
    E1 brand-new hook, no live sessions:  PASS (was PARTIAL) — STEP 2 documented-gap rule:
                                          "recorded as a DOCUMENTED GAP: add a skipped test
                                          naming the missing shape and the capture condition
                                          — never hand-fabricate"; combined with generate-
                                          live path, every row now has a defined path
    E2 live false-positive (STEP 5):      PASS (was PARTIAL) — locate by session id (newest-
                                          JSONL fallback) + "excerpt the FULL turn — all
                                          entries belonging to that turn, not just the
                                          single line"; cross-entry scope operationally
                                          defined via STEP 1's two-user-entry slash row
  Stress test:       5/6 clean (0 CRITICAL, 1 MAJOR — NEW, 1 residual MINOR)
    Conflicting constraints:              PASS (unchanged)
    Partial prerequisite (dir absent):    PASS (was MAJOR) — "create the directory on
                                          first use" now explicit in STEP 2
    Ambiguous I/O contract:               PASS (was MAJOR) — STEP 3 contract-first clause;
                                          empirically verified against both real hooks
    Stale stats:                          MINOR residual — preamble vintaged "(as of
                                          2026-07)", MUST DO restates same figures
                                          unvintaged (D5 partially closed)
    Minimal input (hook path only):       PASS (unchanged) — STEP 1 matrix self-fills
    [NEW] STEP 2 vs STEP 4 contradiction: MAJOR — see NEW DEFECTS
  Baseline delta:    unchanged qualitative conclusion — with-skill catches both historical
                     bug classes the existing without-skill test provably misses
  Output verdict:    FIX (near-miss) — 5/5 scenarios pass; the single STEP 2/STEP 4
                     contradiction is the only blocker

REFERENCE SELF-UPDATE
  N/A — no references/ directory

MODEL COVERAGE
  Tested on:         sonnet (evaluation arm), single-pass analytic routing judgment for
                     triggers (flagged, same limitation as round 1); output eval grounded
                     in direct hook-code reads + live slug-directory check
  Divergent results: N/A

OVERALL VERDICT: FIX
Blocking issues: ONE — STEP 4's "every matrix row must have at least one passing fixture
test before the hook ships" is unreconciled with STEP 2's documented-gap carve-out (a
skipped test is not a passing test). One-line fix.
```

## D1-D6 CLOSURE STATUS

| # | Status | Evidence (current SKILL.md text) |
|---|---|---|
| D1 | **CLOSED** | Description (frontmatter) now names both competitors with an ordering rule: "when a guard hook misfires/false-positives, use THIS (capture the misfiring shape as a fixture first), not generic debugging; /systematic-debugging and /fix-loop come after the fixture reproduces the misfire." 3 new symptom-shaped probe queries all route here. Reciprocal signposting in those two skills remains absent — OPTIONAL per round 1, non-blocking. |
| D2 | **CLOSED** | STEP 3: "FIRST identify the target hook's ACTUAL I/O contract — hooks in one repo differ (some read JSON on stdin per the platform hook contract; some are sourced libraries taking function arguments; some read env vars). Read the hook's own input handling before writing the harness." Empirically verified against the two real hooks: `turn-origin.sh` = sourced function taking `$1`; `no-overask-guard.sh` = `input=$(cat)` + `jq` stdin JSON. |
| D3 | **CLOSED** | STEP 2: "create the directory on first use; or follow the project's existing fixture convention" + slug rule "`<project-dir>` is the project path with separators flattened to dashes, e.g. `D--Abhay-VibeCoding-myrepo`". Verified against the real directory `D--Abhay-VibeCoding-claude-best-practices` under `~/.claude/projects/` — pattern matches exactly (drive letter kept, colon dropped, backslashes→dashes). |
| D4 | **PARTIALLY CLOSED** | STEP 2's documented-gap rule is present exactly as prescribed ("recorded as a DOCUMENTED GAP: add a skipped test naming the missing shape and the capture condition — never hand-fabricate the fixture to fill the row"). But STEP 4 was NOT reconciled: it still reads "every matrix row must have at least one passing fixture test before the hook ships" — a skipped test is not a passing test, so the two steps now contradict. See NEW DEFECTS N1. |
| D5 | **PARTIALLY CLOSED** | Preamble stats now carry "(as of 2026-07)". MUST DO first bullet restates "430+ logged guard misses and ~13 fix commits" WITHOUT the vintage. Residual MINOR, non-blocking. |
| D6 | **CLOSED** | STEP 5: "Locate the session file by its session id under `~/.claude/projects/<project-dir>/` (the misfire report or hook log usually carries the id; otherwise take the newest JSONL there) and excerpt the FULL turn — all entries belonging to that turn, not just the single line that looks wrong, since misclassification usually spans adjacent entries." Both round-1 gaps (location + excerpt scope) closed. |

## NEW DEFECTS

| # | Defect | Severity | Fix |
|---|---|---|---|
| N1 | STEP 2's documented-gap carve-out (skipped test, never fabricate) contradicts STEP 4's unchanged blanket gate "every matrix row must have at least one passing fixture test before the hook ships." For any hook with a legitimately ungeneratable shape — the exact scenario D4 was fixed FOR — a letter-following agent either (a) falsely concludes it cannot ship, or (b) fabricates a fixture to satisfy STEP 4, the precise anti-pattern STEP 2 forbids. Introduced by fixing D4 in STEP 2 only. | MAJOR (sole blocker) | STEP 4: reconcile in one line, e.g. "every matrix row must have at least one passing fixture test — or a documented-gap skipped test per STEP 2 — before the hook ships; only an UN-documented missing fixture blocks shipping." |

No other new defects: no dangling cross-references, no unbalanced fences/lists, no scope
creep — all six edits are localized to their named sections. Previously-PASS items (H2, H3,
conflicting-constraints, minimal-input) re-verified intact, zero regressions.

## Re-eval criterion

Apply the N1 one-line STEP 4 reconciliation (and optionally the D5 vintage tag on the MUST DO
bullet — cheap, non-blocking; a version bump to 1.0.1 would also be good hygiene). Then
re-run `/skill-evaluator full` — expected PASS: trigger arm already passes, all 5 scenarios
pass, and N1 is the only stress-test MAJOR remaining.
