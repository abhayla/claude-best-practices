---
name: adb-test
description: >
  Autonomous Android E2E testing via ADB (uiautomator dump, screencap, input tap).
  Self-healing fix loops, dropdown API fallback (Pattern 14), GitHub issue auto-filing.
  Use when testing app screens without Compose framework, debugging emulator UI,
  or validating user flows manually. Supports 24 screens and 21 flows.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[screen|flow|all-flows|all-flows-from <name>]"
---

# ADB Manual E2E Testing

Test app screens via ADB (uiautomator dump, screencap, input tap) — fully autonomous with self-healing fix loops.

**Target screen:** $ARGUMENTS

If `$ARGUMENTS` is empty, test ALL 24 screens sequentially. If a screen name is provided (e.g., `home`, `grocery`), test only that screen. If a flow name is provided (e.g., `new-user-journey`), test that user journey flow.

**Valid screen names:** `auth-flow`, `home`, `grocery`, `chat`, `favorites`, `stats`, `settings`, `notifications`, `recipe-detail`, `cooking-mode`, `pantry`, `recipe-rules`

**Valid flow names:** `new-user-journey`, `existing-user`, `recipe-interaction`, `chat-ai`, `grocery-management`, `offline-mode`, `edge-cases`, `dark-mode`, `pantry-rules-crud`, `stats-tracking`, `settings-deep-dive`, `multi-family-medical`, `festival-meals`, `nutrition-goals`, `notifications-lifecycle`, `achievement-earning`, `pantry-suggestions`, `photo-analysis`, `multi-week-history`, `recipe-scaling`, `recipe-rules-comprehensive`

**Special arguments:** `all-flows` (run all 21 flows sequentially), `all-flows-from <name>` (run from specified flow onwards)

**Argument detection:**
1. If `$ARGUMENTS` matches a valid screen name — run screen test protocol (see `references/screen-definitions.md`)
2. If `$ARGUMENTS` matches a valid flow name — run flow execution protocol (see `references/flow-definitions.md`)
3. If `$ARGUMENTS` is `all-flows` — run all 21 flows sequentially (flow01 - flow21)
4. If `$ARGUMENTS` is `all-flows-from <name>` — run flows from the specified flow onwards
5. If `$ARGUMENTS` is empty — run all 24 screen tests

---

## AUTO-PROCEED RULES (MANDATORY)

- Do NOT ask for any confirmations before, during, or after testing
- Do NOT ask "Should I proceed?", "Ready to continue?", or similar
- Automatically handle all prerequisites (emulator, backend, build, auth, onboarding)
- If build fails, auto-fix compilation errors and rebuild — do not ask
- If emulator is not running, auto-start it and wait for boot — do not ask
- If backend is not running, auto-start it in the background and wait — do not ask
- If app is on auth screen, auto-authenticate via ADB taps — do not ask
- If app is on onboarding, auto-complete all 5 steps via ADB taps — do not ask
- If no meal plan exists, auto-generate via backend API — do not ask
- Proceed through all screens without pausing for user input
- Never stop for user input. If a screen exhausts 12 fix iterations (3 per issue), skip it and continue.

---

## ADB CONSTANTS & PATTERNS

```
ADB = $HOME/AppData/Local/Android/Sdk/platform-tools/adb.exe
EMULATOR = $HOME/AppData/Local/Android/Sdk/emulator/emulator.exe
SCREENSHOT_DIR = docs/testing/screenshots
LOG_DIR = .claude/logs/adb-test
APP_PACKAGE = com.rasoiai.app
APP_ACTIVITY = com.rasoiai.app.MainActivity
```

> **Literal paths:** Command templates in screen-definitions.md and flow-definitions.md use literal `docs/testing/screenshots` instead of `$SCREENSHOT_DIR` to ensure `post-screenshot.sh` can extract and process paths correctly. The `$SCREENSHOT_DIR` variable is defined here for reference only.

**Read `docs/testing/adb-patterns.md` for the 14 reusable ADB interaction patterns** (UI dump, screenshot, tap, text input, back press, parse bounds, find element, scroll/redump, crash/ANR detection, keyboard dismiss, system dialog detection, screenshot validation, logcat capture, dropdown/popup interaction).

### CRITICAL: Compose testTag() is NOT visible in uiautomator XML

Jetpack Compose `testTag()` values do NOT appear in uiautomator XML dumps. All element searches must use:
- **`text`** attribute — visible text on screen
- **`content-desc`** attribute — accessibility labels
- **`resource-id`** attribute — Android resource IDs (rare in Compose)
- **`class`** attribute — widget type
- **Bounds position** — relative screen position (bottom nav y > 90%, top bar y < 15%)

### Known Limitations

| Component | Limitation | Root Cause | Workaround |
|-----------|-----------|------------|------------|
| ExposedDropdownMenu | Popup items unreachable by `input tap` | Compose popup uses `WindowManager.addView()` as `TYPE_APPLICATION_PANEL` — `input tap` routes to focused main Activity window, not popup | Accept default values in UI, correct via backend API after onboarding (Pattern 14) |
| uiautomator dump | May dismiss popup by forcing focus change | `uiautomator dump` triggers a window focus change that closes the popup | N/A — popup interaction via UI is not viable for ADB testing |
| Compose testTag | Not visible in uiautomator XML | testTag is Compose semantics-only, not mapped to Android accessibility | Use `text`, `content-desc`, bounds position |

### Stall Detection

If the same ADB action (tap/text/dump) fails 3 consecutive times with the same outcome:
1. Log stall: element, action, 3 failure details
2. For dropdowns: skip to backend API fallback immediately (Pattern 14 — UI attempts are known non-working)
3. For other elements: try alternative search strategy (text - content-desc - bounds)
4. NEVER ask the user — use the fallback autonomously

### Onboarding Dropdown Coordinate Hints (Pixel 6, 1080x2400)

| Dropdown | Anchor testTag | Item Height | contentDescription Pattern |
|----------|---------------|-------------|---------------------------|
| Household size | `household_size_dropdown` | ~100px | `"{N} people"` |
| Spice level | `spice_level_dropdown` | ~100px | `"Spice {Level}"` |
| Weekday time | `weekday_time_dropdown` | ~100px | `"Weekday {N} minutes"` |
| Weekend time | `weekend_time_dropdown` | ~100px | `"Weekend {N} minutes"` |

---

## STEP 0: PRE-EXECUTION KNOWLEDGE CHECK

Before any testing, check the failure index for known issues that affect this skill:

1. **Read failure-index.json** for known workarounds and recurring failures:
   ```bash
   python -c "
   import json
   try:
       with open('.claude/logs/learning/failure-index.json') as f:
           d = json.load(f)
       applied = []
       for e in d.get('entries', []):
           if e.get('skill') == 'adb-test' or e.get('skill') == 'fix-loop':
               if e.get('known_workaround'):
                   applied.append(f\"WORKAROUND: {e['issue_type']} -> {e['known_workaround']}\")
                   print(f\"Step 0: Applying workaround for {e['issue_type']}: {e['known_workaround']}\")
               if e.get('threshold_reached'):
                   print(f\"WARNING: {e['issue_type']} has {len(e['occurrences'])} prior failures\")
               if e.get('auto_fix_eligible'):
                   print(f\"AUTO-FIX ELIGIBLE: {e['issue_type']} — flag for post-run delegation\")
       if not applied:
           print('Step 0: No known workarounds to apply')
   except FileNotFoundError:
       print('Step 0: No failure index found (first run)')
   "
   ```

2. **Read fix-patterns.md** for matching code-level patterns:
   ```bash
   python -c "
   import os
   import glob; fp = next(iter(glob.glob(os.path.expanduser('~/.claude/projects/*VibeCoding-KKB/memory/fix-patterns.md'))), '')
   if os.path.exists(fp):
       with open(fp) as f:
           content = f.read()
       if 'Auto-fix eligible' in content:
           print('Step 0: Found auto-fix eligible patterns in fix-patterns.md')
   "
   ```

3. **Scan fix-patterns.md for auto-fix eligible entries and auto-invoke /fix-loop:**
   ```bash
   python -c "
   import re, os
   import glob; fp = next(iter(glob.glob(os.path.expanduser('~/.claude/projects/*VibeCoding-KKB/memory/fix-patterns.md'))), '')
   if not os.path.exists(fp):
       print('Step 0: No fix-patterns.md found')
       exit(0)
   with open(fp) as f:
       content = f.read()
   sections = re.split(r'(?=^### )', content, flags=re.MULTILINE)
   unfixed = []
   for s in sections:
       if 'Auto-fix eligible: Yes' not in s:
           continue
       title_m = re.match(r'### (.+)', s)
       if not title_m:
           continue
       title = title_m.group(1).strip()
       if title.endswith('FIXED'):
           continue
       files_m = re.search(r'\*\*Files?:\*\*\s*(.+)', s)
       files = files_m.group(1).strip() if files_m else 'unknown'
       unfixed.append((title, files))
   if unfixed:
       for t, f in unfixed:
           print(f'UNFIXED AUTO-FIX: {t} -> files: {f}')
   else:
       print('Step 0: All auto-fix eligible patterns are resolved')
   "
   ```
   For each unfixed entry found:
   - Auto-invoke `/fix-loop` with:
     ```
     failure_output: {pattern description from fix-patterns.md}
     failure_context: "Pre-execution auto-fix: {pattern name}"
     files_of_interest: {files from fix-patterns.md entry}
     build_command: appropriate build command
     ```
   - Log: `"Step 0: Auto-fixed {N} patterns from fix-patterns.md"`

4. **Apply known workarounds proactively:**
   - If `dropdown_interaction` workaround exists — pre-set Pattern 14 as default strategy (skip UI attempts)
   - If `crash_anr` workaround exists — add extra crash recovery delay
   - Log: `"Step 0 complete: {N} workarounds applied, {M} auto-fix eligible patterns noted"`

---

## SESSION INITIALIZATION

Before prerequisites, initialize the workflow tracking state:

```bash
python -c "
import json, os, tempfile
state_file = '.claude/workflow-state.json'
if os.path.exists(state_file):
    with open(state_file) as f:
        d = json.load(f)
else:
    d = {}

# Set active command
d['activeCommand'] = 'adb-test'

# Clear flags that would false-block ADB sessions
d['testFailuresPending'] = False
d['fixLoopInvestigating'] = False
d['visualIssuesPending'] = False

# Clear screenshot and evidence state for fresh session
d['screenshotsCaptured'] = []
d.setdefault('evidence', {})['testRuns'] = []

# Clear verify-screenshots flag
d.setdefault('skillInvocations', {})['verifyScreenshotsInvoked'] = False

# Preserve fixLoopCount (cumulative tracking across sessions)
# d.get('skillInvocations', {}).get('fixLoopCount') — intentionally NOT cleared

# Atomic write
fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, state_file)
print('Session state initialized for adb-test')
"
```

Create session log directory and reports directory:
```bash
mkdir -p .claude/logs/adb-test/$(date +%Y%m%d_%H%M%S)
mkdir -p docs/testing/reports/evidence
```

This marks the session as an `adb-test` workflow. Hooks will:
- Track all Skill invocations (fix-loop, post-fix-pipeline)
- Block commits if fixes were applied but pipeline was not invoked
- Log all tool events for audit trail

---

## PREREQUISITES — Run These First (Every Time)

### D1. Check Emulator

```bash
$ADB devices
```

- If a device is listed as `device` — emulator is ready, continue.
- If no device or only `offline` entries:
  1. Start the emulator: `$EMULATOR -avd Pixel_6 &`
  2. Wait for boot: `$ADB wait-for-device` then loop `$ADB shell getprop sys.boot_completed` until `1` (max 120 seconds).

### D2. Check Backend

```bash
curl -s http://localhost:8000/health
```

- If healthy — continue.
- If connection refused — auto-start:
  1. `cd D:/Abhay/VibeCoding/KKB/backend && source venv/bin/activate && uvicorn app.main:app --reload &`
  2. Poll every 3s for 30s: `for i in {1..10}; do curl -sf http://localhost:8000/health && break || sleep 3; done`
  3. If still unhealthy — log warning, continue (screens not requiring backend may still work).

### D3. Build & Install App

```bash
cd D:/Abhay/VibeCoding/KKB/android && ./gradlew assembleDebug
$ADB install -r D:/Abhay/VibeCoding/KKB/android/app/build/outputs/apk/debug/app-debug.apk
```

If build fails, auto-fix compilation errors and rebuild (max 3 attempts).

### D4. Clean Test Data

```bash
cd D:/Abhay/VibeCoding/KKB/backend && PYTHONPATH=. python scripts/cleanup_user.py
```

### D5. Launch App & Detect Current Screen

```bash
$ADB shell am force-stop $APP_PACKAGE
$ADB shell am start -n $APP_PACKAGE/$APP_ACTIVITY
```

Wait 3 seconds, dump UI, detect which screen:

| Screen | Detection |
|--------|-----------|
| Splash | text="RasoiAI" or loading indicator |
| Auth | text="Sign in with Google" or text="Welcome" |
| Onboarding | text="Tell us about your household" or progress bar |
| Home | text="This Week's Menu" or text="BREAKFAST" |

### D6. Auto-Complete Auth & Onboarding (if needed)

**If on Auth screen:**
1. Find "Sign in with Google" button, compute center from bounds, tap via ADB
2. Google account picker appears — select the test account (`abhayfaircent@gmail.com` primary, `zmphzc@gmail.com` secondary). Credentials in `memory/test-accounts.md`
3. Wait up to 15 seconds for OAuth to complete and transition
4. If onboarding appears next, proceed to onboarding steps below

**If on Onboarding — complete all 5 steps:**

| Step | Actions |
|------|---------|
| 1. Household | Find "Next", tap household size dropdown if shown, tap to proceed |
| 2. Dietary | Tap a diet preference (e.g., text="Vegetarian"), tap "Next" |
| 3. Cuisine | Tap a cuisine (e.g., text="North Indian"), tap "Next" |
| 4. Dislikes | Tap "Next" (skip dislikes for speed) |
| 5. Cooking Time | **Accept default dropdown values** (do NOT attempt to change dropdowns via ADB), tap "Create My Meal Plan" or "Generate" |

After each step, wait 1-2s and dump UI to verify progression. If generation screen appears, wait up to 90s for meal plan generation.

**Dropdown API Correction (after onboarding completes):**

Onboarding dropdowns (cooking times, household size, spice level) cannot be changed via ADB `input tap` — see Pattern 14 root cause. After onboarding completes and the user has a JWT, correct any values that differ from the test persona via backend API:

```bash
# Get JWT
JWT=$(curl -s -X POST http://localhost:8000/api/v1/auth/firebase \
  -H 'Content-Type: application/json' \
  -d '{"firebase_token":"fake-firebase-token"}' | \
  python -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))')

# Correct cooking times (and any other dropdown-set values) via API
curl -s -X PUT http://localhost:8000/api/v1/users/preferences \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  -d '{"weekday_cooking_time": 30, "weekend_cooking_time": 60}'
```

**Rule:** For onboarding dropdowns, accept default values via UI tap of "Next"/"Create My Meal Plan", then correct specific values via backend API after onboarding completes but before validation checkpoints.

**If no meal plan data on Home screen:** Generate via backend API:
```bash
curl -X POST http://localhost:8000/api/v1/meal-plans/generate \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/firebase -H 'Content-Type: application/json' -d '{"firebase_token":"fake-firebase-token"}' | python -c 'import sys,json;print(json.load(sys.stdin).get(\"access_token\",\"\"))')" \
  -H "Content-Type: application/json"
```
Wait up to 90s, then force-stop and restart app.

### D7. Clear Logcat Buffer

```bash
$ADB logcat -c
```

---

For screen test protocols, see `references/screen-definitions.md`.
For flow execution protocols, see `references/flow-definitions.md`.

---

## TRACKING VARIABLES

```
// Screen tracking
screens_tested = 0; screens_passed = 0; screens_failed = 0; screens_blocked = 0; screens_unresolved = 0
per_screen_results = {}   // screen_name -> { status, iterations, fixes[], issues[] }
per_screen_issues = {}    // screen_name -> [ { id, severity, description, status, attempts } ]

// Fix tracking
total_fixes = 0; all_fixes = []; total_iterations = 0; definition_updates = 0

// Fix-loop metrics (accumulated from Skill outputs)
fix_loop_metrics = { debugger_invocations: 0, code_reviews: 0, code_reviews_approved: 0, code_reviews_flagged: 0, review_issues: [], build_failures: 0, reverts: 0 }

// Backend, logcat, visual, regression, pipeline tracking
backend_health_checks = 0; backend_restarts = 0; logcat_captures = 0
blank_screenshots = 0; visual_verified_screens = {}
regression_screens_tested = 0; regression_passes = 0; regressions_found = 0
pipeline_status = "NOT_RUN"; test_suite_gate = "NOT_RUN"; commit_hash = ""; commit_message = ""
start_time = now(); per_screen_times = {}

// Flow report tracking (used by G3/G5/G6 protocol)
step_results = []         // per-step array, each entry has 13 fields:
                          //   test_id, test_name, test_scenario, pass_fail,
                          //   screenshot, screenshot_verified, verification_result,
                          //   skill_should_trigger, skill_actually_triggered,
                          //   step_type, verification_method, duration_s, retry_count
api_evidence = []         // { step_id, method, endpoint, request_summary, response_status, response_summary }
validation_checkpoints = []  // { checkpoint_id, args, exit_code, output_summary }
contradictions_tested = []   // { contradiction_id, description, result (PASS/FAIL) }
unresolved_issues = []       // { step_id, description, last_error, attempts }

// Flow halt tracking
flow_halted = false       // true if flow stopped due to UNRESOLVED step
halt_step_id = ""         // step ID where flow halted
not_run_count = 0         // count of steps marked NOT_RUN after halt

// Screenshot verification counters
verify_screenshot_invocations = 0
verify_screenshot_passes = 0
verify_screenshot_failures = 0

// Report output paths
flow_number = 0; flow_name = ""; flow_timestamp = ""
report_file_path = ""     // e.g., docs/testing/reports/flow12-multi-family-medical-20260215_181500.md
evidence_dir_path = ""    // e.g., docs/testing/reports/evidence/flow12-20260215_181500/
flow_start_time = now()
```

---

## SKILL INTEGRATION

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/fix-loop` | Step F2 (screens) or G5 (flows): on FIRST failure — flow STOPS until resolved | Analyze root cause, apply fix, code review gate, rebuild. Max 3 retries per step |
| `/verify-screenshots` | G3: BLOCKING per-UI-step — must complete before next step | Validate each step screenshot via multimodal analysis. API steps skip |
| `/post-fix-pipeline` | Post-run, if any fixes were applied | Test suite verification + documentation + git commit |

**How Skills are invoked:** Via the **Skill tool** — NOT by reading the .md file. See screen-definitions.md Step F2 and Post-Run Pipeline below.

## ENFORCEMENT RULES (BLOCKING GATES)

| Gate | Rule | Consequence |
|------|------|-------------|
| Gate 1: Screenshot Verification | Cannot proceed to next UI step until `/verify-screenshots` returns | Blocks flow progression |
| Gate 2: Fix-Loop Invocation | Cannot proceed past any FAIL without `/fix-loop` | Blocks flow progression |
| Gate 3: Flow Halt | UNRESOLVED after 3 retries = STOP flow entirely | Remaining steps = NOT_RUN |
| Gate 4: Report Completeness | Report cannot be saved if any of (a)-(d) are violated | Report blocked |

**Gate 4 conditions (report CANNOT be saved if):**
- (a) Any UI step has `screenshot_verified = "No"` (except NOT_RUN steps)
- (b) Any step has `skill_should_trigger ≠ skill_actually_triggered` (except NOT_RUN steps)
- (c) `step_results[]` has fewer entries than total steps in flow definition
- (d) Any step has `step_type` in `step_results[]` that does not match the Type column in the flow definition (e.g., step defined as `UI` but recorded as `API`)

### HOOK LIMITATIONS (ADB Sessions)

> **CRITICAL:** ADB commands (`adb exec-out`, `input tap`, `uiautomator dump`) do NOT trigger the standard hook enforcement chain. The `is_test_command()` function in `hook-utils.sh` recognizes `pytest`, `./gradlew test`, and similar — but NOT ADB commands. This means:
>
> 1. **`post-test-update.sh` will NOT auto-record** ADB test results in `evidence.testRuns[]`. The skill must write evidence artifacts (flow reports, screen gate files) directly.
> 2. **`verify-test-rerun.sh` will NOT re-run** ADB tests. Protocol compliance (invoking `/fix-loop` on every FAIL) is the SOLE enforcement mechanism.
> 3. **`validate-workflow-step.sh` will NOT block** code edits based on ADB test failures. The `testFailuresPending` flag must be managed manually in SESSION INITIALIZATION.
> 4. **`verify-evidence-artifacts.sh` checks for** flow reports (`docs/testing/reports/flow*.md`) or screen gate files (`docs/testing/reports/screen-*-gate.json`) instead of `testRuns[]` for `adb-test` sessions.
> 5. **Screenshot paths using `$SCREENSHOT_DIR`** are resolved by `post-screenshot.sh`, but command templates should use literal `docs/testing/screenshots` to avoid edge cases.
>
> **Consequence:** Protocol compliance is enforced by the skill definition itself, not by hooks. Skipping `/fix-loop` on a FAIL or skipping `/verify-screenshots` on a UI step is a protocol violation that hooks cannot catch.

### Post-Run Pipeline

After all screens complete (or single screen), check if fixes were applied.

**If `len(all_fixes) == 0`**: skip — no changes to commit.

**If `len(all_fixes) > 0`**:

> **ENFORCEMENT GATE:** Hooks track whether you invoke `/post-fix-pipeline` via the Skill tool. If fixes were applied and you attempt to commit without invoking the pipeline, the `verify-evidence-artifacts.sh` hook will **block your commit**. You MUST use `Skill("post-fix-pipeline")`.

**Use the Skill tool** to invoke `/post-fix-pipeline`:

Invoke: `skill: "post-fix-pipeline"` with these arguments:
```
fixes_applied:            {all_fixes from tracking}
files_changed:            {all modified file paths}
session_summary:          "ADB test run: {N} fixes across {screens}"
regression_commands:      []   (ADB regression R1-R4 runs inline, not delegated)
test_suite_commands:      [
  { name: "backend", command: "cd backend && PYTHONPATH=. pytest --tb=short -q", timeout: 300 },
  { name: "android-unit", command: "cd android && ./gradlew test --console=plain", timeout: 600 }
]
test_suite_max_fix_attempts: 2
docs_instructions:        "Update docs/CONTINUE_PROMPT.md with session summary"
commit_format:            "fix(adb-test): {summary}"
commit_scope:             "adb-test"
push:                     false
```

**Do NOT commit manually. Do NOT read post-fix-pipeline.md and follow it inline.**

Collect pipeline output for the final report: `test_suite_gate`, commit hash/message.

---

## FINAL REPORT

### Screen Test Report (console only)

```
====================================================================
  ADB MANUAL E2E TEST REPORT
====================================================================
Screen  1: auth-flow        -> PASS (0 fixes)
Screen  2: home             -> PASS (1 fix, 2 iterations)
...
Screen 12: recipe-rules     -> PASS (0 fixes)
--------------------------------------------------------------------
TOTAL: X/24 passed | X fixes | X iterations | X blocked | X unresolved
====================================================================

Fixes Applied:
  1. [file:line] - {root cause and fix description}

Definition Updates (if any):
  1. [screen] — Updated expected value: "{old}" -> "{new}" in adb-test-definitions.md

Unresolved Issues:
  - [screen] — {description} (3 attempts per issue or 12 total exhausted)

Blocked Screens:
  - [screen] — {reason}

Backend Health:
  - Health checks: X, Restarts: X

Regression Testing (if fixes applied):
  - Screens retested: X, Passes: X, Regressions: X

Test Suite Verification (from /post-fix-pipeline):
  - Gate: PASSED | PASSED_AFTER_FIX | FAILED | NOT_RUN

Skill Activity (from /fix-loop + /post-fix-pipeline):
  - Fix-loop invocations: X
  - Debugger invocations: X
  - Code reviews: X (Y approved, Z flagged)
  - Pipeline status: COMPLETED | BLOCKED_BY_TEST_SUITE | NOT_RUN
  - Commit: [hash] — [message]

Session logs: .claude/logs/adb-test/{session}/
Duration: X minutes Y seconds
```

### Flow Test Report (saved markdown file)

**Flow runs produce a structured markdown report** saved to `docs/testing/reports/flow{N}-{name}-{timestamp}.md`. See `references/flow-definitions.md` section G6 for the full report format with 13-column step table, phase summaries, API evidence, and skill activity.

The report file is the **primary audit artifact** for flow test runs. The console summary (G6e) is for quick reference only.

**Evidence files** (API request/response JSON) are saved to `docs/testing/reports/evidence/flow{N}-{timestamp}/`. Screenshots remain in `docs/testing/screenshots/` (gitignored).

---

## POST-RUN LEARNING CAPTURE

After producing the final report (screen or flow), automatically invoke the learning reflection:

```
Skill("reflect", args="session")
```

This captures the session outcomes into structured learning logs and updates memory topic files. The `post-skill-learning.sh` hook will also fire independently on this skill invocation, but the explicit `/reflect session` provides deeper analysis.

**Do NOT skip this step.** It runs even if all screens passed (captures success patterns too).

---

## QUICK REFERENCE

| Screen | Nav From | Backend? | Key Interactions |
|--------|---------|----------|-----------------|
| `auth-flow` | App launch | Yes | Sign-in, 5 onboarding steps |
| `home` | Post-auth | Yes | Day tabs, meal cards, lock, refresh, add, bottom nav |
| `grocery` | Bottom nav | Room | Categories, checkboxes, WhatsApp share |
| `chat` | Bottom nav | Yes (AI) | Type message, send, wait for response |
| `favorites` | Bottom nav | Room | Tabs, recipe cards (or empty state) |
| `stats` | Bottom nav | Room | Time tabs, streak, chart |
| `settings` | Profile icon | No | Toggles, sign-out, links to Pantry/Rules |
| `notifications` | Bell icon | Room | Filters, mark all read (or empty) |
| `recipe-detail` | Meal card tap | Yes | Favorite, servings, start cooking |
| `cooking-mode` | Recipe detail | No | Step navigation, complete |
| `pantry` | Settings link | Room | Add item (or empty) |
| `recipe-rules` | Settings link | Yes | Tabs, add rule, delete |


api-performance-testing - uses Locust