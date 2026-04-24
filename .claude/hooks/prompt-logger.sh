#!/bin/bash
# prompt-logger.sh — UserPromptSubmit hook
# Appends each user prompt to .claude/tasks/prompts.md for local session history.
#
# Configuration:
#   Event: UserPromptSubmit
#   Matcher: (empty — matches all prompts)
#   Exit codes: always 0 (non-blocking)
#   Output: writes to .claude/tasks/prompts.md, NEVER to stdout.
#           UserPromptSubmit stdout is injected into the conversation context —
#           writing there would double every prompt's token cost and leak the
#           log back into the transcript.
#
# Stdin JSON payload fields consumed: prompt, session_id, cwd
#
# Settings.json entry (append after prompt-enhance-reminder.sh):
#   {
#     "hooks": {
#       "UserPromptSubmit": [
#         {
#           "matcher": "",
#           "hooks": [
#             { "type": "command", "command": ".claude/hooks/prompt-enhance-reminder.sh" },
#             { "type": "command", "command": ".claude/hooks/prompt-logger.sh" }
#           ]
#         }
#       ]
#     }
#   }

# Stderr is silenced so a missing jq / git / etc. never surfaces in the
# conversation. This hook is strictly advisory — any failure is a no-op.
exec 2>/dev/null

input=$(cat)

# Gracefully no-op if jq is unavailable
command -v jq >/dev/null || exit 0

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""')
session_id=$(printf '%s' "$input" | jq -r '.session_id // ""')
cwd=$(printf '%s' "$input" | jq -r '.cwd // ""')

# Skip empty prompts (malformed stdin lands here too, since jq returns "")
[ -z "$prompt" ] && exit 0

# Resolve the repo root — prefer git, fall back to the cwd from the payload
repo=$(git rev-parse --show-toplevel 2>/dev/null)
[ -z "$repo" ] && repo="$cwd"
[ -z "$repo" ] && exit 0

log="$repo/.claude/tasks/prompts.md"
mkdir -p "$(dirname "$log")" || exit 0

# Header-on-first-write: ensures the log always opens with a recognisable title
# even if the seed wasn't provisioned (e.g., a fresh downstream project).
if [ ! -s "$log" ]; then
  {
    printf '# Prompt Log\n\n'
    printf '<!-- Auto-appended by .claude/hooks/prompt-logger.sh on every UserPromptSubmit event. -->\n'
    printf '<!-- Gitignored via /.claude/tasks/prompts.md — contains raw user prompts, may include secrets. -->\n\n'
  } >> "$log"
fi

ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
branch=$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null)
sha=$(git -C "$repo" rev-parse --short HEAD 2>/dev/null)

heading_suffix=""
if [ -n "$branch" ] && [ -n "$sha" ]; then
  heading_suffix=" — \`$branch@$sha\`"
fi

# Append the entry as a grouped redirection so each printf's trailing newline
# is preserved. (bash $(...) strips trailing newlines, which would run two
# back-to-back entries together — caught by test_multiple_appends_do_not_clobber.)
# Concurrent prompts can still interleave if both exceed PIPE_BUF; acceptable
# for an append-only log where ordering matters more than strict atomicity.
{
  printf '## %s%s\n' "$ts" "$heading_suffix"
  [ -n "$session_id" ] && printf -- '- session: `%s`\n' "$session_id"
  [ -n "$cwd" ] && printf -- '- cwd: `%s`\n' "$cwd"
  printf '\n~~~text\n%s\n~~~\n\n' "$prompt"
} >> "$log"

exit 0
