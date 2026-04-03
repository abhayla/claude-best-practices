---
name: plan-to-issues
description: >
  Parse a markdown plan into GitHub Issues with labels and duplicate detection.
  Supports text input or file path. Use when converting a structured plan into
  tracked GitHub Issues.
triggers:
  - convert plan to issues
  - create github issues from plan
  - plan to github issues
  - parse plan into issues
  - markdown plan to issues
  - bulk create issues from plan
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<plan-file-path or plan text>"
version: "1.2.0"
type: workflow
---

# Plan to Issues

**Critical:** Requires `gh` CLI authenticated with repo access. If `$ARGUMENTS` is empty, prompt the user for a plan file path or inline text. NOT for creating plans (use /writing-plans) or executing plans (use /executing-plans).

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

## STEP 3: Organize into Epics (if applicable)

If the plan has logical groupings (sections, atomic plans, milestones), organize issues into epics.

### 3.1 Detect Epic Structure

Look for groupings in the plan:
- Top-level headings (`## Feature Area`) → each heading becomes an epic
- Atomic plan groups (`## Atomic Plan 1: <title>`) → each group becomes an epic
- Milestone markers (`## M1: MVP`) → each milestone becomes an epic
- PRD user story groups → each user story becomes an epic

### 3.2 Create Milestone (if milestones detected)

```bash
# Create milestones for each phase/milestone in the plan
gh api repos/:owner/:repo/milestones -f title="M1: MVP" -f description="Core features" -f due_on="2026-04-01T00:00:00Z"
```

### 3.3 Create Epic Issues

For each epic, create a tracking issue that references its child tasks:

```bash
gh issue create --title "Epic: <group title>" --label "epic" --milestone "<milestone>" --body "$(cat <<'EOF'
## <Group Title>

### Tasks
- [ ] #<child-issue-1> — <title>
- [ ] #<child-issue-2> — <title>
- [ ] #<child-issue-3> — <title>

### Acceptance Criteria
<from PRD if available>

### Dependencies
<cross-epic dependencies if any>
EOF
)"
```

### 3.4 Skip Epics When

- Plan has fewer than 5 tasks (flat list is fine)
- Plan has no logical groupings
- User explicitly requests flat issues

## STEP 4: Create Task Issues

For each non-duplicate item (max 20):

```bash
gh issue create --title "Title" --body "Description" --label "label" --milestone "<milestone>"
```

If epics were created, add a reference to the parent epic in each task's body:
```
**Epic:** #<epic-issue-number>
```

After creating all tasks, update the epic issue body with the actual issue numbers.

## STEP 5: Report

```
Created N issues:
  Epics: E
    Epic #100 — "User Registration" (M1: MVP) [3 tasks]
    Epic #101 — "Email Verification" (M1: MVP) [2 tasks]

  Tasks: T
    #102 — Title 1 [label] → Epic #100
    #103 — Title 2 [label] → Epic #100
    #104 — Title 3 [label] → Epic #100
    #105 — Title 4 [label] → Epic #101
    #106 — Title 5 [label] → Epic #101

  Milestones: M
    M1: MVP (5 tasks across 2 epics)

Skipped D duplicates:
  - "Title" (matches #99)
```

---

## CRITICAL RULES

### MUST DO
- Always validate `$ARGUMENTS` is non-empty before proceeding — Why: empty input produces no issues and wastes API calls on duplicate checks
- Always check for duplicates via `gh issue list` before creating — Why: duplicate issues create confusion and tracking overhead
- Always preserve the original plan's ordering in issue creation — Why: issue numbers should reflect the plan's priority/sequence
- Always link tasks back to their parent epic with actual issue numbers — Why: orphaned tasks without epic references break traceability
- Always cap at 20 issues per invocation — Why: bulk creation beyond 20 overwhelms reviewers and risks rate limiting

### MUST NOT DO
- MUST NOT create issues without `gh` CLI access — verify authentication first
- MUST NOT create epics for plans with fewer than 5 tasks — use flat issue list instead
- MUST NOT skip duplicate detection even for small plans — Why: duplicate issues accumulate as technical debt
- MUST NOT create issues with titles longer than 80 characters — Why: GitHub truncates long titles in list views
