# Flow Execution Protocol

Detailed protocol for running user journey flows via ADB. Referenced from the main `adb-test` SKILL.md.

---

## SECTION G: FLOW EXECUTION PROTOCOL

When `$ARGUMENTS` matches a flow name, execute the corresponding flow definition file.

### G1. Load Flow Definition

```
FLOW_DIR=docs/testing/flows
```

| Flow Name | File |
|-----------|------|
| `new-user-journey` | `flow01-new-user-journey.md` |
| `existing-user` | `flow02-existing-user.md` |
| `recipe-interaction` | `flow03-recipe-interaction.md` |
| `chat-ai` | `flow04-chat-ai.md` |
| `grocery-management` | `flow05-grocery-management.md` |
| `offline-mode` | `flow06-offline-mode.md` |
| `edge-cases` | `flow07-edge-cases.md` |
| `dark-mode` | `flow08-dark-mode.md` |
| `pantry-rules-crud` | `flow09-pantry-rules-crud.md` |
| `stats-tracking` | `flow10-stats-tracking.md` |
| `settings-deep-dive` | `flow11-settings-deep-dive.md` |
| `multi-family-medical` | `flow12-multi-family-medical.md` |
| `festival-meals` | `flow13-festival-meals.md` |
| `nutrition-goals` | `flow14-nutrition-goals.md` |
| `notifications-lifecycle` | `flow15-notifications.md` |
| `achievement-earning` | `flow16-achievements.md` |
| `pantry-suggestions` | `flow17-pantry-suggestions.md` |
| `photo-analysis` | `flow18-photo-analysis.md` |
| `multi-week-history` | `flow19-multi-week-history.md` |
| `recipe-scaling` | `flow20-recipe-scaling.md` |
| `recipe-rules-comprehensive` | `flow21-recipe-rules-comprehensive.md` |

Read the flow definition file: `$FLOW_DIR/{flow-file}.md`

### G2. Check Flow Prerequisites

Each flow has a **Prerequisites** section. Verify:
1. Standard D1-D7 prerequisites (same as screen tests)
2. Flow-specific prerequisites (e.g., Flow 2 requires Flow 1 state — do NOT clean test data)
3. **Depends On:** If the flow depends on another flow, verify that flow's state exists

Special handling:
- "Do NOT run cleanup_user.py" -> skip D4
- "needs existing user" -> skip D4 and D6

### G3. Execute Steps

Follow the flow's **Steps** section sequentially using the 13 ADB patterns from `docs/testing/adb-patterns.md`.

**Step 0: Create evidence directory** (before the step loop):

```bash
FLOW_TS=$(date +%Y%m%d_%H%M%S)
EVIDENCE_DIR=docs/testing/reports/evidence/flow{N}-$FLOW_TS
mkdir -p $EVIDENCE_DIR
```

**Per-step execution (13-column evidence capture):**

For each step in the flow definition:

1. **Record start time:** `step_start = now()`
2. **Read step's Type column** from the flow definition table — `UI` or `API`
3. **Read step's Action column** and execute using appropriate ADB pattern (UI) or curl/script (API)
4. **Dump UI and verify Expected column** — determine PASS/FAIL
5. **Capture evidence:**
   - **UI steps (Type=UI):** `$ADB exec-out screencap -p > docs/testing/screenshots/flow{N}_{step_id}.png`
     - Every UI step gets a unique screenshot — no reuse, no skipping
   - **API steps (Type=API):** Save request JSON + response JSON to `$EVIDENCE_DIR/{step_id}_request.json` and `{step_id}_response.json`
6. **BLOCKING: Invoke `/verify-screenshots`** for each UI screenshot:
   ```
   Skill("verify-screenshots", args="path=docs/testing/screenshots/flow{N}_{step_id}.png expected='{Expected column text}'")
   ```
   DO NOT proceed to next step until verification completes.
   Record verification result (PASSED/ISSUES_FOUND) in `step_results[]`.
   API steps: skip verification (`screenshot_verified = N/A`)
7. **Run validation** if step's Validation column specifies a check (G4)
8. **Run crash/ANR detection** (Pattern 9) after major navigation
9. **Determine result:**
   - Expected met + screenshot verified (or N/A for API) → **PASS**
   - Any deviation, validation failure, or screenshot issue → **FAIL**
   - No "PASS with observation" — Expected X, observed Y = FAIL
10. **If FAIL → STOP. Invoke `/fix-loop`** (G5).
    - If fix-loop resolves and retry passes → continue to next step
    - If 3 retries exhausted → UNRESOLVED → **STOP FLOW ENTIRELY (G3-HALT)**
11. **Record step duration:** `step_duration = now() - step_start`
12. **Append to `step_results[]`** with all 13 columns:

| Field | Value |
|-------|-------|
| `test_id` | Step ID from flow definition (e.g., A1, B3, C28) |
| `test_name` | Brief action name from Action column |
| `test_scenario` | Expected outcome from Expected column |
| `pass_fail` | PASS / FAIL / UNRESOLVED / NOT_RUN |
| `screenshot` | Path to .png or "N/A (API)" with evidence path |
| `screenshot_verified` | Yes / No / N/A |
| `verification_result` | "PASSED: {detail}" or "ISSUES_FOUND: {detail}" or "N/A" |
| `skill_should_trigger` | Yes (if failed) / No (if passed) |
| `skill_actually_triggered` | Yes (fix-loop invoked) / No |
| `step_type` | UI / API (from flow definition Type column) |
| `verification_method` | ADB_SCREENCAP / API_RESPONSE / ADB_XML_DUMP / LOGCAT_CHECK / SCRIPT_VALIDATION / N/A |
| `duration_s` | Seconds for this step including retries |
| `retry_count` | 0 = first attempt passed, 1-3 = retries before result |

13. **Also append API calls** to `api_evidence[]` with method, endpoint, request body, response status, response summary

**Per-flow verification count check (MANDATORY):** After the last step completes (or flow halts), verify:
```
verify_screenshot_invocations == count of UI steps executed (not NOT_RUN)
```
If the count does not match, log a protocol violation warning in the report. This catches cases where `/verify-screenshots` was skipped for a UI step.

Between phases: `Phase {X} Complete: {N}/{total} steps passed`

#### G3-HALT: Flow Halt Procedure

When a step is UNRESOLVED after 3 retries:
1. Mark all remaining steps as `NOT_RUN` with: `pass_fail=NOT_RUN, screenshot=N/A, screenshot_verified=N/A, verification_result=N/A, skill_should_trigger=N/A, skill_actually_triggered=N/A, step_type={from definition}, verification_method=N/A, duration_s=0, retry_count=0`
2. Set `flow_halted = true`, `halt_step_id = {failed step ID}`
3. Proceed directly to G6 (report generation)

### G4. Run Validation

When a step's Validation says "V4a-V4k":
```bash
cd D:/Abhay/VibeCoding/KKB
python scripts/validate_meal_plan.py --jwt "$JWT" {args from flow's Validation Checkpoints}
```

JWT acquisition:
```bash
JWT=$(curl -s -X POST http://localhost:8000/api/v1/auth/firebase \
  -H 'Content-Type: application/json' \
  -d '{"firebase_token":"fake-firebase-token"}' | \
  python -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))')
```

Result handling:
  - exit 0 → PASS (continue to next step)
  - exit 1 → FAIL (invoke /fix-loop per G5, retry step)
  - exit 2 → FAIL (SOFT failures ARE failures — invoke /fix-loop per G5, retry step)

There is NO "log and continue" for failures. ALL non-zero exits trigger /fix-loop.

### G5. Per-Step Issue Detection

A step **fails** when:
- Expected text/element not found in XML
- Expected behavior did not occur
- Crash/ANR detected
- Validation exit code 1 (HARD failure)
- Validation exit code 2 (SOFT failure / warnings) — **this IS a failure, not a pass**
- Any behavioral deviation from Expected column
- Screenshot blank AND expected result unverifiable via XML
- `/verify-screenshots` returns ISSUES_FOUND

**"Behavioral deviation" includes:** AI not performing expected actions, missing conflict detection, data not persisting as expected.

> **CRITICAL: ALL failures — including SOFT FAILs (validation exit 2, warnings, minor deviations) — MUST trigger `/fix-loop`. There is NO category of failure that skips fix-loop. No exceptions.**

> **Exit code override:** If a validation script or ADB command returns a non-zero exit code that the shell interprets differently (e.g., `grep` returns 1 for "no match"), the step result is determined by the **Expected column**, not the raw exit code. However, validation scripts (`validate_meal_plan.py`) always use exit 0 = PASS, exit 1 = HARD FAIL, exit 2 = SOFT FAIL — these are authoritative.

**Recording per step:**
- `skill_should_trigger` = Yes for ANY failure (FAIL or UNRESOLVED), No for PASS
- `skill_actually_triggered` = Yes if `/fix-loop` was actually invoked, No otherwise
- These two values MUST match. A mismatch (should=Yes, actually=No) is a protocol violation.

When a step fails, **use the Skill tool** to invoke `/fix-loop`:

Invoke: `skill: "fix-loop"` with arguments:
```
failure_output:             {step failure description + XML evidence + screenshot + logcat + verify-screenshots result}
failure_context:            "ADB flow test: flow={flow_name}, step={step_id}, attempt={N}/3"
files_of_interest:          {from the flow's Fix Strategy section}
build_command:              "./gradlew assembleDebug"
install_command:            "$ADB install -r android/app/build/outputs/apk/debug/app-debug.apk"
attempt_number:             {current attempt for this step}
previous_attempts_summary:  {summary of prior attempts}
prohibited_actions:         ["Delete UI elements", "Weaken checklist", "Skip testing", "Mark PASS with issues"]
fix_target:                 "production"
log_dir:                    ".claude/logs/adb-test/"
session_id:                 {current session id}
```

**Max 3 attempts per step.** After fix, re-execute ONLY the failed step (not entire flow).

**HALT RULE:** If a step still fails after 3 attempts:
1. Mark as UNRESOLVED in `step_results[]`
2. Add to `unresolved_issues[]` with step_id, description, last_error, all 3 attempt summaries
3. **STOP THE FLOW ENTIRELY** — do NOT continue to subsequent steps
4. Mark all remaining steps as NOT_RUN (see G3-HALT)
5. Proceed to G6 (report generation)

**No "PASS with observation" for flow steps.** Expected X, observed Y = FAILED.

### G6. Flow Report (Markdown File + Console)

**Every flow run MUST produce a saved markdown report file.** This is not optional.

#### G6a. Evidence Directory

Evidence directory is created at the start of G3 (before the step loop). The `$EVIDENCE_DIR` and `$FLOW_TS` variables are already set.

#### G6b. Compute Summary Statistics

From `step_results[]`, compute:
- `total_steps`, `passed`, `failed`, `unresolved`, `not_run`
- `pass_rate` = passed / total_steps * 100
- `screenshots_captured` = count of non-N/A screenshots
- `screenshots_verified` = count where screenshot_verified = Yes
- `verify_passes` = count where verification_result starts with "PASSED"
- `verify_failures` = count where verification_result starts with "ISSUES_FOUND"
- `fix_loop_invocations` = count where skill_actually_triggered = Yes
- `total_retries` = sum of retry_count across all steps
- `total_duration` = sum of duration_s (or flow end - flow start)
- Per-phase: group steps by phase prefix, compute pass/fail/duration per phase

#### G6c. Build Report File

Write the full report to: `$REPORT_DIR/flow{N}-{flow_name}-$FLOW_TS.md`

Report sections in order:

```markdown
# Flow {N}: {Flow Name} — Test Report

## Metadata
| Field | Value |
|-------|-------|
| Flow ID | {N} |
| Flow Name | {flow_name} |
| Date | {YYYY-MM-DD HH:MM:SS} |
| Total Duration | {M}m {S}s |
| Result | {PASSED / FAILED / PARTIAL} |
| Pass Rate | {X}% ({passed}/{total}) |
| Screenshots Captured | {count} |
| Screenshots Verified | {count} |
| Fix-Loop Invocations | {count} |
| Halt Step | {step_id} — {brief reason} (omit row if no halt) |

## Test Results

| # | Test Id | Test Name | Test Scenario | Pass/Fail | Screenshot | Screenshot Verified? | Verification Result | Skill Should Trigger | Skill Actually Triggered | Step Type | Verification Method | Duration (s) | Retry Count |
|---|---------|-----------|---------------|-----------|------------|---------------------|--------------------|--------------------|------------------------|-----------|--------------------|--------------:|------------:|
| 1 | {id} | {name} | {scenario} | {result} | {link} | {Y/N/NA} | {detail} | {Y/N} | {Y/N} | {UI/API} | {method} | {sec} | {retries} |
...

## Summary Statistics
- **Total Steps:** {total}
- **Passed:** {passed} ({pass_rate}%)
- **Failed:** {failed}
- **Unresolved:** {unresolved}
- **NOT_RUN:** {not_run} (flow halted at step {halt_step_id})
- **Total Retries:** {total_retries}
- **Screenshots:** {captured} captured, {verified} verified ({verify_passes} passed, {verify_failures} issues found)

## Phase Summary

| Phase | Name | Steps | Passed | Failed | Duration |
|-------|------|------:|-------:|-------:|---------:|
| A | {name} | {N} | {N} | {N} | {Xs} |
...

## Skills Activity

| Skill | Invocations | Context |
|-------|------------:|---------|
| `/fix-loop` | {N} | {step IDs where invoked} |
| `/verify-screenshots` | {N} | {step IDs where invoked} |
| `/post-fix-pipeline` | {0/1} | {if invoked} |
| `/reflect` | {0/1} | Post-run |

## API Evidence

| Step | Method | Endpoint | Request Summary | Response Status | Response Summary |
|------|--------|----------|----------------|----------------:|-----------------|
| {id} | {GET/POST/...} | {path} | {brief} | {200/404/...} | {brief} |
...

## Validation Checkpoints
{If flow uses validate_meal_plan.py — one row per checkpoint with result}
{Or "No validation checkpoints in this flow."}

## Contradictions Tested
{If flow has contradiction steps — C{N}: description → PASS/FAIL}
{Or "No contradiction steps in this flow."}

## Known Issues
{Pattern 14 limitations, known workarounds applied during this run}

## Unresolved Issues
{Steps that failed after 3 retries — step ID, description, last error}
{Or "None — all steps resolved."}
```

#### G6d. Save Report

```bash
# Write report file
cat > "$REPORT_DIR/flow{N}-{flow_name}-$FLOW_TS.md" << 'REPORT_EOF'
{assembled markdown content}
REPORT_EOF
```

Set `report_file_path` to the saved path.

#### G6e. Console Summary (Backward Compatibility)

Also print the legacy console summary:
```
====================================================================
  ADB FLOW TEST REPORT: {flow-name}
====================================================================
Phase A: {name}          -> {N}/{total} steps PASS
Phase B: {name}          -> {N}/{total} steps PASS
...
--------------------------------------------------------------------
TOTAL: {passed}/{total} steps | {fixes} fixes | {screenshots} screenshots
Duration: X minutes Y seconds
Report saved: docs/testing/reports/flow{N}-{flow_name}-{ts}.md
Session logs: .claude/logs/adb-test/{session}/
====================================================================
```

### G7. All-Flows Mode

**`all-flows`:** Run flow01 -> flow21 in order. Do NOT run `cleanup_user.py` between flows. Only D4 before flow01.

Each flow produces its own report file via G6. After all flows complete, generate an additional **combined summary report**:

```bash
COMBINED_TS=$(date +%Y%m%d_%H%M%S)
COMBINED_REPORT=docs/testing/reports/all-flows-summary-$COMBINED_TS.md
```

Combined report contains:
1. **Summary table** — one row per flow: flow #, name, pass/fail/total, pass rate, duration, report file link
2. **Aggregate statistics** — total steps across all flows, overall pass rate, total duration
3. **Cross-flow issues** — any issues that appeared in multiple flows
4. **Links** — to each individual flow report file

**`all-flows-from <name>`:** Find flow number, run from there onwards. Assume prior state exists. Each flow still generates its own report. Combined summary covers only the flows that were run.

---

## FLOW QUICK REFERENCE

| # | Flow | Screens | Contradictions | Duration | Key Feature |
|---|------|---------|----------------|----------|-------------|
| 1 | `new-user-journey` | 13 | C1-C5 | 15-25 min | Full onboarding + 2 meal plans |
| 2 | `existing-user` | 4 | — | 8-12 min | Persistence + plan #3 |
| 3 | `recipe-interaction` | 4 | — | 5-8 min | Favorite, cook, unfavorite |
| 4 | `chat-ai` | 3 | C6-C12 | 8-15 min | Chat + tool calling |
| 5 | `grocery-management` | 2 | C13 | 4-6 min | Categories, checkboxes, share |
| 6 | `offline-mode` | 5 | C14-C15 | 6-10 min | WiFi off, Room cache |
| 7 | `edge-cases` | 10 | C16-C21 | 5-8 min | Rapid nav, back stack |
| 8 | `dark-mode` | 6 | — | 4-6 min | Theme toggle + visual |
| 9 | `pantry-rules-crud` | 3 | C22-C27 | 8-12 min | CRUD + duplicate prevention |
| 10 | `stats-tracking` | 1 | — | 3-5 min | Streak, chart, tabs |
| 11 | `settings-deep-dive` | 13 | — | 15-20 min | 12 sub-screens, CRUD, preferences |
| 12 | `multi-family-medical` | 6 | C28-C33, C34-C37 | 8-10 min | 6-member joint family, medical constraints |
| 13 | `festival-meals` | 4 | — | 6-8 min | Festival calendar, fasting meals |
| 14 | `nutrition-goals` | 3 | — | 5-7 min | Nutrition goal CRUD, tracking |
| 15 | `notifications-lifecycle` | 2 | — | 4-6 min | Notification triggers, mark read |
| 16 | `achievement-earning` | 2 | — | 4-6 min | Achievement milestones, badges |
| 17 | `pantry-suggestions` | 3 | — | 5-7 min | Pantry-based recipe suggestions |
| 18 | `photo-analysis` | 2 | — | 4-6 min | Food photo → Gemini Vision analysis |
| 19 | `multi-week-history` | 1 | — | 3-5 min | Week nav arrows, "Back to This Week" |
| 20 | `recipe-scaling` | 2 | — | 3-5 min | Serving size scaling |
| 21 | `recipe-rules-comprehensive` | 3 | C22-C27 | 8-12 min | Full CRUD + dedup + conflict |
