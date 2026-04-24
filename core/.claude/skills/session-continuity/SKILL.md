---
name: session-continuity
description: >
  Save, restore, and hand over session context between conversations as a
  skill-at-T0 orchestrator (Phase 3.6 of subagent-dispatch-platform-limit
  remediation). The skill body IS the orchestrator — runs in the user's
  T0 session. Modes: save (ending session), restore (starting session),
  handover (produce handover doc from saved session). Invokes sub-skills
  (/save-session, /start-session, /continue, /handover) via Skill();
  optionally dispatches session-summarizer-agent via Agent() at T0 for
  deep session analysis when the save/handover needs it.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<'save', 'restore', 'handover', or session file path>"
version: "2.0.0"
triggers:
  - session continuity
  - manage session
  - save or restore session
  - session management
  - preserve session context
---

# /session-continuity — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `session-continuity-master-agent` is NOT dispatched (deprecated
Phase 3.6, 2026-04-25); its orchestration lives here.

**Why skill-at-T0:** Same platform constraint Phases 3.1–3.5 — dispatched
subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents)). Legacy
`session-continuity-master-agent` → `session-summarizer-agent` (T2)
dispatch would silently inline.

**Critical:** Must NEVER restore from sessions older than 24 hours without
warning the user; never overwrite existing session files (always timestamp-
new-ones); always surface freshness assessment on restore.

**Input:** `$ARGUMENTS` — mode keyword or session-file path.

---

## CLI Signature

```
/session-continuity <mode | session-file-path>
                    [--deep-summary] [--force]
```

| Argument / Flag | Default | Meaning |
|-----------------|---------|---------|
| `mode` | (required) | `save` \| `restore` \| `handover` \| `<session-file-path>` (implicit restore) |
| `--deep-summary` | off | Dispatch session-summarizer-agent in STEP 2/4 for deep analysis |
| `--force` | off | Restore from sessions > 24h old without prompt; overwrite existing session file |

---

## STEP 1: INIT + MODE DETECTION

1. **Parse args.** Detect mode:
   - keyword `save` → save current session
   - keyword `restore` → find most recent session file, restore it
   - keyword `handover` → produce handover doc from most recent saved session
   - path ending in `.json` or `.md` under `.claude/sessions/` → restore that file
2. **Read config.** `config/workflow-contracts.yaml` → `workflows.session-continuity`.
   `master_agent` should be null; `sub_orchestrators` empty (Phase 3.6).
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state** at `.workflows/session-continuity/state.json` (schema
   2.0.0): `mode: "<save|restore|handover>"`, `step_status`, `dispatches_used: 0`.
5. Append INIT event.

---

## STEP 2: SAVE (mode == save)

```
Skill("/save-session", args="<optional session name>")
```

`/save-session` captures working files, git state, key decisions, task
progress. Writes to `.claude/sessions/{run_id}.md` (or json; format per
skill). MUST NOT overwrite existing file without `--force`.

If `--deep-summary`: dispatch session-summarizer-agent for deeper analysis:

```
Agent(subagent_type="session-summarizer-agent", prompt="""
## Workflow: session-continuity
## Mode: deep-summary-for-save
## Session file: <path just written>
## Conversation transcript: <path or in-context>

Analyze the session for non-obvious decisions, emerging patterns, open
questions, and suggested next actions. Append structured findings to
the session file. Return contract with summary fields.
""")
```

Increment `dispatches_used` by 1.

Capture session file path into `state.artifacts.session_file`.

---

## STEP 3: RESTORE (mode == restore OR path arg)

```
Skill("/start-session", args="<session file path>")
```

`/start-session` reads the session file + restores working-file context.
Freshness validation:
- If session > 24 hours old AND `--force` NOT set → surface warning, ask
  user to confirm before proceeding
- If session > 7 days old → harder warning (recommend fresh start instead)

Capture restored state into `state.artifacts.restored_from`.

---

## STEP 4: HANDOVER (mode == handover OR after save)

```
Skill("/handover", args="<session file path>")
```

`/handover` generates a structured handover document (`.claude/handovers/`)
designed for a fresh session to pick up where left off. Covers decisions,
partial work, open questions, and recommended next actions.

If `--deep-summary` (and hasn't already been dispatched in STEP 2): dispatch
session-summarizer-agent here instead for the handover's summary block.

Capture handover doc path into `state.artifacts.handover_doc`.

---

## STEP 5: REPORT

1. **Finalize state.** Write `test-results/session-continuity-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "COMPLETED | WARNED | BLOCKED",
     "mode": "<save|restore|handover>",
     "artifacts": { "session_file": "<path|null>",
                    "handover_doc": "<path|null>",
                    "restored_from": "<path|null>" },
     "freshness": { "age_hours": <float>, "classification": "FRESH|STALE|ANCIENT" },
     "deep_summary_used": <bool>,
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Session Continuity: <COMPLETED | WARNED>
     Run ID: <run_id>
     Mode: <save | restore | handover>
     Session file: <path>
     Handover doc: <path or N/A>
     Freshness: <FRESH | STALE | ANCIENT> (<age_hours>h)
     Deep summary: <YES | NO>
   ============================================================
   ```
3. **Handoff suggestions:**
   - After save: `Next session: /start-session <file>` or `/continue`
   - After restore: state the suggested next action from the session's
     "Resume Notes" section
   - After handover: direct user to share the handover doc with whoever
     picks up next

---

## CRITICAL RULES

- MUST run at T0 — skill body is injected into user's session. Dispatching
  this as a worker strips `Agent` at runtime and optional
  session-summarizer-agent dispatch silently inlines.
- MUST NOT dispatch `session-continuity-master-agent` (deprecated
  2026-04-25, 2-cycle window).
- MUST NOT restore from sessions > 24h old without `--force` or user confirm.
- MUST NOT overwrite existing session files without `--force` — always
  timestamp new ones.
- MUST surface freshness assessment in the restore dashboard — silently
  restoring stale state leads to confused resumption.
- MUST write `.workflows/session-continuity/state.json` + `events.jsonl`
  after every step transition.
