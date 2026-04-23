# Visual Proof Review (auto-verify STEP 2.5)

Detailed implementation of `/auto-verify`'s STEP 2.5. Kept as a reference file
(not in SKILL.md) per `pattern-self-containment.md` size limits — the SKILL.md
retains the canonical invocation contract and points here for the sub-step
details.

**When this runs:** After STEP 2 (Execute Tests). MANDATORY for UI tests;
skipped for non-UI tests unless `--capture-proof` is enabled.

**Output:** Writes `test-evidence/{run_id}/visual-review.json` and influences
STEP 3's verdict via overrides.

---

## 2.5.1 Read Manifest

```bash
MANIFEST="test-evidence/${RUN_ID}/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "No screenshot manifest found — skipping visual review"
  # Set visual_review.enabled = false in structured output, proceed to STEP 3
fi
```

If the manifest exists but has zero screenshots (`screenshot_count: 0` or
empty `screenshots` array), this is normal for non-UI projects (API servers,
CLI tools, libraries). Handle gracefully:

```bash
SCREENSHOT_COUNT=$(python3 -c "import json; print(json.load(open('$MANIFEST')).get('screenshot_count', 0))")
if [ "$SCREENSHOT_COUNT" = "0" ]; then
  echo "Manifest found but 0 screenshots (non-UI project) — skipping visual review"
  # Write visual-review.json with result: PASSED, screenshots_reviewed: 0
  # Proceed to STEP 3
fi
```

Parse the manifest to get the list of all screenshots with their test names,
results, and file paths.

## 2.5.2 Review All Screenshots

For EVERY screenshot in the manifest (100% review rate):

1. **Read the screenshot** using multimodal Read (the image file)
2. **Evaluate** against these criteria (from `/verify-screenshots` Step 2):
   - No error dialogs, crash screens, or unhandled exception modals
   - Text is readable and not truncated
   - Layout appears correct (no overlapping elements)
   - Loading states are resolved (no spinners in final screenshots)
   - Data containers are populated (tables have rows, lists have items)
   - No empty-state placeholders when data is expected
   - No placeholder text ("Lorem ipsum", "undefined", "null", "NaN")
   - Timestamps/dates are within expected recency

3. **Classify** each screenshot:

**UI tests (verdict_source: "screenshot")** — tester-agent already set the
verdict from screenshot. This pass confirms or catches edge cases:

| Tester Verdict | Confirmation Review | Action |
|----------------|-------------------|--------|
| PASSED | Confirms correct | No action — verdict stands |
| PASSED | Spots missed issue | OVERRIDE → FAILED (add to overrides) |
| FAILED | Confirms failure | No action — verdict stands |
| FAILED | Looks actually correct | FLAG for review (possible AI triage error) |

**Non-UI tests (verdict_source: "exit_code")** — screenshot is supplementary:

| Exit Code | Visual Assessment | Verdict | Action |
|-----------|-------------------|---------|--------|
| PASSED | Looks correct | CONFIRMED | No action |
| PASSED | Shows problems | OVERRIDE → FAILED | Add to overrides list |
| FAILED | Shows the failure | CONFIRMED | Enrich failure diagnosis |
| FAILED | Looks correct | FLAG for review | Possible flaky/timing issue |

## 2.5.3 Write Visual Review Results

Write `test-evidence/{run_id}/visual-review.json`:

```json
{
  "skill": "visual-proof-review",
  "run_id": "{run_id}",
  "timestamp": "{ISO-8601}",
  "screenshots_reviewed": 50,
  "screenshots_total": 50,
  "confirmed_passes": 43,
  "confirmed_failures": 5,
  "overrides": [
    {
      "test": "test_dashboard_loads",
      "original_result": "PASSED",
      "visual_verdict": "FAILED",
      "reason": "Dashboard shows empty table — no data rows visible despite test asserting element presence",
      "screenshot": "screenshots/test_dashboard_loads.pass.png"
    }
  ],
  "flags": [
    {
      "test": "test_login_timeout",
      "original_result": "FAILED",
      "visual_observation": "Screenshot shows successful login page — possible timing/flaky issue",
      "screenshot": "screenshots/test_login_timeout.fail.png"
    }
  ],
  "result": "PASSED|FAILED"
}
```

`result` is FAILED if ANY overrides exist (a passed test was visually broken).
`result` is PASSED if zero overrides (all passes confirmed, all failures confirmed).

## 2.5.4 Gate Impact

If visual review `result` is FAILED:
- Report each override with the reason and screenshot path
- The override failures are added to the main failure list in STEP 3
- These count as real failures for the auto-verify verdict

If visual review `result` is PASSED:
- Log: "Visual proof review: {N} screenshots confirmed, 0 overrides"
- Proceed normally
