---
name: skill-authoring-workflow
description: >
  Author, validate, and register new skills, agents, and rules end-to-end.
  Use when creating new patterns from scratch, converting session learnings
  into skills, or when the full authoring pipeline is needed.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<skill name, learning reference, or pattern description>"
version: "1.0.0"
---

# Skill Authoring Workflow — Pattern Creation Pipeline

Dispatch the skill-authoring-master-agent to coordinate the full pattern
creation lifecycle from authoring through validation to registration. Routes
to the agent which handles overlap detection, quality gate enforcement, and
the mandatory /writing-skills process.

**Critical:** All authoring orchestration is owned by the agent. Do not
implement steps inline — this skill is a dispatch wrapper only. Quality
validation is BLOCKING — no pattern ships without passing all checks.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the skill-authoring-master-agent in standalone mode:

```
Agent(subagent_type="skill-authoring-master-agent", prompt="
  ## Workflow: skill-authoring
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Check existing skill catalog for overlap before authoring
3. Execute writing-skills → claude-guardian → skill-master
4. Enforce quality gates (pattern-structure, portability, self-containment)
5. Block on any FAIL validation items — no exceptions
6. Manage state in `.workflows/skill-authoring/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **author** → `writing-skills` → produces draft skill file via the full 6-step process
- **validate** → `claude-guardian` → produces validation report (BLOCKING gate)
- **catalog** → `skill-master` → registers the skill in the catalog

### If Agent Is Not Available
If `skill-authoring-master-agent` is not provisioned in the project, run
the constituent skills manually: `/writing-skills <name>` (follow all 6 steps),
then `/claude-guardian` to validate placement and quality, then verify the
skill appears in `/skill-master catalog`.

## STEP 2: Report Results

After the agent completes, relay the authoring summary to the user:

- Skill created (name, type, location)
- Validation results (pass/fail per check, quality score)
- Overlap check results (similar skills found, if any)
- Registry status (added to catalog or not)

---

## MUST DO

- Always dispatch via skill-authoring-master-agent — do not inline orchestration
- Always use /writing-skills for the authoring step — never create skills via direct file write
- Always report the full validation results including any WARN items

## MUST NOT DO

- MUST NOT implement authoring logic in this skill — delegate to the agent
- MUST NOT bypass the validate step — quality gates are mandatory and blocking
- MUST NOT create duplicate skills — overlap check MUST run before authoring begins
