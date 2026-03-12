#!/bin/bash
# dangerous-command-blocker.sh — PreToolUse hook for Bash
# Blocks destructive commands that could cause irreversible damage
# and prevents interactive command hangs from shell aliases.
#
# Configuration:
#   Event: PreToolUse
#   Matcher: Bash
#   Exit codes: 0 = allow, 2 = block (message fed back to Claude)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Bash",
#           "command": ".claude/hooks/dangerous-command-blocker.sh"
#         }
#       ]
#     }
#   }

COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')
if [[ -z "$COMMAND" ]]; then exit 0; fi

# --- Catastrophic commands (always block) ---
CATASTROPHIC_PATTERNS=(
  'rm -rf /'
  'rm -rf /*'
  'rm -rf ~'
  'rm -rf \.'
  'mkfs\.'
  'dd if='
  ':(){:|:&};:'
  '> /dev/sda'
  'chmod -R 777 /'
  'chown -R .* /'
)

for pattern in "${CATASTROPHIC_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: Catastrophic command detected — '$pattern' matched."
    echo "This command could cause irreversible system damage."
    echo "If you need to delete files, target specific paths instead of root/home directories."
    exit 2
  fi
done

# --- Protected paths (block destructive ops against these) ---
PROTECTED_PATHS=(
  '.git/'
  '.git$'
  '.claude/'
  '.env'
  'node_modules/'
  '__pycache__/'
)

DESTRUCTIVE_OPS='rm |rm -|rmdir |mv .* /dev/null'

for path in "${PROTECTED_PATHS[@]}"; do
  if echo "$COMMAND" | grep -qE "$DESTRUCTIVE_OPS" && echo "$COMMAND" | grep -qE "$path"; then
    echo "BLOCKED: Destructive operation on protected path matching '$path'."
    echo "Protected paths (.git, .claude, .env) must not be deleted or moved to /dev/null."
    echo "If you need to modify these paths, ask the user for explicit confirmation first."
    exit 2
  fi
done

# --- Database destruction (block without explicit confirmation) ---
DB_DESTRUCTIVE='DROP DATABASE|DROP SCHEMA|TRUNCATE .* CASCADE|DROP TABLE .* CASCADE'

if echo "$COMMAND" | grep -qiE "$DB_DESTRUCTIVE"; then
  echo "BLOCKED: Database destructive command detected."
  echo "Commands like DROP DATABASE, DROP SCHEMA, and TRUNCATE CASCADE require explicit user confirmation."
  echo "Use targeted DELETE statements or ask the user to run this command manually."
  exit 2
fi

# --- Force push to main/master (block) ---
if echo "$COMMAND" | grep -qE 'git push.*--force.*(main|master)'; then
  echo "BLOCKED: Force push to main/master branch."
  echo "Force pushing to protected branches can overwrite team members' work."
  echo "Use a feature branch and create a pull request instead."
  exit 2
fi

# --- Recursive permission/ownership changes at root (block) ---
if echo "$COMMAND" | grep -qE '(chmod|chown) -R .* /[^.]'; then
  echo "BLOCKED: Recursive permission change on system path."
  echo "Changing permissions recursively on system directories can break the OS."
  echo "Target a specific project directory instead."
  exit 2
fi

# --- Interactive command hang prevention ---
# On macOS/some Linux configs, cp/mv/rm are aliased to cp -i/mv -i/rm -i.
# When Claude runs these without -f, the command hangs waiting for y/n input
# that never comes. Detect bare cp/mv/rm on files (not dirs) without -f.
#
# We only warn (exit 0) — not block — because most cases are harmless.
# The warning tells Claude to add -f or use 'command rm' to bypass aliases.

if echo "$COMMAND" | grep -qE '^\s*(cp|mv|rm)\s' && \
   ! echo "$COMMAND" | grep -qE '^\s*(cp|mv|rm)\s+-[a-zA-Z]*f'; then
  # Skip if it's a directory operation with -r (rm -r is fine, rm -rf already has -f)
  if echo "$COMMAND" | grep -qE '^\s*rm\s+-r\s' && \
     ! echo "$COMMAND" | grep -qE '^\s*rm\s+-rf'; then
    echo "WARNING: 'rm -r' without '-f' may hang if shell aliases add '-i' (interactive mode)."
    echo "Use 'rm -rf <path>' or 'command rm -r <path>' to bypass aliases."
    # Non-blocking warning
    exit 0
  fi
  # For bare cp/mv/rm without any -f flag
  if echo "$COMMAND" | grep -qE '^\s*(cp|mv)\s+[^-]'; then
    echo "WARNING: '$(echo "$COMMAND" | grep -oE '^\s*(cp|mv)')' may hang if shell aliases add '-i' (interactive mode)."
    echo "Add '-f' flag or prefix with 'command' to bypass aliases: 'command cp ...' or 'command mv ...'"
    # Non-blocking warning
    exit 0
  fi
fi

# --- Block gh run watch (GitHub API rate limit exhaustion) ---
# gh run watch polls every 3 seconds = 1200 requests/hour.
# GitHub's rate limit is 5000/hour — a single watch can exhaust 24% of it.
if echo "$COMMAND" | grep -qE 'gh run watch'; then
  echo "BLOCKED: 'gh run watch' polls every 3s and can exhaust GitHub API rate limits (5000/hr)."
  echo "Use 'gh run view <run-id>' for a single status check instead."
  echo "If you need to wait, use 'gh run view <run-id> --exit-status' which checks once and exits."
  exit 2
fi

# All checks passed
exit 0
