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

- Exact stdin payload schema for `TaskCreated` / `TaskCompleted` / `TeammateIdle` hooks
  (field names) — the hooks parse defensively until confirmed; confirm then tighten.
- Whether `TeammateIdle` exit-2 reliably re-engages a teammate in v2.1.186.
- Real token multiplier on hub-shaped work (the 4–7× figure is community-reported).

## 8. Changelog

- **2026-06-23** — Guide created. Built items 1 (rule) + 2 (3 governance hooks); pilot
  runbook (item 3) documented; items 4 deferred. Cache refreshed to v2.1.186 status.
