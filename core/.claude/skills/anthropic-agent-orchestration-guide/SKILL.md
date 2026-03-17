---
name: anthropic-agent-orchestration-guide
description: >
  Reference guide for designing multi-agent orchestration systems. Covers
  Anthropic's 5 workflow patterns, agent vs skill decision framework,
  orchestration architecture, anti-patterns, and context management.
  Consult when designing new orchestrators or refactoring existing ones.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "[pattern name or question about orchestration]"
version: "1.0.0"
---

# Agent Orchestration Guide

Reference for designing and operating multi-agent systems. Covers workflow patterns, decision frameworks, architecture, anti-patterns, and context management.

**Query:** $ARGUMENTS

---

## Anthropic's 5 Workflow Patterns

These are the canonical agentic workflow patterns. Choose the simplest pattern that solves the problem.

### Pattern 1: Prompt Chaining

**What:** Decompose a task into fixed sequential steps. Each step's output feeds the next step's input. Add programmatic gates between steps.

**When to use:**
- Task naturally decomposes into 2-5 ordered subtasks
- Each subtask transforms input to output in a predictable way
- You want to trade latency for higher accuracy at each step

**Structure:**
```
Input → Step A → Gate → Step B → Gate → Step C → Output
```

**Example:** Document processing: extract → classify → summarize → format. Each step is a focused prompt, and gates validate output quality before proceeding.

**Implementation:** Use `Skill()` calls in sequence. Each skill is a self-contained step with its own validation.

### Pattern 2: Routing

**What:** Classify the input, then route to a specialized handler. The classifier determines which downstream path to take.

**When to use:**
- Inputs vary in type and require different handling
- Specialized prompts per input type outperform a general-purpose prompt
- Categories are well-defined and classifiable with high accuracy

**Structure:**
```
Input → Classifier → Route A (specialized handler)
                   → Route B (specialized handler)
                   → Route C (specialized handler)
```

**Example:** Support ticket system: classify as billing/technical/account, then route to a specialized agent with domain-specific tools and knowledge.

**Implementation:** Use a routing step that reads input, classifies it, then dispatches via `Skill()` or `Agent()` to the appropriate handler.

### Pattern 3: Parallelization

**What:** Divide work into independent subtasks and run them concurrently. Aggregate results when all complete. Two sub-patterns: **sectioning** (split by data partition) and **voting** (same task, multiple attempts, pick best).

**When to use:**
- Subtasks are independent — no shared state, no ordering constraint
- Total work exceeds a single context window's capacity
- Speed matters and the workload is embarrassingly parallel

**Structure:**
```
Input → Split → Agent A (partition 1)  → Aggregate → Output
              → Agent B (partition 2)  →
              → Agent C (partition 3)  →
```

**Example:** Code review across multiple modules: dispatch one review agent per module, aggregate findings into a consolidated report.

**Implementation:** Use multiple `Agent()` calls in a single response. Each agent receives a distinct partition of the work with explicit file boundaries. Main context aggregates results.

### Pattern 4: Orchestrator-Workers

**What:** A central orchestrator dynamically plans and delegates tasks to worker agents. Unlike prompt chaining, the orchestrator decides the plan at runtime based on the input.

**When to use:**
- Tasks are complex and cannot be predicted in advance
- The number and type of subtasks depends on the input
- Need adaptive planning — the orchestrator adjusts based on worker results

**Structure:**
```
Input → Orchestrator → Worker A → Orchestrator (evaluate)
                     → Worker B → Orchestrator (evaluate)
                     → ... (continue until done)
                     → Output
```

**Example:** Pipeline orchestrator: reads a PRD, plans which stages to run, dispatches stage agents, adjusts the plan if stages fail.

**Implementation:** The orchestrator is an agent (`.claude/agents/`) that loads a DAG from config, computes waves, and dispatches workers via `Agent()`. Workers return structured results; the orchestrator evaluates gates and decides next steps.

### Pattern 5: Evaluator-Optimizer

**What:** One agent generates output, another evaluates it, and the loop continues until the evaluator approves. Useful when generation is easier than evaluation, or when iterative refinement produces better results.

**When to use:**
- Clear evaluation criteria exist (rubric, test suite, linter)
- First-draft output consistently needs improvement
- The evaluation can be done by a different prompt/model than the generator

**Structure:**
```
Generator → Output → Evaluator → Feedback → Generator (retry)
                               → APPROVED → Final Output
```

**Example:** Code generation: write code → run tests → if tests fail, feed errors back to generator → retry until tests pass. The `fix-loop` + `auto-verify` pattern is a concrete instance.

**Implementation:** Use `Skill("fix-loop")` which internally runs generate-test-evaluate cycles with retry limits.

### Decision Table

| Signal | Pattern |
|--------|---------|
| Fixed sequence of 2-5 steps | Prompt Chaining |
| Input determines which handler to use | Routing |
| 3+ independent subtasks, speed matters | Parallelization |
| Dynamic planning, adaptive execution | Orchestrator-Workers |
| Generate → evaluate → refine cycle | Evaluator-Optimizer |
| Complex pipeline with DAG dependencies | Orchestrator-Workers + Parallelization |

---

## Agent vs Skill Decision Framework

Agents and skills serve different purposes. Choosing wrong creates unnecessary complexity or insufficient capability.

### Use a Skill When

| Signal | Example |
|--------|---------|
| Single-purpose workflow with defined steps | `/code-quality-gate` — 9 analysis steps |
| No subagent dispatch needed | `/writing-plans` — works entirely in main context |
| Invoked by the user as a slash command | `/brainstorm`, `/implement` |
| Read-only analysis or reference lookup | `/agent-orchestration-guide` (this skill) |
| Produces a single output artifact | `/prd-parser` → normalized PRD |

### Use an Agent When

| Signal | Example |
|--------|---------|
| Dispatches 2+ subagents or sequences 3+ skills | `pipeline-orchestrator` — dispatches stage agents |
| Needs its own context window (bulk reading) | `planner-researcher-agent` — reads many files for analysis |
| Runs as a worker dispatched by an orchestrator | `security-auditor-agent` — dispatched by review-gate |
| Requires tool scoping different from the caller | `code-reviewer-agent` — needs only read tools |
| Long-running with progress tracking | `plan-executor-agent` — executes across many tasks |

### Hybrid: Agent + Thin Skill Wrapper

When an orchestrator needs to be invocable as a slash command:

1. Create the agent in `.claude/agents/` with full orchestration logic
2. Create a thin skill wrapper in `.claude/skills/` that spawns the agent:

```markdown
## STEP 1: Dispatch Orchestrator Agent

Agent(subagent_type="pipeline-orchestrator", prompt="$ARGUMENTS")
```

This preserves the `/pipeline-orchestrator` slash command while keeping orchestration logic in an agent where it belongs.

---

## Orchestration Architecture

### 2-Level Hierarchy

```
Orchestrator Agent
  ├── Worker Agent A (via Agent())
  ├── Worker Agent B (via Agent())
  └── Worker Agent C (via Agent())
```

**Rules:**
- Maximum 2 levels: orchestrator → worker
- Workers MUST NOT spawn their own subagents
- Workers MAY invoke skills via `Skill()`
- All coordination flows through the orchestrator

### Prompt Template for Workers

Every worker agent dispatched by an orchestrator MUST receive:

```
1. OBJECTIVE — One sentence: what this worker must accomplish
2. CONTEXT — Background needed for the task
3. INPUTS — Artifact paths to read (upstream dependencies)
4. OUTPUTS — Artifact paths to produce (with expected format)
5. EXECUTION — Specific Skill() calls or steps to follow
6. VERIFICATION — How to validate outputs before returning
7. RETURN FORMAT — Structured JSON with gate, artifacts, decisions, blockers
```

### Artifact Contracts

Every stage in a pipeline produces typed artifacts consumed by downstream stages:

```yaml
stage_2_plan:
  artifacts_in:
    prd: "stage_1_prd.artifacts_out.prd"
  artifacts_out:
    plan:
      path: "docs/plans/<feature>-plan.md"
      schema: "plan_v1"
```

**Validation rules:**
- Before dispatching: verify all `artifacts_in` exist on disk
- After completion: verify all `artifacts_out` exist and are non-empty
- If gate is PASSED but artifacts are missing: override to FAILED

### State Management

Single state file (`.pipeline/state.json`) is the source of truth:

```json
{
  "pipeline_id": "<uuid>",
  "stages": {
    "stage_1_prd": {
      "status": "passed|failed|pending|running|skipped|blocked|rolled_back",
      "retries": 0,
      "gate_result": null
    }
  },
  "global_retries_used": 0,
  "current_wave": 0
}
```

**Rules:**
- Write state after every mutation before the next action
- Never split state across files or hold it only in memory
- Event log (`.pipeline/event-log.jsonl`) is append-only audit trail

---

## Anti-Patterns

### 1. Subagent Spawning Subagents

**Problem:** Agent A dispatches Agent B, which dispatches Agent C. Creates invisible execution trees where failures are unattributable, token budgets are unpredictable, and no single context has visibility into the full execution.

**Fix:** Flatten to 2 levels. The orchestrator dispatches all agents directly. If Agent B needs work from Agent C, the orchestrator sequences them.

### 2. Inline DAG Definitions

**Problem:** Stage definitions, dependencies, and skip conditions are hardcoded in the orchestrator's prompt. Changing the pipeline requires editing the agent/skill, which risks breaking the orchestration logic.

**Fix:** Externalize to `config/pipeline-stages.yaml`. The orchestrator reads this at runtime. Pipeline structure changes are config changes, not code changes.

### 3. State Scattered Across Files

**Problem:** Pipeline state lives in multiple files: stage statuses in `state.json`, decisions in `decisions.log`, blockers in a separate file. Resume and rollback must reconcile multiple sources.

**Fix:** Single `state.json` with all stage statuses, decisions, blockers, and retries. Event log is separate but append-only (audit trail, not operational state).

### 4. Unbounded Retries

**Problem:** Each stage retries 3 times independently. A pipeline with 11 stages could burn 33 retries before reaching the user. Combined with subagent costs, this wastes significant tokens.

**Fix:** Global retry budget (default: 15). When exhausted, the orchestrator escalates regardless of individual stage limits.

### 5. Orchestrator Doing Worker Work

**Problem:** The orchestrator reads files, makes implementation decisions, writes code, AND coordinates stages. Its context fills up with worker-level details, degrading coordination quality.

**Fix:** Orchestrators coordinate only. They dispatch, validate gates, manage state, and handle failures. All substantive work happens in worker agents or skills.

### 6. Workers Communicating Directly

**Problem:** Agent A writes a file that Agent B reads mid-execution. No guarantee of ordering, no conflict detection, no rollback if A's output was wrong.

**Fix:** All data flows through the orchestrator. Agent A produces artifacts; the orchestrator validates them; then Agent B is dispatched with validated artifact paths.

### 7. Fat Worker Prompts

**Problem:** Dumping entire file contents, full project architecture, and conversation history into every worker prompt. Workers waste tokens re-reading context irrelevant to their task.

**Fix:** Pass file paths (not contents) — let workers read what they need. Include only task-specific requirements, file boundaries, and verification commands.

---

## Context & Token Management

### Budget Allocation

| Component | Recommended Context Budget |
|-----------|---------------------------|
| Orchestrator | Reserve 40% for coordination, state tracking, decision making |
| Worker agents | Each gets its own context window — no sharing |
| Main conversation | Reserve 20% for user communication and final reporting |

### Reducing Orchestrator Context Usage

1. **Externalize stage definitions** — Read from config, don't hold in prompt
2. **Summarize worker results** — Extract gate/artifacts/blockers, discard verbose output
3. **Delegate bulk reading** — Workers read files; orchestrator reads only summaries
4. **Checkpoint to disk** — Write state to `.pipeline/state.json`, not just in-memory

### Worker Context Efficiency

1. **Point, don't paste** — Give file paths, not file contents
2. **Specify line ranges** — "Read `src/api.py` lines 15-45" instead of the whole file
3. **Limit read scope** — Only files essential for the subtask
4. **Provide summaries for large contexts** — "Tests use pytest with fixtures in conftest.py" instead of "read the entire test suite"

### Long-Running Pipelines

For pipelines exceeding 30 minutes or 10+ stages:

1. **Write progress to disk** — Dashboard and state survive context compaction
2. **Use git tags as checkpoints** — Each stage start is tagged for clean rollback
3. **Resume from state file** — If context is lost, re-read `.pipeline/state.json` and continue

---

## References

- [Anthropic: Building Effective Agents](https://docs.anthropic.com/en/docs/build-with-claude/agentic-patterns) — Canonical source for the 5 workflow patterns
- [Anthropic: Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering) — Foundations for agent prompt design
- `config/pipeline-stages.yaml` — Pipeline DAG configuration
- `.claude/agents/project-manager-agent.md` — Production orchestrator implementation
- `.claude/skills/subagent-driven-dev/SKILL.md` — Detailed subagent dispatch patterns
- `.claude/rules/agent-orchestration.md` — Enforced constraints for orchestration

---

## MUST DO

- Always consult the decision table before choosing a workflow pattern — default to the simplest pattern that works
- Always use 2-level hierarchy (orchestrator → workers) — never deeper
- Always externalize DAGs and stage definitions to config files
- Always use a single state file as source of truth
- Always pass structured return contracts to worker agents
- Always validate artifact contracts before dispatching downstream stages

## MUST NOT DO

- MUST NOT let workers spawn their own subagents — flatten to 2 levels
- MUST NOT hardcode pipeline structure in agent/skill bodies — use config files
- MUST NOT scatter state across multiple files — single source of truth
- MUST NOT allow unbounded retries — enforce global budget (15 max)
- MUST NOT let the orchestrator do worker-level work — dispatch, don't implement
- MUST NOT pass full file contents in worker prompts — pass paths, let workers read
