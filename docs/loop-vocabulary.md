# Loop Vocabulary — shared names → hub owners

Shared language for loop-pattern work: when future hub work builds, reviews, or discusses a
loop, it NAMES the pattern from these tables instead of reinventing (or re-describing) it.
Pointer pattern per `core/.claude/rules/configuration-ssot.md` — this doc maps industry names
to the hub asset that OWNS each concept; it never restates the owner's content. For the
per-SDLC-stage coverage/status map, see `docs/sdlc-loop-coverage.md` (not duplicated here).
Sources cited: the three capture files under `docs/process-improvement/sources/` and the hub's
own spec `docs/specs/loop-engineering-spec.md`.

## Table A — the 20 loop design patterns (sairahul)

Source: `docs/process-improvement/sources/2026-07-01-sairahul-20-loop-design-patterns.md`.

| # | Pattern | Hub owner |
|---|---|---|
| 1 | Generate → Critique → Rewrite | `core/.claude/skills/development-loop/SKILL.md`, `core/.claude/skills/fix-loop/SKILL.md`; critic ≠ generator per `core/.claude/rules/supervisor-verification.md` |
| 2 | Score-and-Retry | `.claude/agents/quality-gate-evaluator-agent.md` (hub-only); gate expressions in `config/workflow-contracts.yaml` |
| 3 | Multi-Critic | `core/.claude/skills/five-advisors/SKILL.md` (5 independent lenses) |
| 4 | Adversarial Critique | `core/.claude/skills/grill-me/SKILL.md`, `core/.claude/skills/adversarial-review/SKILL.md` |
| 5 | Judge Ensemble | `/five-advisors` peer-review + synthesis; context-blind reviewer in `.claude/rules/prompt-auto-enhance.md` |
| 6 | Reflexion | `.claude/tasks/lessons.md` (mistake → root cause → rule) + `core/.claude/skills/learning-self-improvement/SKILL.md` |
| 7 | Memory Update | auto-memory; `.remember/` handoff log; `core/.claude/skills/end-session/SKILL.md` checkpoints |
| 8 | Error Library | `.claude/hooks/post-failure-capture.sh` + `.claude/tasks/lessons.md` (searched at session start) |
| 9 | Success Pattern | **planned — plan item 4.1** (`plans/loop-engineering-adoption.md`); today only implicit in the synthesize flywheel |
| 10 | Memory Compression | `.claude/hooks/compaction-handoff.sh`; `.claude/rules/context-management.md` (scratchpad + compaction survival) |
| 11 | Plan → Execute → Replan | `core/.claude/skills/writing-plans/SKILL.md` → `core/.claude/skills/executing-plans/SKILL.md`; `core/.claude/rules/plan-before-coding.md` |
| 12 | Dynamic Workflow | **not covered — YAGNI.** Hub workflows are fixed DAGs (`config/workflow-contracts.yaml`); adopt on concrete need |
| 13 | Goal Decomposition | `goals.yml` (G0–G6 + DoDs); `core/.claude/skills/goal-creator/SKILL.md`; `project-manager-agent` pipeline decomposition |
| 14 | Progress Evaluation | Atlas Goal Pulse banner (reads `goals.yml`); `scripts/trust_score.py` `graduation_status()` |
| 15 | Constraint Satisfaction | required CI check `validate` + gate expressions (`config/workflow-contracts.yaml`); `hard_gates` in `config/trust-score.yml` |
| 16 | Branch-and-Explore | parallel `Agent(isolation:"worktree")` fan-out; worktree tier of `core/.claude/rules/agent-team-selection.md`; `/brainstorm` alternatives |
| 17 | Tree Search | **not covered — YAGNI.** Depth-unbounded exploration has no hub caller; adopt on concrete need |
| 18 | Debate | agent-team `--team` modes (peers challenge mid-flight); selection rule `core/.claude/rules/agent-team-selection.md` |
| 19 | Prompt Optimization | `.claude/rules/prompt-auto-enhance.md` pipeline; plugin `plugins/prompt-auto-enhance/` |
| 20 | Workflow Optimization | `core/.claude/skills/loop-engineering/SKILL.md` (self-* meta-loop); trust-score walk-phase (`scripts/simulate_walk_phase.py`) |

## Table B — Ng's three rings (nested loops at three timescales)

SSOT: `docs/specs/loop-engineering-spec.md` §3.5 (which owns the model, the timescales, and
the context-advantage gate-placement rule). Source capture:
`docs/process-improvement/sources/2026-06-30-andrew-ng-3-product-development-loops.md`.

| Ring | Timescale | Hub implementation (pointers into spec §3.5) |
|---|---|---|
| 1 — Machine (agentic coding loop) | minutes | the spec §3 DAG: DISCOVER → PLAN → EXECUTE → VERIFY → SHIP\|FEEDBACK → LEARN |
| 2 — Developer feedback | hours | `/goal-creator` contracts; `core/.claude/skills/escalation-report/SKILL.md` + triage inbox; `core/.claude/rules/human-approval-gates.md` |
| 3 — External feedback | days–weeks | dogfood flywheel (`/synthesize-hub`); `scripts/aggregate_telemetry.py`; downstream `learnings.json` |

## Table C — Karpathy's 9 harness rules

Source: `docs/process-improvement/sources/2026-karpathy-loops-md-field-notes.md`.

| § | Rule | Hub encoding | Coverage |
|---|---|---|---|
| I | Write the loop, not the prompt | `/loop` + `/goal` (platform); `core/.claude/skills/loop-engineering/SKILL.md`; the platform-native taxonomy + routing table (which primitive for which task shape) is `docs/specs/loop-engineering-spec.md` §3.7 | full |
| II | Separate the roles (planner/generator/evaluator) | maker `plan-executor-agent` ≠ checker `code-reviewer-agent`; `core/.claude/rules/independent-test-verification.md`, `supervisor-verification.md` | full |
| III | Negotiate the contract first | `core/.claude/rules/plan-before-coding.md`; `/goal-creator` contracts; step contracts in `config/workflow-contracts.yaml` | **partial** — contracts are authored + gated, but there is no generator↔evaluator argue-on-disk negotiation step |
| IV | Write to disk, not to context | `.claude/tasks/` (todo + lessons); `.remember/`; `.workflows/loop-engineering/state.json`; `.claude/hooks/compaction-handoff.sh`; git history | full |
| V | Let the loop restart | Ralph-style `/loop` re-entry; bounded FEEDBACK arm (spec §3/§4); escalation fixes the CONTRACT, not the build (spec §3.5) | **partial** — retry/heal is encoded; a deliberate "throw it away and rebuild" restart is not an explicit step |
| VI | Score the subjective | weighted signals in `config/trust-score.yml`; prompt-auto-enhance grade rubric | **partial** — no calibrated taste rubric (design/originality/craft) with reference anchors |
| VII | Read the traces | `.claude/hooks/prompt-logger.sh`; telemetry miss-logs (`.claude/.enhance-misses.log` etc.); `/escalation-report` artifacts | **partial** — traces are captured, but grep-the-divergence transcript review is practiced ad hoc, not encoded |
| VIII | Delete the harness | `core/.claude/rules/rule-curation.md` (reactive, prune what the model does free); `.claude/skills/cc-adoption-scout/` (adopt-platform, delete hand-rolled) | full |
| IX | The bottleneck always moves | goal-pulse cadence (`goals.yml`); `/self-improve` + `/learn-n-improve` continuous-improvement loop | full |

## Other named loops (quick map)

- **Ralph loop** (Geoffrey Huntley — bare `while :; do cat PROMPT.md | claude-code; done`; "sit
  on the loop, not in it"): history + lineage in `plans/loop-goal-framework-research.md` §2.5c.
  The hub deliberately runs the *bounded* descendant — native `/loop`/`/goal` plus the spec §4
  termination guarantees — never the stop-condition-free original.
- **Willison's brakes** (budgets/kill-switches for unattended loops; external — no in-repo
  capture yet): `global_retry_budget` / `max_retries_per_step` in `config/workflow-contracts.yaml`;
  `max_cycles` + wall-clock cap (spec §4); `hard_gates` in `config/trust-score.yml`;
  off-switches `AUTO_PR_DISABLE=1` / `AUTO_MERGE=0` (autonomous branch lifecycle).
- **Anthropic's gather → act → verify → repeat** (agent-loop docs, cited in spec §1): encoded as
  the spec §3 DAG and, per-change, the 7-step workflow in `.claude/rules/workflow.md`
  (understand → test → implement → fix-loop → verify → commit).

## Not-covered ledger (honest gaps, adopt only on concrete need)

| Pattern | Status |
|---|---|
| #12 Dynamic Workflow | not covered — YAGNI (fixed DAGs by design) |
| #17 Tree Search | not covered — YAGNI (no caller) |
| #9 Success Pattern | planned — plan item 4.1, `plans/loop-engineering-adoption.md` |
| Karpathy §III / §V / §VI / §VII | partial — see Table C notes |
