#!/bin/bash
# =============================================================================
# Claude Code Pre-Skill Fix-Loop Unblock Hook (PreToolUse)
# =============================================================================
# When Skill("fix-loop") is about to execute, sets fixLoopInvestigating=true
# so that validate-workflow-step.sh unblocks Write/Edit during the fix-loop.
# Exit 0 always (never blocks Skill invocations).
# =============================================================================

trap 'exit 0' ERR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook-utils.sh" 2>/dev/null || exit 0
parse_hook_input || exit 0

if [ "$HOOK_TOOL_NAME" != "Skill" ]; then exit 0; fi

# Extract skill name
SKILL_NAME=$(printf '%s' "$HOOK_TOOL_INPUT" | python -c "import sys,json;d=json.load(sys.stdin);print(d.get('skill',d.get('name','')))" 2>/dev/null)

if [ "$SKILL_NAME" = "fix-loop" ]; then
    if [ ! -f "$WORKFLOW_STATE_FILE" ]; then init_workflow_state "null"; fi
    update_workflow_state '.fixLoopInvestigating = true'
    log_event "FIXLOOP_UNBLOCK" "action=set_investigating_true"
    echo ""
    echo "FIX-LOOP: Write/Edit to code files is now UNBLOCKED for fix-loop investigation."
    echo ""
fi

exit 0
