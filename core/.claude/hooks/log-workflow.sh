#!/bin/bash
# =============================================================================
# Claude Code Workflow Logging Hook (PostToolUse)
# =============================================================================
# Logs events and tracks Skill invocations (fix-loop, post-fix-pipeline).
# This is the KEY mechanism that detects Skill tool usage.
# Exit 0 always (logging, never blocks).
# =============================================================================

trap 'exit 0' ERR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook-utils.sh" 2>/dev/null || exit 0
parse_hook_input || exit 0

if [ -z "$HOOK_TOOL_NAME" ]; then exit 0; fi

# Skill invocation tracking
if [ "$HOOK_TOOL_NAME" = "Skill" ]; then
    SKILL_NAME=$(printf '%s' "$HOOK_TOOL_INPUT" | python -c "import sys,json;d=json.load(sys.stdin);print(d.get('skill',d.get('name','')))" 2>/dev/null)
    if [ -n "$SKILL_NAME" ]; then
        SKILL_OUTPUT_TEXT=$(get_tool_output)
        SKILL_SUCCESS=$(detect_skill_success "$SKILL_OUTPUT_TEXT")
        log_event "SKILL_INVOKED" "name=$SKILL_NAME" "success=$SKILL_SUCCESS"
        record_skill_invocation "$SKILL_NAME" "$SKILL_SUCCESS"

        # Clear fixLoopInvestigating when fix-loop completes
        # Note: testFailuresPending is cleared by post-test-update.sh when tests pass
        if [ "$SKILL_NAME" = "fix-loop" ]; then
            update_workflow_state '.fixLoopInvestigating = false'
            # Check if fix-loop args contain visual flag clearing request
            CLEAR_VISUAL=$(printf '%s' "$HOOK_TOOL_INPUT" | python -c "import sys,json;d=json.load(sys.stdin);a=d.get('args','');print('true' if 'visualIssuesPending' in str(a) else 'false')" 2>/dev/null)
            if [ "$CLEAR_VISUAL" = "true" ] && [ "$SKILL_SUCCESS" = "true" ]; then
                update_workflow_state '.visualIssuesPending = false'
                update_workflow_state '.visualIssuePendingDetails = null'
                log_event "VISUAL_ISSUES_CLEARED" "by=fix-loop"
            fi
            log_event "FIXLOOP_COMPLETE" "success=$SKILL_SUCCESS" "investigating=cleared"
        fi

        # Track verify-screenshots invocations
        if [ "$SKILL_NAME" = "verify-screenshots" ]; then
            update_workflow_state '.skillInvocations.verifyScreenshotsInvoked = true'
            update_workflow_state ".skillInvocations.verifyScreenshotsResult = \"$SKILL_SUCCESS\""
            log_event "VERIFY_SCREENSHOTS_INVOKED" "success=$SKILL_SUCCESS"
        fi
    fi
    exit 0
fi

# Event logging for other tools
case "$HOOK_TOOL_NAME" in
    "Bash")
        CMD=$(extract_input_field "command")
        log_event "BASH_CMD" "cmd=$(printf '%s' "$CMD" | head -c 100)"
        ;;
    "Write")
        log_event "FILE_WRITTEN" "path=$(extract_input_field file_path)"
        ;;
    "Edit")
        log_event "FILE_MODIFIED" "path=$(extract_input_field file_path)"
        ;;
    "Task")
        AT=$(printf '%s' "$HOOK_TOOL_INPUT" | python -c "import sys,json;print(json.load(sys.stdin).get('subagent_type',''))" 2>/dev/null)
        log_event "AGENT_DELEGATED" "type=$AT"
        ;;
    *)
        log_event "TOOL_USED" "tool=$HOOK_TOOL_NAME"
        ;;
esac

exit 0
