#!/bin/bash
# pattern-quality-gate.sh — PreToolUse hook for Bash (git commit)
# Blocks commits that include non-compliant pattern files.
# Runs workflow_quality_gate_validate_patterns.py only when staged files include patterns.
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
#           "hooks": [
#             {
#               "type": "command",
#               "command": ".claude/hooks/pattern-quality-gate.sh",
#               "timeout": 30
#             }
#           ]
#         }
#       ]
#     }
#   }

# Only intercept git commit commands
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')
if [[ -z "$COMMAND" ]]; then exit 0; fi
if ! echo "$COMMAND" | grep -qE 'git\s+commit'; then exit 0; fi

# Check if any staged files are pattern files
PATTERN_FILES=$(git diff --cached --name-only 2>/dev/null | grep -E \
  '^(core/)?\.claude/(skills/[^/]+/SKILL\.md|agents/[^/]+\.md|rules/[^/]+\.md)$')

if [[ -z "$PATTERN_FILES" ]]; then
  # No pattern files staged — allow commit without validation
  exit 0
fi

# Pattern files are staged — run validator
echo "Pattern Quality Gate: validating staged pattern files..."
echo ""
echo "Staged patterns:"
echo "$PATTERN_FILES" | sed 's/^/  - /'
echo ""

RESULT=$(PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py 2>&1)
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
  echo "BLOCKED: Pattern validation failed. Fix these issues before committing:"
  echo ""
  echo "$RESULT"
  echo ""
  echo "Run 'PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py' to see full details."
  echo "Review .claude/rules/workflow-quality-gate.md for the quality standard."
  exit 2
fi

# Check for warnings (validator exits 0 but may print warnings)
if echo "$RESULT" | grep -qi 'warning'; then
  echo "Pattern Quality Gate: PASSED with warnings"
  echo ""
  echo "$RESULT" | grep -i 'warning'
  echo ""
  echo "Warnings are non-blocking but should be addressed."
fi

echo "Pattern Quality Gate: PASSED"
exit 0
