---
name: documentation-workflow
description: >
  Generate and maintain project documentation end-to-end: ADRs, API docs,
  structure enforcement, and staleness audits. Use when updating documentation
  after architecture decisions or code changes.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<scope: 'full', 'adr', 'api-docs', or specific doc path>"
version: "1.0.0"
---

# Documentation Workflow — Full Doc Generation Orchestration

Dispatch the documentation-master-agent to coordinate documentation
generation and maintenance. Routes to the agent which handles parallel
doc generation, structure enforcement, and staleness detection.

**Critical:** All documentation orchestration is owned by the agent. Do not
implement steps inline — this skill is a dispatch wrapper only.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the documentation-master-agent in standalone mode:

```
Agent(subagent_type="documentation-master-agent", prompt="
  ## Workflow: documentation
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Detect documentation framework (MkDocs, Docusaurus, plain markdown)
3. Execute ADR + API docs in parallel, then structure enforcement, then staleness check
4. Skip ADR/API steps based on project characteristics
5. Manage state in `.workflows/documentation/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **adr** → `adr` → produces architecture decision records (skipped if no decisions)
- **api_docs** → `api-docs-generator` → produces API documentation (skipped if no API)
- **structure** → `doc-structure-enforcer` → produces structure compliance report
- **staleness** → `doc-staleness` → produces staleness report with per-doc scores

### If Agent Is Not Available
If `documentation-master-agent` is not provisioned in the project, run the
constituent skills manually: `/adr` (if needed), then `/api-docs-generator`
(if needed), then `/doc-structure-enforcer`, then `/doc-staleness`.

## STEP 2: Report Results

After the agent completes, relay the documentation summary to the user:

- Documentation coverage (sections present vs missing)
- Staleness report (docs requiring immediate attention)
- ADR index (if generated)
- API doc coverage (endpoints documented vs total)

---

## MUST DO

- Always dispatch via documentation-master-agent — do not inline orchestration
- Always relay staleness scores for documents requiring attention
- Always report which steps were skipped and why (no architecture decisions, no API)

## MUST NOT DO

- MUST NOT implement documentation logic in this skill — delegate to the agent
- MUST NOT generate ADRs for projects without architecture decisions
- MUST NOT generate API docs for non-API projects
