---
name: plan-to-issues
description: >
  Parse a markdown plan into GitHub Issues with labels and duplicate detection.
  Supports text input or file path. Max 20 issues per invocation.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<plan-file-path or plan text>"
---

# Plan to Issues

Parse a structured plan into tracked GitHub Issues.

**Input:** $ARGUMENTS

---

## STEP 1: Parse Plan

Accept input as either:
- A file path → read the file
- Inline text → parse directly

Extract actionable items from:
- Numbered lists (`1. Do something`)
- Checkboxes (`- [ ] Do something`)
- Headings with sub-items

For each item, extract:
- Title (concise, under 80 chars)
- Description (details from sub-items or context)
- Labels (auto-detect: `bug`, `feature`, `enhancement`, `docs`, `test`, `refactor`)

## STEP 2: Check for Duplicates

```bash
gh issue list --limit 100 --json title,number --jq '.[].title'
```

Compare each proposed issue title against existing issues. Skip duplicates.

## STEP 3: Create Issues

For each non-duplicate item (max 20):

```bash
gh issue create --title "Title" --body "Description" --label "label"
```

## STEP 4: Report

```
Created N issues:
  #101 — Title 1 [label]
  #102 — Title 2 [label]

Skipped M duplicates:
  - "Title" (matches #99)
```

---

## RULES

- Maximum 20 issues per invocation
- Auto-detect labels from content keywords
- Always check for duplicates before creating
- Preserve the original plan's ordering
