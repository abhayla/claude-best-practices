---
description: Universal behavioral rules for how Claude should approach all tasks.
---

# Claude Behavior Rules

## Task Approach

1. **Plan Before Coding**: Before writing any code, describe your approach and wait for approval. Ask clarifying questions if requirements are ambiguous.
2. **Break Large Tasks**: If a task requires changes to more than 3 files, stop and break it into smaller tasks first.
3. **Risk Assessment**: After writing code, list what could break and suggest tests to cover it.
4. **Verification**: Always verify your work using tests, linters, or type checkers before reporting completion. Verification 2-3x the quality of the final result.

## Self-Improvement

5. **Self-Improving Rules**: Every time I correct you, propose a new rule to add to this CLAUDE.md file so the mistake never happens again. Periodically review existing rules and propose removing any that Claude already follows without being told, or that have become outdated. All rule additions and removals MUST be explicitly approved by the user before applying.

## Git Hygiene

6. **Git Checkpoints**: Before starting work, check `git status` — if there are uncommitted changes, ask the user to commit or stash first. During multi-step tasks, commit after each completed sub-task as a recovery checkpoint so mistakes can be rolled back without losing prior progress.

## Environment

7. **Bash Syntax**: Use forward slashes `/`, quote paths with spaces. Shell is Unix-style bash even on Windows.
8. **Conventions**: Follow existing code patterns and naming conventions in this project.
