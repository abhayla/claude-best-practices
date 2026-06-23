Source: https://www.anthropic.com/engineering/multi-agent-research-system + https://code.claude.com/docs/en/agent-teams + https://www.anthropic.com/engineering/building-c-compiler + https://www.anthropic.com/engineering/managed-agents + https://code.claude.com/docs/en/sub-agents
Fetched: 2026-06-23

# Anthropic Multi-Agent / Agent-Team Best Practices

Synthesized from official Anthropic sources (Claude Code agent-teams + sub-agents docs;
Anthropic Engineering blogs: "How we built our multi-agent research system", "Building a C
compiler with a team of parallel Claudes", "Scaling Managed Agents"). All items below are
VERIFIED from an official source unless marked otherwise. This is the reference the
agent-team pipeline-upgrade goal contract bakes in.

## A. Task shaping & decomposition
- Each task = a **self-contained unit with a clear deliverable**: objective, output format, tool guidance, explicit out-of-scope. Vague tasks ("research X") directly cause duplication.
- **Not too small** (pure coordination overhead) **/ not too large** (no check-in points). One agent finishes it with observable progress in a session.
- **~5–6 tasks per teammate** is a practical load; beyond that, diminishing returns + coordination drag.
- **Embed effort-scaling rules in the orchestrator prompt** (e.g. "simple fact-find = 1 agent, 3–10 tool calls; complex = 10+"). The orchestrator can't infer this from context.
- For parallelizable work, **structure tasks around independent test suites / failing files** — each agent a distinct failure. If all agents hit the same monolithic bug, parallelism adds nothing.
- Use **extended-thinking upfront planning** in the lead before dispatching (complexity assessment, roles, tool fit).

## B. File / work partitioning (no concurrent same-file edits)
- **Partition files: one teammate owns one set.** The primary documented anti-collision rule.
- **Assign specializations by orthogonal dimension** (perf / dedup / codegen / docs / review), not just by file, so agents progress on different axes.
- **File-lock / task-claim pattern:** each agent writes a claim file (`current_tasks/<task>.txt`); git's atomic push forces a conflict if two claim the same task → the loser pulls, merges, picks another. Replaces custom orchestration.
- **Background-session worktree isolation** (`.claude/worktrees/`) keeps concurrent edits from colliding (agent-view). Full mechanism: `worktrees.md` (cached) — `--worktree`/`-w`, subagent `isolation: worktree`, `.worktreeinclude`, base-branch + cleanup.

## C. Coordination & anti-conflict (no fighting / duplication / contradiction)
- **Detail task boundaries in the spawn prompt** (objective + output format + tool guidance + out-of-scope). Without this, agents duplicate work even on different tasks.
- **Explicit division-of-labor heuristics** in the orchestrator system prompt.
- **Proactive guardrails over reactive correction** — set effort budgets + boundaries + tool-matching in the prompt, don't correct after a spiral.
- **Lead waits; does not start implementing** while teammates work (a flagged failure mode).
- **Use task dependencies** in the shared list to enforce ordering when a task genuinely can't start until another finishes; teammates self-claim the next unblocked task.
- **NOT for sequential tasks, same-file edits, or dependency-heavy flows** — a single session / flat subagents are better + cheaper there.
- **Machine-readable progress + CI output** (errors greppable; essential output only) so agents re-orient without context pollution.

## D. Cross-agent verification (doer ≠ checker)
- **Start with research-and-review teams that write NO code** to learn a feature — clear boundaries, no compounding errors from premature edits.
- **Competing-hypotheses debate** (5+ agents try to disprove each other) for debugging — fights anchoring.
- **Parallel review** (security / perf / test-coverage on the same PR; lead synthesizes).
- **A SEPARATE specialized verifier**, not a role bundled into the doer (the research system's dedicated `CitationAgent` verifies every claim). This is the doer≠checker principle.
- **Iterative synthesis loop:** the lead decides if another pass is needed rather than accepting first-pass output.
- **Subagent interleaved thinking** after each tool result for in-flight self-correction.
- **Evaluate END-STATE, not process** for state-mutating agents (they may find alternative valid paths).

## E. Quality gates & hooks
| Hook | Fires | Exit 2 effect | Use as |
|---|---|---|---|
| `TaskCreated` | task being created | prevents creation + feedback | **scope gate** — task has a deliverable, in-scope, not a duplicate |
| `TaskCompleted` | task marked complete | prevents completion + feedback | **definition-of-done gate** |
| `TeammateIdle` | before a teammate idles | sends feedback + keeps it working | **quality backstop** before output is accepted |
- **Plan approval for teammates:** lead requires a plan before implementing; teammate is read-only until approved; influence approval criteria via prompt ("only approve plans with test coverage").
- **LLM-as-judge rubric** (0.0–1.0 on factual/citation accuracy, completeness, source quality, tool efficiency) — most consistent with human judgement.
- **~20-query baseline eval** is enough to see big prompt-change effects; don't delay eval for a big corpus. **Manual testing stays mandatory** (LLM judges miss hallucinations / system failures / subtle bias).
- **CI blocking commits that break existing tests** is required — autonomous dev accumulates hidden failures.
- **Resume-from-checkpoint, not restart;** session log persists independent of the harness. **Graceful degradation** (tell the agent a tool failed, let it adapt) + deterministic retry.

## F. Team sizing & cost
- **Start with 3–5 teammates**; ~5–6 tasks each; token cost scales ~linearly with active teammates.
- **Agent teams ≈ 4× tokens at init alone** (each teammate reloads project context); **multi-agent ≈ 15× a chat overall**. The C-compiler 16-agent run (~$20k) is a research-scale upper bound, not a target.
- **Subagents (cheaper, result-only) vs teams (pricier, share+challenge):** pick teams only when agents must share findings + challenge each other.
- **Route within the team to cheaper models** (lead Opus, workers Sonnet/Haiku; Opus-lead+Sonnet-workers beat single-Opus by 90.2%). **Model upgrade > doubling token budget.**
- **Teams help:** parallel research/review, new independent modules, competing-hypothesis debug, cross-layer coordination. **Teams hurt:** sequential, same-file, dependency-heavy, shared-context.
- **Measure token value against task value** — multi-agent is viable only when the task value pays for the overhead.
- Platform: **one team/session; no nested teams; teammates can't spawn teammates** (v2.1.186).

## G. Context passing (teammates don't inherit history)
- **All task context goes in the spawn prompt** — teammates load project context (CLAUDE.md/MCP/skills) + the spawn prompt only; the lead's conversation does NOT carry over.
- **Shared task list = passive coordination** (states + dependencies); **mailbox/`SendMessage` = active agent-to-agent messaging**.
- **Artifact system for large outputs:** subagents write outputs to files/memory and pass lightweight references back — avoids the "telephone" degradation of routing everything through the lead.
- **Save plans to external memory** when the orchestrator nears context limits; **spawn fresh subagents with a structured-summary handoff** on overflow (not raw history).

## H. Concrete mechanisms (scanned 2026-06-23 from sub-agents / hooks-guide / worktrees / workflows / large-codebases / best-practices / headless / agents)

### H1. Worktree isolation — the real "no concurrent same-file edits" mechanism (sub-agents, worktrees, agent-view)
- A teammate/subagent is **NOT isolated by default** — it inherits the session's working dir. To physically prevent collisions, give a parallel worker its **own git worktree**: `isolation: worktree` in subagent frontmatter (auto-cleaned if it makes no changes), or `claude --worktree <name>` for a session.
- Subagent worktrees branch from the **default branch** unless `worktree.baseRef: "head"` (carry in-progress work). Branch from a PR with `claude --worktree "#1234"`.
- `.worktreeinclude` (`.gitignore` syntax) copies gitignored files (`.env`, secrets) into each worktree. `.claude/worktrees/` should be in `.gitignore`.
- While an agent runs, Claude `git worktree lock`s its worktree so concurrent cleanup can't remove it mid-run. Background sessions auto-isolate (`worktree.bgIsolation`).
- **At scale (large-codebases):** `worktree.sparsePaths` checks out only needed dirs per worktree (all session worktrees share the same sparsePaths — list every package any agent needs); `symlinkDirectories` (e.g. `node_modules`) avoids duplicating big dirs; `additionalDirectories` / `--add-dir` grant cross-package file access (file access ONLY — does NOT load that dir's CLAUDE.md/rules/skills). A single coupled cross-package change → ONE session, not split across parallel agents.

### H2. Cross-agent verification ladder (best-practices, sub-agents, hooks-guide, workflows)
- Four escalating ways to gate "done" on verification: in-prompt check → **`/goal` condition** (a separate evaluator re-checks every turn) → **Stop hook** (deterministic; Claude overrides after 8 consecutive blocks) → **verification subagent/workflow** (fresh model refutes).
- **Doer≠checker concretely:** a read-only **reviewer subagent** (`tools: Read, Grep, Glob, Bash` only — no Edit/Write); or a **forked subagent** (inherits full context, cheaper via shared prompt cache) to verify in parallel; or an **agent-type Stop hook** that actually runs the test suite + reads files before allowing completion; or a **prompt-type Stop/SubagentStop hook** (Haiku) judging "are all tasks complete?".
- **Show evidence, not assertions** — the test output, the command + its return, or a screenshot (works for runs you didn't watch). Writer/Reviewer across two sessions: a fresh-context reviewer isn't biased toward code it just wrote.
- **Tell the reviewer to flag only correctness/requirement gaps** — a gap-seeking reviewer always reports something; chasing all of it causes over-engineering.

### H3. Hook I/O contract for quality gates (hooks-guide)
- **Exit codes:** `0` = no objection (stdout injected as context for `UserPromptSubmit`/`SessionStart`); `2` = block + stderr becomes Claude's feedback; any other = proceed with a `<hook> hook error`. Don't mix exit-2 with structured JSON (JSON ignored on exit 2). Exit-2 can't block some events (`SessionStart`, `Notification`, …) — check the per-event behavior.
- **Input:** every event gets `session_id`, `cwd`, `hook_event_name`; tool events add `tool_name`/`tool_input` (parse with `jq`). Relevant events: `TaskCreated`/`TaskCompleted`/`TeammateIdle` (agent teams), `SubagentStart`/`SubagentStop` (matchable by agent type), `PostToolBatch` (after a parallel fan-out — natural cross-check point), `Stop`.
- `PreToolUse` fires **before** permission checks; a hook `deny` blocks even under `bypassPermissions`; multiple hooks on one event run in parallel, most-restrictive wins (`deny > defer > ask > allow`). Windows hooks need `shell: powershell`. A Bash command can edit files invisibly to `Edit|Write` matchers → a once-per-turn `Stop` working-tree scan catches it.

### H4. Subagent-definition quality + context (sub-agents)
- Required frontmatter: `name` + `description` (the `description` drives auto-delegation — be specific; add "use proactively" to trigger it). One focused job per subagent; restrict tools (`tools` allowlist / `disallowedTools` denylist); check project subagents into VCS.
- Cost/scope knobs: `model` (haiku/sonnet/opus/inherit), `effort` (low…max), `maxTurns` (runaway cap), `memory: project` (persistent cross-session MEMORY.md), `skills` (preload full skill content at startup).
- **Teammate caveats (critical):** when a subagent definition runs as a **teammate**, `skills` and `mcpServers` frontmatter are **NOT applied** (teammates load skills/MCP from project+user settings); only `tools`, `model`, and the body carry over. Built-in **Explore/Plan skip CLAUDE.md + git status** for speed — restate any rule they must follow in the delegation prompt. **All task context goes in the spawn prompt** (no history inherited).
- **Registry session-pinning:** edited/new agent files on disk require a **session restart** to dispatch (`/agents`-created ones load immediately). Background subagent nesting cap = **5 levels**.

### H5. Selection — who holds the plan (agents, workflows)
- **Subagents** (Claude decides turn-by-turn, results in context, lower cost) · **Agent teams** (a lead supervises peer sessions that message each other + a shared task list, ~4–7× cost) · **Dynamic workflows** (a *script* holds the loop/branching/intermediate state; only the final answer lands in context; 16 concurrent / 1000 total agent caps; resumable in-session; workflow subagents always run `acceptEdits`) · **Agent view** (`claude --bg` + `claude agents` to dispatch + monitor many independent background sessions, `--json` for machine-readable state). Pick by *who coordinates* and *whether workers must talk*.

### H6. Cost & autonomous-run controls (workflows, headless, best-practices)
- Gauge spend on a **small slice first**; every workflow agent uses your **session model** unless the script routes a stage elsewhere (check `/model` before a big run). Per-invocation cost in headless: `--output-format json` → `total_cost_usd` + per-model breakdown. Multi-agent runs count toward plan usage/rate limits.
- Headless/unattended: `--bare` (skip auto-discovery for reproducible CI), `--allowedTools` (prefix-matched — mind the space), `acceptEdits`/`dontAsk` modes, **Auto mode aborts under `-p`** if the classifier repeatedly blocks (no human fallback). Background subagents/workflows are exempt from the 5s exit grace; `claude -p` waits up to 10 min (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`).
- **Save the plan to a markdown file before a long run** — context compacts and the saved plan survives; `/clear` between unrelated tasks and after two failed corrections.

## Caveats / limitations (official)
- Experimental, default-off (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), not GA (v2.1.186).
- No session resumption for in-process teammates; task status can lag; lead is fixed for the session.
- Synchronous batch bottleneck (lead waits for the whole batch; a slow teammate blocks the next batch; no mid-batch steering).
- Domains needing shared context across ALL agents don't suit today's isolated-context model.
