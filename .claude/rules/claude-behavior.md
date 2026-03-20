---
description: Universal behavioral rules for how Claude should approach all tasks.
globs: ["**/*"]
---
# Scope: global

# Claude Behavior Rules

## Task Approach

1. **Plan Before Coding**: Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). Write detailed specs upfront to reduce ambiguity. Use plan mode for verification steps, not just building. If an approach goes sideways, STOP and re-plan immediately instead of pushing forward.
2. **Break Large Tasks**: If a task requires changes to more than 3 files, stop and break it into smaller tasks first.
3. **Risk Assessment**: After writing code, list what could break and suggest tests to cover it.
4. **Verification**: Always verify your work using tests, linters, or type checkers before reporting completion. Check logs and demonstrate correctness. Diff behavior between main and your changes when relevant. Ask yourself: "Would a staff engineer approve this?" Never mark a task complete without proving it works.

## Self-Improvement

5. **Self-Improving Rules**: Every time I correct you, propose a new rule to add to this CLAUDE.md file so the mistake never happens again. Also update `.claude/tasks/lessons.md` with the pattern so lessons persist across sessions. Periodically review existing rules and propose removing any that Claude already follows without being told, or that have become outdated. All rule additions and removals MUST be explicitly approved by the user before applying. Review lessons at session start for the relevant project. Ruthlessly iterate on lessons until mistake rate drops.

## Git Hygiene

6. **Git Checkpoints**: Before starting work, check `git status` — if there are uncommitted changes, ask the user to commit or stash first. During multi-step tasks, commit after each completed sub-task as a recovery checkpoint so mistakes can be rolled back without losing prior progress.

## Code Comments

7. **No Redundant Comments**: NEVER add comments that restate what the code already says (e.g., `// Initialize the variable`, `# Loop through items`, `// Import dependencies`). Only add comments where the logic is non-obvious — explain *why*, not *what*. Do not add docstrings, type annotations, or comments to code you did not change.

## File Structure

8. **No Catch-All Files**: NEVER create files named `utils`, `helpers`, `common`, `misc`, or `shared` (any extension). These become dumping grounds that grow unbounded and violate single responsibility. Instead, name files after what they do: `string-formatting.ts` instead of `utils.ts`, `date-calculations.py` instead of `helpers.py`. If a utility is used by only one module, put it in that module.
9. **Keep Files Focused**: Each file should have a single clear purpose. When a file grows beyond ~300 lines, consider whether it's doing too many things and should be split. Exceptions: generated code, test fixtures, migrations, and configuration files.

## Environment

10. **Bash Syntax**: Use forward slashes `/`, quote paths with spaces. Shell is Unix-style bash even on Windows.
11. **Conventions**: Follow existing code patterns and naming conventions in this project.

## Code Quality

12. **Demand Elegance (Balanced)**: For non-trivial changes, pause and ask "is there a more elegant way?" If a fix feels hacky: "Knowing everything I know now, implement the elegant solution." Skip this for simple, obvious fixes — don't over-engineer. Challenge your own work before presenting it.
13. **Autonomous Bug Fixing**: When given a bug report, just fix it — don't ask for hand-holding. Point at logs, errors, failing tests — then resolve them. Zero context switching required from the user. Go fix failing CI tests without being told how.

## Task Management

14. **Task Tracking**: (1) Write plan to `.claude/tasks/todo.md` with checkable items before starting. (2) Check in with user before starting implementation. (3) Mark items complete as you go. (4) Provide high-level summary at each step. (5) Add review section to `.claude/tasks/todo.md` when done. (6) Update `.claude/tasks/lessons.md` after corrections.

## Core Principles

15. **Simplicity First**: Make every change as simple as possible. Impact minimal code.
16. **No Laziness**: Find root causes. No temporary fixes. Never apply band-aid solutions when the underlying issue can be identified and fixed properly.
17. **Senior Developer Standards**: Hold all output to the bar of a senior developer. Code, explanations, and decisions should reflect depth of understanding, not just surface-level correctness.
