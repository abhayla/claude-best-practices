# Contract: upgrade the build pipeline's workflows to agent-team-ready

**Executor:** `claude --bg` background session — **NOT** headless `/goal` / `claude -p` (probe-confirmed
2026-06-23: headless forms NO team). **CRITICAL — each team-stage runs as its OWN single-stage `claude --bg`
session** (one team = one session = one stage). A single session **cycling** teammates across stages was
probe-confirmed UNRELIABLE 2026-06-23 — it spawned ZERO teammates and **narrated a fake team**. The only
reliable unit is single-stage `--bg` (verified 3×). The top-level run orchestrates: per team-stage it
launches a fresh `--bg` session, **verifies the team actually formed (ground-truth gate below)**, then proceeds.
·   **Created:** 2026-06-23
**Status:** A2/A3/A4 RESOLVED + goal-creator-compliant. **Probes 2026-06-23:** headless `/goal` forms NO
team; single-stage `--bg` DOES (3×); **a single `--bg` session running MULTI-stage team work is UNRELIABLE —
it spawned 0 teammates and narrated a FAKE team (1×)**. → Contract restructured: **each team-stage = its own
single-stage `--bg` session**, with a hard **team-actually-formed ground-truth gate** (members>1 + hooks) that
fails any fake-team stage. **KNOWN RISK:** autonomous team-spawning is **non-deterministic** (the model
sometimes does the work solo and fabricates team activity) — so the **first run MUST be SUPERVISED** (a human
verifies the per-stage team-formed ground truth), not fully unattended. Pending: (1) owner decision to run
SUPERVISED, and (2) ideally a per-stage-session orchestration validation. NOT yet safe for fully-unattended launch.
**Mission:** Upgrade EVERY workflow the standard build pipeline requires to be *agent-team-ready*
at the resource level (each skill/agent/rule per the §12 inventory), **baking in Anthropic's
documented multi-agent best practices** (no concurrent same-file edits, no inter-agent conflict,
properly-shaped tasks, cross-agent verification — see `docs/claude-references/multi-agent-best-practices.md`),
**test each upgrade**, and **declare the goal complete**. "Done" = every required workflow + its
resources is team-ready, best-practice-compliant, and CI-green in the hub, each verified by a test or
a small validation run; results recorded. **NO product/app is built by this contract.**

> ## Scope split (read this first — it changed 2026-06-23)
> - **THIS contract** (autonomous **`claude --bg`** background session, separate from your interactive
>   session): upgrade + test + declare-done the workflows ONLY. It does NOT build any application.
>   (Launched via `claude --bg`, NOT headless `/goal` — see the Executor note; headless forms no teams.)
> - **The monitoring session** (the owner's interactive session): after this goal is declared
>   complete, it builds a TODO tracker USING the upgraded workflows as a real-world VALIDATION
>   HARNESS — and when that build surfaces a workflow defect, it fixes the workflow and continues.
>   That work is OUT of this contract (tracked in `docs/specs/agent-teams-measure-first-experiment-spec.md`).
> ## Refinement points — RESOLVED (owner-confirmed 2026-06-23)
> - **A2 — Reliability bar [CONFIRMED]:** a team completes each validation run end-to-end on **≥2 of 3 runs, no rescue**.
> - **A3 — Workflow set [CONFIRMED]:** Clarify(`brainstorm`,`research-mode`), Execute(`development-loop`,`executing-plans`,
>   `implement`,`tdd`,`fix-loop` + `plan-executor-agent`,`planner-researcher-agent`), Verify(`auto-verify`+
>   `tester-agent`, `code-review-workflow`/`review-gate` + `code-reviewer-agent`/`security-auditor-agent`)
>   actively USE teams. Plan/Commit made team-COMPATIBLE only (not forced to spawn a team).
> - **A4 — Token ceilings [RESOLVED]:** **400k output tokens/stage** halt-and-report, AND a **hard total-run cap
>   of 1.5M output tokens** (adjustable) — exceeding the total halts the whole run with a continuation note.

## §0.1 Worktree isolation
> **First action of the run, before §0.2 and any stage. Non-negotiable.** This run MUST execute in a
> **dedicated git worktree**, never the user's primary interactive checkout.
>
> 1. **Isolate:** `root=$(git rev-parse --show-toplevel)`. If `root` is the user's primary checkout,
>    create + switch before any stage:
>    `git worktree add ../claude-best-practices-run-agent-teams -b auto/agent-teams-pipeline-upgrade`
>    and run every stage there.
> 2. **Claim it:** export a unique `RUN_TOKEN` (e.g. `agent-teams-$RANDOM`) and write the lock:
>    `printf '%s\n' "$RUN_TOKEN" > "$(git rev-parse --show-toplevel)/.run-active.lock"`. A pre-commit hook
>    HARD-BLOCKS any commit whose `RUN_TOKEN` does not match the lock.
> 3. **Release on exit:** the run's FINAL action (after merge/push, OR on any halt/defer) removes the lock:
>    `rm -f "$(git rev-parse --show-toplevel)/.run-active.lock"`. `.run-active.lock` is gitignored.
> 4. **Self-clean ON SUCCESS ONLY:** after the branch is merged + pushed + lock released, `cd` to the
>    primary repo root and `git worktree remove --force ../claude-best-practices-run-agent-teams ;
>    git branch -D auto/agent-teams-pipeline-upgrade ; git worktree prune`. On DEFER/HALT, keep the
>    worktree + branch to resume (release only the lock).

## §0.2 Idempotency preflight
> **First action after §0.1, before ANY stage. Non-negotiable.**
>
> 1. **Read the coverage/gap ledger** — `plans/agent-teams-incorporation.md` §12 (the per-resource
>    team-readiness tracker with status checkboxes) is the single source of truth for what is done.
> 2. **For every resource/stage, check the ledger + actual code + `git log` before building.** If §12
>    says done or the code already implements it (grep/read to confirm — don't trust the ledger blindly),
>    SKIP the build, do a verify-only pass, move on. If partial, build only the missing delta.
> 3. **Record every skip** in the final report's "skipped (already covered)" list, and tick §12.

## §0.3 Progress log
> **Append-only progress log for the entire run. Update BEFORE moving on from each stage/event.**
>
> 1. **Location:** `docs/contracts/.run/agent-teams-pipeline-upgrade-PROGRESS.md` (this run's worktree;
>    `.run/` is gitignored). Read cross-session via `git worktree list`.
> 2. **First line:** slug · branch · worktree · start time · contract path · one-line mission.
> 3. **Append a SHORT entry (≤2 lines) at:** stage start; stage done (gate result); every major defect;
>    every "something not working" event + what you did; each independent-review outcome; each defer/skip;
>    each blocker/halt; the final result.
> 4. **Entry format:** `[YYYY-MM-DD HH:MM] <STAGE|PROGRESS|DEFECT|EVENT|DECISION|RECOVERY|BLOCKER|DONE> — <≤2-line summary>`.
> 5. **At run-end, route learnings per `core/.claude/rules/learnings-routing.md`** (GENERIC → skill/process
>    rule; PRODUCT-SPECIFIC → product doc/this contract; prefer a gate over prose; one canonical home, dedup).
>    Auto-write only the one-line lessons-log entry; everything else is PROPOSE-only for approval.
> 6. **Run-end SUMMARY:** DONE · PENDING (+reason) · BLOCKED (+why) · NEXT (single next action + owner).

## Scope boundary
- **In scope (hub tree only):** the §12-listed required-workflow resources (skills/agents/rules in
  `core/.claude/`), their team-readiness upgrades, the multi-agent best-practice bake-in, the `team-*`
  hooks + `agent-team-selection` rule, `registry/patterns.json`, `scripts/tests/`, the §12 tracker, and
  the §3a provisioning change (must-have-dormant + rule self-gating).
- **Out of scope:** building ANY application (the TODO build is the monitoring session's job); deprecated
  `*-master-agent` files; workflows the build pipeline does not use; any production deploy; the `.claude/`
  operational-only resources beyond what §12 names.
- **Goal type:** propagation/refactor (upgrade existing workflows + bake in best practices + verify).

## Context to read first
- `docs/claude-references/multi-agent-best-practices.md` — **THE standard.** Every workflow upgrade MUST satisfy the relevant items (A–G). This is the bake-in source.
- `plans/agent-teams-incorporation.md` — §11 (real captured hook payload schema; do NOT regress the calibrated hooks) + §12 (the tracker/ledger of what to upgrade + done-state).
- `docs/specs/agent-teams-measure-first-experiment-spec.md` — staged plan, win bar (D>B), §3a must-have-dormant provisioning, and (new) the two-phase execution architecture.
- `docs/claude-references/agent-teams.md` — feature: teams form via `claude --bg` (NOT `-p`); hooks `TaskCreated`/`TaskCompleted`/`TeammateIdle`; in-process on Windows; one team/session; no nested teams.
- `core/.claude/rules/agent-orchestration.md` — single-level dispatch convention + skill-at-T0 (how workflows dispatch workers today — the thing being upgraded).
- `core/.claude/rules/agent-team-selection.md` + `core/.claude/hooks/team-*.sh` — already-built scaffolding (calibrated to the real schema — preserve it).
- `CLAUDE.md` — two-`.claude/`-dirs boundary, registry-maintenance steps, full-local-CI gate, autonomous git lifecycle. CWD trap: run hub Python with `PYTHONPATH=.`.

## Multi-agent best practices the upgrades MUST bake in (and the gates that verify them)
Every team-mode workflow upgrade MUST implement these (source: `docs/claude-references/multi-agent-best-practices.md`),
and each is a per-stage verification gate — an upgrade that does not satisfy its applicable items is NOT done:

1. **Task shaping (A,E):** the orchestrator spawns self-contained tasks with objective + output format +
   out-of-scope, sized ~5–6/teammate. Verified by: the `team-task-created-deliverable` hook (`TaskCreated`)
   rejecting deliverable-less tasks (already built) + a test asserting the workflow emits shaped tasks.
2. **File/work partitioning — NO concurrent same-file edits (B, §H1):** the build orchestrator partitions
   work so each teammate owns a disjoint file set AND each parallel-editing teammate runs in its own **git
   worktree** (`isolation: worktree` on the build subagents / `claude --worktree` per session — teammates are
   NOT isolated by default). Verified by: a partition manifest + a post-run assertion that no file was written
   by 2+ teammates (git-blame / claim-file check) + worktree-lock evidence, zero unresolved collisions. A
   coupled cross-file change goes to ONE teammate, never split.
3. **Anti-conflict / no fighting (C):** division-of-labor heuristics in the spawn prompts; the lead WAITS
   (does not implement while teammates work); task dependencies enforce ordering. Verified by: review of
   the spawn prompts + a run showing no duplicated/contradictory edits.
4. **Cross-agent verification — doer ≠ checker (D, §H2):** a teammate's output is verified by a DIFFERENT
   agent, never self-attested, via the verification LADDER (in-prompt check → `/goal` condition → Stop hook →
   verification subagent). The verifier is a **read-only reviewer** (`tools: Read, Grep, Glob, Bash` only) in a
   fresh context, told to flag ONLY correctness/requirement gaps, and it must **show evidence (test output /
   command + result), not assertions**. Verified by: a separate verifier wired into the workflow +
   `independent-test-verification` / `supervisor-verification` applied at the teammate boundary.
5. **Quality-gate hooks (E, §H3):** the workflow runs with `TaskCreated` (scope gate), `TaskCompleted`
   (definition-of-done gate), `TeammateIdle` (quality backstop) active; plan-approval-for-teammates where the
   work writes code. Hooks honor the exit-code contract (exit 2 = block + stderr feedback; don't mix exit-2
   with JSON). Verified by: the honest-team-audit log showing the hooks fired with real values.
6. **Context passing (G, §H4):** all task context is in the spawn prompt (teammates inherit no history);
   the long-run plan is saved to a markdown file before the run (survives compaction); the upgrade accounts
   for `skills`/`mcpServers` frontmatter being DROPPED for teammates and Explore/Plan skipping CLAUDE.md.
   Verified by: spawn-prompt review.
7. **Team sizing & cost (F, §H5/H6):** 3–5 teammates; cheaper models per worker via `model`/`effort`
   frontmatter where viable; teams used ONLY for team-shaped work (Plan/Commit stay non-team); spend gauged
   on a small slice first. Verified by: the `agent-team-selection` rule routing + per-run token record.
8. **Teammate-readiness audit (§H4):** each agent used as a teammate is audited — no `skills`/`mcpServers`
   reliance, a sufficient `tools` allowlist, a specific auto-delegation `description`, and the session-restart
   pinning is honored (new/edited agent files reload only on restart). Verified by: a frontmatter audit per agent.

> **Full mechanism detail for every item lives in `docs/claude-references/multi-agent-best-practices.md`
> §A–§H** (the bake-in standard) — this contract names the requirements; the standard carries the how.

## Stages
### Stage A: Harness + provisioning + the upgrade standard (hub)
- **Do:** add the self-gating line to `core/.claude/rules/agent-team-selection.md`; flip the 4 team patterns
  to `tier: must-have` in `registry/patterns.json` (resync normalized sha256 hashes); wire the 3 `team-*`
  hooks pre-wired-but-inert; record the §"Multi-agent best practices" checklist above as the per-upgrade
  acceptance standard in §12; run `generate_docs.py` + full local CI.
- **Acceptance:** full local CI PASS (4 validators + pytest); rule self-gates; hashes match; §12 carries the standard. One commit.

### Stage B: Verify workflow → team (SAFE read-only) — bake in D, E, G
- **Do:** add a `--team` path to `code-review-workflow`/`review-gate` that spawns a real parallel review team
  (correctness / security / tests lenses) via `--bg`, sharing + challenging before the lead synthesizes, with
  a SEPARATE verifier (doer≠checker); make `code-reviewer-agent`, `security-auditor-agent`, `tester-agent`
  teammate-ready (frontmatter audit: no `skills`/`mcpServers` reliance). Validate by running the team review
  on a real recent hub PR diff, 3 attempts.
- **Acceptance:** ≥2/3 runs complete end-to-end, no rescue; all 3 hooks fire with honest audit; best-practice
  items 1,4,5,6 verified; a usable synthesized review produced; CI green; §12 ticked. One commit.

### Stage C: Execute workflow → team (RISKY parallel edits) — bake in A, B, C, D
- **Do:** add a `--team` build path to `development-loop`/`executing-plans`/`implement` that PARTITIONS tasks
  by disjoint file ownership, runs with the hooks active, the lead WAITS, and a verifier teammate checks the
  builder's output; make `plan-executor-agent`, `planner-researcher-agent` teammate-ready. Validate by having
  the team build ONE small self-contained throwaway module in a scratch dir, 3 attempts, asserting NO file
  written by 2+ teammates (collision check) and no contradictory edits.
- **Acceptance:** ≥2/3 runs complete, no rescue, ZERO unresolved file collisions, no duplicated/contradictory
  work; module builds + its tests pass; best-practice items 1–6 verified; honest hook audit; CI green; §12 ticked. One commit.

### Stage D: Remaining required workflows → team-ready (hub) — bake in A, G
- **Do:** make Clarify (`brainstorm` advisor-panel `--team`; `research-mode` parallel) and team-COMPATIBLE
  Plan/Commit; self-gate the supporting rules (`independent-test-verification`, `supervisor-verification`) to
  the teammate boundary. Update §12.
- **Acceptance:** each upgraded resource has a green unit test (or doc-only change validated); the relevant
  best-practice items verified; CI green; §12 reflects reality. One commit per logical change.

### Stage E: Measure + declare complete (hub)
- **Do:** record per-stage reliability (pass/fail, rescues), token cost vs a single flat-subagent baseline,
  and a **best-practice-compliance checklist** (items 1–7, per workflow) to a calibration note (+ trust-score
  ledger if present). Write the final report. Tick every §12 row to done-with-evidence.
- **Acceptance:** all §A3 workflows are team-ready + best-practice-compliant + CI-green; the report records the
  compliance checklist + reliability/cost; the goal is declared COMPLETE.

## Verification gates
> **All global rules in `.claude/rules/` are operative.** Test by BLAST RADIUS of the changed surface.

| Gate | Hub rule / mechanism | What it gates | Fires when |
|---|---|---|---|
| **Best-practice compliance** | `docs/claude-references/multi-agent-best-practices.md` (items 1–7 above) | Each team-mode upgrade satisfies the applicable task-shaping / partitioning / anti-conflict / cross-verification / hook / context / sizing items | every workflow upgrade |
| **No-collision (worktree-isolated)** | `isolation: worktree` + git-blame / claim-file check | Each parallel-editing teammate runs in its own worktree; no file written by 2+ teammates; zero unresolved collisions | every Execute team run |
| **Doer≠checker ladder** | `multi-agent-best-practices.md` §H2 | A read-only reviewer (fresh context) verifies each builder's output and SHOWS evidence, not assertions; flags only correctness gaps | every team build output |
| **Supervisor verification** | `supervisor-verification.md` | Reproduce the claimed gate + inspect substance; drive any UI a workflow renders | every team/worker output |
| **Blind test verification** | `independent-test-verification.md` | Every test verdict re-checked by a SEPARATE context-blind agent (doer≠checker) | any test verdict (non-skippable) |
| **Team ACTUALLY formed (anti-fake-team)** | `~/.claude/teams/<name>/config.json` `members` + hook payloads | A stage is FAILED unless ground truth shows **>1 member** (real teammates joined, not just the lead) AND `TaskCreated`/`Completed` hooks fired. The model narrating "teammates" with `members==[team-lead]` + 0 hooks is a FAKE team — never accept it (probe-confirmed failure mode 2026-06-23) | every team stage, BEFORE accepting its output |
| **Honest team audit** | this contract | The `team-*` hook audit log shows real `session=`/`team=` values, never fabricated/`?` (regression guard for the calibrated hooks) | every team stage |
| **Bug-triage discipline** | `bug-triage-discipline.md` | Each fixed workflow bug carries "why was this missed?" + sibling-class audit | any bug-fix |
| **DoD verbs** | `dod-verbs.md` | Every DoD criterion states ACTION + COMPLETENESS BAR | DoD authored |
| **Static gates** | `PYTHONPATH=. python -m pytest scripts/tests/` + the 3 validators (`dedup_check --validate-all`, `--secret-scan`, `workflow_quality_gate_validate_patterns`) | hub tests + validators green for every change | every code stage |

**Evidence-handoff note:** before handing evidence to the blind verifier, copy/absolute-path artifacts into
the run worktree's evidence dir and `ls`-confirm each exists.

## Failure-recovery budget
- **Per-task fix budget:** ~15 attempts (≈5 inline → `/fix-loop` → `/systematic-debugging`) → then DEFER the task and continue; do NOT halt the whole run.
- **Tool-hang recovery (browser/MCP/`--bg` team):** 3 cycles — (1) wait + retry; (2) `claude stop` + respawn the team session; (3) kill + restart any background process (captured PID) + retry. All 3 fail → log DEFERRED + `completed (deferred)` + continue.
- **Token ceilings (A4):** 400k output tokens/stage → halt-and-report that stage; AND a hard **total-run cap of
  1.5M output tokens** → halt the whole run with a continuation note when reached. Do not silently overrun either.
- **Hard halt ONLY:** dependency install failure; a decision contradiction in this contract; irrecoverable build break after the full fix budget; OS permission denial; missing required credential. Context-budget anxiety is NOT a halt — hand off via a one-line continuation note, never fake-complete.

## Commit + push policy
- **Granularity:** one conventional commit per stage (per logical change in Stage D).
- **Message format:** Conventional Commits (`core/.claude/rules/git-collaboration.md`).
- **Branch / push target:** `auto/agent-teams-pipeline-upgrade` → PR → CI-gated squash-merge. NO direct main push, NO force-push, NO `--no-verify`.
- **Do NOT stage:** `.run-active.lock`, `test-results/`, `test-evidence/`, `.claude/.team-*.log`, any scratch/throwaway module dirs used for validation.

## Definition of Done (ACTION + COMPLETENESS BAR — load-bearing)
- [ ] **Upgrade** every §A3 required workflow + its resources to team-ready, EACH verified by a passing unit test or a small validation run; §12 status reflects every one as done-with-evidence.
- [ ] **Bake in** the multi-agent best practices (items 1–7) into every team-mode upgrade; the best-practice-compliance checklist is filled per workflow with evidence (not a single example — every team-mode workflow).
- [ ] **Verify** the team-correctness properties on a real team run: parallel-editing teammates are
  worktree-isolated, zero concurrent same-file collisions, no duplicated/contradictory edits, a read-only
  doer≠checker reviewer verified each builder's output SHOWING evidence (not assertions), hooks fired with
  honest audit — each asserted, not assumed.
- [ ] **Flip** the 4 team patterns to `must-have` + the rule self-gates + hooks ship pre-wired-but-inert; full hub local CI green (4 validators + pytest).
- [ ] **Reliability:** every team validation run met ≥2/3 no-rescue; rescues/failures recorded.
- [ ] **Measure + declare:** the report records the best-practice-compliance checklist + reliability + token cost vs the flat-subagent baseline; the goal is declared COMPLETE.
- [ ] All baked-in verification gates passed (or each skip recorded with reason).
- [ ] Final report written (below).
- [ ] Run-end SUMMARY (DONE / PENDING / BLOCKED / NEXT) in PROGRESS.md + final report. NEXT names the handoff to the monitoring session (build TODO app to validate).

## Guardrails (hard stops)
- No new hub dependencies.
- No design reinvention — upgrade the EXISTING workflows/agents; do not rewrite from scratch.
- No synthetic/fake data; surface uncertainty as `**Assumption:** X`.
- NEVER build a product/app in this contract — the TODO build is the monitoring session's job (out of scope).
- NEVER write product code into the hub tree (`product-incubation`).
- NEVER dispatch a deprecated `*-master-agent`.
- NEVER regress the calibrated `team-*` hooks (honest audit, real schema).
- NEVER use headless `-p` for a team step — always `claude --bg`.
- NEVER accept a stage whose team config shows ONLY the lead (`members==[team-lead]`) + 0 hook events — that
  is the model NARRATING a fake team (probe-confirmed 2026-06-23). Treat it as a FAILED stage and re-run it
  as a fresh single-stage `--bg` session; NEVER cycle teammates across stages within one session.

## Final report (what the closing report must contain)
- What shipped, per stage, with commit SHAs.
- Skipped (already covered) list from the §0.2 preflight.
- The best-practice-compliance checklist (items 1–7 × each team-mode workflow) with evidence.
- Reliability table + token cost vs the flat-subagent baseline.
- LEARNINGS TO FOLD BACK (PROPOSE-only — routed per `learnings-routing.md`).
- The DONE / PENDING / BLOCKED / NEXT summary; NEXT = handoff to the monitoring session.

## Authorization trail (decisions resolved in this draft)
| Fork | Decision | Why |
|---|---|---|
| TODO build in the contract? | **NO — removed** | Owner 2026-06-23: the contract upgrades workflows only; the build is the monitoring session's validation harness |
| Scope of workflows | Maximalist — all build-required workflows, resource-level (A3) | Owner: the upgrades ARE the deliverable |
| Best practices | Baked in from `docs/claude-references/multi-agent-best-practices.md` as requirements + gates | Owner: the workflows must follow all multi-agent best practices, verified |
| Staging | Verify (safe) before Execute (risky) | de-risk the merge-conflict path last |
| Provisioning | must-have-dormant, env-var master switch | Owner decision §3a |
| Reliability bar (A2) | ≥2/3 no-rescue per validation run | Owner: D (reliable end-to-end) is the primary win bar |
| Permission mode | Auto (autonomous run) | `decision-authority.md` S7 |

## References (load transitively)
- `docs/claude-references/multi-agent-best-practices.md` (THE bake-in standard)
- `core/.claude/rules/{supervisor-verification, independent-test-verification, output-plausibility-verification, dod-verbs, bug-triage-discipline, testing, git-collaboration, agent-orchestration, agent-team-selection, learnings-routing}`
- `core/.claude/skills/git-worktrees` (SKILL — worktree isolation mechanism, not a rule)
- `.claude/rules/product-incubation.md` (HUB-ONLY rule — present in this repo; not in `core/`)
- `plans/agent-teams-incorporation.md` (§11 schema, §12 tracker/ledger)
- `docs/specs/agent-teams-measure-first-experiment-spec.md` (staged plan, win bar, §3a provisioning, two-phase architecture)
- `docs/claude-references/agent-teams.md` (feature mechanics)
