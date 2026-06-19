# Claude Code Native Hook Events — Reference Catalog

> **Verified against live `code.claude.com/docs` on 2026-06-20** (Claude Code v2.1.183).
> Source of truth is always the official [hooks reference](https://code.claude.com/docs/en/hooks) and
> [hooks guide](https://code.claude.com/docs/en/hooks-guide) — re-verify before relying on a specific
> event, since per-event availability can shift between versions. This doc exists so hub authors don't
> re-run a web scan every time the question "is there a native hook for X?" comes up (DRY).

## Why this file exists

The migration ledger (`plans/platform-migration-2026H2.md`, Phase 1.3) decided to **KEEP** the hub's
existing governance hooks (`session-governance-status`, `no-overask-guard`, `verifier-edge-guard`,
`prompt-enhance-reminder`, `ba-usecase-discovery-reminder`) rather than re-home them onto native events —
migrating would be churn (KISS/YAGNI). Native events are recorded here as **available for additive
governance only when a concrete gap appears**. This catalog is the lookup table for that decision.

The hub currently wires only **3 of the 30** events in `.claude/settings.json`: `UserPromptSubmit`,
`Stop`, `SessionStart` (plus `PreToolUse`/`PostToolUse` for telemetry). The rest are available, not unused-by-defect.

## The 30 events

`matcher` = supports a matcher string (tool name / agent type / sub-type). `if` = supports a conditional
`if` expression (permission-rule syntax, e.g. `Bash(git *)`). `block` = can block/deny the action.

| Event | matcher | `if` | block | Notes |
|---|---|---|---|---|
| `SessionStart` | ✅ (`startup`,`resume`,`clear`,`compact`) | ❌ | ❌ | Outputs `additionalContext`, `sessionTitle`, `reloadSkills`. Only `command`/`mcp_tool` handlers. |
| `Setup` | ✅ (`init`,`maintenance`) | ❌ | ❌ | Fires on `--init-only`/`--init`/`--maintenance`. Only `command`/`mcp_tool` handlers. |
| `SessionEnd` | ✅ (`clear`,`resume`,`logout`,`other`,…) | ❌ | ❌ | Cleanup/logging only. |
| `UserPromptSubmit` | ❌ | ✅ | ✅ (exit 2) | 30 s default timeout (shorter than others). **Hub uses this.** |
| `UserPromptExpansion` | ✅ (command name) | ✅ | ✅ | Fires when a slash-command expands into a prompt. |
| `Stop` | ❌ | ❌ | ✅ (exit 2) | Supports `additionalContext` for feedback w/o full block. **Hub uses this.** |
| `StopFailure` | ✅ (error type: `rate_limit`,`overloaded`,…) | ❌ | ❌ | Observability only; output + exit code ignored. |
| `PreToolUse` | ✅ (tool name) | ✅ | ✅ | Can modify `updatedInput`; supports `permissionDecision`. **Hub uses this.** |
| `PermissionRequest` | ✅ (tool name) | ❌ | ✅ (allow/deny) | Can modify `updatedInput`. |
| `PermissionDenied` | ✅ (tool name) | ❌ | retry only | `hookSpecificOutput.retry: true` to allow retry. |
| `PostToolUse` | ✅ (tool name) | ✅ | ✅ | Can replace output via `updatedToolOutput`. **Hub uses this.** |
| `PostToolUseFailure` | ✅ (tool name) | ✅ | ❌ | Shows stderr to Claude; can replace tool output. |
| `PostToolBatch` | ❌ | ❌ | ✅ | Fires after all parallel tool calls in a batch resolve. |
| `MessageDisplay` | ❌ | ❌ | ❌ | Display-only; `displayContent` overlay does NOT modify transcript. |
| `SubagentStart` | ✅ (agent type) | ❌ | ❌ | Outputs `additionalContext` only. |
| `SubagentStop` | ✅ (agent type) | ❌ | ✅ | Can block subagent completion. |
| `TaskCreated` | ❌ | ❌ | ✅ (exit 2) | Fires on a `TaskCreate` tool call. |
| `TaskCompleted` | ❌ | ❌ | ✅ (exit 2) | |
| `TeammateIdle` | ❌ | ❌ | ✅ | Agent-team teammate about to idle (experimental Agent Teams). |
| `Notification` | ✅ (`permission_prompt`,`idle_prompt`,…) | ❌ | ❌ | Observability/logging only. |
| `Elicitation` | ✅ (MCP server name) | ❌ | ✅ (accept/decline/cancel) | MCP server requests user input mid-tool-call. |
| `ElicitationResult` | ✅ (MCP server name) | ❌ | ✅ | Fires after user responds; can override fields. |
| `ConfigChange` | ✅ (`user_settings`,`project_settings`,`local_settings`,`skills`,…) | ❌ | ✅ | Fires when a config/skills file changes mid-session. |
| `InstructionsLoaded` | ✅ (`session_start`,`path_glob_match`,`include`,…) | ❌ | ❌ | CLAUDE.md / `.claude/rules` loaded; observability only. |
| `CwdChanged` | ❌ | ❌ | ❌ | Working dir changed; async, can write `CLAUDE_ENV_FILE`. |
| `FileChanged` | ✅ (literal filenames) | ❌ | ❌ | Watched file changed on disk; async. |
| `WorktreeCreate` | ❌ | ❌ | ✅ (non-zero exit) | Replaces default git-worktree behavior; returns path via stdout. |
| `WorktreeRemove` | ❌ | ❌ | ❌ | Failures logged in debug mode only. |
| `PreCompact` | ✅ (`manual`,`auto`) | ❌ | ✅ | Before context compaction. |
| `PostCompact` | ✅ (`manual`,`auto`) | ❌ | ❌ | After compaction; observability only. |

**Conditional `if` is supported on only 5 events** (all tool-adjacent): `UserPromptSubmit`,
`UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`. It is **NOT** available on
`Stop`/`SessionStart`/`SubagentStop` — which is exactly why the hub's `Stop`-hook governance
(`no-overask-guard`, `verifier-edge-guard`) is implemented in shell logic, not declarative `if`.

## Handler types

All events accept `command`, `http`, `mcp_tool`, `prompt`, `agent` — **except** `SessionStart` and `Setup`
(only `command`/`mcp_tool`). The `agent`-type handler is flagged **experimental** in the docs.

## Candidate additive-governance gaps (not yet adopted — see ledger Phase 1.3 / audit P3)

- **`ConfigChange`** → could back the resource-CRUD approval gate that today lives only as prose in
  `.claude/rules/prompt-auto-enhance.md` (fires post-change as a detection backstop, the same role
  `no-overask-guard` plays for the enhance banner). **Status: design-only — runtime support in the
  installed CC version must be smoke-tested before wiring** (do not assume from the docs).
- **`SubagentStop`** → could move `verifier-edge-guard`'s done-claim check closer to the subagent boundary,
  but the ledger found this changes semantics, not improves them (the Stop-hook catches *main-loop*
  done-claims by design). Keep as-is unless a concrete subagent-level gap appears.
