# Contract: agent-team-ready pipeline + TODO test build

**Executor:** /goal (built-in autonomous run)   ·   **Created:** 2026-06-23
**Status:** DRAFT — owner will refine over several rounds before execution. Do NOT run yet.
**Mission:** Make every workflow the TODO-tracker build requires *agent-team-ready* at the
resource level (each skill/agent/rule per the §12 inventory), then build a TODO tracker
end-to-end USING those upgraded team-workflows (in an isolated sibling repo), looping
upgrade→build→fix until the app runs and its tests pass. "Done" = the required workflows are
team-ready and CI-green in the hub, the TODO app is built by the team-workflows and works,
all loop-surfaced issues are fixed, and reliability/cost results are recorded.

> ## DRAFT — refinement points the owner will iterate on (NOT open questions; current decisions)
> These are stated decisions so the contract is runnable, but they are the most likely things
> to change in refinement rounds:
> - **A1 — TODO app stack:** Vite + React + TS + Tailwind frontend + a small Hono (Node) API +
>   vitest (unit) + Playwright (E2E). 3-way teammate partition: `web/` · `api/` · `tests/`.
> - **A2 — Reliability bar:** a team completes a stage end-to-end on **≥2 of 3 runs, no rescue**.
> - **A3 — Workflow set to upgrade:** Clarify(`brainstorm`,`research-mode`), Execute
>   (`development-loop`,`executing-plans`,`implement`,`tdd`,`fix-loop` + `plan-executor-agent`,
>   `planner-researcher-agent`), Verify(`auto-verify`+`tester-agent`, `code-review-workflow`/
>   `review-gate` + `code-reviewer-agent`/`security-auditor-agent`). Plan/Commit made
>   team-COMPATIBLE only (not forced to spawn teams).
> - **A4 — Per-stage token budget ceiling:** 400k output tokens/stage; halt-and-report a stage
>   that exceeds it (the experiment is spend-bounded).
> - **A5 — Sibling repo path:** `../todo-team-tracker/` (own git, outside the hub tree).

## §0.1 Worktree isolation

> **First action of the run, before §0.2 and any stage. Non-negotiable.** The HUB portion of this
> run MUST execute in a **dedicated git worktree**, never the user's primary interactive checkout.
> The TODO app is a SEPARATE repo (§Stage E) and is unaffected by this isolation.
>
> 1. **Isolate:** `root=$(git rev-parse --show-toplevel)`. If `root` is the user's primary checkout
>    (not an already-dedicated run worktree), create and switch before any stage:
>    `git worktree add ../claude-best-practices-run-agent-teams -b auto/agent-teams-pipeline-upgrade`
>    and run every hub stage there.
> 2. **Claim it:** export a unique `RUN_TOKEN` (e.g. `agent-teams-$RANDOM`) and write the lock:
>    `printf '%s\n' "$RUN_TOKEN" > "$(git rev-parse --show-toplevel)/.run-active.lock"`. A pre-commit
>    hook HARD-BLOCKS any commit whose `RUN_TOKEN` does not match the lock.
> 3. **Release on exit:** the run's FINAL action (after merge/push, OR on any halt/defer) removes the
>    lock: `rm -f "$(git rev-parse --show-toplevel)/.run-active.lock"`. `.run-active.lock` is gitignored.
> 4. **Self-clean ON SUCCESS ONLY:** after the hub branch is merged + pushed + lock released, `cd` to
>    the primary repo root and `git worktree remove --force ../claude-best-practices-run-agent-teams ;
>    git branch -D auto/agent-teams-pipeline-upgrade ; git worktree prune`. On DEFER/HALT, keep the
>    worktree + branch to resume (release only the lock).

## §0.2 Idempotency preflight

> **First action after §0.1, before ANY stage. Non-negotiable.** A parallel session may already have
> implemented part of this. This contract must be safe to run at any time without redoing finished work.
>
> 1. **Read the coverage/gap ledger** — `plans/agent-teams-incorporation.md` §12 (the per-resource
>    team-readiness tracker, with status checkboxes) is the single source of truth for what is done.
> 2. **For every resource/stage, check the ledger + actual code + `git log` before building.** If the
>    §12 status is done or the code already implements it (grep/read to confirm — don't trust the ledger
>    blindly), SKIP the build, do a verify-only pass, move on. If partial, build only the missing delta.
> 3. **Record every skip** in the final report's "skipped (already covered)" list, and tick §12.

## §0.3 Progress log

> **Append-only progress log for the entire run. Update BEFORE moving on from each stage/event.**
>
> 1. **Location:** `docs/contracts/.run/agent-teams-pipeline-upgrade-PROGRESS.md` (in this run's
>    worktree; `.run/` is gitignored). Read cross-session via `git worktree list`.
> 2. **First line:** slug · branch · worktree · start time · contract path · one-line mission.
> 3. **Append a SHORT entry (≤2 lines) at:** stage start; stage done (with gate result); every major
>    defect; every "something not working" event + what you did; each independent-review outcome; each
>    defer/skip; each blocker/halt; the final result.
> 4. **Entry format:** `[YYYY-MM-DD HH:MM] <STAGE|PROGRESS|DEFECT|EVENT|DECISION|RECOVERY|BLOCKER|DONE> — <≤2-line summary>`.
> 5. **At run-end, route learnings per `core/.claude/rules/learnings-routing.md`** (GENERIC →
>    skill/process rule; PRODUCT-SPECIFIC → product doc/this contract; prefer a gate over prose;
>    one canonical home, dedup). Auto-write only the one-line lessons-log entry; everything else is
>    PROPOSE-only for approval.
> 6. **Run-end SUMMARY:** DONE · PENDING (+reason) · BLOCKED (+why) · NEXT (single next action + owner).

## Scope boundary
- **In scope (hub tree):** the §12-listed required-workflow resources (skills/agents/rules in
  `core/.claude/`), their team-readiness upgrades, the `team-*` hooks + `agent-team-selection` rule,
  `registry/patterns.json`, `scripts/tests/`, and the §12 tracker doc. Provisioning tier flip
  (nice-to-have → must-have) + rule self-gating per the §3a decision in
  `docs/specs/agent-teams-measure-first-experiment-spec.md`.
- **In scope (sibling repo `../todo-team-tracker/`):** the TODO app built by the team-workflows.
- **Out of scope:** deprecated `*-master-agent` files (never dispatch); workflows the TODO build does
  NOT use; the hub's `.claude/` operational-only resources beyond what §12 names; any production deploy.
- **Goal type:** mixed — propagation/refactor (resource upgrades) + fresh build (TODO app) + bug-fix loop.

## Context to read first
- `plans/agent-teams-incorporation.md` — §11 (real captured hook payload schema) + §12 (the tracker/ledger). The map of what to upgrade + done-state.
- `docs/specs/agent-teams-measure-first-experiment-spec.md` — the staged plan, win bar (D>B), reliability bar, and §3a must-have-dormant provisioning decision.
- `docs/claude-references/agent-teams.md` — the feature: teams form via `claude --bg` (NOT `-p`); hooks `TaskCreated`/`TaskCompleted`/`TeammateIdle`; in-process on Windows.
- `core/.claude/rules/agent-orchestration.md` — single-level dispatch convention; skill-at-T0; how workflows already dispatch workers (the thing being upgraded to teams).
- `core/.claude/rules/agent-team-selection.md` + `core/.claude/hooks/team-*.sh` — the already-built scaffolding (gotcha: hooks are calibrated to the real schema; do not regress them).
- `CLAUDE.md` — the two-`.claude/`-dirs boundary, registry-maintenance steps, full-local-CI gate, autonomous git lifecycle. (CWD trap: run hub Python with `PYTHONPATH=.`.)

## Pre-made design decisions (the run must NOT pause on these)
1. **Teams run via `claude --bg`** (a full background session forms a team); headless `-p` does NOT form a team — never use `-p` for a team step. One team per session; in-process mode on Windows.
2. **"team-ready" per type:** orchestrator skill → gains a `--team` path that spawns a real team where the work is team-shaped, file-partitioned, with the `team-*` hooks active; degrades to the existing flat-subagent path when the env var is off. Agent → works as a teammate (no `skills`/`mcpServers` frontmatter reliance; tools sufficient; peer-prompt via SendMessage/task tools). Rule → notes the teammate boundary. Plan/Commit steps stay team-COMPATIBLE (no pointless team spawn).
3. **Provisioning = must-have-dormant** (§3a): flip the 4 team patterns to `tier: must-have`; the `agent-team-selection` rule opens with a self-gating line — "only relevant if `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; otherwise ignore." Hooks ship pre-wired-but-inert.
4. **TODO app (A1):** Vite + React + TS + Tailwind `web/`; Hono API `api/` (localStorage is NOT the persistence signal — the API + its store is); vitest unit + Playwright E2E `tests/`. Features: add / list / toggle-complete / delete / filter (all/active/done); persistence via the API.
5. **File partition for the build team:** teammate-web owns `web/`, teammate-api owns `api/`, teammate-tests owns `tests/` — no two teammates write the same file (the merge-collision guard).
6. **Reliability (A2):** each team stage passes only on ≥2/3 end-to-end completions with no rescue and clean honest hook audit (no fabricated `team=?` or wrong session-derived values).
7. **Hub git:** conventional commits, feature branch `auto/agent-teams-pipeline-upgrade`, PR, CI-gated squash-merge; NO force-push, NO `--no-verify` (deny-rules). Sibling repo: its own `git init`, its own commits, never added to the hub tree (`product-incubation`).
8. **Autonomous run = Auto permission mode** (`decision-authority.md` S7): launch the executor with `--permission-mode auto`.

## Stages
### Stage A: Harness + provisioning prep (cheap, hub)
- **Do:** add the self-gating line to `core/.claude/rules/agent-team-selection.md`; flip the 4 team patterns to `tier: must-have` in `registry/patterns.json` (resync normalized sha256 hashes); wire the 3 `team-*` hooks pre-wired-but-inert into the hub experiment harness; run `generate_docs.py` + the full local CI (`dedup_check.py --validate-all`, `--secret-scan`, `workflow_quality_gate_validate_patterns.py`, `pytest`). Tick §12 rows.
- **Acceptance:** full local CI PASS (validate-all, secret-scan clean, validator PASS, pytest all-green); the rule self-gates; registry hashes match. Commit one conventional commit.

### Stage B: Verify workflow → team (SAFE read-only, mechanism proof)
- **Do:** add a `--team` path to `code-review-workflow`/`review-gate` that spawns a real review team (correctness / security / tests lenses) via `--bg`, sharing+challenging before the lead synthesizes; make `code-reviewer-agent`, `security-auditor-agent`, `tester-agent` teammate-ready (frontmatter audit). Validate by running the team review on a real recent hub PR diff, 3 attempts.
- **Acceptance:** ≥2/3 runs complete end-to-end, no rescue; all 3 hooks fire with honest audit; a usable synthesized review is produced; CI green; §12 rows ticked. One commit.

### Stage C: Execute workflow → team (RISKY parallel edits)
- **Do:** add a `--team` build path to `development-loop`/`executing-plans`/`implement` that partitions tasks by file ownership across teammates and runs the build with the hooks active; make `plan-executor-agent`, `planner-researcher-agent` teammate-ready. Validate by having the team build ONE small self-contained module in a throwaway scratch dir, 3 attempts, asserting no merge collisions.
- **Acceptance:** ≥2/3 runs complete, no rescue, no unresolved file collisions; module builds + its tests pass; honest hook audit; CI green; §12 ticked. One commit.

### Stage D: Remaining required workflows → team-ready (hub)
- **Do:** make Clarify (`brainstorm` advisor-panel `--team`, `research-mode` parallel), and team-COMPATIBLE Plan/Commit, plus the supporting rules (independent-test-verification, supervisor-verification self-gate to the teammate boundary). Update §12.
- **Acceptance:** each upgraded resource has a green unit test (or doc-only change validated); CI green; §12 status reflects reality. One commit per logical change.

### Stage E: Build the TODO app USING the team-workflows (sibling)
- **Do:** `git init ../todo-team-tracker/`; provision the hub patterns into it (`recommend.py --local ../todo-team-tracker --provision`); set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for the build session; drive the build through the UPGRADED team-workflows end-to-end (Clarify → Plan → Execute team build → Verify team review), file-partitioned per decision #5. Up to 3 full attempts for the A2 bar.
- **Acceptance:** the app builds; `web/` renders the TODO UI; the `api/` persists (independent API read-back of a created todo — not a closed dialog); ≥2/3 no-rescue; no merge collisions. (Sibling repo commits.)

### Stage F: Iterate to working (fix-loop, sibling)
- **Do:** run the app + its full test suite; for every failure, run the team Verify + `/fix-loop` until green; apply per-iteration persistence verification (`e2e-persistence-verification`) and output plausibility on any computed value.
- **Acceptance:** `vitest` unit + `playwright` E2E all green; a created todo is verified persisted via API read-back AND a reloaded-UI row-count assertion; the app runs.

### Stage G: Measure + report
- **Do:** record per-stage reliability (pass/fail, rescues), token cost vs a single flat-subagent baseline build, quality delta, coordination failures, to a calibration note (and the trust-score ledger if present). Write the final report.
- **Acceptance:** the D>B verdict is recorded with evidence; §12 statuses final; report written.

## Verification gates
> **All global rules in `.claude/rules/` are operative for this run.** Test by BLAST RADIUS of the
> changed surface — full depth in every layer the change touches, not "render-only". Placement per
> `core/.claude/rules/testing.md` + `e2e-best-practices.md`.

| Gate | Hub rule (loads transitively) | What it gates | Fires when |
|---|---|---|---|
| **Supervisor verification** | `supervisor-verification.md` | Reproduce the claimed gate + inspect substance; for the TODO UI, DRIVE the running app (screenshot + ARIA + console + interact) | every team/worker output; UI rows on `web/` changes |
| **Blind test verification** | `independent-test-verification.md` | Every test verdict re-checked by a SEPARATE context-blind agent given the same inputs + raw evidence | any test verdict (non-skippable) |
| **Output plausibility** | `output-plausibility-verification.md` | Computed user-facing values domain-SANE on the DEFAULT path | the diff reaches a computed/user-facing value |
| **Persistence verification** | `e2e-persistence-verification.md` | A created todo actually persisted — **independent API read-back** (GET the just-created todo), per-iteration in loops, + reload + assert row count. A closed dialog is NOT a saved row | any TODO write path |
| **Bug-triage discipline** | `bug-triage-discipline.md` | Each fixed bug carries "why was this missed?" + repo-wide sibling-class audit before close | any bug-fix in Stage F |
| **Honest team audit** | this contract | The `team-*` hook audit log shows real `session=`/`team=` values, never fabricated/`?` — regression guard for the calibrated hooks | every team stage |
| **DoD verbs** | `dod-verbs.md` | Every DoD criterion states ACTION + COMPLETENESS BAR | DoD authored |
| **Static gates** | hub: `PYTHONPATH=. python -m pytest scripts/tests/` + the 3 validators · sibling: `vitest` + `tsc --noEmit` + `playwright test` | type-check + lint + tests green for each tree the change touches | every code stage |

**Evidence-handoff note:** browser-automation may write screenshots to the session/primary worktree;
before handing evidence to the blind verifier, copy/absolute-path artifacts into the run worktree's
evidence dir and `ls`-confirm each exists.

## Failure-recovery budget
- **Per-task fix budget:** ~15 attempts (≈5 inline → `/fix-loop` → `/systematic-debugging`) → then DEFER the task and continue; do NOT halt the whole run.
- **Tool-hang recovery (browser/MCP/`--bg` team):** 3 cycles — (1) wait + retry; (2) close + re-open / `claude stop`+respawn the team session; (3) kill + restart the background dev server (captured PID) + retry. All 3 fail → log DEFERRED + `completed (deferred)` + continue.
- **Per-stage token ceiling (A4):** 400k output tokens/stage → halt-and-report that stage (spend-bounded experiment), do not silently overrun.
- **Hard halt ONLY:** dependency install failure; a decision contradiction in this contract; irrecoverable build break after the full fix budget; OS permission denial; missing required credential. Context-budget anxiety is NOT a halt — hand off via a one-line continuation note, never fake-complete.

## Commit + push policy
- **Granularity:** one conventional commit per stage (hub); logical commits in the sibling.
- **Message format:** Conventional Commits (`core/.claude/rules/git-collaboration.md`).
- **Branch / push target (hub):** `auto/agent-teams-pipeline-upgrade` → PR → CI-gated squash-merge. NO direct main push, NO force-push, NO `--no-verify`.
- **Sibling:** local `git init` + commits in `../todo-team-tracker/`; never `git add` the sibling into the hub.
- **Do NOT stage:** `.run-active.lock`, `test-results/`, `test-evidence/`, `.claude/.team-*.log`, any sibling path from within the hub.

## Definition of Done (ACTION + COMPLETENESS BAR — load-bearing)
- [ ] **Upgrade** the §A3 required workflows + their resources to team-ready, EACH verified by a passing unit test or a driven run; §12 status reflects every one as done with evidence.
- [ ] **Flip** the 4 team patterns to `must-have` + the rule self-gates + hooks ship pre-wired-but-inert; full hub local CI is green (4 validators + pytest).
- [ ] **Build** the TODO tracker in `../todo-team-tracker/` end-to-end BY the upgraded team-workflows (not raw spawns), with the `web/`+`api/`+`tests/` partition; the app runs.
- [ ] **Persist-verify** a created todo via independent API read-back AND a reloaded-UI row-count assertion (per `e2e-persistence-verification`); `vitest` + `playwright` all green.
- [ ] **Reliability:** every team stage met ≥2/3 no-rescue with honest hook audit; rescues/failures recorded.
- [ ] **Measure:** record the D>B verdict — team reliability + token cost vs the flat-subagent baseline + quality delta — in a calibration note.
- [ ] All baked-in verification gates passed (or each skip recorded with reason).
- [ ] Final report written (below).
- [ ] Run-end SUMMARY (DONE / PENDING / BLOCKED / NEXT) in PROGRESS.md + final report.

## Guardrails (hard stops)
- No new hub dependencies; the sibling app uses only its own declared deps.
- No design reinvention — upgrade the EXISTING workflows/agents; do not rewrite them from scratch.
- No synthetic/fake data; surface uncertainty as `**Assumption:** X`.
- NEVER write product code into the hub tree — the TODO app lives only in `../todo-team-tracker/` (`product-incubation`).
- NEVER dispatch a deprecated `*-master-agent`.
- NEVER regress the calibrated `team-*` hooks (honest audit, real schema) — the honest-audit gate guards this.
- NEVER use headless `-p` for a team step (it does not form a team) — always `claude --bg`.

## Final report (what the closing report must contain)
- What shipped, per stage, with commit SHAs (hub) and the sibling repo's final state.
- Skipped (already covered) list from the §0.2 preflight.
- The D>B measurement: reliability table, token cost vs baseline, quality delta, coordination failures.
- LEARNINGS TO FOLD BACK (PROPOSE-only — routed per `learnings-routing.md`).
- The DONE / PENDING / BLOCKED / NEXT summary.

## Authorization trail (decisions resolved in this draft)
| Fork | Decision | Why |
|---|---|---|
| Scope of workflows | Maximalist — all TODO-build-required workflows, resource-level (A3) | Owner override 2026-06-23: the upgrades ARE the deliverable, not a subset |
| Teams direct vs upgraded workflows | Build the app THROUGH the upgraded team-workflows | Owner: a build without the upgraded workflows is pointless |
| Staging | Verify (safe) before Execute (risky) before the full build | De-risk the merge-conflict path last (measure-first spec) |
| Provisioning | must-have-dormant, env-var master switch | Owner decision §3a |
| App placement | sibling `../todo-team-tracker/` | `product-incubation` — product code never in the hub tree |
| App stack (A1) | Vite+React+TS+Tailwind + Hono API + vitest/Playwright | Clean 3-way teammate partition; refinable |
| Reliability bar (A2) | ≥2/3 no-rescue per stage | Owner: D (reliable end-to-end) is the primary win bar |
| Permission mode | Auto (autonomous run) | `decision-authority.md` S7 |

## References (load transitively)
- `core/.claude/rules/{supervisor-verification, independent-test-verification, output-plausibility-verification, e2e-persistence-verification, dod-verbs, bug-triage-discipline, testing, e2e-best-practices, git-worktrees, git-collaboration, agent-orchestration, agent-team-selection, product-incubation, learnings-routing}`
- `plans/agent-teams-incorporation.md` (§11 schema, §12 tracker/ledger)
- `docs/specs/agent-teams-measure-first-experiment-spec.md` (staged plan, win bar, §3a provisioning)
- `docs/claude-references/agent-teams.md` (feature mechanics)
