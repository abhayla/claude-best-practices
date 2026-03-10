#!/bin/bash
# =============================================================================
# Claude Code Workflow Validation Hook (PreToolUse)
# =============================================================================
# Reads JSON from stdin. Exit 0 = allow, Exit 2 = block with message.
# =============================================================================

trap 'exit 0' ERR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook-utils.sh" 2>/dev/null || exit 0
parse_hook_input || exit 0

if [ -z "$HOOK_TOOL_NAME" ]; then exit 0; fi

get_step_status() {
    local step_name="$1"
    if [ -f "$WORKFLOW_STATE_FILE" ]; then
        if command -v jq &>/dev/null; then
            jq -r ".steps.${step_name}.completed" "$WORKFLOW_STATE_FILE" 2>/dev/null || echo "false"
        else
            python -c "
import json
with open('$WORKFLOW_STATE_FILE') as f:
    d = json.load(f)
v = d.get('steps',{}).get('$step_name',{}).get('completed', False)
print(str(v).lower())
" 2>/dev/null || echo "false"
        fi
    else
        echo "false"
    fi
}

check_all_steps_complete() {
    local steps=("step1_requirements" "step2_tests" "step3_implement" "step4_runTests" "step5_fixLoop" "step6_screenshots" "step7_verify")
    for step in "${steps[@]}"; do
        local status; status=$(get_step_status "$step")
        if [ "$status" != "true" ]; then echo "$step"; return 1; fi
    done
    echo "all"; return 0
}

is_test_file() { printf '%s' "$1" | grep -qE "(androidTest|test_|Test\.kt|_test\.py)"; }
is_code_file() { printf '%s' "$1" | grep -qE "\.(kt|py|java|xml)$" && ! is_test_file "$1"; }
is_requirement_file() { printf '%s' "$1" | grep -qE "(docs/requirements|Functional-Requirement)"; }

# Graceful init: if no state file, create it and allow
if [ ! -f "$WORKFLOW_STATE_FILE" ]; then
    init_workflow_state "null"
    exit 0
fi

# =============================================================================
# Test Failure Pending Gate (independent of activeCommand)
# Blocks code edits and commits when test failures are pending and fix-loop
# has NOT been invoked. This fires for ALL test runs, including ad-hoc.
# =============================================================================
TFP=$(get_state_field ".testFailuresPending")
FLI=$(get_state_field ".fixLoopInvestigating")

if [ "$TFP" = "true" -o "$TFP" = "True" ] && [ "$FLI" != "true" ] && [ "$FLI" != "True" ]; then
    case "$HOOK_TOOL_NAME" in
        "Write"|"Edit")
            TFP_FILE=$(extract_input_field "file_path")
            if [ -n "$TFP_FILE" ]; then
                # Normalize Windows backslashes to forward slashes
                TFP_FILE_NORM=$(printf '%s' "$TFP_FILE" | sed 's|\\|/|g')
                # Allow: .claude/, docs/, .github/, CLAUDE.md, any .md file
                if printf '%s' "$TFP_FILE_NORM" | grep -qE "(\.claude/|docs/|\.github/|CLAUDE\.md|\.md$)"; then
                    : # Allowed — documentation and config files
                else
                    # Block: all code files (.kt, .py, .java, .xml, etc.)
                    if printf '%s' "$TFP_FILE_NORM" | grep -qE "\.(kt|py|java|xml|kts|gradle|json|yaml|yml|toml|properties)$"; then
                        TFP_DETAILS=$(get_state_field ".testFailurePendingDetails")
                        echo ""
                        echo "BLOCKED: Test failures are pending. Write/Edit to code files is blocked."
                        echo ">>> You MUST invoke Skill(\"fix-loop\") to investigate ALL test failures. <<<"
                        echo ">>> No exceptions for 'pre-existing' or 'unrelated' failures. <<<"
                        echo "Failure details: $TFP_DETAILS"
                        echo ""
                        log_event "BLOCKED" "reason=testFailuresPending" "file=$TFP_FILE"
                        exit 2
                    fi
                fi
            fi
            ;;
        "Bash")
            TFP_CMD=$(extract_input_field "command")
            if printf '%s' "$TFP_CMD" | grep -qE "git commit"; then
                echo ""
                echo "BLOCKED: Test failures are pending. Commits are blocked."
                echo ">>> You MUST invoke Skill(\"fix-loop\") to investigate ALL test failures. <<<"
                echo ">>> No exceptions for 'pre-existing' or 'unrelated' failures. <<<"
                echo ""
                log_event "BLOCKED" "reason=testFailuresPending_commit"
                exit 2
            fi
            ;;
    esac
fi

# =============================================================================
# Visual Issues Pending Gate (independent of activeCommand)
# Mirrors the Test Failure Pending Gate for screenshot validation issues.
# =============================================================================
VIP=$(get_state_field ".visualIssuesPending")

if [ "$VIP" = "true" -o "$VIP" = "True" ] && [ "$FLI" != "true" ] && [ "$FLI" != "True" ]; then
    case "$HOOK_TOOL_NAME" in
        "Write"|"Edit")
            VIP_FILE=$(extract_input_field "file_path")
            if [ -n "$VIP_FILE" ]; then
                # Normalize Windows backslashes to forward slashes
                VIP_FILE_NORM=$(printf '%s' "$VIP_FILE" | sed 's|\\|/|g')
                # Allow: .claude/, docs/, .github/, CLAUDE.md, any .md file
                if printf '%s' "$VIP_FILE_NORM" | grep -qE "(\.claude/|docs/|\.github/|CLAUDE\.md|\.md$)"; then
                    : # Allowed — documentation and config files
                else
                    # Block: all code files (.kt, .py, .java, .xml, etc.)
                    if printf '%s' "$VIP_FILE_NORM" | grep -qE "\.(kt|py|java|xml|kts|gradle|json|yaml|yml|toml|properties)$"; then
                        VIP_DETAILS=$(get_state_field ".visualIssuePendingDetails")
                        echo ""
                        echo "BLOCKED: Visual issues are pending. Write/Edit to code files is blocked."
                        echo ">>> You MUST invoke Skill(\"fix-loop\") to fix visual issues. <<<"
                        echo "Details: $VIP_DETAILS"
                        echo ""
                        log_event "BLOCKED" "reason=visualIssuesPending" "file=$VIP_FILE"
                        exit 2
                    fi
                fi
            fi
            ;;
        "Bash")
            VIP_CMD=$(extract_input_field "command")
            if printf '%s' "$VIP_CMD" | grep -qE "git commit"; then
                echo ""
                echo "BLOCKED: Visual issues are pending. Commits are blocked."
                echo ">>> You MUST invoke Skill(\"fix-loop\") to fix visual issues. <<<"
                echo ""
                log_event "BLOCKED" "reason=visualIssuesPending_commit"
                exit 2
            fi
            ;;
    esac
fi

case "$HOOK_TOOL_NAME" in
    "Write"|"Edit")
        FILE_PATH=$(extract_input_field "file_path")
        if [ -z "$FILE_PATH" ]; then exit 0; fi
        # Normalize Windows backslashes to forward slashes for pattern matching
        FILE_PATH_NORM=$(printf '%s' "$FILE_PATH" | sed 's|\\|/|g')
        if is_requirement_file "$FILE_PATH_NORM"; then log_event "STEP_1_PROGRESS" "file=$FILE_PATH"; exit 0; fi
        if printf '%s' "$FILE_PATH_NORM" | grep -qE "(\.claude/|\.github/|docs/rules|docs/design|CLAUDE\.md)"; then exit 0; fi
        if is_test_file "$FILE_PATH_NORM"; then
            if [ "$(get_step_status step1_requirements)" != "true" ]; then
                echo ""; echo "WORKFLOW BLOCKED: Cannot create tests before Step 1 (requirements)."
                echo "Run: gh issue list --search \"keyword\""; echo ""
                log_event "BLOCKED" "reason=step2_before_step1" "file=$FILE_PATH"; exit 2
            fi
            exit 0
        fi
        if is_code_file "$FILE_PATH_NORM"; then
            if [ "$(get_step_status step2_tests)" != "true" ]; then
                echo ""; echo "WORKFLOW BLOCKED: Cannot implement code before Step 2 (tests)."
                echo "Create test file first."; echo ""
                log_event "BLOCKED" "reason=step3_before_step2" "file=$FILE_PATH"; exit 2
            fi
            exit 0
        fi
        exit 0
        ;;
    "Bash")
        CMD=$(extract_input_field "command")
        # Detect bash file-modification commands targeting code files
        if printf '%s' "$CMD" | grep -qE "(sed -i|awk.*>|echo.*>|cat.*>|tee |printf.*>|cp .*(\.kt|\.py|\.java|\.xml)|mv .*(\.kt|\.py|\.java|\.xml))"; then
            # Extract target file from common patterns
            BASH_TARGET=$(printf '%s' "$CMD" | grep -oE "[^ \"'>|]+\.(kt|py|java|xml)" | tail -1)
            if [ -n "$BASH_TARGET" ]; then
                # Exclude non-production paths
                if ! printf '%s' "$BASH_TARGET" | grep -qE "(\.claude/|docs/|test_|Test\.kt|androidTest|_test\.py)"; then
                    if is_code_file "$BASH_TARGET"; then
                        if [ "$(get_step_status step2_tests)" != "true" ]; then
                            echo ""; echo "WORKFLOW BLOCKED: Bash command modifies code file before Step 2 (tests)."
                            echo "File: $BASH_TARGET — Create test file first."; echo ""
                            log_event "BLOCKED" "reason=bash_modify_before_step2" "file=$BASH_TARGET"; exit 2
                        fi
                    fi
                fi
            fi
        fi
        if printf '%s' "$CMD" | grep -qE "git commit"; then
            INCOMPLETE=$(check_all_steps_complete)
            if [ "$INCOMPLETE" != "all" ]; then
                echo ""; echo "WORKFLOW BLOCKED: Cannot commit. Incomplete step: $INCOMPLETE"
                echo "Complete all 7 steps. See: .claude/rules/workflow.md"; echo ""
                log_event "BLOCKED" "reason=commit_incomplete" "missing=$INCOMPLETE"; exit 2
            fi
            ACTIVE_CMD=$(get_state_field ".activeCommand")
            if [ -n "$ACTIVE_CMD" ] && [ "$ACTIVE_CMD" != "null" ] && [ "$ACTIVE_CMD" != "None" ]; then
                TC=$(python -c "import json;print(len(json.load(open('$WORKFLOW_STATE_FILE')).get('evidence',{}).get('testRuns',[])))" 2>/dev/null)
                if [ "${TC:-0}" -gt 0 ]; then
                    PI=$(get_state_field ".skillInvocations.postFixPipelineInvoked")
                    if [ "$PI" != "true" ] && [ "$PI" != "True" ]; then
                        echo ""; echo "COMMIT BLOCKED: /post-fix-pipeline was not invoked."
                        echo "Use Skill tool to invoke /post-fix-pipeline first."; echo ""
                        log_event "BLOCKED" "reason=pipeline_not_invoked"; exit 2
                    fi
                fi
            fi
            log_event "COMMIT_ALLOWED"; exit 0
        fi
        ;;
esac

exit 0
