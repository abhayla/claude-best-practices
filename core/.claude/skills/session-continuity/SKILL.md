---
name: session-continuity
description: >
  Save, restore, and hand over session context between conversations.
  Use when ending a session to preserve context, or when starting a
  new session to restore previous working state.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<'save', 'restore', 'handover', or session file path>"
version: "1.0.0"
---

# Session Continuity — Save, Restore, and Handover

Dispatch the session-continuity-master-agent to coordinate session
persistence and restoration. Routes to the agent which handles mode
detection (save vs restore), freshness validation, and handover generation.

**Critical:** All session management is owned by the agent. Do not implement
steps inline — this skill is a dispatch wrapper only.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the session-continuity-master-agent in standalone mode:

```
Agent(subagent_type="session-continuity-master-agent", prompt="
  ## Workflow: session-continuity
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Detect mode: save (ending session), restore (starting session), or handover only
3. Execute save → handover for save mode, or read session file for restore mode
4. Validate session freshness when restoring (warn if > 24 hours old)
5. Manage state in `.workflows/session-continuity/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **save** → `save-session` → produces session file in `.claude/sessions/`
- **handover** → `handover` → produces handover document from session data

### If Agent Is Not Available
If `session-continuity-master-agent` is not provisioned in the project, run
the constituent skills manually: `/save-session` to capture state, then
`/handover` to generate the handover document. For restore, use `/start-session`
or `/continue`.

## STEP 2: Report Results

After the agent completes, relay the session summary to the user:

- Session file location and key context preserved
- Freshness assessment (if restoring)
- Files modified, decisions made, and blockers captured
- Suggested next action for the new session

---

## MUST DO

- Always dispatch via session-continuity-master-agent — do not inline orchestration
- Always relay the session freshness assessment when restoring
- Always include the list of modified files and open blockers in the report

## MUST NOT DO

- MUST NOT implement session logic in this skill — delegate to the agent
- MUST NOT restore from sessions older than 24 hours without warning the user
- MUST NOT overwrite existing session files — create new ones with timestamps
