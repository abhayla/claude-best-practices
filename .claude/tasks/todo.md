# Task Tracker

<!-- Claude maintains this file during implementation sessions. -->
<!-- Format: checkable items grouped by task, marked complete as work progresses. -->

## Current Task

### Subagent Dispatch Platform Limit Remediation (2026-04-24 session 2)

Context: three independent probes and Anthropic's official docs confirm
subagents cannot dispatch further subagents. Current 4-tier dispatch model
in `core/.claude/rules/agent-orchestration.md` is platform-incompatible.
Plan refined through anthropic-multi-agent-reviewer-agent audit (grade C);
Phase 0 empirical probe further narrowed the architectural options.

## Phase 0 — Empirical parallelism probe — ✅ COMPLETE

- [x] 0.1 Dispatched general-purpose subagent probe → findings captured
- [x] 0.2 T0 self-test (same Bash timing test) → findings captured
- [x] 0.3 Lessons entry appended — `.claude/tasks/lessons.md`
- [x] Verdict recorded:
  - `Bash` ×N in one message → **serial** (10s gap at T0, 7s gap in subagent)
  - `Skill` ×N in one message → **blocked from concurrent execution** (queues as next-turn prompt injection)
  - `Agent` ×N at T0 → parallel (documented + confirmed)
  - `Agent` from subagent → blocked (Anthropic platform constraint)

## BLOCKED ON USER — Wave 1 parallelism strategy decision

Three options:
- **A — T0-only orchestrator.** `/test-pipeline` becomes a prompt-injection skill; user's T0 session IS the orchestrator; it dispatches two lane subagents via `Agent()` for Wave 1.
- **B — External script wrapper.** `scripts/run-test-pipeline.sh` spawns two `claude -p` processes for Wave 1; reads JSON artefacts; continues.
- **C — Accept serial Wave 1.** Simplest. Loses ~2× wall-clock on balanced suites.

Phase 1 streams 1.1 and 1.4 depend on this choice (they make architectural claims in docs). Phase 1 streams 1.2 and 1.3 are strategy-independent and may start immediately.

## Phase 1 — Docs + rename (single PR)

### Strategy-independent streams (may start now)

- [ ] 1.2 Fix T1 contradiction in `testing-pipeline-master-agent.md` — line 44 wins; align `workflow-contracts.yaml`
- [ ] 1.3 Delete `/testing-pipeline-workflow`; rename `testing-pipeline-master-agent` → `test-orchestrator-agent`; update `registry/patterns.json` + grep all cross-references

### Strategy-dependent streams (wait for user decision)

- [ ] 1.1 Rewrite `agent-orchestration.md` §2 AND Rule 3 — content depends on chosen strategy for Wave 1
- [ ] 1.4 Amend `pattern-structure.md` Tool Grants — content depends on chosen strategy

### Cross-cutting for Phase 1

- [ ] 1.5 Ship Phase 1 as a single PR (1.1+1.2 MUST be one commit per reviewer's ordering finding)

## Phase 2 — Validator

- [ ] 2.1 Add `dispatched_from:` frontmatter field across all agents
- [ ] 2.2 Invert `test_orchestrator_tool_grants.py` — context-aware based on `dispatched_from`
- [ ] 2.3 Runtime-probe integration test with `@pytest.mark.integration`; wire into `validate-pr.yml`

## Phase 3 — Architectural refactor

- [ ] 3.0 Micro-spec: merged `test-orchestrator-agent` responsibilities (exactly 4 per Rule 8), state ownership (Rule 6), Wave 1 dispatch shape (depends on strategy A/B/C)
- [ ] 3.1 PR 3.1 — merge T2B into orchestrator
- [ ] 3.2 EVAL GATE — before/after on 50-test representative suite; 5-criterion rubric
- [ ] 3.3 PR 3.2 — merge T2A three-lane + complexity classifier
- [ ] 3.4 PR 3.3 — three-lane spec rewrite with executable Skill() examples

## Cross-cutting (throughout all phases)

- [ ] Cutover guard: every Phase 3 PR checks `.workflows/testing-pipeline/` for in-progress runs
- [ ] Intermediate-state contract: valid `pipeline-verdict.json` between Phase 3 PRs
- [ ] Principle 2 preservation: NON-NEGOTIABLE contents re-encoded in each `Skill()` dispatch prompt

## Completed sections below (preserved for reference)

### Prompt Logger Hook (2026-04-24)

Goal: persist every `UserPromptSubmit` prompt to `.claude/tasks/prompts.md` as append-only Markdown. Distributable via `core/.claude/hooks/` so downstream projects get the hook on provision.

Approved design (Q1=A gitignore live log, Q2=A Markdown with `~~~text` fence, Q3=A empty seed in `core/`):
- Hook writes to `$(git rev-parse --show-toplevel)/.claude/tasks/prompts.md`; NEVER writes to stdout (stdout on `UserPromptSubmit` is injected into the conversation context).
- Entry format: `## <iso-ts> — branch@shortsha` heading, `- session:` + `- cwd:` bullets, `~~~text` fence around raw prompt (triple-tilde survives prompts containing triple-backtick blocks).
- Non-blocking under every failure mode: malformed stdin, missing `jq`, missing git, empty prompt → exit 0, log unchanged.

Tasks:
- [x] Write failing tests in `scripts/tests/test_prompt_logger.py` (TDD red — 1 failing on missing hook)
- [x] Implement `core/.claude/hooks/prompt-logger.sh`
- [x] Mirror to `.claude/hooks/prompt-logger.sh` (byte-identical; test_hub_hook_exists_and_matches_core_byte_for_byte pins this)
- [x] Create empty seed `core/.claude/tasks/prompts.md` (header only, tracked)
- [x] Create live log `.claude/tasks/prompts.md` (header only, gitignored)
- [x] Wire second `UserPromptSubmit` hook into `.claude/settings.json`
- [x] Gitignore `/.claude/tasks/prompts.md`
- [x] Document in `core/.claude/hooks/README.md` — new "Prompt Logger" section
- [x] Register in `registry/patterns.json` (type=hook, tier=nice-to-have) + bump `_meta.total_patterns` 237→238
- [x] Run pytest (1283 passed, 60 skipped, 1 xfailed)
- [x] Run full CI replication: dedup --validate-all ✅, dedup --secret-scan ✅, workflow_quality_gate_validate_patterns ✅, pytest ✅
- [x] Append review section

### Review (Prompt Logger)

Outcome: 9 files changed, 16 new tests, all 4 CI gates green. Hook is live in this session — `.claude/tasks/prompts.md` already captured a real prompt during implementation, confirming end-to-end.

TDD caught one real bug during the green phase:
- `entry=$(printf ...)` stripped trailing newlines (bash `$(...)` semantics), causing two back-to-back prompts to run together (`~~~## next` with no blank line). Fixed by switching to grouped redirection `{ ...; } >> "$log"`. Test `test_multiple_appends_do_not_clobber` pins this forever.

What could break:
- On systems without `jq`, the hook becomes a no-op silently (by design — no-blocking is a hard requirement). If a user *expects* prompts to be logged and `jq` is missing, they won't notice. Mitigation: `test_settings_json_wires_prompt_logger_hook` confirms wiring, but no runtime "is logging actually working?" signal exists. Acceptable for v1; layer a statusline hint later if needed.
- Concurrent prompts exceeding PIPE_BUF (4 KB on Linux) can interleave — accepted trade-off, documented in the hook preamble.
- Windows path backslashes appear verbatim in the `- cwd:` bullet. Harmless in Markdown.
- `core/.claude/tasks/prompts.md` seed ships via provisioning; downstream projects need to add `/.claude/tasks/prompts.md` to their own `.gitignore` — this is documented in the hooks README section but NOT enforced. A `synthesize-project` hook could auto-append the gitignore line, but that widens scope beyond this task.

Nothing pushed. No commit created — awaiting user approval per default policy.
