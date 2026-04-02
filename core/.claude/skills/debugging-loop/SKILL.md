---
name: debugging-loop
description: >
  Orchestrate the full bug resolution cycle by chaining four skills:
  systematic-debugging (diagnosis) → fix-loop (iterative fix with retries) →
  auto-verify (structured test verification) → learn-n-improve (knowledge capture).
  Use when you want end-to-end bug resolution with retry escalation and verified
  proof — not just diagnosis. For diagnosis only, use /systematic-debugging instead.
type: workflow
triggers:
  - debug and fix
  - full debugging pipeline
  - resolve bug end to end
  - diagnose fix verify
  - own this bug
  - take over debugging
  - complete debug cycle
  - debug fix and verify
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<bug description, error output, or issue URL>"
version: "1.1.0"
---

# Debugging Loop — Structured Bug Resolution

Dispatch the debugging-loop-master-agent to coordinate the full
diagnosis-to-fix cycle with mandatory learning capture. Routes to the agent
which handles root cause classification, fix-loop escalation, and knowledge
recording.

**Critical:** This is a full-cycle orchestrator, NOT a diagnosis-only tool. For diagnosis without fix, use `/systematic-debugging` instead. All debugging orchestration is owned by the agent — do not implement steps inline. Learning capture is MANDATORY — never skip it.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the debugging-loop-master-agent in standalone mode:

```
Agent(subagent_type="debugging-loop-master-agent", prompt="
  ## Workflow: debugging-loop
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Execute systematic-debugging → fix-loop → auto-verify → learn-n-improve
3. Classify root cause (TIMING, STATE, CONFIG, LOGIC, EXTERNAL)
4. Escalate from fix-loop to debugger-agent if 2 iterations fail with same error
5. Enforce mandatory learning capture before completion
6. Manage state in `.workflows/debugging-loop/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **diagnose** → `systematic-debugging` → produces root cause diagnosis JSON
- **fix** → `fix-loop` → produces fix result JSON (guided by diagnosis)
- **verify** → `auto-verify` → produces verification result JSON
- **learn** → `learn-n-improve` → records fix pattern to knowledge base

### If Agent Is Not Available
If `debugging-loop-master-agent` is not provisioned in the project, run the
constituent skills manually: `/systematic-debugging`, then `/fix-loop` with
the diagnosis context, then `/auto-verify`, then `/learn-n-improve session`.

## STEP 2: Report Results

After the agent completes, relay the debugging summary to the user:

- Root cause classification and confidence level
- Fix applied and verification result
- Hypothesis trail (what was tested and eliminated)
- Learning recorded (topic and file location)
- Handoff suggestions (`/testing-pipeline-workflow` for regression check)

---

## MUST DO

- Always dispatch via debugging-loop-master-agent — do not inline orchestration
- Always relay root cause classification and learning details
- Always ensure the learn step executed — it is mandatory per workflow contract

## MUST NOT DO

- MUST NOT implement debugging logic in this skill — delegate to the agent
- MUST NOT skip the learning capture step — every fix must be recorded
- MUST NOT retry the same fix approach more than twice — escalate to debugger-agent instead
- MUST NOT be used for diagnosis-only — use /systematic-debugging for that
- MUST NOT skip any step in the chain (diagnose → fix → verify → learn) — the value is the full cycle
