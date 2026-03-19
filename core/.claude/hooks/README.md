# Hooks

Hooks are shell scripts that run in response to Claude Code events. They are project-specific and should be adapted for your needs.

> **Note:** Hooks are configured in your project's `.claude/settings.json` or `~/.claude/settings.json`.

## Included Hooks

### Dangerous Command Blocker (`dangerous-command-blocker.sh`)

PreToolUse hook on `Bash` that blocks catastrophic commands (`rm -rf /`, `dd`, `mkfs`), protects critical paths (`.git/`, `.claude/`, `.env`), blocks database destruction (`DROP DATABASE`, `TRUNCATE CASCADE`), prevents force pushes to main/master, blocks CI bypass attempts (`--no-verify`, `[skip ci]`), warns about interactive command hangs (`cp`/`mv`/`rm` without `-f` that may hang from `-i` aliases), and blocks `gh run watch` (API rate limit exhaustion). Exit code 2 blocks the command and feeds the error message back to Claude.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": ".claude/hooks/dangerous-command-blocker.sh"
      }
    ]
  }
}
```

### Secret Scanner (`secret-scanner.sh`)

PreToolUse hook on `Write|Edit` that scans file content for leaked secrets before they're written to disk. Detects AWS keys, GitHub tokens, Google/Stripe/Slack/Anthropic/OpenAI API keys, private keys (PEM), database connection strings with passwords, JWTs, and hardcoded passwords. Skips safe file types (`.md`, `.txt`, images). Exit code 2 blocks the write and suggests using environment variables or a secrets manager.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": ".claude/hooks/secret-scanner.sh"
      }
    ]
  }
}
```

### Context Window Monitor — two options

Monitors context window usage and warns Claude when sessions get too long, preventing silent quality degradation. Choose ONE of the two approaches below.

**Option A: Tool-Count Heuristic (`context-window-monitor.sh`)** — Portable, works everywhere. Counts tool invocations per session and warns at configurable thresholds (default: 50 = WARNING, 80 = CRITICAL). Less precise but zero dependencies.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "command": ".claude/hooks/context-window-monitor.sh"
      }
    ]
  }
}
```

Environment variables: `CONTEXT_WARN_THRESHOLD` (default 50), `CONTEXT_CRIT_THRESHOLD` (default 80), `CONTEXT_DEBOUNCE` (default 10).

**Option B: Statusline Bridge (`context-window-statusline.sh` + `context-window-statusline-hook.sh`)** — Precise % monitoring. The statusline script receives actual token counts from Claude Code, writes them to a bridge file. The hook reads the bridge file and warns at % thresholds (default: 35% remaining = WARNING, 25% = CRITICAL). Requires Claude Code statusline support.

```json
{
  "statusline": ".claude/hooks/context-window-statusline.sh",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "command": ".claude/hooks/context-window-statusline-hook.sh"
      }
    ]
  }
}
```

Environment variables: `CONTEXT_WARN_PCT` (default 35), `CONTEXT_CRIT_PCT` (default 25), `CONTEXT_DEBOUNCE` (default 10).

Both options integrate with your existing `context-management` rules and `context-reducer-agent` — the warnings reference `/handover`, context-reducer-agent, and subagent delegation.

### Session Reminder (`session-reminder.sh`)

PostToolUse hook on `*` (all tools) that reminds Claude to checkpoint progress via `/save-session` at configurable intervals. Uses a counter-based approach: counts tool invocations per session and emits a non-blocking reminder at the threshold. Complements `context-window-monitor.sh` — session-reminder fires first (default: 40 tool uses) as a save prompt, then context-monitor fires later (default: 50) for handover/compaction. Always exits 0 (non-blocking, advisory only).

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "command": ".claude/hooks/session-reminder.sh"
      }
    ]
  }
}
```

Environment variables: `SESSION_REMIND_THRESHOLD` (default 40), `SESSION_REMIND_DEBOUNCE` (default 20).

### Prompt Enhance Reminder (`prompt-enhance-reminder.sh`)

UserPromptSubmit hook that injects a deterministic reminder so Claude never skips the `*Enhanced: ...*` indicator from the `prompt-auto-enhance` rule. The rule is advisory — Claude can skip it under context pressure. This hook makes it deterministic by injecting the reminder on every user prompt. Always exits 0 (non-blocking).

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/prompt-enhance-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

### Auto-Format on File Write (`auto-format.sh`)

PostToolUse hook on `Write|Edit` that auto-formats files after Claude writes them. Supports Python (black/ruff), JS/TS/JSON/YAML/CSS/HTML (prettier), Kotlin (ktfmt), Go (gofmt), Rust (rustfmt), Swift (swift-format), and Shell (shfmt). Only runs formatters that are installed — missing ones are silently skipped. Always non-blocking (exit 0). Customize the formatters to match your project tooling.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": ".claude/hooks/auto-format.sh"
      }
    ]
  }
}
```

## Example Hooks

### Test Verification After Code Changes

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "scripts/verify-tests.sh"
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/verify-tests.sh — Warn if tests might be affected
FILE=$(echo "$TOOL_INPUT" | jq -r '.file_path // .path // empty')
if [[ -z "$FILE" ]]; then exit 0; fi

# Check if a corresponding test file exists
TEST_FILE=$(echo "$FILE" | sed 's|src/|tests/test_|; s|app/|tests/test_|')
if [[ -f "$TEST_FILE" ]]; then
  echo "⚠️  Test file exists: $TEST_FILE — consider running tests"
fi
```

## Example: Workflow Step Logging

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Skill",
        "command": "scripts/log-workflow.sh"
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/log-workflow.sh — Log skill invocations for audit
SKILL=$(echo "$TOOL_INPUT" | jq -r '.skill // empty')
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TIMESTAMP | skill: $SKILL" >> .claude/logs/workflow.log
```

## Creating Your Own Hooks

1. Write a shell script that reads `$TOOL_INPUT` (JSON) from the environment
2. Add it to your settings.json with the appropriate event matcher
3. Keep hooks fast — they run synchronously and block the tool call

### Available Events

| Event | When it fires |
|-------|--------------|
| `PreToolUse` | Before a tool executes |
| `PostToolUse` | After a tool executes |
| `UserPromptSubmit` | When the user sends a message (before Claude responds) |
| `Notification` | When Claude sends a notification |

### Available Matchers

Match tool names: `Bash`, `Read`, `Write`, `Edit`, `Grep`, `Glob`, `Skill`, etc.

### Tips

- Use `jq` to parse the JSON input
- Exit 0 for success, non-zero to signal issues
- Keep hooks idempotent — they may run multiple times
- Log to `.claude/logs/` for debugging
