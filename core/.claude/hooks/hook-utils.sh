#!/bin/bash
# =============================================================================
# Claude Code Hook Utilities - Shared Library
# =============================================================================
# Sourced (not executed) by all workflow hooks.
# All functions fail open (return 0 / allow on error).
# =============================================================================

WORKFLOW_STATE_FILE=".claude/workflow-state.json"
WORKFLOW_LOG_FILE=".claude/logs/workflow-sessions.log"
EVIDENCE_DIR=".claude/logs/test-evidence"

HOOK_TOOL_NAME=""
HOOK_TOOL_INPUT=""
HOOK_TOOL_OUTPUT=""
HOOK_RAW_INPUT=""

parse_hook_input() {
    HOOK_RAW_INPUT=$(cat)
    if [ -z "$HOOK_RAW_INPUT" ]; then return 0; fi

    # Write raw input to temp file (safe for any content — no echo/printf mangling)
    local tmpfile
    tmpfile=$(mktemp 2>/dev/null || echo ".claude/.tmp_hook_input_$$.json")
    printf '%s' "$HOOK_RAW_INPUT" > "$tmpfile"

    # Parse JSON via Python, write results to separate files (NOT eval — eval breaks
    # when tool_input contains bash code with single quotes, because Python repr()
    # switches to double-quote strings which bash interprets as code)
    python -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    with open(sys.argv[1] + '.name', 'w') as f:
        f.write(d.get('tool_name', ''))
    with open(sys.argv[1] + '.input', 'w') as f:
        f.write(json.dumps(d.get('tool_input', {})))
except Exception:
    pass
" "$tmpfile" 2>/dev/null

    HOOK_TOOL_NAME=$(cat "${tmpfile}.name" 2>/dev/null) || HOOK_TOOL_NAME=""
    HOOK_TOOL_INPUT=$(cat "${tmpfile}.input" 2>/dev/null) || HOOK_TOOL_INPUT="{}"

    # tool_output is too large for file passing — hooks that need it read HOOK_RAW_INPUT directly
    HOOK_TOOL_OUTPUT=""
    rm -f "$tmpfile" "${tmpfile}.name" "${tmpfile}.input" 2>/dev/null
}

extract_input_field() {
    local field="$1"
    printf '%s' "$HOOK_TOOL_INPUT" | python -c "import sys,json;print(str(json.load(sys.stdin).get('$field','')))" 2>/dev/null
}

get_state_field() {
    local field_path="$1"
    if [ ! -f "$WORKFLOW_STATE_FILE" ]; then echo ""; return 1; fi
    if command -v jq &>/dev/null; then
        jq -r "$field_path // empty" "$WORKFLOW_STATE_FILE" 2>/dev/null
    else
        python -c "
import json
with open('$WORKFLOW_STATE_FILE') as f:
    d = json.load(f)
parts = '$field_path'.lstrip('.').split('.')
v = d
for p in parts:
    v = v.get(p) if isinstance(v, dict) else None
    if v is None: break
if v is not None: print(v)
" 2>/dev/null
    fi
}

update_workflow_state() {
    local jq_expr="$1"
    if [ ! -f "$WORKFLOW_STATE_FILE" ]; then return 1; fi
    if command -v jq &>/dev/null; then
        local tf; tf=$(mktemp 2>/dev/null || echo ".claude/.tmp_ws_$$.json")
        jq "$jq_expr" "$WORKFLOW_STATE_FILE" > "$tf" 2>/dev/null && mv "$tf" "$WORKFLOW_STATE_FILE" || rm -f "$tf" 2>/dev/null
    else
        python -c "
import json, os, tempfile
with open('$WORKFLOW_STATE_FILE') as f:
    d = json.load(f)
expr = r'''$jq_expr'''
if '=' in expr:
    pp, vp = expr.split('=', 1)
    pp = pp.strip().lstrip('.')
    vp = vp.strip()
    if vp=='true': val=True
    elif vp=='false': val=False
    elif vp=='null': val=None
    elif vp.startswith('\"') and vp.endswith('\"'): val=vp[1:-1]
    else:
        try: val=int(vp)
        except:
            try: val=float(vp)
            except: val=vp
    parts = pp.split('.')
    obj = d
    for p in parts[:-1]:
        if p not in obj or not isinstance(obj[p], dict): obj[p] = {}
        obj = obj[p]
    obj[parts[-1]] = val
fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, '$WORKFLOW_STATE_FILE')
" 2>/dev/null
    fi
}

init_workflow_state() {
    local command_name="${1:-null}"
    local session_id
    session_id=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo "session-$$")
    mkdir -p .claude/logs .claude/logs/test-evidence .claude/logs/fix-loop .claude/logs/post-fix-pipeline 2>/dev/null
    python -c "
import json, os
cn = '$command_name'
state = {
    'sessionId': '$session_id',
    'issueNumber': None, 'requirementId': None,
    'activeCommand': cn if cn != 'null' else None,
    'steps': {
        'step1_requirements': {'completed': False, 'timestamp': None, 'artifacts': []},
        'step2_tests': {'completed': False, 'timestamp': None, 'testFile': None},
        'step3_implement': {'completed': False, 'timestamp': None, 'filesChanged': []},
        'step4_runTests': {'completed': False, 'timestamp': None, 'testsPassed': None, 'testsTotal': None},
        'step5_fixLoop': {'completed': False, 'iterations': 0, 'allTestsPassing': False},
        'step6_screenshots': {'completed': False, 'before': None, 'after': None,
                              'validated': False, 'validationResult': None},
        'step7_verify': {'completed': False, 'verification': None,
                         'backendChecksResult': None}
    },
    'testFailuresPending': False,
    'testFailurePendingDetails': None,
    'fixLoopInvestigating': False,
    'blocked': False, 'blockedReason': None,
    'skillInvocations': {
        'fixLoopInvoked': False, 'fixLoopCount': 0,
        'fixLoopEvidence': [], 'postFixPipelineInvoked': False,
        'postFixPipelineEvidence': None,
        'verifyScreenshotsInvoked': False,
        'verifyScreenshotsResult': None
    },
    'evidence': {'testRuns': [], 'screenshots': [], 'fixLoopLogs': []},
    'agentDelegations': [],
    'visualIssuesPending': False,
    'visualIssuePendingDetails': None,
    'screenshotsCaptured': [],
    'backendChecks': []
}
os.makedirs('.claude', exist_ok=True)
with open('.claude/workflow-state.json', 'w') as f:
    json.dump(state, f, indent=2)
" 2>/dev/null
    log_event "SESSION_START" "id=$session_id" "command=$command_name"
}

is_test_command() {
    local cmd="$1"
    printf '%s' "$cmd" | grep -qiE "(pytest|gradlew.*(test|Test)|connectedDebugAndroidTest)"
}

extract_test_target() {
    local cmd="$1"
    if printf '%s' "$cmd" | grep -qiE "pytest"; then
        printf '%s' "$cmd" | grep -oE "tests/[^ ]*\.py" | head -1
        return 0
    fi
    if printf '%s' "$cmd" | grep -qiE "gradlew"; then
        local t; t=$(printf '%s' "$cmd" | grep -oE "class=[^ ]*" | sed 's/class=//')
        if [ -n "$t" ]; then echo "$t"; return 0; fi
        t=$(printf '%s' "$cmd" | grep -oE "\-\-tests[= ]+\"?[^ \"]*" | sed 's/--tests[= ]*//' | tr -d '"')
        if [ -n "$t" ]; then echo "$t"; return 0; fi
    fi
    echo ""
}

is_screenshot_command() {
    local cmd="$1"
    printf '%s' "$cmd" | grep -qiE "(screencap|screenshot)"
}

extract_screenshot_path() {
    local cmd="$1"
    printf '%s' "$cmd" | grep -oE '>\s*[^ ]+\.png' | sed 's/^>\s*//'
}

get_tool_output() {
    # Safely extract tool_output from HOOK_RAW_INPUT (truncated to 50000 chars).
    # Uses temp file to avoid echo/printf issues with large/special-char content.
    if [ -z "$HOOK_RAW_INPUT" ]; then echo ""; return; fi
    local tmpfile
    tmpfile=$(mktemp 2>/dev/null || echo ".claude/.tmp_hook_output_$$.json")
    printf '%s' "$HOOK_RAW_INPUT" > "$tmpfile"
    python -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    o = d.get('tool_output', '')
    if isinstance(o, dict):
        print(json.dumps(o)[:50000])
    else:
        print(str(o)[:50000])
except Exception:
    print('')
" "$tmpfile" 2>/dev/null
    rm -f "$tmpfile" 2>/dev/null
}

detect_test_result() {
    local output="$1"
    # If output is empty, try extracting from raw hook input
    if [ -z "$output" ]; then
        output=$(get_tool_output)
    fi
    if [ -z "$output" ]; then echo "unknown"; return; fi
    if printf '%s' "$output" | grep -qE "passed.*failed|failed.*passed"; then echo "fail"; return; fi
    if printf '%s' "$output" | grep -qE "[0-9]+ passed" && ! printf '%s' "$output" | grep -qE "[0-9]+ failed|[0-9]+ error"; then echo "pass"; return; fi
    if printf '%s' "$output" | grep -qE "[0-9]+ failed|[0-9]+ error|FAILED|FAILURES"; then echo "fail"; return; fi
    if printf '%s' "$output" | grep -qE "BUILD SUCCESSFUL"; then echo "pass"; return; fi
    if printf '%s' "$output" | grep -qE "BUILD FAILED|Tests? failed"; then echo "fail"; return; fi
    echo "unknown"
}

write_evidence() {
    local dir="$1"; local filename="$2"; local json_content="$3"
    mkdir -p "$dir" 2>/dev/null
    echo "$json_content" > "$dir/$filename" 2>/dev/null
    echo "$dir/$filename"
}

log_event() {
    local event_type="${1:-INFO}"; shift
    mkdir -p .claude/logs 2>/dev/null
    local ts; ts=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
    local entry="[$ts] $event_type"
    for arg in "$@"; do entry="$entry | $arg"; done
    echo "$entry" >> "$WORKFLOW_LOG_FILE" 2>/dev/null
}

append_test_run_evidence() {
    local cmd="$1"; local target="$2"; local result="$3"
    local ts; ts=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
    if [ ! -f "$WORKFLOW_STATE_FILE" ]; then return 1; fi
    # Write command to temp file to avoid shell expansion issues in Python
    local cmd_tmp
    cmd_tmp=$(mktemp 2>/dev/null || echo ".claude/.tmp_hook_cmd_$$.txt")
    printf '%s' "$cmd" | head -c 200 > "$cmd_tmp"
    python -c "
import json, os, tempfile, sys
cmd_text = ''
try:
    with open(sys.argv[1]) as f:
        cmd_text = f.read()
except: pass
with open('$WORKFLOW_STATE_FILE') as f:
    d = json.load(f)
if 'evidence' not in d:
    d['evidence'] = {'testRuns': [], 'screenshots': [], 'fixLoopLogs': []}
d['evidence']['testRuns'].append({
    'timestamp': '$ts', 'command': cmd_text,
    'target': '$target', 'claimedResult': '$result', 'independentVerification': None
})
fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, '$WORKFLOW_STATE_FILE')
" "$cmd_tmp" 2>/dev/null
    rm -f "$cmd_tmp" 2>/dev/null
}

detect_skill_success() {
    local output="$1"
    if printf '%s' "$output" | grep -qiE "UNRESOLVED|MAX_ITERATIONS_EXCEEDED|MAX_CASCADE_EXCEEDED"; then
        echo "false"; return
    fi
    if printf '%s' "$output" | grep -qiE "Traceback|stacktrace|FATAL|panic:"; then
        echo "false"; return
    fi
    if printf '%s' "$output" | grep -qiE "RESOLVED|COMPLETED|PASSED"; then
        echo "true"; return
    fi
    echo "unknown"
}

record_skill_invocation() {
    local skill_name="$1"
    local succeeded="${2:-unknown}"
    if [ ! -f "$WORKFLOW_STATE_FILE" ]; then return 1; fi
    python -c "
import json, os, tempfile
with open('$WORKFLOW_STATE_FILE') as f:
    d = json.load(f)
si = d.setdefault('skillInvocations', {
    'fixLoopInvoked': False, 'fixLoopCount': 0, 'fixLoopSucceeded': None,
    'fixLoopEvidence': [], 'postFixPipelineInvoked': False,
    'postFixPipelineEvidence': None
})
s = '$skill_name'
succ = '$succeeded'
if s == 'fix-loop':
    si['fixLoopInvoked'] = True
    si['fixLoopCount'] = si.get('fixLoopCount', 0) + 1
    if succ in ('true', 'false'):
        si['fixLoopSucceeded'] = (succ == 'true')
elif s == 'post-fix-pipeline':
    si['postFixPipelineInvoked'] = True
fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, '$WORKFLOW_STATE_FILE')
" 2>/dev/null
}

# =============================================================================
# Failure Index Utilities
# =============================================================================

FAILURE_INDEX=".claude/logs/learning/failure-index.json"

init_failure_index() {
    if [ ! -f "$FAILURE_INDEX" ]; then
        mkdir -p "$(dirname "$FAILURE_INDEX")" 2>/dev/null
        echo '{"version":1,"entries":[]}' > "$FAILURE_INDEX" 2>/dev/null
    fi
}

read_failure_entry() {
    # Read entry by (skill, issue_type) key. Returns JSON or empty.
    local skill="$1" issue_type="$2"
    init_failure_index
    python -c "
import json
with open('$FAILURE_INDEX') as f:
    d = json.load(f)
for e in d.get('entries', []):
    if e.get('skill') == '$skill' and e.get('issue_type') == '$issue_type':
        print(json.dumps(e))
        break
" 2>/dev/null
}

update_failure_index() {
    # Append an occurrence to an existing entry, or create new entry.
    # Args: $1=skill, $2=issue_type, $3=outcome, $4=component, $5=workaround, $6=auto_fix_eligible
    local skill="$1" issue_type="$2" outcome="$3" component="${4:-}" workaround="${5:-}" auto_fix_eligible="${6:-false}"
    init_failure_index
    python -c "
import json, os, tempfile
with open('$FAILURE_INDEX') as f:
    d = json.load(f)
ts = '$(date +%Y-%m-%d 2>/dev/null || echo "unknown")'
skill, itype = '$skill', '$issue_type'
entry = None
for e in d.get('entries', []):
    if e.get('skill') == skill and e.get('issue_type') == itype:
        entry = e
        break
if entry is None:
    entry = {'skill': skill, 'issue_type': itype, 'component': '$component',
             'first_seen': ts, 'occurrences': [], 'known_workaround': None,
             'prevention': None, 'threshold_reached': False, 'auto_escalation': None}
    d['entries'].append(entry)
entry['occurrences'].append({
    'date': ts, 'outcome': '$outcome', 'workaround_used': '$workaround' or None
})
if len(entry['occurrences']) >= 3:
    entry['threshold_reached'] = True
if '$workaround':
    entry['known_workaround'] = '$workaround'
if '$auto_fix_eligible' == 'true':
    entry['auto_fix_eligible'] = True
fd, tmp = tempfile.mkstemp(dir='.claude/logs/learning')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, '$FAILURE_INDEX')
" 2>/dev/null
}

check_known_limitations() {
    # Search failure index for matching (skill, issue_type) with a known workaround.
    # Returns workaround string or empty.
    local skill="$1" issue_type="$2"
    init_failure_index
    python -c "
import json
with open('$FAILURE_INDEX') as f:
    d = json.load(f)
for e in d.get('entries', []):
    if e.get('skill') == '$skill' and e.get('issue_type') == '$issue_type':
        w = e.get('known_workaround')
        if w:
            print(w)
        break
" 2>/dev/null
}

# =============================================================================
# Learning System Utilities (Phase 1)
# =============================================================================

LEARNING_LOG_DIR=".claude/logs/learning"
MEMORY_DIR=$(ls -d "$HOME"/.claude/projects/*VibeCoding-KKB/memory 2>/dev/null | head -1)
if [ -z "$MEMORY_DIR" ]; then MEMORY_DIR=""; fi

parse_skill_outcome() {
    # Extract structured outcome from Skill tool_output text.
    # Sets shell variables: SKILL_OUTCOME, SKILL_ISSUES_FOUND, SKILL_ISSUES_RESOLVED,
    # SKILL_FIXES (JSON array), SKILL_UNRESOLVED (JSON array)
    local output="$1"
    local tmpfile
    tmpfile=$(mktemp 2>/dev/null || echo ".claude/.tmp_skill_outcome_$$.json")

    # Write results to a JSON file (NOT eval — eval breaks on single quotes in content)
    python -c "
import re, json, sys

output = sys.stdin.read()

# Detect outcome
outcome = 'UNKNOWN'
if re.search(r'RESOLVED(?!.*UN)', output[:500]):
    outcome = 'RESOLVED'
elif re.search(r'UNRESOLVED|MAX_ITERATIONS_EXCEEDED|MAX_CASCADE_EXCEEDED', output):
    outcome = 'UNRESOLVED'
elif re.search(r'PARTIALLY_RESOLVED', output):
    outcome = 'PARTIALLY_RESOLVED'
elif re.search(r'PASS(?:ED)?.*(?:\d+/\d+|\ball\b)', output, re.I):
    outcome = 'PASSED'
elif re.search(r'FAIL|BLOCKED|ERROR', output, re.I):
    outcome = 'FAILED'

# Extract fix counts
found_m = re.search(r'Issues?\s*found:\s*(\d+)', output, re.I)
resolved_m = re.search(r'Issues?\s*resolved:\s*(\d+)', output, re.I)
issues_found = int(found_m.group(1)) if found_m else 0
issues_resolved = int(resolved_m.group(1)) if resolved_m else 0

# Extract fixes applied (file:line patterns)
fixes = []
for m in re.finditer(r'\[([^\]]+?):(\d+)\]\s*[-\u2014]\s*(.+)', output):
    fixes.append({'file': m.group(1), 'line': int(m.group(2)), 'description': m.group(3).strip()[:200]})

# Extract unresolved items
unresolved = []
in_unresolved = False
for line in output.split('\n'):
    if re.search(r'Unresolved\s*(Issues|Items)', line, re.I):
        in_unresolved = True
        continue
    if in_unresolved:
        if line.strip().startswith(('-', '*', '1', '2', '3', '4', '5')):
            item = re.sub(r'^[\s\-\*\d.]+', '', line).strip()
            if item:
                unresolved.append(item[:200])
        elif line.strip() == '' or line.startswith('#'):
            in_unresolved = False

result = {
    'outcome': outcome,
    'issues_found': issues_found,
    'issues_resolved': issues_resolved,
    'fixes': json.dumps(fixes),
    'unresolved': json.dumps(unresolved)
}
with open(sys.argv[1], 'w') as f:
    json.dump(result, f)
" "$tmpfile" <<< "$output" 2>/dev/null

    # Read results from file (safe — no eval)
    if [ -f "$tmpfile" ]; then
        SKILL_OUTCOME=$(python -c "import json;d=json.load(open('$tmpfile'));print(d.get('outcome','UNKNOWN'))" 2>/dev/null)
        SKILL_ISSUES_FOUND=$(python -c "import json;d=json.load(open('$tmpfile'));print(d.get('issues_found',0))" 2>/dev/null)
        SKILL_ISSUES_RESOLVED=$(python -c "import json;d=json.load(open('$tmpfile'));print(d.get('issues_resolved',0))" 2>/dev/null)
        SKILL_FIXES=$(python -c "import json;d=json.load(open('$tmpfile'));print(d.get('fixes','[]'))" 2>/dev/null)
        SKILL_UNRESOLVED=$(python -c "import json;d=json.load(open('$tmpfile'));print(d.get('unresolved','[]'))" 2>/dev/null)
    else
        SKILL_OUTCOME="UNKNOWN"
        SKILL_ISSUES_FOUND=0
        SKILL_ISSUES_RESOLVED=0
        SKILL_FIXES="[]"
        SKILL_UNRESOLVED="[]"
    fi
    rm -f "$tmpfile" 2>/dev/null
}

format_issue_body() {
    # Format a GitHub issue body for auto-filing from unresolved test items.
    # Args: $1=screen/context, $2=description, $3=session_id, $4=skill_name
    local context="$1" desc="$2" session_id="$3" skill_name="$4"
    cat <<ISSUE_EOF
## Auto-Filed Issue

**Source:** \`/$skill_name\` skill run
**Context:** $context
**Session:** $session_id
**Filed:** $(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")

## Description

$desc

## Reproduction

This issue was discovered during automated testing. Re-run \`/$skill_name\` targeting the affected area to reproduce.

## Evidence

- Session logs: \`.claude/logs/${skill_name}/${session_id}/\`
- Learning capture: \`.claude/logs/learning/\`

---
*Auto-filed by the learning system (post-skill-learning.sh)*
ISSUE_EOF
}

append_memory_topic() {
    # Append a timestamped entry to a memory topic file, keeping under 500 lines.
    # Args: $1=topic filename (e.g., "testing-lessons.md"), $2=entry text
    local topic_file="$1" entry="$2"
    local full_path="$MEMORY_DIR/$topic_file"
    if [ ! -f "$full_path" ]; then return 1; fi
    local ts
    ts=$(date +"%Y-%m-%d %H:%M" 2>/dev/null || date +"%Y-%m-%d")
    python -c "
import sys

topic_file = '$full_path'
timestamp = '$ts'
entry = '''$entry'''.strip()
if not entry:
    sys.exit(0)

with open(topic_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find insertion point (after the '<!-- Entries' comment line)
insert_idx = len(lines)
for i, line in enumerate(lines):
    if '<!-- Entries' in line:
        insert_idx = i + 1
        break

# Build new entry
new_entry = f'\n### {timestamp}\n{entry}\n'
lines.insert(insert_idx, new_entry)

# Trim to 500 lines (remove oldest entries from bottom)
if len(lines) > 500:
    lines = lines[:500]

with open(topic_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)
" 2>/dev/null
}
