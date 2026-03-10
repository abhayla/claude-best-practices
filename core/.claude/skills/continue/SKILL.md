---
name: continue
description: >
  Resume work from a previous session. Use when starting a new conversation,
  returning after a break, or when the user says "continue", "pick up where I left off",
  or "what was I working on". Reads continuation state, workflow progress, git state,
  and recent test evidence to produce a briefing with suggested next action.
allowed-tools: "Bash Read Grep Glob"
disable-model-invocation: true
---

# Continue — Session Resume Briefing

Read project state and produce a briefing with suggested next action.

**Request:** $ARGUMENTS

---

## STEP 1: Read Continuation State

Read `docs/CONTINUE_PROMPT.md` and extract:
- **Current State** line (top-level status summary)
- **Test Results** table (backend, Android unit, UI, E2E counts and status)
- **Implementation Status** table (latest items with status)
- **Last Updated** date

Present the current state summary and any items marked as in-progress or recently completed.

---

## STEP 2: Parse Workflow State

```bash
if [ -f .claude/workflow-state.json ]; then
  python -c "
import json
with open('.claude/workflow-state.json') as f:
    d = json.load(f)
cmd = d.get('activeCommand')
issue = d.get('issueNumber')
req = d.get('requirementId')
steps = d.get('steps', {})
completed = sorted([k for k, v in steps.items() if v.get('completed')])
pending = sorted([k for k, v in steps.items() if not v.get('completed')])
skills = d.get('skillInvocations', {})
blocked = d.get('blocked', False)
reason = d.get('blockedReason')

print('WORKFLOW STATE:')
if cmd:
    print(f'  Active command: {cmd}')
if issue:
    print(f'  Issue: #{issue}')
if req:
    print(f'  Requirement: {req}')
print(f'  Completed steps: {len(completed)}/7')
for s in completed:
    print(f'    + {s}')
if pending:
    print(f'  Pending steps:')
    for s in pending:
        print(f'    - {s}')
if skills.get('fixLoopInvoked'):
    print(f'  Fix-loop: invoked {skills.get(\"fixLoopCount\", 0)}x')
if skills.get('postFixPipelineInvoked'):
    print(f'  Post-fix pipeline: invoked')
if blocked:
    print(f'  BLOCKED: {reason}')
"
else
  echo "WORKFLOW STATE: No active workflow (fresh session)"
fi
```

---

## STEP 3: Git State

```bash
echo "GIT STATE:" && \
echo -n "  Branch: " && git branch --show-current && \
echo "  Last 5 commits:" && git log --oneline -5 | sed 's/^/    /' && \
CHANGED=$(git status --short | wc -l | tr -d ' ') && \
echo "  Uncommitted changes: $CHANGED files" && \
if [ "$CHANGED" -gt 0 ]; then
  echo "  Modified:" && git status --short | head -10 | sed 's/^/    /'
  if [ "$CHANGED" -gt 10 ]; then
    echo "    ... and $((CHANGED - 10)) more"
  fi
fi
```

---

## STEP 4: Recent Test Evidence

```bash
echo "RECENT TEST EVIDENCE:" && \
if ls .claude/logs/test-evidence/run-*.json 1>/dev/null 2>&1; then
  ls -t .claude/logs/test-evidence/run-*.json | head -3 | while read f; do
    python -c "
import json, os
with open('$f') as fh:
    d = json.load(fh)
ts = d.get('timestamp', 'unknown')
cmd = d.get('command', 'unknown')
result = d.get('claimedResult', 'unknown')
target = d.get('target', 'unknown')
print(f'  [{ts}] {target} -> {result}')
" 2>/dev/null
  done
else
  echo "  No recent test evidence files"
fi
```

---

## STEP 5: Suggested Next Action

Based on the gathered state, determine the most useful next action:

**Decision logic (in priority order):**

1. **Workflow blocked** -> "Unblock: {blockedReason}"
2. **Incomplete workflow with issue** -> "Continue step N (next pending) for issue #{issueNumber}"
3. **Test failures pending** (last evidence shows fail) -> "Fix failing tests. Consider `/fix-loop`"
4. **Uncommitted changes** -> "Review changes with `git diff` and commit, or continue working"
5. **Active command but no pending steps** -> "Workflow complete for #{issue}. Run `/post-fix-pipeline` or commit."
6. **All clear** -> "Ready for new work. Use `/fix-issue <N>` or `/implement <description>`"

**Output Format:**
```
============================================
  Session Resume Briefing
============================================

CURRENT STATE
  [from CONTINUE_PROMPT.md]

WORKFLOW
  [from workflow-state.json]

GIT
  Branch: [branch]
  Uncommitted: [N] files
  Last commit: [hash] [message]

RECENT TESTS
  [last 3 test evidence entries]

SUGGESTED NEXT ACTION
  -> [action based on priority logic above]
============================================
```
