---
name: anthropic-multi-agent-research-system-skill
description: >
  Review and design multi-agent systems against Anthropic's research-backed principles
  for prompt engineering, evaluation methodology, and production deployment. Use when
  building, auditing, or improving multi-agent orchestration systems.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "[principle name, evaluation question, or production concern]"
version: "1.0.0"
---

# Anthropic Multi-Agent Research System

Reference for building and auditing multi-agent systems based on Anthropic's published
research on their production Research feature. Covers the orchestrator-worker architecture,
8 prompt engineering principles for multi-agent systems, LLM-as-judge evaluation
methodology, and production engineering patterns.

**Source:** [How Anthropic Built Their Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

**Query:** $ARGUMENTS

**Relationship to existing patterns:**
- `anthropic-agent-orchestration-guide` covers the 5 workflow patterns and decision frameworks
- `agent-orchestration.md` rule covers structural constraints (tiers, state, retries)
- THIS skill covers the **operational principles** — how to make agents effective at runtime

---

## Architecture: Orchestrator-Worker Pattern

Anthropic's Research feature uses a lead agent (higher-capability model) that decomposes
user queries into subtasks and delegates to specialized subagents (faster model) operating
in parallel.

### Data Flow

```
User Query
  → Lead Agent (Opus) — develops strategy, spawns subagents
    → Subagent A (Sonnet) — independent web search + interleaved thinking
    → Subagent B (Sonnet) — independent web search + interleaved thinking
    → Subagent C (Sonnet) — independent web search + interleaved thinking
  → Lead Agent — synthesizes results
  → CitationAgent — processes findings for proper attribution
  → Final Output (with citations)
```

### Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Lead agent uses higher-capability model** | Decomposition and synthesis require stronger reasoning than individual searches |
| **Subagents use faster model** | Individual search tasks are well-scoped; speed and parallelism matter more than peak reasoning |
| **Subagent outputs bypass coordinator via filesystem** | Avoids "game of telephone" information loss when results pass through the lead agent's summarization |
| **CitationAgent is a separate stage** | Attribution is a distinct concern from research — separating it improves both accuracy and maintainability |
| **Lead agent saves plan to memory at ~200k tokens** | Context window management — externalize the research plan before context pressure degrades coordination quality |

### Mapping to This Hub's Architecture

| Anthropic's System | Hub Equivalent | Notes |
|--------------------|---------------|-------|
| Lead Agent (Opus) | T0/T1 orchestrator agent | `project-manager-agent`, workflow masters |
| Subagents (Sonnet) | T2/T3 worker agents | `test-scout-agent`, `code-reviewer-agent` |
| Filesystem bypass | Artifact contracts | `artifacts_out` paths in `workflow-contracts.yaml` |
| Research plan in memory | `.pipeline/state.json` | Externalized state survives context compaction |
| CitationAgent | Dedicated post-processing skill | Separation of concerns pattern |

---

## 8 Prompt Engineering Principles for Multi-Agent Systems

These principles are specific to multi-agent coordination — they go beyond single-agent
prompt engineering by addressing the unique challenges of agent-to-agent communication,
effort scaling, and parallel execution.

### Principle 1: Think Like Your Agents

**What:** Build simulations using exact prompts and tools to observe failure modes directly.
Run the same prompt your agent will run, with the same tools, and watch what happens.

**How to apply:**
- Before deploying an agent, manually run its prompt with the same tool set
- Log every tool call decision the agent makes — identify where it chooses wrong tools or wrong parameters
- Pay attention to what the agent does when it gets ambiguous results — this is where most failures hide

**Anti-pattern:** Designing agent prompts theoretically without ever running them yourself.
You cannot predict failure modes from the prompt text alone — you must observe them.

**Audit question:** "Have I personally run this agent's exact prompt and observed its tool selection behavior?"

### Principle 2: Teach Orchestration

**What:** Provide clear objectives, output formats, tool guidance, and task boundaries
to prevent subagent duplication and coordination failures.

**How to apply:**
- Every subagent dispatch MUST include: objective, expected output format, which tools to use, what NOT to do
- Define explicit task boundaries — "Search for X. Do NOT search for Y. That is handled by another agent."
- Include output format templates in the dispatch prompt — agents that know their output shape produce more focused results

**Anti-pattern:** Dispatching subagents with vague instructions like "research this topic"
and hoping they coordinate themselves. Without boundaries, multiple agents will search
for the same thing and produce redundant results.

**Audit question:** "Does each subagent know its boundaries — what it owns and what another agent handles?"

### Principle 3: Scale Effort Appropriately

**What:** Embed explicit rules that match computational effort to task complexity.
Simple tasks should use fewer agents; complex tasks should use more.

**Scaling guidelines from Anthropic:**

| Task Complexity | Agents | Tool Calls per Agent | Example |
|----------------|--------|---------------------|---------|
| Simple fact-finding | 1 agent | 3-10 calls | "What is the capital of France?" |
| Comparison / analysis | 2-4 subagents | 5-15 calls each | "Compare pricing of 3 cloud providers" |
| Complex research | 10+ subagents | 10-20 calls each | "Analyze market trends in AI infrastructure" |

**How to apply:**
- Include a complexity classifier in the orchestrator's prompt
- Map complexity levels to concrete agent counts and tool call budgets
- Prevent over-engineering simple queries (wasting tokens) and under-resourcing complex ones (producing shallow results)

**Anti-pattern:** Using the same number of agents regardless of task complexity.
A simple lookup dispatching 10 agents wastes 15x tokens. A deep research question
using 1 agent produces surface-level results.

**Audit question:** "Does the orchestrator adjust agent count and depth based on input complexity?"

### Principle 4: Design Tools Critically

**What:** Agent-tool interfaces matter as much as human-computer interfaces.
Tool descriptions, parameter names, and error messages directly affect agent behavior.

**How to apply:**
- Write tool descriptions as if for a new team member — clear, specific, with examples
- Include what the tool returns AND what it does NOT return
- Name parameters descriptively — `search_query` not `q`, `max_results` not `n`
- Return structured errors that tell the agent what to try next, not just "failed"

**Anti-pattern:** Copying tool descriptions from API docs without adapting them for
agent consumption. Human-readable API docs often omit the "when to use this vs. that"
guidance that agents need.

**Audit question:** "Would a new team member know exactly when to use each tool and how to interpret its output?"

### Principle 5: Enable Self-Improvement

**What:** Claude 4 models can diagnose their own failure modes and rewrite tool
descriptions. This yielded a 40% improvement in task completion in Anthropic's system.

**How to apply:**
- After observing failure patterns, ask the model to analyze why it chose the wrong tool or approach
- Let the model propose revised tool descriptions or prompt modifications
- A/B test the original vs. revised versions on the same inputs
- Iterate: observe → diagnose → revise → test → deploy

**Anti-pattern:** Manually rewriting prompts based on your interpretation of why
the agent failed. The model often has better insight into its own decision process
than external observers.

**Audit question:** "Have I asked the model to diagnose its own failures and propose prompt improvements?"

### Principle 6: Start Broad, Narrow Later

**What:** Begin with short, general queries before drilling into specifics.
This produces better results than starting with narrow, specific searches.

**How to apply:**
- First search pass: broad terms, general context gathering
- Second pass: refine based on what the first pass revealed
- Avoid front-loading specificity — you don't know the right specific terms until you've done broad exploration

**Anti-pattern:** Starting with highly specific, narrow queries that miss relevant
context because the search terms were too restrictive.

**Audit question:** "Does the agent's search strategy start broad and narrow progressively?"

### Principle 7: Guide Thinking Processes

**What:** Extended thinking mode provides controllable scratchpads. Interleaved
thinking helps subagents adapt their approach based on intermediate results.

**How to apply:**
- Use extended thinking for complex decomposition and synthesis steps (lead agent)
- Use interleaved thinking for subagents — they should evaluate each tool result
  and decide whether to continue, pivot, or report back
- The thinking budget is a lever: more thinking = better quality but higher latency and token cost

**Anti-pattern:** Running agents without thinking mode when the task requires
multi-step reasoning. The agent makes premature decisions without evaluating
intermediate results.

**Audit question:** "Are agents using interleaved thinking to evaluate intermediate results before proceeding?"

### Principle 8: Parallelize Aggressively

**What:** Spin up 3-5 subagents simultaneously. Use 3+ parallel tool calls per subagent.
Parallelization reduced research time by up to 90% in Anthropic's system.

**How to apply:**
- Default to parallel dispatch unless tasks have true data dependencies
- Each subagent should make multiple tool calls in parallel (not sequential)
- Aggregate results after all parallel branches complete — don't wait for each sequentially

**Anti-pattern:** Sequential execution of independent tasks. If subagent B doesn't
depend on subagent A's results, running them sequentially wastes time proportional
to the number of agents.

**Audit question:** "Are independent subtasks running in parallel? Are subagents making parallel tool calls?"

### Principle Compliance Quick-Check

| # | Principle | Check | Status |
|---|-----------|-------|--------|
| 1 | Think like your agents | Have I run the agent's exact prompt myself? | |
| 2 | Teach orchestration | Does each subagent know its boundaries? | |
| 3 | Scale effort | Does agent count match task complexity? | |
| 4 | Design tools critically | Are tool descriptions agent-optimized? | |
| 5 | Enable self-improvement | Has the model diagnosed its own failures? | |
| 6 | Start broad, narrow later | Do searches start general then refine? | |
| 7 | Guide thinking | Are agents using interleaved thinking? | |
| 8 | Parallelize aggressively | Are independent tasks running in parallel? | |

---

## Evaluation Methodology

### Small-Sample Starting Point

Start with ~20 queries representing real usage patterns. This is sufficient to reveal
dramatic impacts from prompt changes (30% to 80% success rates observed).

**Why small samples work:** Multi-agent systems have high variance. A small, representative
sample catches gross failures quickly. Scale up evaluation only after the system handles
the initial 20 queries well.

### LLM-as-Judge Methodology

Use a single LLM call to evaluate outputs against a structured rubric:

| Criterion | What It Measures | Score Range |
|-----------|-----------------|-------------|
| **Factual accuracy** | Do claims match cited sources? | 0.0 - 1.0 |
| **Citation accuracy** | Do sources actually support the claims? | 0.0 - 1.0 |
| **Completeness** | Are all aspects of the query covered? | 0.0 - 1.0 |
| **Source quality** | Primary vs. secondary sources used? | 0.0 - 1.0 |
| **Tool efficiency** | Were tools used appropriately (no wasted calls)? | 0.0 - 1.0 |

Each output receives a composite 0.0-1.0 score and a pass/fail grade.

### Human Evaluation Remains Essential

Automated evals catch systematic issues. Human evaluation catches:
- Hallucinations that sound plausible but are factually wrong
- Source selection biases (preferring certain types of sources)
- Edge cases in formatting, attribution, or presentation
- Subtle quality issues that rubric-based scoring misses

**Rule:** Never rely solely on LLM-as-judge. Periodic human review is a safety net
for evaluation blind spots.

### Evaluation Integration Checklist

| Component | Exists? | Where? |
|-----------|---------|--------|
| Representative query set (20+) | | |
| LLM-as-judge with 5-criterion rubric | | |
| Scoring threshold for pass/fail | | |
| Human review schedule | | |
| Before/after comparison for prompt changes | | |

---

## Production Engineering Patterns

### Statefulness: Checkpoint Over Restart

Minor system failures can be catastrophic for agents without proper mitigation.
The system MUST support resuming from checkpoint rather than requiring full restarts.

**Implementation:**
- Save progress after each completed subtask
- On failure, resume from the last successful checkpoint
- Do not re-execute completed work — validate that prior artifacts still exist, then continue

**Hub mapping:** `.pipeline/state.json` + git tag checkpoints per stage

### Debugging: Production Tracing

Non-determinism between runs demands production tracing of decision patterns and
interaction structures — without monitoring conversation contents (privacy).

**What to trace:**
- Which tools were called, in what order, with what parameters
- Decision points: what the agent chose and what alternatives existed
- Token usage per agent, per tool call
- Time spent per stage, per agent

**What NOT to trace:**
- Full conversation content (privacy risk)
- User queries verbatim (PII risk)

### Deployment: Rainbow Deployments

Rainbow deployments gradually shift traffic between versions, preventing disruption
to long-running agents. Unlike blue-green (instant cutover), rainbow protects
agents that are mid-execution during a deployment.

**Why this matters for agents:** A standard deployment that restarts all instances
kills any agent mid-research. Rainbow deployments let in-progress agents complete
on the old version while new agents start on the new version.

### Token Economics

Multi-agent systems use approximately 15x more tokens than single-agent chat interactions.
This overhead is justified only for high-value tasks.

| Metric | Value |
|--------|-------|
| Multi-agent vs single-agent performance | 90.2% win rate for multi-agent |
| Token usage explains performance variance | 80% of variance |
| Time reduction from parallelization | Up to 90% |
| Token overhead vs chat | ~15x |

**Decision framework:** Use multi-agent when the task value justifies 15x token cost
AND the task is parallelizable. Use single-agent for simple, sequential tasks.

### Production Readiness Checklist

| Concern | Check | Status |
|---------|-------|--------|
| Checkpoint/resume | Can the system resume from failure without re-executing completed work? | |
| Production tracing | Are decision patterns logged without exposing conversation content? | |
| Deployment safety | Does deployment protect in-progress agents? | |
| Token budget | Is there a per-run token budget with alerting? | |
| Retry budget | Is there a global retry limit (not just per-stage)? | |
| Context management | Does the lead agent externalize state before context pressure? | |

---

## Performance Benchmarks

These benchmarks are from Anthropic's production system and serve as reference
points — not as universal targets.

| Metric | Value | Context |
|--------|-------|---------|
| Multi-agent win rate vs single-agent | 90.2% | Opus lead + Sonnet workers vs single Opus |
| Performance variance explained by tokens | 80% | More tokens = better results, up to a point |
| Time reduction from parallelization | Up to 90% | For embarrassingly parallel research tasks |
| Token overhead | ~15x vs chat | The cost of coordination and parallel execution |
| Optimal subagent count | 3-5 simultaneous | Diminishing returns beyond 5 for most tasks |
| Optimal parallel tool calls per agent | 3+ | Sequential tool calls waste time on independent lookups |

---

## When Multi-Agent Works (and Doesn't)

### Works Well For

- Breadth-first research with parallelizable subtasks
- Tasks where quality improves with more diverse source coverage
- Problems that decompose into independent sub-problems
- High-value tasks where 15x token overhead is justified

### Struggles With

- Tasks requiring all agents to share identical context
- Heavy interdependencies between agents (sequential by nature)
- Real-time coordination and delegation (latency-sensitive)
- Low-value tasks where single-agent is sufficient

### Decision Table

| Signal | Approach |
|--------|----------|
| Task decomposes into 3+ independent subtasks | Multi-agent with parallelization |
| Task is sequential with each step depending on the previous | Single agent or prompt chaining |
| High value, broad research needed | Multi-agent (justify 15x cost) |
| Simple lookup or single-file change | Single agent (multi-agent is overkill) |
| All subtasks need the same full context | Single agent (context sharing overhead too high) |

---

## MUST DO

- Always check the 8-principle compliance table when reviewing orchestration patterns — Why: implicit violations degrade system quality silently over time
- Always start evaluation with a small representative sample (20 queries) before scaling — Why: catches gross failures quickly without wasting evaluation budget
- Always include human evaluation alongside LLM-as-judge — Why: automated evals have blind spots for plausible-sounding hallucinations
- Always implement checkpoint/resume for multi-agent pipelines — Why: minor failures become catastrophic without recovery points
- Always scale agent count to task complexity — Why: over-provisioning wastes 15x tokens; under-provisioning produces shallow results

## MUST NOT DO

- MUST NOT skip Principle 1 (think like your agents) — run the exact prompt yourself before deploying. Without direct observation, failure modes are invisible
- MUST NOT dispatch subagents without explicit task boundaries (Principle 2) — use structured dispatch with objective, output format, and scope limits instead
- MUST NOT rely solely on LLM-as-judge evaluation — complement with periodic human review to catch evaluation blind spots
- MUST NOT use sequential execution for independent subtasks — parallelize aggressively (Principle 8) to reduce time by up to 90%
- MUST NOT deploy multi-agent systems without production tracing — trace decision patterns and tool usage, not conversation content
