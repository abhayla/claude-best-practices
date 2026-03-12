#!/bin/bash
# secret-scanner.sh — PreToolUse hook for Write|Edit
# Scans file content for leaked secrets before they're written to disk.
#
# Configuration:
#   Event: PreToolUse
#   Matcher: Write|Edit
#   Exit codes: 0 = allow, 2 = block (message fed back to Claude)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Write|Edit",
#           "command": ".claude/hooks/secret-scanner.sh"
#         }
#       ]
#     }
#   }

# Extract content to scan — Write uses "content", Edit uses "new_string"
CONTENT=$(echo "$TOOL_INPUT" | jq -r '.content // .new_string // empty')
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')
if [[ -z "$CONTENT" ]]; then exit 0; fi

# Skip scanning known safe file types
case "$FILE_PATH" in
  *.md|*.txt|*.csv|*.svg|*.png|*.jpg|*.gif|*.ico)
    exit 0
    ;;
esac

FOUND=""

# --- AWS credentials ---
if echo "$CONTENT" | grep -qE 'AKIA[0-9A-Z]{16}'; then
  FOUND="${FOUND}\n- AWS Access Key ID (AKIA...)"
fi
if echo "$CONTENT" | grep -qE 'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}'; then
  FOUND="${FOUND}\n- AWS Secret Access Key"
fi

# --- Generic API keys/tokens (quoted strings with key-like prefixes) ---
if echo "$CONTENT" | grep -qiE '(api_key|apikey|api_secret|access_token|auth_token|secret_key)\s*[=:]\s*["\x27][A-Za-z0-9_\-]{20,}["\x27]'; then
  FOUND="${FOUND}\n- API key or token assignment"
fi

# --- Private keys ---
if echo "$CONTENT" | grep -qE '-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'; then
  FOUND="${FOUND}\n- Private key (PEM format)"
fi

# --- GitHub tokens ---
if echo "$CONTENT" | grep -qE 'gh[pousr]_[A-Za-z0-9_]{36,}'; then
  FOUND="${FOUND}\n- GitHub personal access token"
fi

# --- Google API/OAuth ---
if echo "$CONTENT" | grep -qE 'AIza[0-9A-Za-z_\-]{35}'; then
  FOUND="${FOUND}\n- Google API key"
fi

# --- Slack tokens ---
if echo "$CONTENT" | grep -qE 'xox[baprs]-[0-9a-zA-Z\-]{10,}'; then
  FOUND="${FOUND}\n- Slack token"
fi

# --- Stripe keys ---
if echo "$CONTENT" | grep -qE '(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}'; then
  FOUND="${FOUND}\n- Stripe API key"
fi

# --- Database connection strings with passwords ---
if echo "$CONTENT" | grep -qiE '(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@'; then
  FOUND="${FOUND}\n- Database connection string with embedded password"
fi

# --- Generic password assignments ---
if echo "$CONTENT" | grep -qiE '(password|passwd|pwd)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]'; then
  # Exclude common placeholder/example values
  if ! echo "$CONTENT" | grep -qiE '(password|passwd|pwd)\s*[=:]\s*["\x27](password|changeme|example|placeholder|your_|TODO|xxx|REPLACE_ME)'; then
    FOUND="${FOUND}\n- Hardcoded password"
  fi
fi

# --- JWT tokens ---
if echo "$CONTENT" | grep -qE 'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_\-]{10,}'; then
  FOUND="${FOUND}\n- JWT token"
fi

# --- Anthropic API keys ---
if echo "$CONTENT" | grep -qE 'sk-ant-[A-Za-z0-9_\-]{20,}'; then
  FOUND="${FOUND}\n- Anthropic API key"
fi

# --- OpenAI API keys ---
if echo "$CONTENT" | grep -qE 'sk-[A-Za-z0-9]{20,}'; then
  # Exclude Stripe keys already caught above
  if ! echo "$CONTENT" | grep -qE 'sk_(test|live)_'; then
    FOUND="${FOUND}\n- OpenAI API key"
  fi
fi

# --- Report findings ---
if [[ -n "$FOUND" ]]; then
  echo "BLOCKED: Potential secrets detected in file content for '$FILE_PATH'."
  echo ""
  echo "Detected patterns:"
  echo -e "$FOUND"
  echo ""
  echo "Do NOT write secrets directly into source files."
  echo "Use environment variables, .env files (gitignored), or a secrets manager instead."
  echo "If this is a false positive (e.g., documentation or test fixtures), ask the user to confirm."
  exit 2
fi

# All checks passed
exit 0
