Source: https://code.claude.com/docs/en/workflows
Fetched: 2026-06-23

# Orchestrate subagents at scale with dynamic workflows

> Dynamic workflows orchestrate many subagents from a script Claude writes and you can rerun. Use them for codebase audits, large migrations, and cross-checked research.

**Note:** Dynamic workflows require Claude Code v2.1.154 or later and are available on all paid plans, with Anthropic API access, and on Amazon Bedrock, Google Cloud Vertex AI, and Microsoft Foundry. On Pro, turn them on from the Dynamic workflows row in `/config`.

A dynamic workflow is a JavaScript script that orchestrates [subagents](https://code.claude.com/docs/en/sub-agents) at scale. Claude writes the script for the task you describe, and a runtime executes it in the background while your session stays responsive.

Reach for a workflow when a task needs more agents than one conversation can coordinate, or when you want the orchestration codified as a script you can read and rerun. Examples: a codebase-wide bug sweep, a 500-file migration, a research question that needs sources cross-checked, a hard plan worth drafting from several independent angles before you commit.

## When to use a workflow

Subagents, skills, agent teams, and workflows can all run a multi-step task. The difference is **who holds the plan**:

| | Subagents | Skills | Agent teams | Workflows |
|---|---|---|---|---|
| What it is | A worker Claude spawns | Instructions Claude follows | A lead agent supervising peer sessions | A script the runtime executes |
| Who decides what runs next | Claude, turn by turn | Claude, following the prompt | The lead agent, turn by turn | The script |
| Where intermediate results live | Claude's context window | Claude's context window | A shared task list | Script variables |
| What's repeatable | The worker definition | The instructions | The team definition | The orchestration itself |
| Scale | A few delegated tasks per turn | Same as subagents | A handful of long-running peers | Dozens to hundreds of agents per run |
| Interruption | Restarts the turn | Restarts the turn | Teammates keep running | Resumable in the same session |

A workflow moves the plan into code. With subagents/skills/agent-teams, Claude is the orchestrator (decides turn by turn; every result lands in a context window). A workflow script holds the loop, branching, and intermediate results itself, so Claude's context holds only the final answer.

Moving the plan into code also lets a workflow apply a **repeatable quality pattern**, not just run more agents: independent agents can adversarially review each other's findings before they're reported, or draft a plan from several angles and weigh them — a more trustworthy result than a single pass.

## Run a bundled workflow

Quickest way to see one: `/deep-research`, the built-in workflow for investigating a question across many sources. Agents work through phases in the background while your session stays free; you get one cited report at the end.

1. **Run it:** `/deep-research What changed in the Node.js permission model between v20 and v22?` — fans out web searches across angles, fetches + cross-checks sources, synthesizes a cited report.
2. **Allow workflows:** Claude Code asks whether to allow it; select **Yes**. Exact prompt depends on permission mode.
3. **Watch progress:** run `/workflows`, arrow-select the run, Enter to open its progress view (each phase with agent count, token total, elapsed time; drill into a phase to see its agents). A one-line summary also appears in the task panel below the input.
4. **Read the report:** when finished, the cited report lands in your session, with claims that didn't survive cross-checking filtered out.

### Bundled workflows
| Command | What it does |
|---|---|
| `/deep-research <question>` | Fans out web searches across several angles, fetches + cross-checks sources, votes on each claim, returns a cited report with non-surviving claims filtered out. Requires the WebSearch tool. |

Workflows you save yourself become commands the same way and appear in `/` autocomplete.

### Watch the run
Run `/workflows` to list running + completed workflows; select one for its progress view (phases with agent counts, token totals, elapsed time). Footer keys:

| Key | Action |
|---|---|
| `↑`/`↓` | Select a phase or agent |
| `Enter`/`→` | Drill into the selected phase, then an agent (prompt, recent tool calls, result) |
| `Esc` | Back out one level |
| `j`/`k` | Scroll within agent detail when it overflows |
| `f` | (v2.1.186+) Filter the agent list in the selected phase by status; press again to cycle |
| `p` | Pause or resume the run |
| `x` | Stop the selected agent, or stop the whole workflow when focus is on the run |
| `r` | Restart the selected running agent |
| `s` | Save the run's script as a command |

## Have Claude write a workflow

Two ways:
- **Ask for a workflow in your prompt** — in your own words ("use a workflow"/"run a workflow") or with the keyword `ultracode`. Example: `ultracode: audit every API endpoint under src/routes/ for missing auth checks`. (Before v2.1.160 the literal trigger keyword was `workflow`; natural-language requests work in both.) Dismiss an accidental highlight with `Option+W`/`Alt+W` or backspace; disable via "Ultracode keyword trigger" in `/config`. If you already have an orchestrator (a folder of subagent prompts, or a fan-out skill), point Claude at it and ask for a workflow that does the same thing.
- **Let Claude decide with ultracode** — `/effort ultracode` combines `xhigh` reasoning effort with automatic workflow orchestration: Claude plans a workflow for each substantive task. One request can become several workflows in a row (understand → change → verify). Costs more tokens + time; lasts the session, resets on a new one; drop back with `/effort high`. Available only on models supporting `xhigh` effort.

### Approve the plan before it runs
CLI per-run prompt shows the planned phases + options: **Yes, run it** · **Yes, and don't ask again for `<name>` in `<path>`** · **View raw script** · **No**. `Ctrl+G` opens the script in your editor; `Tab` lets you adjust the prompt first.

| Permission mode | When you're prompted |
|---|---|
| Default, accept edits | Every run, unless you selected "don't ask again" for that workflow in this project |
| Auto | First launch only; any **Yes** records consent in user settings; later launches start without prompting. Skipped entirely when ultracode is on |
| Bypass permissions, `claude -p`, Agent SDK | Never — the run starts immediately |

Your permission mode controls only the launch prompt. **The subagents the workflow spawns always run in `acceptEdits` mode** and inherit your tool allowlist regardless of session mode; file edits are auto-approved. Shell commands, web fetches, and MCP tools not in your allowlist can still prompt mid-run — add them to your allowlist before a long run. In `claude -p`/Agent SDK there's no one to prompt, so tool calls follow configured rules without interactive confirmation.

### Save the workflow for reuse
Run `/workflows`, select the run, press `s`. `Tab` toggles two save locations: `.claude/workflows/` (project, shared via repo) or `~/.claude/workflows/` (home, every project, private). Enter to save → runs as `/<name>` in future sessions. (v2.1.178+) In a monorepo, project saves write to the closest existing `.claude/workflows/` between cwd and repo root (or repo root); project workflows load from every `.claude/workflows/` along that path, and the closest-to-cwd wins on name collision. A project workflow beats a personal one of the same name.

### Pass input to a saved workflow
A saved workflow accepts input through the `args` parameter, read as a global named `args`. Example: `Run /triage-issues on issues 1024, 1025, and 1030` — Claude passes the list as structured data, so the script calls array/object methods on `args` directly. If `args` is omitted, the global is `undefined`.

## How a workflow runs

The runtime executes the script in an **isolated environment, separate from your conversation**; intermediate results stay in script variables, not Claude's context. Every run writes its script to a file under your session's directory in `~/.claude/projects/`; Claude gets the path at start (you can ask for it) — open it to read the orchestration, diff against a previous run, or edit + relaunch. The runtime tracks each agent's result, which makes a run resumable within the same session.

### Behavior and limits
| Constraint | Why |
|---|---|
| No mid-run user input | Only agent permission prompts can pause a run. For sign-off between stages, run each stage as its own workflow |
| No direct filesystem or shell access from the workflow itself | Agents read/write/run commands; the script coordinates the agents |
| Up to 16 concurrent agents (fewer on limited CPU) | Bounds local resource use |
| 1,000 agents total per run | Prevents runaway loops |

## Manage runs
Manage from the `/workflows` view or by expanding its progress line in the task panel.
- **Resume after a pause:** stop a run, then resume — completed agents return cached results, the rest run live. Resume from `/workflows` (select + `p`) or ask Claude to relaunch with the same script. Resume works only within the same session; exiting Claude Code mid-run means the next session starts fresh.
- **Cost:** a workflow spawns many agents → a single run can use meaningfully more tokens than the same task in conversation; counts toward plan usage/rate limits. Gauge spend by running on a small slice first; the `/workflows` view shows per-agent token usage and you can stop anytime without losing completed work. The agent caps bound a runaway script's cost. Every agent uses your session's model unless the script routes a stage elsewhere — check `/model` before a large run; ask Claude to use a smaller model for stages that don't need the strongest.
- **Turn workflows off:** toggle "Dynamic workflows" off in `/config`; or `"disableWorkflows": true` in `~/.claude/settings.json`; or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`. Org-wide via managed settings. When disabled, bundled workflow commands are unavailable, `ultracode` no longer triggers a run and is removed from `/effort`.

## Related
- Run agents in parallel (/en/agents): compare subagents, agent view, agent teams, workflows
- Create custom subagents (/en/sub-agents): the worker primitive workflows orchestrate
- Manage costs (/en/costs): how multi-agent runs count toward usage limits

---
**Hub relevance:** the native `/workflows` tool was A/B-measured vs the hub's skill-at-T0 model (no benefit for a fixed sibling fan-out → KEEP skill-at-T0; viable for genuinely dynamic/multi-stage DAGs). See `core/.claude/rules/agent-orchestration.md`.
