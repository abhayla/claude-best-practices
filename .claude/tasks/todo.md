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

## Strategy decision — RESOLVED (2026-04-24)

User confirmed **Option A** (T0-only orchestrator). Every workflow becomes
a skill-at-T0 pattern: slash command injects the orchestration logic into
the user's T0 session, where `Agent()` actually works, so the session can
dispatch flat worker subagents via `Agent()`.

## Phase 1 — Docs + deprecation markers — ✅ COMPLETE (branch: fix/subagent-dispatch-platform-limit-phase1)

- [x] 1.1 Rewrite `agent-orchestration.md` §1, §2, §3, §6, §10 for single-level dispatch reality — commit `2b00b3d`
- [x] 1.2 Rewrite `pattern-structure.md` Tool Grants for platform reality — commit `932c6de`
- [x] 1.3 Deprecate `/testing-pipeline-workflow` skill; update registry; update `/test-pipeline` cross-ref — commit `ff58452`
- [x] 1.4 Deprecate the 3 tiered agents (testing-pipeline-master-agent, test-pipeline-agent, failure-triage-agent) in bodies + registry — commit `a26d0c4`
- [x] 1.5 Migrate pinned-content tests; align registry hashes; fix description to pass validator — commit `84ac305`

All 4 CI gates green:
- dedup_check --validate-all PASSED
- dedup_check --secret-scan PASSED
- workflow_quality_gate_validate_patterns PASSED (0 warnings)
- pytest 1295 passed, 60 skipped, 1 xfailed

### Phase 1 Review (2026-04-24)

**Outcome:** 5 commits on feature branch, 0 CI warnings, 0 test regressions.
Approach chosen: Option A (T0-only orchestrator). Per user-approved
architecture review by anthropic-multi-agent-reviewer-agent + Phase 0
empirical finding that only T0 Agent() dispatch is reliably parallel
(Skill and Bash in one message both serialized at runtime).

Key changes on disk:
- `agent-orchestration.md` rules rewritten: §2 is now "Single-Level
  Dispatch Model" citing Anthropic docs + GH #19077 + GH #4182. Tier
  labels retained as responsibility-ownership documentation only.
- `pattern-structure.md` Tool Grants section: `Agent` in `tools:` is
  only functional at T0; workers MUST NOT declare it; dual-mode agents
  declare it but worker path must not rely on it.
- Three agents marked deprecated with banners + registry fields:
  `testing-pipeline-master-agent` (T1), `test-pipeline-agent` (T2A),
  `failure-triage-agent` (T2B). Their files stay in place for the
  2-version-cycle deprecation window per pattern-structure.md.
- `/testing-pipeline-workflow` skill deprecated in favor of
  `/test-pipeline`; legacy slash command still resolvable but marked
  in both frontmatter and registry.

**What could break:**
- Downstream projects with `/testing-pipeline-workflow` in muscle
  memory will see a deprecation banner but the skill still works
  (just dispatches a deprecated agent that silently inlines its work —
  same runtime behavior as before, now documented).
- Auto-generated docs (`docs/workflows/*`, `docs/dashboard.*`) still
  reference the deprecated patterns. Will regenerate correctly next
  `generate_docs.py` / `generate_workflow_docs.py` run. Manual docs
  (`README.md`, `docs/specs/*`, `docs/plans/*`) still reference the
  old names and will be pruned in Phase 3 when the test pipeline is
  re-architected.
- The `agent-orchestration.md` rewrite is a big semantic change —
  every sentence that talked about "T1 dispatches T2 via Agent()" is
  now "orchestrator dispatches worker at T0 only". Any code or agent
  body that silently assumed the tiered runtime behavior will now
  fail the validator in Phase 2 (by design — that's the gate we're
  building).

**Pushed.** Branch `fix/subagent-dispatch-platform-limit-phase1` up on
origin; PR #20 open at https://github.com/abhayla/claude-best-practices/pull/20
awaiting review/merge.

## Phase 1.5 — Blast-radius audit — ✅ COMPLETE (2026-04-24)

Before Phase 2, audited the hub for all other patterns assuming nested
`Agent()` dispatch. Finding: the broken pattern is not confined to the
test pipeline. It's the entire **workflow-master** idiom. Every workflow
in `config/workflow-contracts.yaml` declares `sub_orchestrators:`; every
`/<workflow>-workflow` skill dispatches a `<workflow>-master-agent` whose
body assumes it can further dispatch those sub-orchestrators. All 8
master-agents (7 non-deprecated + 1 deprecated in Phase 1) and 8 skill
wrappers are affected.

Findings (see `.claude/tasks/lessons.md` 2026-04-24 audit entry for details):
- **7 non-deprecated master-agents** with broken design:
  `code-review-master-agent`, `debugging-loop-master-agent`,
  `development-loop-master-agent`, `documentation-master-agent`,
  `learning-self-improvement-master-agent`,
  `session-continuity-master-agent`, `skill-authoring-master-agent`.
- **3 standalone orchestrators** declaring `Agent` in tools:
  `project-manager-agent` (T0-only — needs explicit enforcement),
  `parallel-worktree-orchestrator-agent` (T0-only — needs enforcement),
  `e2e-conductor-agent` (sub-orchestrator of test pipeline — broken).
- **1 template**: `core/.claude/agents/workflow-master-template.md`
  seeds the broken pattern for future copy-paste. **Highest-leverage fix.**
- **8 `workflow-contracts.yaml` entries** with `sub_orchestrators:` lists
  (testing-pipeline, development-loop, debugging-loop, code-review,
  documentation, session-save, session-learn, skill-authoring).
- **Manual docs** (README.md, docs/specs/*, docs/plans/*) still describe
  the tier model — to be pruned per-workflow in each Phase 3 sub-PR.

Phase 3 rescoped from "dissolve test-pipeline tier" to "retire entire
workflow-master pattern across hub" — ~9 PRs, ~3000-4000 lines net.

## Phase 2 — Validator (prerequisite for machine-verifying Phase 3 deprecations)

- [ ] 2.1 Add `dispatched_from:` frontmatter field to every agent in
      `core/.claude/agents/` (enum: `T0` | `worker` | `dual-mode`)
- [ ] 2.2 Invert `scripts/tests/test_orchestrator_tool_grants.py` —
      context-aware based on `dispatched_from`: T0 MUST declare Agent;
      worker MUST NOT; dual-mode MAY with body-scan warning
- [ ] 2.3 Runtime-probe integration test with `@pytest.mark.integration`;
      dispatches a throwaway subagent and asserts Agent is absent from
      its tool list; wire into `validate-pr.yml` required checks
- [ ] 2.4 Update `core/.claude/rules/pattern-structure.md` to document
      the new `dispatched_from:` field in Agent Structure section

Estimated: 1 PR, ~300 lines, after PR #20 merges.

## Phase 3 — Workflow-master pattern retirement (template-first sequence)

**Key principle:** template-first (highest leverage) then per-workflow PRs
in priority order (test pipeline, then by impact). Each PR ≤ 400 lines
per git-collaboration.md. Eval gate between PR 3.1 and PR 3.2 (test
pipeline as canary).

- [x] 3.0 TEMPLATE-FIRST — rewrite `workflow-master-template.md` to
      document the skill-at-T0 pattern; update `pattern-structure.md`'s
      workflow-master section; ~150 lines — PR #22

### Phase 3.1 — IN PROGRESS (branch `feat/phase3-1-test-pipeline-skill-at-t0`)

**Open questions resolved 2026-04-24 session 3:** all 4 questions answered
with the "lean" option per spec v2.1 §7:
- Q1 Inline orchestration (no sub-skill delegation for orchestration logic)
- Q2 Preserve empty `sub_orchestrators: []` in workflow-contracts.yaml
- Q3 `/e2e-visual-run` stays independent from `/test-pipeline`
- Q4 Complexity classifier ships in 3.1 behind `lanes.parallel_classifier.enabled`
   (default on for suites ≥50 tests, off otherwise)

Sub-commit plan:
- [ ] 3.1.1 Spec lock — §7 RESOLVED, status PROPOSED → ACCEPTED, v2.2
      revision note; SUPERSEDED banner on v1.7 spec
- [ ] 3.1.2 Skill rewrites — `/test-pipeline` SKILL.md inline 9-step
      orchestrator per v2 §3.1; `/e2e-visual-run` SKILL.md independent
      queue-worker dispatcher; SemVer MAJOR bump on both
- [ ] 3.1.3 Worker-body + skill prune — 8 agent bodies drop tier-dispatch
      language; 9 skill bodies drop deprecated-agent refs per checklist
- [ ] 3.1.4 Config + classifier — `config/workflow-contracts.yaml`
      testing-pipeline empty `sub_orchestrators:`; add
      `lanes.parallel_classifier` block to `config/test-pipeline.yml`;
      registry hashes refreshed
- [ ] 3.1.5 Docs prune + regen — README + `docs/plans/*` +
      `docs/stages/STAGE-7-IMPLEMENTATION.md` + QA research post-script
      per checklist; `generate_docs.py` + `generate_workflow_docs.py`
      regenerate; AC-001–AC-005 verification

- [ ] 3.1 TEST PIPELINE — `/test-pipeline` body becomes the orchestration;
      deprecate `e2e-conductor-agent`; rewrite `/e2e-visual-run`; update
      `config/workflow-contracts.yaml` testing-pipeline entry; rewrite
      spec §3.3/3.5/3.8 with executable Skill() + Agent() examples; ~800 lines
- [ ] 3.1-gate EVAL GATE — run current vs post-3.1 on representative
      50-test suite; 5-criterion rubric (lane-dispatch correctness, budget
      enforcement, gate evaluation, return-contract fidelity, wall-clock);
      human review checkpoint
- [ ] 3.2 DEVELOPMENT LOOP — deprecate `development-loop-master-agent`;
      rewrite `/development-loop` skill body; ~250 lines
- [ ] 3.3 DEBUGGING LOOP — deprecate `debugging-loop-master-agent`;
      rewrite `/debugging-loop`; ~250 lines
- [ ] 3.4 CODE REVIEW — deprecate `code-review-master-agent`;
      rewrite `/code-review-workflow`; ~250 lines
- [ ] 3.5 DOCUMENTATION — deprecate `documentation-master-agent` (also
      has inline Agent(subagent_type=...) calls to clean up);
      rewrite `/documentation-workflow`; ~250 lines. **Halfway eval
      checkpoint — is the pattern holding?**
- [ ] 3.6 SESSION CONTINUITY — deprecate `session-continuity-master-agent`;
      rewrite `/session-continuity`; update session-save + session-learn
      workflow contracts; ~200 lines
- [ ] 3.7 LEARNING — deprecate `learning-self-improvement-master-agent`;
      rewrite `/learning-self-improvement`; ~200 lines
- [ ] 3.8 SKILL AUTHORING — deprecate `skill-authoring-master-agent`;
      rewrite `/skill-authoring-workflow`; ~200 lines
- [ ] 3.9 STANDALONES — `project-manager-agent` +
      `parallel-worktree-orchestrator-agent` get `dispatched_from: T0`
      frontmatter enforcement; verify `/pipeline-orchestrator` is already
      skill-at-T0; final grep for any remaining nested `Agent()` patterns
      in the hub. ~100 lines

## Cross-cutting (throughout Phase 3)

- [ ] Cutover guard: every Phase 3 PR checks `.workflows/<workflow-id>/`
      for in-progress runs and fails fast if any exist
- [ ] Intermediate-state contract: between PRs, the system must still
      produce valid per-workflow return contracts (workflows don't
      depend on each other, so single-workflow refactors stay isolated)
- [ ] Principle 2 (Anthropic skill) boundary preservation:
      NON-NEGOTIABLE block contents from each deprecated master-agent
      re-encoded in the replacement skill's dispatch prompts — no
      behavioral regression, just relocation
- [ ] Auto-generated doc regen: after each Phase 3 PR merges, trigger
      `generate_docs.py` + `generate_workflow_docs.py` to refresh
      `docs/workflows/*`, `docs/DASHBOARD.md`, `docs/dashboard.html`
- [ ] Manual doc prune: each Phase 3 PR removes its workflow's
      references from `README.md`, `docs/specs/*`, `docs/plans/*`

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
