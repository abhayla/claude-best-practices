# Skill Evaluation Report — loop-engineering (2026-07-02)

Evaluated per `.claude/skills/skill-evaluator/SKILL.md` v2.3.0 (full mode) and
`EVAL-WORKFLOW.md`, executing plans/loop-engineering-adoption.md item 1.3.
**Scope honesty:** no live autonomous loop was executed (that is Phase 2's pilot).
Trigger reliability was measured with 3 independent context-blind subagent runs;
output quality was judged by walking the skill text against
`docs/specs/loop-engineering-spec.md` plus an independent adversarial text review
(fresh-context subagent), with every finding re-verified against the text before
scoring (supervisor gate). Tested as text; model coverage: sonnet x2 + haiku x1
for triggers, sonnet for the adversarial review.

```
SKILL EVALUATION REPORT: loop-engineering
=====================================
Mode: full (text-executability adaptation — no live loop run)
Iteration: 1

SKILL NECESSITY
  Without skill: an ad-hoc "run autonomously" session has no maker/checker split,
  no budgets, no preflight closure gate, no hub-ward telemetry (analytical
  baseline — not live-run). With skill: all four are specified.
  Delta: adds clear value — the skill should exist.

PRE-FLIGHT (STEP 0)
  0.1 Registry sync:   PASS — hash MATCH (normalized abd2260…), version 1.1.0
                       consistent (frontmatter = registry = changelog),
                       description semantically matched, all 11 dispatched
                       skills/agents present in `dependencies`.
                       Minor: advisory refs /update-practices,
                       /code-review-workflow not listed (not dispatched — OK);
                       /goal referenced in description but exists nowhere.
  0.2 Frontmatter:     PASS — name matches dir; desc 834/1024 chars, third
                       person, verb-first, states what AND when; type workflow;
                       allowed-tools = standard T0-orchestrator set; SemVer OK.
                       Minor: 7 triggers (workflow band is 3–6).
  0.3 Structural:      PASS — 28 fences (balanced), STEPs 1→8 contiguous with
                       no dead step refs, no placeholders, no vague language
                       (one grep hit was a false positive inside "en-try to"),
                       constraints in BOTH preamble and CRITICAL RULES,
                       390 lines (<500). Minor: `/goal` is a dead skill ref;
                       `/loop` exists only as a host-level plugin, not in core.
  0.4 Self-update:     N/A — skill has no references/ directory.

TRIGGER EVALUATION
  Should-trigger:    10/10 activated (100% — 30/30 across 3 blind runs)
  Should-not:        10/10 correctly ignored (0/30 misfires)
  Cross-skill:       0 conflicts vs development-loop, debugging-loop, fix-loop,
                     systematic-debugging, /loop (interval runner), ralph-loop
  Regressions:       N/A (no --baseline)
  Fresh validation:  N/A (no description optimization was needed)
  Trigger verdict:   PASS
  Evidence: evals/trigger-queries.json (full query set + per-run routings).
  Ecosystem note (fix belongs in the NEIGHBORS, not this skill): boundary
  signposting is one-directional — loop-engineering names /development-loop,
  /debugging-loop, /fix-loop, but none of those three mention the meta-loop
  back ("missing reciprocal boundary" per evaluator 2.3).

OUTPUT EVALUATION (text executability vs spec)
  Scenarios:         core DAG walk — 1 CRITICAL, 5 MAJOR, 6 MINOR (below)
  Stress test:       70% (7/10 clean; 0 CRIT, 0 MAJOR, 3 MINOR: --max-cycles 0
                     edge undefined; prior-run state.json silently overwritten
                     on re-invocation; unfetchable issue-URL input unhandled)
  Assertions:        maker≠checker asserted and enforceable via the contracts
                     config read (see F6); budgets/termination arithmetic
                     consistent — no defined path loops without incrementing a
                     budget; PREFLIGHT block path complete except the probe
                     mechanism (F5)
  Baseline delta:    N/A (no live runs)
  Output verdict:    FAIL (1 CRITICAL on the default path)

MODEL COVERAGE
  Tested on:         text-eval; trigger runs on sonnet x2 + haiku x1 (identical
                     results); adversarial review on sonnet
  Divergent results: none

OVERALL VERDICT: FAIL
Blocking issues: F1 (worktree changes never integrated before VERIFY/SHIP).
Remediation is TARGETED TEXT EDITS (≈6–8 edits), not a redesign — the loop
skeleton, budgets, preflight intent, telemetry design, and trigger surface are
all sound. Re-run this eval after fixes.
```

## Findings (verified against the text; severity per evaluator 3.4 scale)

### CRITICAL

- **F1 — Maker worktree output is never integrated back before VERIFY/SHIP.**
  STEP 4 dispatches the maker with `isolation="worktree"` ("Commit after each
  task"), but STEP 5's mechanical gate (`Skill("/auto-verify")` runs inline at
  T0), the supervisor reproduction ("re-run the test/lint command itself"),
  and STEP 6's `Skill("/post-fix-pipeline")` commit all execute against the T0
  working tree. No merge/apply/checkout-branch step exists anywhere in skill or
  spec. As written, a literal executor verifies an unchanged tree (false green
  or false red) and SHIP commits nothing — the maker's work is stranded in the
  worktree. Fix: add an explicit integration sub-step between STEP 4 and STEP 5
  (merge/cherry-pick the maker's worktree branch into the run branch, or run
  VERIFY inside the worktree and ship from it), and state which tree every
  later step operates on.

### MAJOR

- **F2 — `shipped` telemetry can be double-emitted.** The Monitoring emit-points
  list places the emit at "STEP 6 SHIP … (in addition to STEP 7 LEARN)" while
  STEP 7's body says "Then directly `emit_signal("shipped", …)`". STEP 6's PASS
  text contains no emit, so the two passages conflict and a literal executor
  obeying both writes two `shipped` entries per unit — inflating the exact
  effectiveness metric spec §5.1 exists to keep honest. Fix: one emit site.
- **F3 — An `$ARGUMENTS`-named unit can be re-selected forever.** STEP 2 rule 1
  ("If `$ARGUMENTS` names a concrete task/issue → that is the unit; skip
  scanning") re-fires on every loop-back from STEP 7; the "nothing actionable →
  PASSED" exit lives on the *else triage* branch. Literal reading: a
  single-issue run re-executes the same unit until `cycle > max_cycles` and
  terminates ESCALATED instead of PASSED — the wrong verdict on the most common
  invocation shape. (A competent model likely terminates via the DoD-met
  reading; the trap is the literal rule order.) Fix: mark the argument unit
  consumed once shipped.
- **F4 — HEAL path reviews a stale diff.** STEP 6 FAIL routes healing through
  inline `Skill("/fix-loop")` at T0, then "return to STEP 5 VERIFY" — but the
  STEP 5 reviewer prompt is parameterized on "the maker's changed_files", which
  is never refreshed with the heal's edits. Healed code can pass a review that
  never saw it, then SHIP. (Independence itself survives — code-reviewer-agent
  still reviews work T0 authored; the supervisor-reproduction step being run by
  the heal author is the pattern `supervisor-verification.md` itself prescribes.)
  Fix: recompute changed_files (git diff) before each VERIFY pass.
- **F5 — PREFLIGHT's "probe runtime dispatchability early" is not actionable as
  written.** STEP 1.5 declares the file-existence check "necessary but NOT
  sufficient" and then supplies no probe mechanism (no recipe, no expected
  error signature, no statement whether a probe counts against
  `dispatches_used`). A literal executor stalls or silently falls back to the
  file check the text just disqualified — recreating the 2026-04-24 failure the
  step exists to prevent. Fix: specify the probe (e.g. check the session's
  available-subagent-types list, or a documented no-op dispatch).
- **F6 — `--no-ship` has no defined terminal path.** The CLI table says "Stop
  after VERIFY" but the PASS-with-`--no-ship` branch is never written: no
  result value (PASSED? the unreachable FAILED?), no LEARN decision, no
  continue-vs-stop, and no emit — leaving the run's verdict to improvisation.
  Fix: define the branch (suggest: result PASSED, `commits: SKIPPED`, still
  LEARN, still loop).
- **F7 — Spec/skill divergence: the spec's "blind test verify" layer is absent.**
  Spec §3's VERIFY row promises "`/auto-verify` + `Agent(code-reviewer-agent)`
  … + blind test verify"; SKILL STEP 5 implements mechanical gate + adversarial
  code review + supervisor reproduction but no context-blind test verifier per
  `independent-test-verification.md`. Fix in whichever direction is intended —
  either add the blind verifier to STEP 5 or amend the spec row.

### MINOR

- **F8 — Verdict value `FAILED` is unreachable** — every defined terminal path
  writes PASSED / ESCALATED / BLOCKED; the dead enum value invites inconsistent
  improvisation on the undefined paths (F6).
- **F9 — "use the inline DAG below" is a dangling reference** (no artifact in
  the body is labeled as an inline DAG; the numbered STEPs presumably are it),
  and the STEP 1 state template hardcodes `"max_cycles": 5` /
  `"global_retry_budget": 15` without saying `--max-cycles` / config-read
  budgets override the template values.
- **F10 — Maker≠checker assert input is underspecified.** "Resolved"
  subagent_types are obtainable from the contracts DAG's `dispatch:` fields
  (which STEP 1.2 reads), but the skill never says that's the source; STEPs 4/5
  hardcode the names, so a literal comparison of two literals cannot detect a
  project remap. One sentence fixes it.
- **F11 — Clean PASSED-with-zero-units exit emits no hub-ward signal.** The
  CRITICAL RULE enumerates the four signals as "every terminal outcome", so
  this is a monitoring blind spot by design rather than a self-contradiction —
  but a downstream project whose loop always exits clean is invisible to the
  aggregator.
- **F12 — STEP 1.5 BLOCKED verdict shape underspecified** — whether `result` is
  `"BLOCKED"` (STEP 8 enum) with a `WORKER_REGISTRY_NOT_LOADED` reason field,
  and which STEP 8 required fields are written that early.
- **F13 — Small drifts:** spec §4 names `max_retries_per_step: 3` and an
  optional wall-clock cap the skill never surfaces (it is in
  `config/workflow-contracts.yaml` defaults — verified — so this is a doc-only
  drift); spec §3 DISCOVER says `triage.json`, skill writes `triage-inbox.md`;
  `dispatches_used` increments only for the maker (STEP 4), not the checker
  (STEP 5), understating the STEP 8 dashboard count; registry deps omit the
  advisory `/update-practices` / `/code-review-workflow` refs; `/goal` is a
  dead reference; 7 triggers exceeds the 3–6 authoring band.

## What was checked and found CLEAN (recorded per EVAL-WORKFLOW critical rule 8)

- Registry: hash (normalized, `dedup_check.hash_pattern`) matches; version and
  changelog consistent; dependency closure (11 dispatched skills/agents + 9
  cited rules) fully present on disk in `core/.claude/`.
- Contracts: `workflows.loop-engineering` present and identical in shape in
  both `config/workflow-contracts.yaml` and `core/.claude/config/…`;
  `master_agent: null`, `sub_orchestrators: []` as STEP 1 expects; defaults
  carry `global_retry_budget: 15` / `max_retries_per_step: 3` matching the
  skill's inline budget.
- Guard tests named by the spec exist:
  `test_loop_engineering_emits_hub_linked_telemetry`
  (test_workflow_closure_consistency.py:107) and
  `test_learnings_only_pattern_is_aggregated` (test_aggregate_telemetry.py:374).
- Budgets/termination: every defined loop path increments `cycle` (STEP 2) or
  `retries_used` (STEP 6 heal); exhaustion condition reachable; `healed` and
  `escalated` each have exactly one emit point; `emit_signal` is
  append-never-overwrite and matches spec §5.1 including the
  committed-learnings constraint.
- T0-only mandate, KISS composition claim (no re-implementation of the healers/
  verifiers/learners it routes into), and the stress categories 1, 2, 4, 5, 6,
  9, 10 (empty input, off-topic, oversized triage, missing workers, pinned
  registry, unbounded-phrasing) are all handled by explicit text.

## Recommended fixes (prioritized, mapped)

1. F1 (CRITICAL, artifact-flow): add the worktree-integration step; state the
   operative tree for STEPs 5–6.
2. F2 (telemetry): single emit site for `shipped`.
3. F3 + F6 + F8 (termination): consume the argument unit after ship; define the
   `--no-ship` terminal branch; give `FAILED` a producer or drop it.
4. F4 (verification integrity): refresh changed_files before every VERIFY pass.
5. F5 + F10 (preflight): specify the dispatchability probe; name the contracts
   `dispatch:` fields as the source of the maker/checker assert.
6. F7 (spec sync): reconcile the "blind test verify" layer.
7. F11–F13 + neighbor signposting (ecosystem polish, can batch with any of the
   above): consider a `clean_exit` signal; fix the spec's `triage.json` naming;
   count checker dispatches; add reciprocal boundary lines to development-loop /
   debugging-loop / fix-loop descriptions.
