# Lessons Learned

<!-- Claude appends entries here after corrections or surprising outcomes. -->
<!-- Review at session start to avoid repeating mistakes. -->
<!-- Format: date, what went wrong, what to do instead. -->

## 2026-04-22 — Aggregator "union of failures" rule needs a superset check

**Surfaced during:** Phase H of the testing-pipeline overhaul, `test_flaky_scenario_surfaces_quarantined_issue` in `scripts/tests/test_pipeline_e2e.py`.

**What I got wrong:** In `scripts/pipeline_aggregator.py`, the verdict check
was `if failures or screenshot_failures:` — meaning a stage that reported
`result: FAILED` but provided an empty `failures[]` array (e.g., a conductor
that moved a test to `known_issues` without producing an individual failure
entry) was counted as PASSED. Top-level FAILED status was effectively
invisible to the aggregator.

**What to do instead:** The "union of failures" rule is a SUPERSET —
stage-level FAILED counts regardless of per-failure detail. The aggregator
MUST also check `any(r["result"] == "FAILED" for r in results)` and fail
the pipeline when any stage reports FAILED, even if its `failures[]` is
empty. Generalizable rule: for any aggregator that unions typed evidence,
always include a stage-level failure check as a safety net — don't trust
that every FAILED skill populates its evidence array.

**Pinned by:** `test_stage_failed_with_empty_failures_still_fails` in
`scripts/tests/test_pipeline_aggregator.py`.

## 2026-04-22 — Pinned-content tests break on consolidation; update homes, don't skip

**Surfaced during:** Phase A of the testing-pipeline overhaul. The test
`test_skill_md_version_is_3_0_0` in `test_e2e_visual_run_playwright_only.py`
asserted the old skill version and broke when the skill was consolidated
into v4.0.0. Similarly `test_pipeline_verdict_schema_in_orchestrator`
asserted the schema was in `test-pipeline-agent.md` but the schema moved
to `testing-pipeline-master-agent.md` when aggregation was centralized.

**What I did right:** Updated both tests to target the new homes
(e2e-conductor-agent for the skill content, testing-pipeline-master-agent
for the verdict schema) rather than deleting them or marking them skipped.
The tests now carry their original intent forward.

**Generalizable rule:** When content is moved between files during a
consolidation, pinned-content tests are valuable regression nets — migrate
the assertions to the new authoritative location. Deleting them loses the
regression surface; skipping them masks drift.

## 2026-04-24 — Parallel tool dispatch in Claude Code is more restricted than prompt-engineering guidance suggests

**Surfaced during:** Phase 0 empirical probe for the subagent-dispatch-platform-limit remediation, session 2026-04-24.

**What I expected:** Multiple tool calls issued in a single assistant message would execute in parallel, per the common Claude Code prompt directive ("make all independent tool calls in parallel"). A reviewer (anthropic-multi-agent-reviewer-agent) specifically claimed that parallel `Skill()` calls in one orchestrator message would preserve the testing-pipeline Wave 1 (functional+API lanes concurrent) — and that this was the cheap alternative to an external script wrapper.

**What actually happened:** Empirical probes in both a dispatched `general-purpose` subagent session AND my own T0 session measured:
- Two `Bash` calls with 3-second sleeps issued in one message → **serial** (7s and 10s gaps respectively between end-of-A and start-of-B)
- Two `Skill` calls in one message → **blocked from concurrent execution**; `Skill` appears to inject the target SKILL.md into the caller's next user-turn context, creating a serial prompt queue in the same session (no new subagent context, no concurrency)
- Two `Read` calls → returned in the same turn, but Read is fast enough that parallelism vs serialism is unobservable from timing
- Two `Agent` calls in one message at T0 → confirmed parallel (documented + standard), but unavailable in subagent sessions per Anthropic's official docs (https://code.claude.com/docs/en/sub-agents — "subagents cannot spawn other subagents")

**Generalizable rule:** In Claude Code, "parallel tool calls in one message" is only reliably parallel for `Agent()` dispatched from the T0 user session. `Bash`, `Skill`, and most other tools appear to be serialized by the runtime regardless of session level, at least on Windows/Opus 4.7 at the hub's current version. Any architecture that assumes parallel `Bash`/`Skill` from a dispatched subagent WILL run serially at runtime. Verify parallelism empirically with nanosecond timestamps before designing around it — don't trust the "issue in one message → parallel" folklore.

**Downstream implication:** For the testing-pipeline refactor, Wave 1 (functional + API in parallel) requires one of three non-obvious paths: (1) move the orchestrator to T0 so the user's session dispatches lane subagents via `Agent()`, (2) externalize via a shell-script wrapper running `claude -p` twice, or (3) accept serial Wave 1. Parallel `Skill()` from the orchestrator is NOT a viable option. The reviewer's premise was wrong.

**Evidence on disk:**
- Subagent probe transcript: returned inline in session 2026-04-24 (T2 of session 2)
- T0 timings: A=1777025367927028600→1777025371086561100, B=1777025381209802100→1777025384403795200 (10.12s gap)

## 2026-04-24 — Registry hash field was dead data; wire enforcement or drop the field

**Surfaced during:** Tech-debt cleanup after REQ-S004 (analyzer v2.3.0). A
todo.md review flagged that `registry/patterns.json` had a stale hash for
`test-failure-analyzer-agent`. Checking the full registry revealed **228
of ~237 patterns** had drifted hashes — the column had been effectively
cosmetic for a long time because `validate_registry()` only checked that
the `hash` field **existed**, not that it **matched** the file.

**What I got wrong initially:** Recommended fixing only the analyzer's hash.
That would have left 227 other stale hashes and accomplished nothing —
the column still would not have been trustworthy for future gating. The
honest fix was either (a) regenerate all + add enforcement, or (b) drop
the field entirely.

**What to do instead:** When fixing a single instance of a broader quality
signal, first measure whether the signal is drift-enforced. If not, either
wire enforcement alongside the fix, or admit the field is decorative and
stop maintaining it. Regenerating one value without enforcement is
busy-work — the whole column keeps rotting.

**Resolution:** `validate_registry()` now compares each entry's `hash`
against `hash_pattern(<on-disk file>)` and `test_no_drift_in_shipped_registry`
pins the invariant. The `resolve_pattern_file()` helper handles hub-only
skills living at `.claude/skills/<name>/SKILL.md` (fallback) alongside
canonical `core/.claude/` paths, and skips `config`-type patterns that
aren't file-hashable.

**Also worth flagging** (surfaced but not actioned here): downstream
projects whose `.claude/config/test-pipeline.yml` lacks an `auto_heal:`
block will now hit the REQ-S004 fail-safe fallback — WARN logs +
`ISSUE_ONLY` defaults. Pick this up in the next `sync-to-projects` pass
so downstream maintainers add the block.

## 2026-04-24 — Agent `tools:` frontmatter MUST be a YAML list, not scalar

**Surfaced during:** v2-pipeline-testbed autonomous run Phase 5a finding —
`failure-triage-agent` and `github-issue-manager-agent` were NOT
discoverable as `subagent_type` despite being present on disk post-
provisioning. Pipeline dispatch silently collapsed to inline execution
at T1; outputs looked right but the 4-tier architectural invariant
(REQ-M006 / M009 / M013) was broken.

**Root cause:** 6 agents declared `tools: "Agent Bash Read Write Edit
Grep Glob Skill"` — a space-separated scalar. Claude Code's agent
discovery requires the YAML list form `tools: ["Agent", "Bash", ...]`.
The scalar parses as a single string and the agent is not exposed as a
valid `subagent_type`.

**What was wrong about the existing test:** `test_orchestrator_tool_grants.py`'s
`_tools_set()` accepted BOTH forms as equivalent (split the string on
whitespace). So the test would pass for agents with the broken scalar
form, never catching the discovery failure.

**Generalizable rule:** When a test pins an invariant by reading a
normalized view of the data, the normalization step can silently accept
the broken form. Reviewing the test's failure cases (what SHOULD make
it fail) is as important as reviewing the assertion.

**Resolution:** `_tools_set()` now raises TypeError on scalar input;
`pattern-structure.md` rule shows list form as canonical; all 6
affected agents fixed; pins expanded to cover failure-triage-agent and
github-issue-manager-agent. Committed `f5036c6`.

## 2026-04-24 — Runtime is the arbiter when docs and runtime disagree

**Surfaced during:** Phase 2b finding "Config naming mismatch (TIMEOUT
vs TIMING)" — widened grep revealed: analyzer `category` output
(SELECTOR, TIMEOUT, ASSERTION_FAILURE...), spec §3.6 matrix
(BROKEN_LOCATOR, TIMEOUT_TIMING...), and config `auto_heal:` keys all
used slightly-different names for overlapping concepts. Three
taxonomies, none aligned.

**What I got wrong initially:** treated as a 1-pair naming fix. Broader
grep exposed 6 mismatched pairs + 60 eval scenario files with old names.

**What to do instead:** when documentation and runtime disagree, the
runtime is the source of truth. Align docs to what actually runs, not
the reverse. But be honest about scope — updating 60 eval fixtures in
the same pass as a runtime fix is scope creep. Commit runtime
alignment; call out the deferred fixture cleanup explicitly.

**Resolution:** Config + spec §3.6 + §3.13 aligned to analyzer
categories. Eval scenarios + `_gen_pr2_evals.py` + research docs
DEFERRED (still reference old names but don't affect runtime —
they're evaluated via /agent-evaluator, not pytest). Committed `c6dac7d`.

## 2026-04-24 — Provisioning tier gap: must-have-only default hides upgrades

**Surfaced during:** Phase 0 P0c FAIL — `recommend.py --provision` default
(`--tier must-have`) "listed but did not apply" prompt-logger hook
(nice-to-have) and the updated test-pipeline.yml config.

**What to do instead:** When a pattern benefits every Claude Code
session regardless of project type, tier it `must-have` so downstream
projects get it on default provision. Universal hooks and ubiquitous
configs should not wait for a user to opt into `--tier nice-to-have`.

**Resolution:** prompt-logger promoted to must-have; `test-pipeline`
added to CONFIG_SKILL_MAP so its config inherits must-have tier.
Committed `2e71a6e`.
