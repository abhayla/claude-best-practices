---
name: status
description: >
  Quick project health snapshot. Use when starting a session, after returning from
  a break, or when unsure about project state. Shows git status, test counts,
  workflow progress, and backend health in a single report.
allowed-tools: "Bash Read Grep Glob"
disable-model-invocation: true
---

# Project Status Dashboard

Quick health check across git, tests, workflow state, and backend.

**Request:** $ARGUMENTS

---

## STEP 1: Git State

```bash
echo "=== GIT ===" && \
git branch --show-current && \
echo "---" && \
git log --oneline -3 && \
echo "---" && \
echo "Changed files:" && \
git status --short | wc -l | tr -d ' '
```

---

## STEP 2: Test Counts

```bash
echo "=== TESTS ===" && \
echo -n "Backend test files: " && find backend/tests -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ' && \
echo -n "Backend tests (collected): " && (cd backend && PYTHONPATH=. python -m pytest --collect-only -q 2>/dev/null | tail -1) && \
echo -n "Android unit test files: " && find android/app/src/test -name "*Test.kt" 2>/dev/null | wc -l | tr -d ' ' && \
echo -n "Android UI test files: " && find android/app/src/androidTest -name "*Test.kt" 2>/dev/null | wc -l | tr -d ' ' && \
echo -n "Android E2E flow files: " && find android/app/src/androidTest -path "*/e2e/flows/*Test.kt" 2>/dev/null | wc -l | tr -d ' '
```

---

## STEP 3: Workflow State

```bash
echo "=== WORKFLOW ===" && \
if [ -f .claude/workflow-state.json ]; then
  python -c "
import json
with open('.claude/workflow-state.json') as f:
    d = json.load(f)
cmd = d.get('activeCommand', 'none')
issue = d.get('issueNumber', 'none')
steps = d.get('steps', {})
completed = [k for k, v in steps.items() if v.get('completed')]
pending = [k for k, v in steps.items() if not v.get('completed')]
skills = d.get('skillInvocations', {})
print(f'  Active command: {cmd}')
print(f'  Issue: #{issue}' if issue else '  Issue: none')
print(f'  Completed: {len(completed)}/7 steps')
if pending:
    print(f'  Next pending: {pending[0]}')
if skills.get('fixLoopInvoked'):
    print(f'  Fix-loop invoked: {skills.get(\"fixLoopCount\", 0)}x')
if d.get('blocked'):
    print(f'  BLOCKED: {d.get(\"blockedReason\", \"unknown\")}')
"
else
  echo "  No workflow state (fresh session)"
fi
```

---

## STEP 4: Backend Health

```bash
echo "=== BACKEND ===" && \
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "  Status: RUNNING" && \
  curl -sf http://localhost:8000/health 2>/dev/null | python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f'  Response: {json.dumps(d)}')
except:
    print('  Response: OK (non-JSON)')
" 2>/dev/null
else
  echo "  Status: NOT RUNNING"
fi
```

---

## STEP 5: Present Report

Combine all output into a single formatted block:

```
============================================
  RasoiAI Project Status
============================================

GIT
  Branch: main
  Recent: [last 3 commits]
  Changed files: N

TESTS
  Backend: ~580 (46 files)
  Android Unit: ~580 (N files)
  Android UI/E2E: N files

WORKFLOW
  Active: none | fix-issue | implement | run-e2e
  Issue: #N | none
  Progress: N/7 steps

BACKEND
  Status: RUNNING | NOT RUNNING
============================================
```
