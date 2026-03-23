---
name: status
description: >
  Generate a project health snapshot showing git status, test status, and project
  state in a single report. Use when starting a session or checking project health.
allowed-tools: "Bash Read Grep Glob"
argument-hint: ""
version: "1.0.1"
type: reference
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
- Optionally run `--collect-only` to count available tests without executing them
- Check CI status via `gh run list --limit 1` if GitHub CLI is available

## Health Criteria

Assess overall project health based on these signals:
- **GOOD**: Clean git state, tests passing, no stale PRs
- **NEEDS_ATTENTION**: Uncommitted changes, open PRs older than 3 days, or test warnings
- **BLOCKED**: Failing tests, merge conflicts, or CI failures on the current branch
- Check CI status via `gh run list --limit 1` if GitHub CLI is available## Health CriteriaAssess overall project health based on these signals:- **GOOD**: Clean git state, tests passing, no stale PRs- **NEEDS_ATTENTION**: Uncommitted changes, open PRs older than 3 days, or test warnings- **BLOCKED**: Failing tests, merge conflicts, or CI failures on the current branch

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
