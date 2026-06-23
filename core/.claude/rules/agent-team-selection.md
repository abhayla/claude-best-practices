---
description: When to reach for an agent TEAM (peer Claude Code sessions that message + self-coordinate) vs a SUBAGENT (flat worker that reports back) vs a git WORKTREE. Complements agent-orchestration.md.
globs: [".claude/agents/*.md", ".claude/skills/*/SKILL.md"]
---

# Agent Team vs Subagent vs Worktree — selection rule

> Loads when editing agents/skills (the places that orchestrate). Companion to
> `agent-orchestration.md` (which governs single-level subagent dispatch). Feature
> reference: `docs/claude-references/agent-teams.md`.

## The three primitives

| Primitive | What it is | Communication | Cost |
|---|---|---|---|
| **Subagent** | Worker dispatched via `Agent()` inside one session | Reports result back to the caller ONLY | Low — result summarized back |
| **Agent team** | Lead + peer Claude Code sessions (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) | Teammates message EACH OTHER + share a task list + are individually addressable | High — **~4–7× tokens**, each teammate is a full instance |
| **Git worktree** | Isolated checkout for parallel file edits | None (manual) | Low — disk only |

## Decision order (cheapest sufficient primitive wins — KISS/YAGNI)

1. **Default to a SUBAGENT.** If a worker only needs to *do a focused task and return a
   result*, dispatch a flat subagent. This is the hub's default and covers almost all work.
2. **Reach for an AGENT TEAM only when workers must CHALLENGE EACH OTHER** — not just run
   in parallel, but read and dispute each other's findings mid-flight. Genuine fits:
   - parallel **code review** where reviewers share + challenge before synthesis;
   - **competing-hypothesis debugging** (teammates try to disprove each other);
   - **multi-advisor debate** (e.g. a real `/five-advisors`).
   Teams are **experimental, default-off, no GA** (Claude Code v2.1.186) and cost ~4–7×.
3. **Use a WORKTREE** (or background-session isolation) when the need is parallel *file
   edits without conflicts*, not cross-talk. Subagents get `isolation: worktree` for this.

## Hard rules

- MUST NOT pick an agent team for sequential work, same-file edits, dependency-heavy
  pipelines, or anything where only the *result* matters — use a subagent (docs are explicit).
- MUST NOT make agent teams a default-on path. Adopt **opt-in, measure-first**: enable the
  env var per task, and prefer the cheaper simulated/single-context form until real
  cost/quality data justifies the multiplier (see `plans/agent-teams-incorporation.md`).
- MUST account for the constraints before choosing a team: one team per session, **no
  nested teams** (teammates can't spawn teammates), no session resumption, lead fixed for
  the session, permissions set at spawn. If any breaks your design, use subagents.
- On **Windows**, only `teammateMode: "in-process"` works (split panes need tmux/iTerm2).
- Teammates do NOT inherit conversation history or a definition's `skills`/`mcpServers`
  frontmatter — put all task context in the spawn prompt.

## Governance

When a team IS used, the teammate-boundary governance hooks
(`team-task-created-deliverable`, `team-task-completed-verifier`, `team-teammate-idle-drain`)
extend the hub's existing subagent governance (plan-first, reproduce-the-gate,
drain-the-queue) to teammates. They ship fail-open; set `TEAM_GOVERNANCE_STRICT=1` to enforce.
