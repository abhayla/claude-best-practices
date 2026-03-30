---
name: learning-self-improvement
description: >
  Capture session learnings, detect recurring patterns, and generate skill
  proposals from accumulated knowledge. Use after completing work to record
  what was learned or when enough learnings exist to detect patterns.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<'session', 'detect-patterns', 'full', or specific learning topic>"
version: "1.0.0"
---

# Learning & Self-Improvement — Knowledge Accumulation

Dispatch the learning-self-improvement-master-agent to coordinate the
knowledge accumulation cycle from learning capture through pattern detection
to skill proposals. Routes to the agent which handles pattern thresholds,
evidence validation, and knowledge freshness.

**Critical:** All learning orchestration is owned by the agent. Do not
implement steps inline — this skill is a dispatch wrapper only. Skill
proposals require 3+ evidence occurrences — never propose from a single incident.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the learning-self-improvement-master-agent in standalone mode:

```
Agent(subagent_type="learning-self-improvement-master-agent", prompt="
  ## Workflow: learning-self-improvement
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Execute learn-n-improve → skill-factory → test-knowledge
3. Enforce 3+ occurrence threshold for pattern detection
4. Validate skill proposals have evidence, uniqueness, and clear scope
5. Flag stale learnings (> 90 days) for review
6. Manage state in `.workflows/learning-self-improvement/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **capture** → `learn-n-improve` → produces learnings JSON
- **detect_patterns** → `skill-factory` → produces skill proposals (3+ occurrences only)
- **knowledge_test** → `test-knowledge` → validates knowledge accuracy and freshness

### If Agent Is Not Available
If `learning-self-improvement-master-agent` is not provisioned in the project,
run the constituent skills manually: `/learn-n-improve session`, then
`/skill-factory` to detect patterns, then `/test-knowledge` to validate.

## STEP 2: Report Results

After the agent completes, relay the learning summary to the user:

- Learnings captured (count and categories)
- Patterns detected (with evidence count per pattern)
- Skill proposals (with confidence and evidence citations)
- Knowledge health (fresh vs stale entries)
- Handoff suggestion (`/skill-authoring-workflow` if proposals exist)

---

## MUST DO

- Always dispatch via learning-self-improvement-master-agent — do not inline orchestration
- Always report the evidence count for each detected pattern
- Always flag stale learnings (> 90 days) in the report

## MUST NOT DO

- MUST NOT implement learning logic in this skill — delegate to the agent
- MUST NOT propose skills from fewer than 3 occurrences — that violates reactive curation policy
- MUST NOT skip the knowledge_test step — stale knowledge is worse than no knowledge
