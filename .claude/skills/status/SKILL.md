---
name: status
description: >
  Quick project health snapshot. Shows git status, test status, and project state
  in a single report. Use when starting a session or checking project health.
allowed-tools: "Bash Read Grep Glob"
argument-hint: ""
---

# Status — Project Health Snapshot

Quick overview of project state.

---

## Gather Information

Run these checks in parallel where possible:

### 1. Git State
```bash
git branch --show-current
git status --short
git log --oneline -3
git stash list
```

### 2. Uncommitted Changes
```bash
git diff --stat
```

### 3. Open PRs/Issues (if gh available)
```bash
gh pr list --state open --limit 3 2>/dev/null || echo "gh not available"
gh issue list --assignee @me --state open --limit 3 2>/dev/null || echo ""
```

### 4. Recent Test Results
Check for recent test output files or run a quick test count:
- Look for test result artifacts in common locations
- Optionally run `--collect-only` to count available tests

## Report

```markdown
## Project Status

### Git
- Branch: [current branch]
- Uncommitted: [N files changed]
- Last 3 commits: [summaries]

### Tests
- [Latest test result summary if available]

### Open Work
- PRs: [count and titles]
- Issues: [assigned issues]

### Health: [GOOD / NEEDS_ATTENTION / BLOCKED]
[One-line explanation]
```
