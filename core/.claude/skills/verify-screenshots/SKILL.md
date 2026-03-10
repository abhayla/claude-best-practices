---
name: verify-screenshots
description: >
  Deep screenshot and backend API verification. Validates file integrity, analyzes
  visual content (multimodal Read), compares before/after screenshots, performs ADB
  structural checks (uiautomator dump), verifies backend state via API calls.
  Use after capturing screenshots to confirm visual changes and backend consistency.
allowed-tools: "Bash Read Grep"
---

# Verify Screenshots

Deep screenshot validation and backend API verification for the current workflow session.

**Arguments:** $ARGUMENTS

---

## Overview

This skill performs 6 validation steps on screenshots captured during Step 6 of the workflow, plus optional backend API verification. It sets `visualIssuesPending` if critical issues are found, blocking further progress until resolved.

---

## STEP 0: Load State

```bash
python -c "
import json
with open('.claude/workflow-state.json') as f:
    d = json.load(f)
sc = d.get('screenshotsCaptured', [])
bc = d.get('backendChecks', [])
s6 = d.get('steps', {}).get('step6_screenshots', {})
print(f'Screenshots captured: {len(sc)}')
for s in sc:
    print(f'  - {s[\"path\"]} (type={s[\"type\"]}, valid={s[\"validated\"]}, size={s[\"fileSize\"]})')
print(f'Backend checks: {len(bc)}')
for b in bc:
    print(f'  - {b[\"method\"]} {b[\"endpoint\"]} -> expect: {b[\"expect\"]}')
print(f'Before: {s6.get(\"before\", \"not set\")}')
print(f'After: {s6.get(\"after\", \"not set\")}')
"
```

If no screenshots are recorded:
- Check `docs/testing/screenshots/` for recently created files
- If found, manually record them and continue
- If none found, report error and exit

---

## STEP 1: File Validation

For each screenshot in `screenshotsCaptured[]`:
1. Verify the file exists on disk
2. Check file size is > 100 bytes (not empty/corrupt)
3. Verify file extension is `.png` or `.jpg`/`.jpeg`

Record findings:
- PASS: File exists, valid size, correct format
- FAIL: File missing, too small, or wrong format

If ANY file validation fails — flag as **critical** issue.

---

## STEP 2: Content Analysis (Visual)

For each valid screenshot file:
1. **Read the screenshot image** using the Read tool (Claude is multimodal)
2. Analyze the image content for these issues:

| Issue | Severity | Detection |
|-------|----------|-----------|
| Error dialog/toast visible | critical | Red/orange error messages, "Error", "Failed", crash dialogs |
| Blank/empty screen | critical | Completely white/black screen with no content |
| Stuck loading spinner | warning | Loading indicator visible with no content loaded |
| Broken layout | warning | Overlapping elements, cut-off text, misaligned components |
| Missing images/icons | warning | Placeholder icons, broken image indicators |
| Unexpected screen | warning | Wrong screen displayed (e.g., login when expecting home) |
| Normal UI with expected content | info | Feature appears to be working correctly |

Record each finding with:
- Screenshot path
- Issue type
- Severity (critical/warning/info)
- Description

---

## STEP 3: Before/After Comparison

If both `before` and `after` screenshots exist:
1. Read both screenshots using the Read tool
2. Compare them visually:
   - **Identical?** — Flag as **warning** ("Feature change may not be visible in UI")
   - **Different?** — Describe the visible differences
   - **Regression?** — Check if the "after" screenshot shows degraded UI compared to "before"
   - **Expected change visible?** — Does the difference match what the feature should look like?

If only one screenshot exists:
- Flag as **warning** ("Missing before/after pair — cannot compare")

---

## STEP 4: Structural UI Verification (Android only)

Attempt Android UI hierarchy check:

```bash
# Try to dump UI hierarchy
adb shell uiautomator dump /sdcard/window_dump.xml 2>/dev/null
adb pull /sdcard/window_dump.xml docs/testing/screenshots/ui_dump.xml 2>/dev/null
```

If ADB is available and dump succeeds:
1. Read the XML file
2. Check for:
   - Error/crash dialog elements (`android.app.AlertDialog`, text containing "error", "crash", "unfortunately")
   - Expected UI elements for the feature (by resource-id or content-desc)
   - Missing key elements that should be present

If ADB is unavailable:
- Log `"ADB unavailable — skipping structural verification"`
- Continue to next step (non-blocking)

---

## STEP 5: Backend API Verification

If `backendChecks[]` is non-empty in workflow state:

For each check:
1. Execute the API call:
   ```bash
   # Get auth token from workflow state or use test token
   curl -s -X {method} "http://localhost:8000{endpoint}" \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json"
   ```
2. Validate:
   - HTTP status code matches expected (default: 200)
   - Response body contains expected fields
   - No error responses

Record results:
- PASS: Status and body match expectations
- FAIL: Unexpected status or missing expected fields

If `backendChecks[]` is empty:
- Log `"No backend checks defined — skipping"`
- This is normal for UI-only changes

---

## STEP 6: Set Flags & Record Results

### Determine Overall Result

```
PASSED — No critical issues found (warnings are OK)
ISSUES_FOUND — One or more critical issues detected
```

### Update Workflow State

```bash
python -c "
import json, os, tempfile
from datetime import datetime

sf = '.claude/workflow-state.json'
with open(sf) as f:
    d = json.load(f)

# Update step6_screenshots
s6 = d.get('steps', {}).get('step6_screenshots', {})
s6['validated'] = True
s6['validationResult'] = '{RESULT}'  # PASSED or ISSUES_FOUND
d['steps']['step6_screenshots'] = s6

# Update skillInvocations
si = d.get('skillInvocations', {})
si['verifyScreenshotsInvoked'] = True
si['verifyScreenshotsResult'] = '{RESULT}'

# Update step7_verify backend checks result
s7 = d.get('steps', {}).get('step7_verify', {})
s7['backendChecksResult'] = '{BACKEND_RESULT}'  # PASSED/FAILED/SKIPPED
d['steps']['step7_verify'] = s7

# Set visual issues flag if critical issues found
if '{RESULT}' == 'ISSUES_FOUND':
    d['visualIssuesPending'] = True
    d['visualIssuePendingDetails'] = '{DETAILS}'
elif '{RESULT}' == 'PASSED':
    # Clear flag if re-running after fix
    d['visualIssuesPending'] = False
    d['visualIssuePendingDetails'] = None

fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, sf)
"
```

### Write Evidence File

Write validation evidence to `.claude/logs/test-evidence/screenshot-validation-{timestamp}.json`:

```json
{
  "timestamp": "ISO8601",
  "overallResult": "PASSED|ISSUES_FOUND",
  "screenshotsAnalyzed": N,
  "findings": [
    {
      "screenshot": "path",
      "issue": "description",
      "severity": "critical|warning|info"
    }
  ],
  "beforeAfterComparison": {
    "identical": false,
    "differences": "description",
    "regressionDetected": false
  },
  "structuralCheck": {
    "performed": true,
    "errorDialogsFound": false,
    "expectedElementsPresent": true
  },
  "backendChecks": {
    "performed": true,
    "results": [
      {"endpoint": "...", "status": "PASS|FAIL", "details": "..."}
    ]
  }
}
```

---

## Output

```markdown
## Screenshot Verification Results

### Overall: {PASSED | ISSUES_FOUND}

### File Validation
- {path}: {PASS/FAIL} ({size} bytes)

### Content Analysis
- {path}: {severity} — {description}

### Before/After Comparison
- {Identical / Different: description / Missing pair}

### Structural UI Check
- {Performed / Skipped (ADB unavailable)}
- {Findings or "No issues"}

### Backend API Checks
- {endpoint}: {PASS/FAIL} — {details}
- (or "No backend checks defined")

### Evidence
- File: .claude/logs/test-evidence/screenshot-validation-{timestamp}.json

### Next Steps
- If PASSED: Proceed to /post-fix-pipeline
- If ISSUES_FOUND: Invoke /fix-loop with clear_flags=["visualIssuesPending"]
```

---

## Re-run Behavior

When invoked again after a fix-loop:
- Re-reads screenshots from workflow state
- If new screenshots were captured, validates those
- If PASSED on re-run, clears `visualIssuesPending` flag
- Evidence is written with new timestamp (preserving prior evidence)
