# T-393 freshness note (2026-08-27, FOREGROUND ONLY dispatch mandate)

Registry class `sonnet-subagent-backgrounds-tests-and-stops` (3 occurrences today, 2026-08-27):
a Sonnet subagent ran its own tests/builds via `run_in_background` and then ended its turn.
Nothing re-invokes a subagent — a background job it starts has no owner to report back to, so
each dispatch stalled until the dispatcher noticed and nudged it. Root cause: neither the
SubagentStart injected guidance nor the worker prompt skeleton said "foreground only" anywhere.

## What changed

- `.claude/hooks/subagent-governance-inject.sh` — added one mandate line to the injected
  `additionalContext` heredoc (appended after the existing PLAN FIRST / ROOT CAUSE / STRUCTURED
  CONTRACT trio, verbatim per the contract): "FOREGROUND ONLY: never run tests/builds with
  run_in_background - a background job never re-invokes you; run in the foreground with a
  timeout and report the result in the same turn (registry: sonnet-subagent-backgrounds-tests-
  and-stops, T-393)." Every dispatched subagent now receives this at SubagentStart.
- `scripts/tests/test_native_governance_hooks.py::test_subagent_hook_emits_mandates_as_valid_json`
  — added three new assertions (`"FOREGROUND ONLY" in ctx`, `"run_in_background" in ctx`,
  `"T-393" in ctx`) pinning the new line the same way the pre-existing three mandates are pinned.
  RED before the hook edit, GREEN after; a mutation (stripping the new line back out of the hook
  script) reproduced RED, then the hook was restored — both runs captured under
  `scratch_t393/T393-red.txt` / `T393-green.txt` / `T393-mutation-red.txt` and pasted into the PR
  body.
- `.claude/skills/get-work-done/SKILL.md` — STEP 6 item 6 (LAUNCH) now ends with "Workers run
  tests/builds in the FOREGROUND only, never `run_in_background` (T-393)." The skill has no
  separate in-session `Agent()`-brief prompt skeleton to mirror this into — its one `Agent()`
  mention (STEP 7, checker-tier selection) is not a dispatch-prompt template, so nothing else
  needed the sentence.

## Byte budget

SKILL.md was 29,984 B before this change (16 B under the 30,000 B shrink-only ratchet ceiling,
`config/gwd-skill-conformance-grandfather.yml` `max_bytes`). The new sentence costs 84 B. To
stay under budget, non-normative prose was trimmed: the frontmatter `description:` line (523 B
-> 473 B, no test greps its exact text) and the Mode router's `intake` row wording (235 B -> 212
B). No `MUST` bullet, gate id, exit code, settings key, or any phrase pinned by
`scripts/tests/test_gwd_skill_conformance*.py`, `test_gwd_skill_musts_have_gates.py`,
`test_get_work_done_fast_lane.py`, `test_owner_status_cadence_guidance.py`,
`test_root_cause_gate_guidance.py`, or `test_skip_ci_guidance.py` was touched or removed. Final
size: 29,995 B (5 B headroom).

## Verification

- Targeted guards green (`GWD_ROOT` set, conformance ratchet exercised against the live fleet
  checkout): `test_native_governance_hooks.py`, `test_gwd_skill_conformance.py`,
  `test_gwd_skill_conformance_grandfather_ratchet.py`, `test_gwd_skill_musts_have_gates.py`,
  `test_eval_coverage_freshness.py`, `test_get_work_done_fast_lane.py`,
  `test_owner_status_cadence_guidance.py`, `test_root_cause_gate_guidance.py`,
  `test_skip_ci_guidance.py`.
- Full local suite (`pytest scripts/tests/ --ignore=scripts/tests/smoke-test`) + the four CI
  validators re-run per the contract's DoD before landing — counts recorded in the PR body.

This note satisfies the eval-coverage freshness ratchet for a one-line governance-mandate
addition with no new user-facing behavior to scenario-test — the change is fully covered by the
red/green/mutation hook test above plus the full suite.
