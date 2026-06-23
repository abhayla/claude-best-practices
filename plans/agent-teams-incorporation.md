# Agent Teams → this hub: research + incorporation guide

> **Status:** LIVING DOCUMENT — keep updating as the feature evolves and as the hub
> adopts/measures more of it. Last updated: 2026-06-23.
> **Owner-approved scope (2026-06-23):** build the selection rule + teammate governance
> hooks + a hub-only five-advisors pilot, and maintain this as the implementation guide.
> **Source of truth for the feature itself:** `docs/claude-references/agent-teams.md`
> (cache, currency-checked 2026-06-23) and `docs/claude-references/agent-view.md`.

## 0. TL;DR

Agent teams coordinate multiple **full Claude Code sessions** (a lead + independently
addressable teammates) that **message each other** and **self-coordinate via a shared
task list** — a *different primitive* from the hub's subagents (which only report back to
their caller). It is **experimental, default-off** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`),
**no GA** as of Claude Code v2.1.186, and costs **~4–7× the tokens** of a single session.

It does **not** replace the hub's skill-at-T0 / flat-worker model. It is a complementary
tool for the *subset* of workflows where workers must **challenge each other** (review,
competing-hypothesis debugging, multi-advisor debate). The hub adopts it **opt-in,
measure-first** — never default-on.

## 1. Capability summary (verified, Claude Code v2.1.186)

| Aspect | Detail |
|---|---|
| What | Lead session + teammates, each a full independent Claude Code instance / context window |
| Communication | Mailbox — teammates message **each other** directly; you can address any teammate by name |
| Coordination | Shared task list (pending/in-progress/completed, dependencies, file-locked claiming); self-claim or lead-assign |
| Enable | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (settings.json `env` or shell). Default OFF |
| Teammate defs | Can reference any subagent type — its `tools` allowlist + `model` are honored; body appended to system prompt. **`skills`/`mcpServers` frontmatter NOT applied** to a teammate (it loads skills/MCP from project+user settings) |
| Display | `teammateMode`: `in-process` (default, any terminal) / `tmux` / `iterm2` (v2.1.186, needs `it2`). Split panes NOT on Windows Terminal/VS Code terminal |
| Hooks | `TaskCreated`, `TaskCompleted`, `TeammateIdle` — **exit code 2 = block + send feedback** |
| Cost | ~4–7× tokens vs single session (4× at init alone — each teammate reloads project context). Scales ~linearly with active teammate count |
| Status | **Experimental, default-off, no GA** as of v2.1.186 (2026-06-22) |

**Hard constraints (all still true at v2.1.186):** one team per session · no nested teams
(teammates can't spawn teammates) · no session resumption with in-process teammates
(`/resume`, `/rewind` don't restore them) · lead is fixed for the session's lifetime ·
permissions set at spawn (all teammates start with the lead's mode).

**Only official Anthropic blog post:** "Building a C compiler with a team of parallel
Claudes" (2026-02-05) — 16 parallel Opus agents, ~$20k, compiled Linux 6.9. The high-cost
ceiling, not a routine pattern.

## 2. Why it is orthogonal to the hub's doctrine

The hub's orchestration model (`core/.claude/rules/agent-orchestration.md`,
`workflow-master-template.md`, the skill-at-T0 convention) dispatches **flat worker
subagents that only report back**. Agent teams does **not** lift the "no nested dispatch"
behaviour teams care about — teammates *also* can't spawn teammates. It is a **lateral
peer-coordination** primitive, not deeper nesting. So it slots in **beside** subagents as a
selection option, governed by `core/.claude/rules/agent-team-selection.md`.

## 3. Hub-fit map

| Hub workflow | Fit | Why |
|---|---|---|
| `five-advisors` | ★★★ | Already *simulates* independent advisors who peer-review each other — teams makes it real. Read-only (no merge risk) → ideal first pilot |
| `debugging-loop` / `/systematic-debugging` | ★★★ | Competing-hypothesis debate is Anthropic's flagship use case; fights anchoring |
| `code-review-workflow` | ★★★ | Parallel reviewers (security/perf/tests) that share + challenge before the lead synthesizes |
| `self-improve` / scan workflows | ★★ | Multi-angle scanning maps to teammates, but mostly report-back → subagents already suffice |
| `development-loop`, `test-pipeline`, `documentation` | ★ | Sequential, same-file edits → docs say single session/subagents are better |
| PRD-to-Production (`project-manager-agent`) | ✗ | Long, sequential, stateful; no-resumption + lag + cost are disqualifying |

## 4. Incorporation status (owner-approved 2026-06-23)

| # | Item | Verdict | State | Artifact |
|---|---|---|---|---|
| 1 | Selection rule | ADOPT (distributable) | ✅ built | `core/.claude/rules/agent-team-selection.md` |
| 2 | Teammate governance hooks | ADOPT (distributable, opt-in) | ✅ built (unwired) | `core/.claude/hooks/team-task-completed-verifier.sh`, `team-teammate-idle-drain.sh`, `team-task-created-deliverable.sh` |
| 3 | `five-advisors` team pilot | MEASURE-FIRST (hub-only) | 📋 runbook (§6) | this guide |
| 4 | `code-review` / `debugging-loop` team variants | DEFER until pilot data | ⏸ not started | — |

## 5. Downstream distribution

- Rule + hooks live in `core/.claude/` → provisioned via `recommend.py`/`bootstrap.py`,
  registered in `registry/patterns.json`.
- **Opt-in by construction:** hooks are inert unless a project both wires them into
  `settings.json` **and** sets `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Zero behaviour
  change for projects that don't opt in (matches how `AUTO_MERGE=0` / `SECRET_SCAN_CMD`
  ship as opt-outs/pluggable knobs).
- Hooks default **fail-open**; hard-blocking (exit 2) only under `TEAM_GOVERNANCE_STRICT=1`
  — telemetry-first, matching `verifier-edge-guard.sh`.
- The pilot stays hub-only until calibrated against the trust-score ledger, then promotes
  to `core/` (the standard prove-in-hub-then-distribute path).

## 6. Pilot runbook — five-advisors as a real agent team (hub-only, measure-first)

> Goal: get REAL cost/effectiveness numbers on this hub's own work before committing the
> heavier review/debug variants. Read-only by design (no file edits → no merge conflicts).

**Preconditions**
1. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set (settings.json `env` or shell).
2. `teammateMode: "in-process"` (Windows-safe; split panes unavailable on Windows Terminal).
3. Default teammate model set in `/config` (teammates don't inherit the lead's `/model`).

**Run**
1. In a lead session, prompt: *"Spawn 5 teammates as independent advisors on `<decision>`.
   Each analyzes from a distinct lens (architecture / cost / risk / user / contrarian),
   in read-only plan mode. Then each reads the others' findings via the shared task list
   and challenges them anonymously. Do not edit files. Synthesize a final verdict."*
2. Require plan approval for teammates ("only approve plans grounded in cited evidence").
3. Lead synthesizes — same output contract as the existing `/five-advisors` skill.

**Measure (log to the trust-score ledger / a calibration note)**
- Total tokens vs a baseline single-session `/five-advisors` run on the same decision.
- Wall-clock to verdict.
- Verdict quality delta (did real peer-challenge surface something the simulated version missed?).
- Coordination failures (teammates not receiving messages, tasks not marked complete).

**Promote-or-reject gate:** promote a `core/` team variant only if the quality delta
justifies the measured cost multiplier on ≥3 real decisions. Otherwise keep the simulated
single-context `/five-advisors` (cheaper) and record the negative result here.

## 7. Open questions / to verify on a live run

- ~~Exact stdin payload schema for the three hooks~~ — **RESOLVED 2026-06-23, see §11.**
- Whether `TeammateIdle` exit-2 reliably re-engages a teammate (deferred — payload lacks a
  pending count; would require reading the on-disk task list, see §11).
- Real token multiplier on hub-shaped work (the 4–7× figure is community-reported).

## 11. Captured hook payload schema (live, in-process team, 2026-06-23)

A `claude --bg` background session (a full conversation — unlike `-p`, which does NOT form a
team) formed a real team `session-4a3e63c9` (lead + `dx-analyst` + `arch-analyst`). All three
hooks fired; the demo capture hook logged these REAL payloads:

```
TaskCreated   : { session_id, transcript_path, cwd, hook_event_name,
                  task_id, task_subject, task_description }
TaskCompleted : { ...same..., task_id, task_subject, task_description,
                  teammate_name, team_name }          # NO work-product / result field
TeammateIdle  : { session_id, transcript_path, cwd, permission_mode,
                  hook_event_name, teammate_name, team_name }   # NO pending-task count
```

**Bugs this exposed (all fixed 2026-06-23):**
1. `team-task-created-deliverable` read `.task.description`; real field is top-level
   `task_description` (+ `task_subject`). Was a silent no-op → now functional.
2. `team-task-completed-verifier` assumed a result/summary to scan for evidence — **the
   payload has none.** Repurposed to an honest completion **audit logger** (never blocks);
   real verification stays with the lead reproducing the gate.
3. `team-teammate-idle-drain` assumed a `pending_tasks` count — **not present.** Kept
   loop-safe; repurposed to an idle **audit logger**. Future: read `~/.claude/tasks/{team_name}/`
   (team_name IS in the payload) to count pending work and re-engage under strict mode.
4. A regression bug in the first fix: `eval`-based multi-field extraction ran a spaced
   `task_subject`'s second word as a shell command — replaced with safe per-field
   `jq` command substitution (also closes an injection vector). Pinned by a test.

Audit hooks append to `${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.team-activity.log` when a
`.claude` dir is present (else no-op). Tests in `scripts/tests/test_team_governance_hooks.py`
now use this real schema (13 tests).

## 9. Testing

Two tiers:

- **Tier 1 — deterministic (DONE, CI-gating):** `scripts/tests/test_team_governance_hooks.py`
  (19 tests) drives each hook via subprocess and pins the safety properties — fail-open by
  default, strict-mode hard-block **with stderr feedback**, evidence detection, idle
  **loop-safety** (never re-engage on an empty/unknown queue), malformed/empty-payload
  fail-open, registry registration, and a regression guard that the hooks never
  blanket-redirect stderr. `jq`-dependent assertions skip cleanly where `jq` is absent
  (the hooks correctly no-op/fail-open without it).
- **Tier 2 — live integration (PARTIALLY RUN 2026-06-23):**
  - **Finding A — headless `claude -p` does NOT form a real agent team.** A child session
    launched with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` + the demo settings *claimed* in
    its text to "spawn 2 teammates," but ground truth disproved it: **no `~/.claude/teams/`
    directory, no hook payloads captured, no `session-xxxxxxxx` task dir**. The model did the
    analysis in-context and narrated teams (shape-not-substance). Conclusion: **agent teams
    is an interactive-terminal feature** (the teammate panel you arrow-select, sessions you
    watch open/close) — it does not form under non-interactive `-p`.
  - **Finding B — multi-session open/close IS drivable via agent-VIEW** (the related
    feature). `claude --bg --name demo-alpha/--name demo-beta` spawned two real, independent
    Claude Code sessions (separate PIDs); `claude agents --json` showed them go
    dispatched → idle; `claude stop` + `claude rm` closed them (0 remaining). Verified live.
  - **Still pending — the hook payload schema (§7) is UNCAPTURED** because no team formed
    headlessly. It needs an **interactive** team run (see §6/§10). Hooks stay **unwired**
    until then; tighten the jq field paths the moment a real payload lands in
    `.claude/.team-demo/payloads.log`.

## 10. Interactive demo + payload-capture (the part that needs a human terminal)

Headless can't form a team, so the real team demo runs in an interactive terminal. A ready
harness lives in `.claude/.team-demo/` (gitignored): `settings.json` (enables the flag +
`teammateMode: in-process` + wires a payload-capture logger AND the three real governance
hooks) and `capture.sh` (logs each event's raw stdin to `payloads.log`).

**Run it (new terminal, this repo dir):**
```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --settings .claude/.team-demo/settings.json
```
Then paste a read-only team prompt, e.g.: *"Spawn 2 teammates to analyze the trade-offs of
a CLI TODO-comment tracker — one DX lens, one architecture lens; read-only; create a shared
task each, return 3 bullets, then synthesize."*

**What you'll see:** an agent panel below the prompt input listing the teammates; ↑/↓ selects
one, Enter opens its transcript, Esc interrupts. Teammates open as they're spawned and close
when shut down / the session ends. On Windows use `in-process` mode (split panes need tmux/iTerm2).

**After one run**, `.claude/.team-demo/payloads.log` holds the real `TaskCreated` /
`TaskCompleted` / `TeammateIdle` payloads → then tighten the hooks' jq field paths to match
and re-enable strict mode with confidence.

## 12. Pipeline resource inventory → team-readiness tracker

Goal: uniquely identify every Claude resource the 6-step build pipeline uses, then make each
one **agent-team-ready** (or explicitly keep it non-team). Inventory built by reading the
actual `core/.claude/` files (verified 2026-06-23 — no dead references). "Team-ready" means
different things per type:
- **Orchestrator skill** → can spawn a real team (not just flat subagents) where it helps, with
  file-partitioning + the governance hooks wired.
- **Agent** → works correctly when spawned as a *teammate*: no reliance on `skills`/`mcpServers`
  frontmatter (NOT applied to teammates), sufficient `tools` allowlist, prompt works as an
  independently-addressable peer using `SendMessage`/task tools.
- **Rule** → accounts for the teammate boundary (e.g. the lead reproduces the gate).
- **Hook** → has a team-event analog (`TaskCreated`/`TaskCompleted`/`TeammateIdle`).

### Readiness tiers
- 🟢 **SAFE-FIT** — read-only, benefits from peer-challenge/parallel analysis. **Zero merge risk → do first.**
- 🟠 **RISKY-FIT** — parallel *file edits*; high value but needs partition + merge handling. **Validate after SAFE.**
- ⚪ **KEEP NON-TEAM** — mechanical or single-coherent-owner; flat subagents / single-context are strictly better.

### Per-step resource map (entry points)
| Step | Resources (entry → dispatched) |
|---|---|
| 1 Clarify | skills `brainstorm`, `grill-me`, `research-mode`, `grill-with-docs`; agent `web-research-specialist-agent` |
| 2 Plan | skill `writing-plans`; rule `dod-verbs` |
| 3 Isolate | rule `product-incubation` *(hub-only)*; skills `bootstrap-dogfood-project` *(hub-only)*, `contribute-practice`, `synthesize-hub` |
| 4 Execute | skills `development-loop`, `executing-plans`, `implement`, `tdd`, `fix-loop`, `learn-n-improve`; agents `plan-executor-agent`, `planner-researcher-agent`; rules `workflow`, `plan-before-coding`, `tdd`, `testing` |
| 5 Verify | skills `auto-verify`, `code-review-workflow`, `review-gate`, `code-quality-gate`, `architecture-fitness`, `security-audit`, `change-risk-scoring`, `regression-test`; agents `tester-agent`, `code-reviewer-agent`, `security-auditor-agent`; rules `independent-test-verification`, `supervisor-verification`, `output-plausibility-verification` |
| 6 Commit | hooks `auto-git`, `auto-pr`; skills `post-fix-pipeline`, `request-code-review`, `receive-code-review`; agent `git-manager-agent`; rule `git-collaboration` |

### Per-upgrade acceptance standard (the bar every 🟢/🟠 upgrade is ticked against)

> **Recorded by Stage A of the pipeline-upgrade contract (`docs/contracts/2026-06-23-agent-teams-pipeline-upgrade.md`).**
> Source of the full mechanism: `docs/claude-references/multi-agent-best-practices.md` §A–§H.
> An upgrade is NOT done until it satisfies every item APPLICABLE to its tier, each verified by a
> test or a real validation run (not asserted). The item numbers below are the contract's items 1–8.

| # | Best-practice item | Applies to | How it's verified (gate) |
|---|---|---|---|
| 1 | **Task shaping (A,E)** — self-contained tasks: objective + output format + out-of-scope, ~5–6/teammate, effort-scaling in the orchestrator prompt | 🟢🟠 orchestrators | `team-task-created-deliverable` (`TaskCreated`) rejects deliverable-less tasks + a test asserting shaped tasks |
| 2 | **File/work partitioning (B,§H1)** — disjoint file ownership; each parallel-editing teammate in its OWN git worktree; a coupled cross-file change goes to ONE teammate | 🟠 execute only | partition manifest + post-run assertion no file written by 2+ teammates (git-blame/claim-file) + worktree-lock evidence |
| 3 | **Anti-conflict (C)** — division-of-labor heuristics in spawn prompts; the lead WAITS; task dependencies order the work | 🟢🟠 | spawn-prompt review + a run showing no duplicated/contradictory edits |
| 4 | **Cross-agent verification (D,§H2)** — doer≠checker: a SEPARATE read-only reviewer (`Read,Grep,Glob,Bash` only), fresh context, flags only correctness gaps, SHOWS evidence not assertions | 🟢🟠 all team output | verifier wired into the workflow + `independent-test-verification`/`supervisor-verification` at the teammate boundary |
| 5 | **Quality-gate hooks (E,§H3)** — `TaskCreated`/`TaskCompleted`/`TeammateIdle` active; plan-approval-for-teammates when work writes code; exit-code contract honored | 🟢🟠 | honest-team-audit log showing the hooks fired with real values |
| 6 | **Context passing (G,§H4)** — all task context in the spawn prompt; long-run plan saved to a markdown file; account for `skills`/`mcpServers` DROPPED for teammates + Explore/Plan skipping CLAUDE.md | 🟢🟠 | spawn-prompt review |
| 7 | **Team sizing & cost (F,§H5/H6)** — 3–5 teammates; cheaper per-worker models where viable; teams ONLY for team-shaped work; spend gauged on a small slice first | 🟢🟠 | `agent-team-selection` routing + per-run token record |
| 8 | **Teammate-readiness audit (§H4)** — each teammate agent: no `skills`/`mcpServers` reliance, sufficient `tools` allowlist, specific auto-delegation `description`, session-restart pinning honored | agents used as teammates | per-agent frontmatter audit |

### Master tracker (unique resources)

**✅ Already team-ready (built this session):** `agent-team-selection` (rule), `team-task-created-deliverable` / `team-task-completed-verifier` / `team-teammate-idle-drain` (hooks). These ARE the team-boundary scaffolding.

**Stage A (pipeline-upgrade contract, 2026-06-23):** the 4 scaffolding patterns above flipped `nice-to-have → must-have` (dormant by default — §3a env-var master switch); the rule carries the `EXPERIMENTAL_AGENT_TEAMS` self-gate line; the 3 `team-*` hooks wired pre-but-inert in `core/.claude/settings.json` (`TaskCreated`/`TaskCompleted`/`TeammateIdle`). The acceptance standard above is now recorded. ✅

**Stage B (Verify cluster, 2026-06-23) — LIVE-VALIDATED with a REAL team:** `code-review-workflow` gained a `--team` parallel-review-team mode (STEP 2-TEAM, baking in best-practice items 1,4,5,6); the 3 review agents passed the teammate-readiness audit (`security-auditor-agent` got a teammate note — no `Skill` tool as a teammate). **Validation run:** one `claude --bg` review team on the real PR #198 diff → ground truth **members=3** (`team-lead` + `correctness` + `tests`), **12 hook events** (2 TaskCreated + 2 TaskCompleted + 8 TeammateIdle, honest real-schema audit), and a **usable synthesized review** with a genuine cross-challenge (the lenses interlocked; correctness reproduced a real false-positive class with live git). Anti-fake-team gate PASSED. Evidence in the run worktree's `docs/contracts/.run/evidence/` (gitignored). `review-gate` team mode = Stage B remainder, still ⬜. ✅

| Resource | Type | Step | Tier | Work to make team-ready | Status |
|---|---|---|---|---|---|
| `code-review-workflow` | skill | 5 | 🟢 | Add a `--team` mode: spawn security/perf/tests/correctness reviewers who share+challenge before the lead synthesizes (Anthropic flagship pattern) | ✅ done — `--team` mode added (STEP 2-TEAM); LIVE-VALIDATED 2026-06-23 (real 3-member team, 12 hook events, usable review) |
| `review-gate` | skill | 5 | 🟢 | It already dispatches 3 inline gate agents → convert to a real review team (quality/arch/security as teammates) | ⬜ not started (Stage B remainder) |
| `code-reviewer-agent` | agent | 5 | 🟢 | Teammate-readiness check: no `skills`/`mcpServers` reliance; tools OK; peer-prompt. Already `dispatched_from: dual-mode` | ✅ done — audit PASS (no skills/mcpServers frontmatter; tools OK), no edit needed |
| `security-auditor-agent` | agent | 5 | 🟢 | Same teammate-readiness check | ✅ done — audit PASS + added teammate note (no `Skill` tool as teammate → inline OWASP path) |
| `tester-agent` | agent | 5 | 🟢 | Teammate-readiness check; fan-out test areas as teammates | ✅ done — audit PASS (no skills/mcpServers frontmatter; `Skill` in tools works for teammates), no edit needed |
| `auto-verify` | skill | 5 | 🟢 | Optional `--team` to run parallel test-area teammates (no source edits) | ⬜ not started |
| `brainstorm` | skill | 1 | 🟢 | Advisor-panel mode (multi-lens spec debate, read-only) — overlaps the five-advisors pilot | ⬜ not started |
| `research-mode` | skill | 1 | 🟢 | Parallel multi-source research teammates | ⬜ not started |
| `planner-researcher-agent` | agent | 1,4 | 🟢 | Teammate-readiness check (read-only research) | ⬜ not started |
| `web-research-specialist-agent` | agent | 1 | 🟢 | Teammate-readiness check | ⬜ not started |
| `code-quality-gate` / `architecture-fitness` / `security-audit` | skills | 5 | 🟢 | Run as review-team members under `review-gate`'s team mode | ⬜ not started |
| `independent-test-verification` / `supervisor-verification` / `output-plausibility-verification` | rules | 5 | 🟢 | Extend wording to the teammate boundary (lead reproduces the gate) | ⬜ not started |
| `development-loop` | skill | 4 | 🟠 | `--team` build mode: partition by file ownership (frontend/backend/tests), merge discipline. **The risky core — validate via the test-build first** | ⬜ not started |
| `executing-plans` | skill | 4 | 🟠 | Partition plan tasks by file ownership across teammates | ⬜ not started |
| `implement` | skill | 4 | 🟠 | Same partition/merge handling | ⬜ not started |
| `plan-executor-agent` | agent | 4 | 🟠 | Teammate-readiness + file-partition contract to avoid collisions | ⬜ not started |
| `grill-me` | skill | 1 | ⚪ | Keep non-team — single interviewer is the point | — |
| `grill-with-docs` | skill | 1 | ⚪ | Keep non-team | — |
| `writing-plans` | skill | 2 | ⚪ | Keep non-team — one coherent plan owner (judge-panel via flat subagents at most) | — |
| `tdd` / `fix-loop` / `learn-n-improve` | skills | 4 | ⚪ | Keep non-team — tight single-thread cycles | — |
| `dod-verbs` / `workflow` / `plan-before-coding` / `tdd` / `testing` / `git-collaboration` | rules | 2,4,6 | ⚪ | Apply regardless of team/subagent; no change needed | — |
| `product-incubation` / `bootstrap-dogfood-project` / `contribute-practice` / `synthesize-hub` | rule+skills | 3 | ⚪ | Mechanical config/feedback wiring — keep non-team | — |
| `change-risk-scoring` / `regression-test` | skills | 5 | ⚪ | Single scoring / targeted run — keep non-team | — |
| `request-code-review` / `receive-code-review` / `post-fix-pipeline` | skills | 5,6 | ⚪ | PR + commit mechanics, sequential — keep non-team | — |
| `auto-git` / `auto-pr` / `git-manager-agent` | hooks+agent | 6 | ⚪ | Git mechanics, sequential — keep non-team | — |

### Recommended sequence (lowest-risk first)
1. **SAFE-FIT review cluster first** — `code-review-workflow --team` + `review-gate` team mode + the 3 review agents' teammate-readiness. Read-only, flagship pattern, reinforces the hub's existing independent-review discipline. *This is the same conclusion as the §3 hub-fit map.*
2. **SAFE-FIT clarify/research** — `brainstorm` advisor-panel (overlaps the five-advisors pilot) + research agents.
3. **RISKY-FIT execute** — `development-loop --team` etc. **Only after** the small parallel-edit test-build proves the merge-conflict path. This is the one tier carrying real risk.
4. Everything ⚪ stays non-team.

> Gap noted: there is **no `TeammateStart` hook**, so the hub's `subagent-governance-inject.sh` (which injects plan-first/root-cause mandates into every subagent) has **no direct teammate analog** — teammate governance must come via the spawn prompt + the `TaskCreated`/`Completed`/`Idle` hooks instead. Tracked as an open item.

## 8. Changelog

- **2026-06-23** — Guide created. Built items 1 (rule) + 2 (3 governance hooks); pilot
  runbook (item 3) documented; items 4 deferred. Cache refreshed to v2.1.186 status.
- **2026-06-23** — Added Tier-1 deterministic hook tests (19, all green); fixed a defect
  where `exec 2>/dev/null` swallowed exit-2 stderr feedback; corrected a misleading
  "grep fallback" comment. Live Tier-2 confirmation remains spend-gated (§9).
- **2026-06-23** — Ran Tier-2 live probe: confirmed headless `-p` does NOT form a team
  (Finding A) and that multi-session open/close is drivable via agent-view `claude --bg`
  (Finding B). Built the interactive demo harness (`.claude/.team-demo/`, gitignored) + §10.
- **2026-06-23** — TIER-2 COMPLETE: a `claude --bg` session formed a real team; all three
  hooks fired; captured the real payload schema (§11). Fixed 4 bugs the schema exposed
  (wrong field path; two hooks repurposed to audit loggers since the payload lacks
  work-product/pending-count; an eval injection/spaces bug). Tests rewritten to real
  schema (13 green). Hooks now match reality.
- **2026-06-23** — `/brainstorm` converged the team-readiness DIRECTION: end-goal =
  measure-first (C); win bar = reliable end-to-end completion first, cost-bounded quality
  second (D>B); experiment = staged (read-only mechanism proof → real build); reliability
  bar = ≥2/3 runs no-rescue. Captured in `docs/specs/agent-teams-measure-first-experiment-spec.md`.
  The §12 tracker work is GATED on that experiment passing — not started until then.
- **2026-06-23** — Added §12: pipeline resource inventory → team-readiness tracker.
  Mapped every Claude resource the 6-step build pipeline uses (verified by reading
  `core/.claude/` files), deduplicated to a unique master list, tagged each with a
  readiness tier (🟢 safe / 🟠 risky / ⚪ non-team) + the work needed + status. Recommended
  sequence: SAFE-FIT review cluster first, RISKY execute only after the test-build.
- **2026-06-23** — Iterate-until-flawless loop. Run #1 exposed a 5th issue: the
  `TaskCompleted` payload schema VARIES — when the lead completes a task, `teammate_name`
  and `team_name` are ABSENT, so the audit line showed bare `?`. Run #2 then exposed a 6th:
  my first fix *fabricated* `team=session-<first8 of session_id>`, but the payload's
  `session_id` is the FIRING session, NOT the lead session the team is named after — so the
  derived name (`session-6fdc1b66`) did not match the real team (`session-446a161e`): a
  plausible-but-wrong value, worse than `?`. Honest fix: never fabricate — log the real
  `session_id` under its own `session=` field and show `team=-` when `team_name` is absent
  (it is present + correct for `TeammateIdle`). Tests corrected to assert no fabrication
  (15 green). Re-running (Run #3) to confirm flawless.
