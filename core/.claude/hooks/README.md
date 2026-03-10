# Hook Examples

Hooks are shell scripts that run in response to Claude Code events. They are project-specific and should be adapted for your needs.

> **Note:** Hooks are configured in your project's `.claude/settings.json` or `~/.claude/settings.json`. The examples below show common patterns you can adapt.

## Example: Auto-Format on File Write

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "scripts/auto-format.sh"
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/auto-format.sh — Auto-format files after Claude writes them
FILE=$(echo "$TOOL_INPUT" | jq -r '.file_path // .path // empty')
if [[ -z "$FILE" ]]; then exit 0; fi

case "$FILE" in
  *.py)   black "$FILE" 2>/dev/null ;;
  *.js|*.ts|*.tsx) npx prettier --write "$FILE" 2>/dev/null ;;
  *.kt)   ktfmt "$FILE" 2>/dev/null ;;
esac
```

## Example: Test Verification After Code Changes

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
| `Notification` | When Claude sends a notification |

### Available Matchers

Match tool names: `Bash`, `Read`, `Write`, `Edit`, `Grep`, `Glob`, `Skill`, etc.

### Tips

- Use `jq` to parse the JSON input
- Exit 0 for success, non-zero to signal issues
- Keep hooks idempotent — they may run multiple times
- Log to `.claude/logs/` for debugging
