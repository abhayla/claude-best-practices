Source: https://code.claude.com/docs/en/agent-teams.md
Fetched: 2026-06-22
Currency-checked: 2026-06-23 (latest Claude Code v2.1.186 — still EXPERIMENTAL, gated behind CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1, no GA)

> **Post-v2.1.178 deltas (verified from official changelog, 2026-06-23):**
> - **v2.1.179** — default `teammateMode` flipped `"auto"` → `"in-process"`; split panes now only on explicit opt-in.
> - **v2.1.181** — idle teammate rows hide after 30s, reappear on next turn (still running/addressable while hidden). *(already reflected in body below)*
> - **v2.1.186** — new `teammateMode: "iterm2"` (native iTerm2 split panes, needs `it2` CLI); teammates spawned via tmux/pane backends now inherit the lead's `--effort`.
> - Constraints UNCHANGED: experimental + default-off, one team/session, no nested teams (teammates can't spawn teammates), no session resumption with in-process teammates, lead fixed for the session's life.
> - Only official Anthropic blog post: "Building a C compiler with a team of parallel Claudes" (2026-02-05) — 16 parallel Opus agents, ~$20k, compiled Linux 6.9. Establishes the high-cost ceiling.
> - Practitioner-reported cost: ~4–7× tokens vs a single session (4× at init alone from each teammate reloading project context); merge conflicts + permission bottlenecks the main pain points.

# Orchestrate teams of Claude Code sessions

> Coordinate multiple Claude Code instances working together as a team, with shared tasks, inter-agent messaging, and centralized management.

> **Warning:** Agent teams are experimental and disabled by default. Enable them by adding `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to your settings.json or environment. Without that variable, no team is set up at session start, no team directories are written, and Claude does not spawn or propose teammates. Agent teams have known limitations around session resumption, task coordination, and shutdown behavior.

Agent teams let you coordinate multiple Claude Code instances working together. One session acts as the team lead, coordinating work, assigning tasks, and synthesizing results. Teammates work independently, each in its own context window, and communicate directly with each other.

Unlike subagents, which run within a single session and can only report back to the main agent, you can also interact with individual teammates directly without going through the lead.

> **Note:** This page describes agent teams as of v2.1.178. With `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set, spawning a teammate no longer needs a setup step, and cleanup happens automatically when the session exits. Before v2.1.178, you asked Claude to create and name a team first, and Claude used the `TeamCreate` and `TeamDelete` tools to set it up and remove it. Both tools no longer exist. The `team_name` input on the Agent tool is accepted but ignored, and the `team_name` field in `TaskCreated`, `TaskCompleted`, and `TeammateIdle` hook payloads carries the session-derived name and is deprecated.

## When to use agent teams

Agent teams are most effective for tasks where parallel exploration adds real value. The strongest use cases are:

* **Research and review**: multiple teammates can investigate different aspects of a problem simultaneously, then share and challenge each other's findings
* **New modules or features**: teammates can each own a separate piece without stepping on each other
* **Debugging with competing hypotheses**: teammates test different theories in parallel and converge on the answer faster
* **Cross-layer coordination**: changes that span frontend, backend, and tests, each owned by a different teammate

Agent teams add coordination overhead and use significantly more tokens than a single session. They work best when teammates can operate independently. For sequential tasks, same-file edits, or work with many dependencies, a single session or subagents are more effective.

### Compare with subagents

|                   | Subagents                                        | Agent teams                                         |
| :---------------- | :----------------------------------------------- | :-------------------------------------------------- |
| **Context**       | Own context window; results return to the caller | Own context window; fully independent               |
| **Communication** | Report results back to the main agent only       | Teammates message each other directly               |
| **Coordination**  | Main agent manages all work                      | Shared task list with self-coordination             |
| **Best for**      | Focused tasks where only the result matters      | Complex work requiring discussion and collaboration |
| **Token cost**    | Lower: results summarized back to main context   | Higher: each teammate is a separate Claude instance |

Use subagents when you need quick, focused workers that report back. Use agent teams when teammates need to share findings, challenge each other, and coordinate on their own.

## Enable agent teams

Agent teams are disabled by default. Enable them by setting the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` environment variable to `1`, either in your shell environment or through settings.json:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Start your first agent team

After enabling agent teams, describe the task and the teammates you want in natural language. Claude spawns them and coordinates work based on your prompt. Example:

```text
I'm designing a CLI tool that helps developers track TODO comments across
their codebase. Spawn three teammates to explore this from different angles:
one on UX, one on technical architecture, one playing devil's advocate.
```

Claude populates a shared task list, spawns teammates for each perspective, has them explore, and synthesizes findings. The lead's terminal lists teammates in the agent panel below the prompt input. From the panel: Up/down arrows select a teammate; Enter opens its transcript and lets you message it; Escape interrupts its current turn. As of v2.1.181, an idle teammate's row hides after 30 seconds and reappears on its next turn (it stays running and addressable while hidden).

## Control your agent team

### Choose a display mode

* **In-process** (default): all teammates run inside your main terminal; arrow keys select, Enter views/messages. Works in any terminal.
* **Split panes**: each teammate gets its own pane. Requires tmux or iTerm2.

Set `teammateMode` in `~/.claude/settings.json` (`"in-process"` | `"auto"` | `"tmux"`), or per session `claude --teammate-mode auto`. Split panes need tmux or iTerm2 with the `it2` CLI (enable Python API in iTerm2 settings).

### Specify teammates and models

Claude decides the count, or you specify (e.g. "Spawn 4 teammates… Use Sonnet for each"). Teammates don't inherit the lead's `/model` by default — set **Default teammate model** in `/config` (or pick "Default (leader's model)").

### Require plan approval for teammates

Ask the lead to require teammates to plan before implementing; the teammate works in read-only plan mode until the lead approves. The lead approves/rejects autonomously — influence it via prompt criteria ("only approve plans that include test coverage").

### Talk to teammates directly

Each teammate is a full independent session. In-process: arrow-select + Enter to view/message; `x` to stop; Ctrl+T toggles the task list. Split-pane: click into the pane.

### Assign and claim tasks

Shared task list states: pending, in progress, completed; tasks can depend on other tasks. Lead assigns explicitly, or teammates self-claim the next unblocked task. Task claiming uses file locking to prevent races.

### Shut down teammates

Refer to a teammate by name ("Ask the researcher teammate to shut down"). The teammate can approve or reject. Shared directories are cleaned up automatically when the session ends.

### Enforce quality gates with hooks

* `TeammateIdle`: runs when a teammate is about to go idle. Exit code 2 sends feedback and keeps it working.
* `TaskCreated`: runs when a task is being created. Exit code 2 prevents creation + sends feedback.
* `TaskCompleted`: runs when a task is being marked complete. Exit code 2 prevents completion + sends feedback.

## How agent teams work

### How Claude starts agent teams

A team forms when the first teammate is spawned, with the main session as lead. Either you request teammates, or Claude proposes them (you confirm). Claude won't spawn teammates without approval.

### Architecture

| Component     | Role                                                                    |
| :------------ | :---------------------------------------------------------------------- |
| **Team lead** | The main Claude Code session that spawns teammates and coordinates work |
| **Teammates** | Separate Claude Code instances that each work on assigned tasks         |
| **Task list** | Shared list of work items that teammates claim and complete             |
| **Mailbox**   | Messaging system for communication between agents                       |

Teams/tasks are stored locally under a session-derived name (`session-` + first 8 chars of the session ID):

* **Team config**: `~/.claude/teams/{team-name}/config.json` (removed when the session ends)
* **Task list**: `~/.claude/tasks/{team-name}/` (persists locally, never uploaded; retention governed by `cleanupPeriodDays`)

Don't hand-edit/pre-author the team config — it holds runtime state and is overwritten. There is no project-level team config. The config's `members` array lists each teammate's name, agent ID, and agent type.

### Use subagent definitions for teammates

When spawning, reference a subagent type from any scope (project/user/plugin/CLI): "Spawn a teammate using the security-reviewer agent type…". The teammate honors that definition's `tools` allowlist and `model`; the body is appended to its system prompt. Team coordination tools (`SendMessage`, task management) are always available even if `tools` restricts others. Note: `skills` and `mcpServers` frontmatter fields are NOT applied when a definition runs as a teammate — teammates load skills/MCP from project + user settings.

### Permissions

Teammates start with the lead's permission settings (incl. `--dangerously-skip-permissions`). You can change individual teammate modes after spawning, but not per-teammate modes at spawn time.

### Context and communication

Each teammate has its own context window and loads the same project context (CLAUDE.md, MCP servers, skills) plus the spawn prompt. The lead's conversation history does NOT carry over. Sharing mechanisms: automatic message delivery, idle notifications to the lead, shared task list, name-addressed teammate messaging.

### Token usage

Agent teams use significantly more tokens than a single session — usage scales with active teammate count. Worthwhile for research/review/new-feature work; a single session is cheaper for routine tasks.

## Use case examples

**Parallel code review** — spawn 3 teammates for PR #142: one security, one performance, one test-coverage; lead synthesizes.

**Investigate with competing hypotheses** — spawn 5 teammates to investigate different hypotheses and debate to disprove each other ("like a scientific debate"); the surviving theory is more likely the root cause (fights anchoring).

## Best practices

* **Give teammates enough context** — they don't inherit conversation history; put task-specific details in the spawn prompt.
* **Choose an appropriate team size** — start with 3–5 teammates; ~5–6 tasks per teammate; token costs scale linearly; coordination overhead and diminishing returns past a point.
* **Size tasks appropriately** — self-contained units producing a clear deliverable; not too small (overhead) or too large (no check-ins).
* **Wait for teammates to finish** — if the lead starts implementing itself, tell it to wait.
* **Start with research and review** — clear boundaries, no code-writing, to learn the feature.
* **Avoid file conflicts** — partition files so each teammate owns a different set.
* **Monitor and steer** — check in, redirect, synthesize.

## Troubleshooting

* **Teammates not appearing** — check the agent panel (in-process); idle rows hide after 30s; ensure the task was complex enough; for split panes confirm tmux/`it2`.
* **Too many permission prompts** — pre-approve common operations before spawning.
* **Teammates stopping on errors** — view their output and instruct, or spawn a replacement.
* **Lead shuts down before work is done** — tell it to keep going / wait for teammates.
* **Orphaned tmux sessions** — `tmux ls` then `tmux kill-session -t <name>`.

## Limitations

* No session resumption with in-process teammates (`/resume`, `/rewind` don't restore them).
* Task status can lag (teammates sometimes fail to mark tasks complete).
* Shutdown can be slow (teammates finish the current request/tool call first).
* One team per session; no nested teams (teammates can't spawn teammates); lead is fixed for its lifetime.
* Permissions set at spawn (all start with the lead's mode).
* Split panes require tmux or iTerm2 (not VS Code integrated terminal, Windows Terminal, or Ghostty).

CLAUDE.md works normally — teammates read CLAUDE.md from their working directory.

## Next steps

* Lightweight delegation: subagents (/en/sub-agents)
* Manual parallel sessions: Git worktrees (/en/worktrees)
* Compare approaches: subagent vs agent team (/en/features-overview#compare-similar-features)
