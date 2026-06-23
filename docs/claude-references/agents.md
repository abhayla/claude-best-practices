Source: https://code.claude.com/docs/en/agents.md
Fetched: 2026-06-22

# Run agents in parallel

> Compare the ways Claude Code can take on multiple tasks at once: subagents, agent view, agent teams, and dynamic workflows.

Subagents, agent view, agent teams, and dynamic workflows each parallelize work in a different way. The right one depends on whether you want to stay in each conversation yourself, hand tasks off and check back later, or have Claude coordinate a group of workers for you.

| Approach            | What it gives you                                                                                                                                         | Use it when                                                                                                                                                          |
| :------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Subagents           | Delegated workers inside one session that do a side task in their own context and return a summary                                                        | A side task would flood your main conversation with search results, logs, or file contents you won't reference again                                                |
| Agent view          | One screen to dispatch and monitor sessions running in the background, opened with `claude agents`. Research preview                                       | You have several independent tasks and want to hand them off, check status at a glance, and step in only when one needs you                                          |
| Agent teams         | Multiple coordinated sessions with a shared task list and inter-agent messaging, managed by a lead. Experimental and disabled by default                  | You want Claude to split a project into pieces, assign them, and keep the workers in sync                                                                            |
| Dynamic workflows   | A script that runs many subagents and cross-checks their results, for work too big to coordinate one turn at a time or that needs more than a single pass | A job outgrows a handful of subagents, or you want findings verified against each other: a codebase-wide audit, a 500-file migration, cross-checked research         |

In every approach the workers are Claude sessions. To involve a different tool, expose it to Claude as an MCP server.

Two more tools support this work without being a way to run agents themselves:

* **Worktrees** give each session a separate git checkout, so parallel sessions never edit the same files. Agent view moves each dispatched session into its own worktree automatically; subagents can each get one too.
* **`/batch`** is a skill that has Claude split one large change into 5–30 worktree-isolated subagents that each open a PR. It's a packaged use of subagents + worktrees, not a separate coordination style.

A few other features run Claude without you driving each step but solve a different problem:

* A **background bash command** runs one shell command without blocking the conversation (doesn't spawn an agent).
* A **forked subagent** inherits your full conversation context instead of starting fresh (a way to spawn a subagent).
* A **routine** runs a session on a schedule in Anthropic's cloud, not in parallel on your machine.

> **Note:** Running several sessions or subagents at once multiplies token usage. See Costs for usage and rate-limit details.

## Choose an approach

* **Who coordinates the work?**
  * Claude delegates and collects results inside one conversation → subagents
  * You hand off independent tasks and check back later → agent view
  * Claude plans, assigns, and supervises a group of workers → agent teams (experimental, disabled by default)
  * A script holds the plan instead of Claude's turn-by-turn judgment → dynamic workflows
* **Do the workers need to talk to each other?** Subagents report back to the conversation that spawned them; agent view sessions report only to you; agent-team teammates share a task list and message each other directly.
* **Do the tasks touch the same files?** Isolate with worktrees. Subagents and self-run sessions can each use a separate worktree. Agent teams don't isolate teammates in worktrees, so partition the work so each owns a different set of files.

## Check on running work

* Background sessions → `claude agents` opens agent view.
* Subagents in the current session → `/agents` (Running tab + Library tab). Separate from `claude agents`.
* Anything running in the background of the current session → `/tasks`.
* Dynamic workflows → `/workflows`.

For a desktop view of all sessions, see parallel sessions in the desktop app.

## Learn more

* Create custom subagents (/en/sub-agents)
* Manage agents with agent view (/en/agent-view)
* Orchestrate agent teams (/en/agent-teams)
* Orchestrate dynamic workflows (/en/workflows)
* Run parallel sessions with worktrees (/en/worktrees)
