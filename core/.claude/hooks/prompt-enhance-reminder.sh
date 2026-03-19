#!/bin/bash
# prompt-enhance-reminder.sh — UserPromptSubmit hook
# Injects a deterministic reminder so Claude never skips the Enhanced indicator.
#
# The prompt-auto-enhance rule (.claude/rules/prompt-auto-enhance-rule.md) is
# advisory — Claude can skip it under context pressure. This hook makes it
# deterministic by injecting the reminder on every user prompt.
#
# Configuration:
#   Event: UserPromptSubmit
#   Matcher: (empty — matches all prompts)
#   Exit codes: always 0 (non-blocking)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "UserPromptSubmit": [
#         {
#           "matcher": "",
#           "command": ".claude/hooks/prompt-enhance-reminder.sh"
#         }
#       ]
#     }
#   }

echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
echo "Gather Tier 1 context (patterns, CLAUDE.md, git state) before responding."
exit 0
