---
name: plan-to-issues
description: >
  Parse a markdown plan into GitHub Issues with labels and duplicate detection.
  Use when you have a numbered plan, checklist, or task breakdown and want to
  create tracked GitHub Issues from it. Supports text input or file path.
  Max 20 issues per invocation.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<plan text or file path>"
---

# Plan to Issues — Markdown Plan to GitHub Issues

Parse a markdown plan and create GitHub Issues with smart labeling and duplicate detection.

**Request:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | string/path | (required) | Markdown plan text or path to a `.md` file |
| `--dry-run` | flag | false | Show what would be created without actually creating |
| `--labels` | string | (auto) | Override auto-detected labels (comma-separated) |

---

## STEP 1: Extract Items

If input is a file path (ends in `.md`), read the file. Otherwise use the provided text directly.

Extract actionable items by matching these patterns (in priority order):

1. **Numbered lists:** `1. Description`, `2. Description`
2. **Checkboxes:** `- [ ] Description`, `- [x] Description` (skip checked items)
3. **Heading-based:** `### Title` followed by description paragraph
4. **Bullet points under a heading:** `## Section` → `- item 1`, `- item 2`

For each item, extract:
- **Title:** First line or heading (max 80 chars, truncate with `...`)
- **Body:** Remaining description, sub-items, code blocks
- **Section:** Parent heading (becomes label context)

**Max 20 items per invocation.** If more found, warn and take first 20.

---

## STEP 2: Auto-Detect Labels

Apply labels based on keyword matching in title and body:

| Keyword Pattern | Label |
|----------------|-------|
| `fix`, `bug`, `broken`, `error` | `bug` |
| `add`, `new`, `feature`, `implement` | `enhancement` |
| `test`, `e2e`, `unit test`, `verify` | `testing` |
| `android`, `compose`, `kotlin`, `screen`, `viewmodel` | `android` |
| `backend`, `api`, `endpoint`, `python`, `fastapi` | `backend` |
| `household`, `family`, `member` | `household` |
| `recipe`, `meal`, `generation` | `meal-planning` |
| `docs`, `document`, `readme` | `documentation` |
| `refactor`, `cleanup`, `optimize` | `refactoring` |
| `ci`, `deploy`, `pipeline` | `infrastructure` |

Each item gets 1-3 labels max. Always include at least one of: `bug`, `enhancement`, `testing`, `documentation`, `refactoring`.

---

## STEP 3: Duplicate Check

For each item, search existing open issues:

```bash
gh issue list --search "${KEYWORDS}" --state open --limit 3 --json number,title
```

Extract 2-3 keywords from the title for the search. If a match is found with >70% title similarity, mark as **SKIP (duplicate of #N)**.

---

## STEP 4: Create Issues (unless --dry-run)

For each non-duplicate item:

```bash
gh issue create \
  --title "${TITLE}" \
  --body "$(cat <<'EOF'
## Description

${BODY}

## Source

Extracted from plan: ${SOURCE_REFERENCE}

---
*Created by /plan-to-issues*
EOF
)" \
  --label "${LABELS}"
```

Pause 1 second between creations to avoid rate limiting.

---

## STEP 5: Report

```
Plan to Issues Report
=====================

Source: {file path or "inline text"}
Items found: N
Created: N
Skipped (duplicate): N
Skipped (checked): N

Created Issues:
  #XX  [enhancement,android]  Add logout button to settings
  #XX  [bug,backend]          Fix 500 error on recipe search
  #XX  [testing]              Add E2E test for grocery flow

Skipped (duplicates):
  "Fix auth error" -> duplicate of #45
  "Update docs" -> duplicate of #38

{If --dry-run: "DRY RUN — no issues were created"}
```

---

## CRITICAL NOTES

- Max 20 issues per invocation to prevent accidental spam
- Always run duplicate check before creating
- Use `--dry-run` first to preview what will be created
- Labels must exist in the repo — if a label doesn't exist, `gh` will error. Stick to known labels: `bug`, `enhancement`, `testing`, `android`, `backend`, `household`, `documentation`
- Items from checked checkboxes (`- [x]`) are skipped (already done)
