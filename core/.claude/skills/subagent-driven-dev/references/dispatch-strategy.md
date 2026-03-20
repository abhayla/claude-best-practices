# STEP 4: Dispatch Strategy

### 4.1 Full Parallel (Fan-Out)

Use when all subtasks are independent and touch different files.

```
Dispatch pattern: Fan-out
  Agent A: User validation     (users.py, test_users.py)
  Agent B: Order validation    (orders.py, test_orders.py)
  Agent C: Product validation  (products.py, test_products.py)
  ↓ all complete ↓
  Main: Aggregate results, run full test suite, commit
```

Dispatch all agents simultaneously:

```
Agent("Subtask A: User validation ... [full prompt]")
Agent("Subtask B: Order validation ... [full prompt]")
Agent("Subtask C: Product validation ... [full prompt]")
```

### 4.2 Sequential with Parallel Waves

Use when some subtasks depend on others but independent groups exist within waves.

```
Wave 1 (sequential pre-work):
  Main context: Create base validator class, commit

Wave 2 (parallel):
  Agent A: User validation
  Agent B: Order validation
  Agent C: Product validation

Wave 3 (sequential post-work):
  Main context: Integration test, update API docs, commit
```

### 4.3 Pipeline (Sequential Fan-Out)

Use when later subtasks depend on earlier ones but each wave has parallelism.

```
Wave 1: Agent A (data models) + Agent B (config setup)
  ↓ both complete ↓
Wave 2: Agent C (API endpoints, depends on A) + Agent D (CLI commands, depends on A)
  ↓ both complete ↓
Wave 3: Agent E (integration tests, depends on C and D)
```

### 4.4 Research Fan-Out + Sequential Implementation

Use when you need to gather information from multiple sources before implementing.

```
Research phase (parallel):
  Agent A: "Read src/api/ and summarize all endpoint patterns"
  Agent B: "Read tests/ and summarize test conventions"
  Agent C: "Read docs/API.md and extract validation requirements"
  ↓ all complete ↓

Synthesis (main context):
  Combine research findings, make design decisions

Implementation (parallel or sequential based on findings):
  Dispatch implementation subagents with full context from research
```

This pattern is especially useful when exploring unfamiliar codebases. The research subagents consume their own context windows, keeping the main conversation lean.

---

