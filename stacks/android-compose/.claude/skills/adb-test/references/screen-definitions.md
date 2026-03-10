# Screen Testing Protocol

Detailed protocol for testing individual screens via ADB. Referenced from the main `adb-test` SKILL.md.

---

## SCREEN TESTING PROTOCOL

### Test Definitions Reference

Read `docs/testing/adb-test-definitions.md` for per-screen test checklists (navigation path, primary identifier, required elements, interactive elements, data validation, known issues).

### Execution Order

1. `auth-flow` -> 2. `home` -> 3. `grocery` -> 4. `chat` -> 5. `favorites` -> 6. `stats` -> 7. `settings` -> 8. `notifications` -> 9. `recipe-detail` -> 10. `cooking-mode` -> 11. `pantry` -> 12. `recipe-rules`

### Per-Screen Protocol (8 Steps)

**E0. Pre-Screen Checks**

**E0a. Backend Health** (only for: `auth-flow`, `home`, `chat`, `recipe-detail`, `recipe-rules`):
```bash
curl -sf http://localhost:8000/health --max-time 5
```
If unhealthy: kill existing uvicorn, restart, poll 30s. If still down -> BLOCKED.
Track: `backend_health_checks += 1`, `backend_restarts += 1` if restarted.

**E0b. System Dialog Check:** Run Pattern 11 to detect/dismiss any permission/battery/system dialogs. Re-dump XML after dismissal.

**E1. Navigate to Screen**

Follow navigation path from `adb-test-definitions.md`. Use ADB taps. Wait 1-2s after each tap for animation.

**E2. Verify Arrival (with Crash Detection)**

**E2a. Crash/ANR Check:** Dump UI. Run Pattern 9. If crash detected:
1. Capture logcat (Pattern 13), screenshot, dismiss dialog
2. Relaunch app, re-navigate (repeat E1), re-dump XML
3. Log as CRITICAL issue

**E2b. Primary Identifier Check:** Search XML for screen's primary identifier. If not found after 3 dump attempts (2s gaps), classify as BLOCKED.

**E3. Element Checklist (Two-Phase Scroll Protocol)**

**Phase 1 — Initial Scan:** Parse UI dump, check each required element. Record: FOUND (with bounds) or PENDING_SCROLL (below fold) or MISSING (not below-fold and not found).

**Phase 2 — Scroll Search** (only if PENDING_SCROLL elements exist): Use Pattern 8 — max 3 scroll attempts. Re-check after each scroll. Scroll back to top when done.

**Final Status:** FOUND, FOUND_AFTER_SCROLL, or MISSING.

**ISSUE threshold:** >50% MISSING elements is an ISSUE.

**E4. Screenshot + AI Visual Analysis**

Capture: `$ADB exec-out screencap -p > docs/testing/screenshots/adb-test_{screen}_{timestamp}.png`

Validate with Pattern 12. If BLANK_SUSPECT: wake device, retry (max 2 retries). If still blank -> `visual_verified=false`.

If `visual_verified=true`: Read screenshot with Read tool, analyze layout, alignment, data, colors, empty states.

If `visual_verified=false`: Skip visual analysis, log warning. Screen CANNOT be PASS unless ALL elements verified via XML AND all interactions pass.

> **Screen mode vs Flow mode:** `/verify-screenshots` is NOT required per-screenshot in screen mode. Screen mode uses the Pre-Classification Gate (E5.7) for pass/fail determination. `/verify-screenshots` is only BLOCKING per-UI-step in flow mode (see flow-definitions.md G3).

**E5. Interactive Testing**

For each interactive element: find in XML -> compute center -> tap -> wait -> dump -> verify expected result -> screenshot if meaningful -> navigate back. Dismiss keyboard (Pattern 10) after text input.

**E5.5. Logcat Pre-Check**

Capture app-level logcat before classification:
```bash
$ADB logcat -d -t 50 --pid=$($ADB shell pidof $APP_PACKAGE) > $LOG_DIR/{session}/logcat_{screen}_precheck.txt
```
Scan for errors (` E `, `FATAL`, `Exception`). Record `app_error_count`.

**E5.6b. ANR Auto-Detection (MANDATORY)**

Before the Pre-Classification Gate, scan for ANR signals:
```bash
# Check logcat for ANR patterns
$ADB logcat -d -t 100 --pid=$($ADB shell pidof $APP_PACKAGE) 2>/dev/null | grep -iE "ANR in|isn't responding|Application Not Responding|Input dispatching timed out" > /tmp/anr_check.txt
ANR_LINES=$(wc -l < /tmp/anr_check.txt)
if [ "$ANR_LINES" -gt 0 ]; then
    echo "ANR DETECTED ($ANR_LINES occurrences) -> auto-classify as ISSUE_FOUND"
    cat /tmp/anr_check.txt
fi
```
If ANR detected:
- Auto-classify as `ISSUE_FOUND` (skip remaining gate questions)
- Capture full logcat: `$ADB logcat -d -t 500 > $LOG_DIR/{session}/logcat_{screen}_anr.txt`
- **MUST invoke `/fix-loop`** — ANR is always a code bug, never skip

**E5.7. Pre-Classification Gate (MANDATORY)**

Copy and fill in ALL 6 questions before classifying:
```
Pre-Classification Gate for [{screen_name}]:
  0. "ANR auto-detection clear?" -> [YES / NO — ISSUE_FOUND (must invoke /fix-loop)]
  1. "All required elements found (FOUND or FOUND_AFTER_SCROLL)?" -> [YES: N/N / NO: N missing — ISSUE_FOUND]
  2. "All interactive tests passed?" -> [YES: N/N / NO: N failed — ISSUE_FOUND]
  3. "Screenshot visually verified?" -> [YES / NO (blank/GPU issue)]
  4. "Zero crashes/ANRs detected?" -> [YES / NO — ISSUE_FOUND]
  5. "Logcat shows zero app errors?" -> [YES / NO: N errors — ISSUE_FOUND]
  6. "Any observations that indicate unexpected behavior?" -> [NO / YES: {list} — ISSUE_FOUND]

  GATE RESULT: [PASS_ELIGIBLE / ISSUE_FOUND]
```

Rules:
- If `visual_verified=false`: Question 3 is NO. Screen CAN still pass if 1,2,4,5,6 are YES.
- An "observation" IS an issue — no category for "noted behavior".
- You MUST NOT proceed to E6 without completing this gate.

**Gate artifact (MANDATORY):** Write gate answers to a JSON file before classifying:
```bash
cat > docs/testing/reports/screen-{screen_name}-gate.json << 'EOF'
{
  "screen": "{screen_name}",
  "timestamp": "{ISO timestamp}",
  "gate_result": "PASS_ELIGIBLE|ISSUE_FOUND",
  "questions": {
    "anr_clear": true,
    "all_elements_found": true,
    "all_interactions_passed": true,
    "screenshot_verified": true,
    "zero_crashes": true,
    "zero_app_errors": true,
    "no_unexpected_behavior": true
  },
  "element_count": "{found}/{total}",
  "interaction_count": "{passed}/{total}",
  "screenshot_path": "docs/testing/screenshots/adb-test_{screen}_{timestamp}.png"
}
EOF
```
This file serves as commit evidence for the `verify-evidence-artifacts.sh` hook (see HOOK LIMITATIONS in SKILL.md).

**E5.8. Backend API Bug Detection (during flow steps)**

If a flow step or interactive test reveals a backend API returning incorrect data (e.g., stale values, wrong defaults, missing fields):
1. Classify as **ISSUE_FOUND** (not "Known Issue" or observation)
2. Check fix-patterns.md for matching auto-fix eligible entry:
   ```bash
   python -c "
   import re, os
   import glob; fp = next(iter(glob.glob(os.path.expanduser('~/.claude/projects/*VibeCoding-KKB/memory/fix-patterns.md'))), '')
   if not os.path.exists(fp):
       exit(0)
   with open(fp) as f:
       content = f.read()
   sections = re.split(r'(?=^### )', content, flags=re.MULTILINE)
   for s in sections:
       if 'Auto-fix eligible: Yes' not in s:
           continue
       title_m = re.match(r'### (.+)', s)
       if not title_m:
           continue
       title = title_m.group(1).strip()
       if title.endswith('FIXED'):
           continue
       print(f'UNFIXED: {title}')
   "
   ```
3. If matching auto-fix entry found -> invoke `/fix-loop` immediately with fix-patterns context
4. If no matching entry -> log as new discovery, add to fix-patterns.md after fix-loop resolves it

**E6. Classify Screen Result**

| Classification | Criteria |
|----------------|----------|
| **PASS** | Gate PASS_ELIGIBLE: all 6 questions YES, zero missing/failed/crashes |
| **ISSUE_FOUND** | Gate ISSUE_FOUND: any question NO |
| **BLOCKED** | Cannot reach screen after 3 attempts |

**No "PASS with observations".** Any deviation = ISSUE_FOUND.

**E6.5. Post-Classification Logcat**

| Result | Capture |
|--------|---------|
| PASS | E5.5 pre-check sufficient |
| ISSUE_FOUND | `$ADB logcat -d -t 200 *:E > $LOG_DIR/{session}/logcat_{screen}_errors.txt` |
| BLOCKED | `$ADB logcat -d -t 100 AndroidRuntime:E *:S > $LOG_DIR/{session}/logcat_{screen}_crash.txt` |

Then clear: `$ADB logcat -c`

If **PASS** -> next screen. If **ISSUE_FOUND** -> Fix Loop (Section F). If **BLOCKED** -> log, next screen.

> **REMINDER: When ISSUE_FOUND, you MUST use the Skill tool to invoke `/fix-loop`. Do NOT fix issues inline. Do NOT read fix-loop.md and follow it manually.**

---

## FIX LOOP (when ISSUE_FOUND)

**MANDATORY — NO EXCEPTIONS.** Every ISSUE_FOUND enters this loop regardless of whether the issue is known, pre-existing, or seems architectural. Budget: **3 attempts per issue, 12 max total iterations per screen.**

Issues are enumerated from E2a/E3/E4/E5 and processed in severity order: CRASH -> MISSING -> FAILED -> VISUAL.

### Fix Loop Steps

For each issue, for each attempt (up to 3 per issue, 12 total per screen):

**Step F1: Pre-Fix Decision — Code vs. Definition**

Before assuming a code bug, check if the test definition is outdated:
1. Cross-reference the screenshot — does the element exist with different text?
2. Search XML for partial/semantic matches
3. **Decision:**
   - Partial match found -> update `docs/testing/adb-test-definitions.md`. Track: `definition_updates += 1`. Re-verify E3 with updated definition. If still fails -> revert, proceed to F2.
   - No match -> proceed to F2 (fix via Skill)
   - **Limit:** Max 2 definition updates per screen.

**Step F2: Invoke /fix-loop Skill (Single Fix mode)**

> **ENFORCEMENT GATE:** Hooks track whether you invoke `/fix-loop` via the Skill tool. If you fix issues inline without using the Skill tool, the `log-workflow.sh` hook will NOT record a `fixLoopInvoked` event, and if fixes are applied, the `verify-evidence-artifacts.sh` hook will **block your commit**. You MUST use `Skill("fix-loop")`.

> **ADB HOOK LIMITATION:** In ADB sessions, `post-test-update.sh` does NOT auto-set `testFailuresPending` because ADB commands are not recognized as test commands. The `validate-workflow-step.sh` hook will NOT block inline fixes. **Protocol compliance is the SOLE enforcement mechanism** — you MUST invoke `/fix-loop` via the Skill tool for every ISSUE_FOUND, even though hooks cannot enforce it.

**MANDATORY: Use the Skill tool** to invoke `/fix-loop`. Do NOT read fix-loop.md and follow it inline — you MUST invoke it as a Skill.

Invoke: `skill: "fix-loop"` with these arguments:
```
failure_output:             {issue description + XML evidence + screenshot path + logcat}
failure_context:            "ADB test: screen={screen_name}, issue={issue_id} ({severity})"
files_of_interest:          {relevant source files for this screen}
build_command:              "./gradlew assembleDebug"
install_command:            "$ADB install -r android/app/build/outputs/apk/debug/app-debug.apk"
attempt_number:             {current attempt for this issue}
previous_attempts_summary:  {summary of prior attempts from iteration logs}
prohibited_actions:         ["Delete UI elements", "Weaken checklist", "Skip testing", "Mark PASS with issues", "Fix-later issues", "Downgrade issues to observations", "Skip Pre-Classification Gate", "Classify PASS with visual_verified=false AND missing/failed elements"]
fix_target:                 "production"
log_dir:                    ".claude/logs/adb-test/"
session_id:                 {current session id}
```
Budget rationale: Single Fix mode (no `retest_command`) — caller retests via ADB. 3 attempts per issue allows escalation through normal -> thinkhard -> ultrathink (see fix-loop Thinking Escalation).

Collect output: if `fix_applied` -> append to `all_fixes[]`. If `revert_applied` or `fix_applied == false` -> log, proceed to F5.

**Step F3: Relaunch App & Navigate** (caller responsibility)
```bash
$ADB shell am force-stop $APP_PACKAGE
$ADB shell am start -n $APP_PACKAGE/$APP_ACTIVITY
```
Wait for Home, navigate back to screen under test.

**Step F4: Retest** (caller responsibility)

Repeat full screen protocol (E1-E6.5) for this screen.

**Structured retest result (MANDATORY):** After each retest, record the outcome:
```
Retest [{screen_name}] attempt {N}/3 for issue {issue_id}:
  - Gate result: PASS_ELIGIBLE | ISSUE_FOUND
  - Issue status: RESOLVED | STILL_FAILING | NEW_ISSUE
  - Fix applied: {file:line — brief description} | None
  - Screenshot: docs/testing/screenshots/adb-test_{screen}_{timestamp}.png
```
This structured output ensures fix-loop iterations are traceable in session logs.

**Step F5: Per-Issue Increment**
- Issue RESOLVED and others remain -> next OPEN issue (reset attempt counter)
- Issue exhausted (3 attempts) -> UNRESOLVED, next OPEN issue
- ALL issues resolved -> exit with PASS
- Screen total >= 12 -> exit, classify remaining issues
- **PARTIAL** — some resolved, some not

**Step F5.5: Auto-Delegate to /fix-loop for Recurring UNRESOLVED Items**

After fix-loop exhaustion for an issue, if the issue is UNRESOLVED:

1. **Check failure-index.json** for prior occurrences of `(adb-test, {issue_type})`:
   ```bash
   python -c "
   import json
   try:
       with open('.claude/logs/learning/failure-index.json') as f:
           d = json.load(f)
       for e in d.get('entries', []):
           if e.get('skill') == 'adb-test' and e.get('issue_type') == '{detected_issue_type}':
               count = len(e.get('occurrences', []))
               eligible = e.get('auto_fix_eligible', False)
               print(f'OCCURRENCES: {count}, AUTO_FIX_ELIGIBLE: {eligible}')
               break
   except: pass
   "
   ```

2. **Also check fix-patterns.md** for matching auto-fix eligible entry:
   ```bash
   python -c "
   import re, os
   import glob; fp = next(iter(glob.glob(os.path.expanduser('~/.claude/projects/*VibeCoding-KKB/memory/fix-patterns.md'))), '')
   issue_type = '{detected_issue_type}'
   if not os.path.exists(fp):
       exit(0)
   with open(fp) as f:
       content = f.read()
   sections = re.split(r'(?=^### )', content, flags=re.MULTILINE)
   for s in sections:
       if 'Auto-fix eligible: Yes' not in s:
           continue
       title_m = re.match(r'### (.+)', s)
       if not title_m:
           continue
       title = title_m.group(1).strip()
       if title.endswith('FIXED'):
           continue
       if issue_type.lower() in title.lower() or any(kw in title.lower() for kw in issue_type.lower().split('_')):
           files_m = re.search(r'\*\*Files?:\*\*\s*(.+)', s)
           files = files_m.group(1).strip() if files_m else 'unknown'
           print(f'FIX_PATTERN_MATCH: {title} -> files: {files}')
   "
   ```
   If fix-patterns.md has a match -> use those file paths as `files_of_interest`.

3. **If occurrences >= 2 AND auto_fix_eligible is true** (or fix-patterns.md has matching entry with file paths):
   - Auto-invoke `/fix-loop` with enhanced context:
     ```
     Skill("fix-loop") with:
       failure_output:            {issue description + all prior attempt summaries from failure-index}
       failure_context:           "AUTO-DELEGATED: adb-test recurring issue #{count} for {issue_type}"
       files_of_interest:         {target files from fix-patterns.md}
       force_thinking_level:      {"thinkhard" if count <= 3, "ultrathink" if count >= 4}
       previous_attempts_summary: {concatenated summaries from failure-index occurrences}
     ```
   - Log: `"Auto-delegating to /fix-loop (occurrence #{count} for {issue_type})"`

3. **If occurrences < 2 OR not auto_fix_eligible** -> proceed to F5.5b (auto-file issue)

**Step F5.5b: Auto-File GitHub Issues for UNRESOLVED Items**

After fix-loop exhaustion for a screen (all issues processed), for each UNRESOLVED issue:

1. **Skip conditions** (do NOT auto-file):
   - Screen is BLOCKED (navigation failure, not a code bug)
   - Issue matches a known pre-existing issue in MEMORY.md (search `Key Lessons` and `skill-gaps.md`)

2. **Duplicate check:**
   ```bash
   gh issue list --search "ADB Test: {screen_name} - {issue_description}" --state open --limit 5
   ```
   If a matching open issue exists -> skip, log "Duplicate of #{N}"

3. **Auto-file:**
   ```bash
   gh issue create \
     --title "ADB Test: {screen_name} - {brief_description}" \
     --body "{formatted body with context, reproduction steps, evidence paths}" \
     --label "bug,adb-test,unresolved,auto-filed"
   ```

4. **Track:** Append filed issue number to `auto_filed_issues[]`

5. **Log:** `log_event "AUTO_FILED_ISSUE" "screen={screen}" "issue=#{N}" "description={desc}"`

---

## REGRESSION TESTING (after Fix Loop)

**Trigger:** `total_fixes > 0` AND at least one screen PASSED.

For each previously-passed screen (in execution order):

**R1. Navigate** — E1 path. **R2. Verify Arrival** — E2 (including crash detection). If crash -> REGRESSED. **R3. Element Spot-Check** — E3 only (skip E5 for speed). **R4. Classify:** All present -> REGRESSION_PASS. Missing/crash -> REGRESSED.

Track: `regression_screens_tested`, `regression_passes`, `regressions_found`.

Regressions are logged for manual review — NOT auto-fixed.

---

## LOGGING

### Session Directory

Create at start: `.claude/logs/adb-test/{YYYYMMDD_HHMMSS}/`

### Per-Iteration Log

File: `iteration-{NNN}-{screen}.md` — Contains metadata, UI dump analysis, screenshot analysis, interaction results, issues found, root cause, fix applied, retest result.

### Per-Screen Summary

File: `screen-{name}-summary.md` — Final status, total iterations, fix history, remaining issues, screenshots.
