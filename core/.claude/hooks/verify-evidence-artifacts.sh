#!/bin/bash
# =============================================================================
# Claude Code Evidence Artifacts Verification Hook (PreToolUse)
# =============================================================================
# Blocks git commit when required evidence is missing.
# Exit 0 = allow, Exit 2 = BLOCK (missing evidence).
# No active workflow (null) = always allow.
# =============================================================================

trap 'exit 0' ERR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook-utils.sh" 2>/dev/null || exit 0
parse_hook_input || exit 0

if [ "$HOOK_TOOL_NAME" != "Bash" ]; then exit 0; fi

CMD=$(extract_input_field "command")
if ! printf '%s' "$CMD" | grep -qE "git commit"; then exit 0; fi
if [ ! -f "$WORKFLOW_STATE_FILE" ]; then exit 0; fi

ACTIVE_CMD=$(get_state_field ".activeCommand")
if [ -z "$ACTIVE_CMD" ] || [ "$ACTIVE_CMD" = "null" ] || [ "$ACTIVE_CMD" = "None" ]; then exit 0; fi

MISSING=""

case "$ACTIVE_CMD" in
    "fix-issue"|"implement")
        TC=$(python -c "import json;print(len(json.load(open('$WORKFLOW_STATE_FILE')).get('evidence',{}).get('testRuns',[])))" 2>/dev/null)
        if [ "${TC:-0}" -gt 0 ]; then
            HF=$(python -c "import json;r=json.load(open('$WORKFLOW_STATE_FILE')).get('evidence',{}).get('testRuns',[]);print('true' if any(x.get('claimedResult')=='fail' for x in r) else 'false')" 2>/dev/null)
            if [ "$HF" = "true" ]; then
                FLI=$(get_state_field ".skillInvocations.fixLoopInvoked")
                if [ "$FLI" != "true" ] && [ "$FLI" != "True" ]; then
                    MISSING="$MISSING  - /fix-loop not invoked (test failures detected)\n"
                fi
                # Check fix-loop succeeded (budget exhaustion blocking)
                FLS=$(get_state_field ".skillInvocations.fixLoopSucceeded")
                if [ "$FLS" = "false" ] || [ "$FLS" = "False" ]; then
                    # Also check latest summary-evidence for confirmation
                    LATEST_SUMMARY=$(ls -t .claude/logs/fix-loop/*/summary-evidence.json 2>/dev/null | head -1)
                    if [ -n "$LATEST_SUMMARY" ]; then
                        OVERALL=$(python -c "import json;print(json.load(open('$LATEST_SUMMARY')).get('overallStatus',''))" 2>/dev/null)
                        if [ "$OVERALL" = "UNRESOLVED" ] || [ "$OVERALL" = "MAX_ITERATIONS_EXCEEDED" ]; then
                            MISSING="$MISSING  - /fix-loop ended with $OVERALL (tests still failing)\n"
                        fi
                    else
                        MISSING="$MISSING  - /fix-loop did not succeed (fixLoopSucceeded=false)\n"
                    fi
                fi
            fi
            PI=$(get_state_field ".skillInvocations.postFixPipelineInvoked")
            if [ "$PI" != "true" ] && [ "$PI" != "True" ]; then
                MISSING="$MISSING  - /post-fix-pipeline not invoked\n"
            fi
        fi
        ;;
    "adb-test")
        FLC=$(get_state_field ".skillInvocations.fixLoopCount"); FLC=${FLC:-0}
        if [ "$FLC" -gt 0 ]; then
            PI=$(get_state_field ".skillInvocations.postFixPipelineInvoked")
            if [ "$PI" != "true" ] && [ "$PI" != "True" ]; then
                MISSING="$MISSING  - /post-fix-pipeline not invoked (fixes applied)\n"
            fi
        fi
        # ADB tests don't populate testRuns[] — check for flow reports or screen gate files instead
        HAS_EVIDENCE="false"
        if ls docs/testing/reports/flow*.md 1>/dev/null 2>&1; then
            HAS_EVIDENCE="true"
        fi
        if ls docs/testing/reports/screen-*-gate.json 1>/dev/null 2>&1; then
            HAS_EVIDENCE="true"
        fi
        if [ "$HAS_EVIDENCE" = "false" ]; then
            MISSING="$MISSING  - No ADB test evidence found (no flow reports or screen gate files)\n"
        fi
        ;;
    "run-e2e")
        FLC=$(get_state_field ".skillInvocations.fixLoopCount"); FLC=${FLC:-0}
        if [ "$FLC" -gt 0 ]; then
            PI=$(get_state_field ".skillInvocations.postFixPipelineInvoked")
            if [ "$PI" != "true" ] && [ "$PI" != "True" ]; then
                MISSING="$MISSING  - /post-fix-pipeline not invoked (fixes applied)\n"
            fi
        fi
        TC=$(python -c "import json;print(len(json.load(open('$WORKFLOW_STATE_FILE')).get('evidence',{}).get('testRuns',[])))" 2>/dev/null)
        if [ "${TC:-0}" -eq 0 ]; then
            MISSING="$MISSING  - No test runs recorded\n"
        fi
        ;;
esac

# =============================================================================
# Screenshot verification gate (applies to ALL active commands)
# If screenshots were captured during this session, /verify-screenshots must
# have been invoked before committing — regardless of workflow type.
# =============================================================================
SC_COUNT=$(python -c "import json;print(len(json.load(open('$WORKFLOW_STATE_FILE')).get('screenshotsCaptured',[])))" 2>/dev/null)
if [ "${SC_COUNT:-0}" -gt 0 ]; then
    VSI=$(get_state_field ".skillInvocations.verifyScreenshotsInvoked")
    if [ "$VSI" != "true" ] && [ "$VSI" != "True" ]; then
        MISSING="$MISSING  - /verify-screenshots not invoked (${SC_COUNT} screenshots captured but not validated)\n"
    fi
fi

if [ -n "$MISSING" ]; then
    echo ""; echo "COMMIT BLOCKED - Missing evidence for $ACTIVE_CMD workflow:"
    echo -e "$MISSING"
    echo "Use Skill tool to invoke missing Skills, then retry."; echo ""
    log_event "COMMIT_BLOCKED_EVIDENCE" "command=$ACTIVE_CMD"
    exit 2
fi

exit 0
