#!/bin/bash
# prompt-enhance-reminder.sh — UserPromptSubmit hook
# Injects a deterministic reminder so Claude never skips the Enhanced indicator
# and the Grade → Diagnose → Fix pipeline for non-trivial prompts.
#
# The prompt-auto-enhance rule is advisory — Claude can skip it under context
# pressure. This hook makes the behavioral contract deterministic.
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
echo "For non-trivial prompts (ambiguous, multi-file, multi-step): run the Grade → Diagnose → Fix pipeline from /prompt-auto-enhance. Grade on 6 dimensions first — only fix dimensions scoring below 4. Skip for direct instructions, single-file changes, and questions."
exit 0
