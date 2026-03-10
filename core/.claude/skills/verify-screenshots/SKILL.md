---
name: verify-screenshots
description: >
  Verify screenshot files and visual content. Validates files exist, uses multimodal
  Read for content analysis, compares before/after screenshots. Use after capturing
  screenshots to confirm visual changes are correct.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<screenshot-path or directory>"
---

# Verify Screenshots — Visual Content Validation

Validate screenshot files and analyze their content.

**Target:** $ARGUMENTS

---

## STEP 1: File Validation

Verify the target screenshots exist and are valid:

```bash
ls -la $TARGET_PATH
file $TARGET_PATH  # Check file type
```

Ensure files are:
- Non-zero size
- Valid image format (PNG, JPG, etc.)
- Recently created/modified

## STEP 2: Content Analysis

Use multimodal Read to analyze each screenshot:

1. Read the image file to view its contents
2. Check for:
   - Expected UI elements are visible
   - No error dialogs or crash screens
   - Text is readable and not truncated
   - Layout appears correct (no overlapping elements)
   - Loading states are resolved (no spinners in final screenshots)

## STEP 3: Before/After Comparison (if applicable)

If both before and after screenshots are provided:

1. Read both images
2. Compare:
   - What changed between them
   - Whether the change matches expectations
   - No unintended side effects visible

## STEP 4: Report

```
Screenshot Verification:
  Files checked: N
  Valid: Y
  Issues found: Z

  Per-file results:
  - [filename]: PASS — [brief description of content]
  - [filename]: FAIL — [issue description]
```

---

## RULES

- Always validate file existence before attempting to read
- Report specific issues, not just pass/fail
- If screenshots show errors or crashes, flag as critical
- Compare against expected state if provided in arguments
