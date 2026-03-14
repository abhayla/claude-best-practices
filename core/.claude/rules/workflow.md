---
description: Development workflow guidelines for structured feature implementation and bug fixes.
globs: ["**/*"]
---
# Scope: global

# Workflow Guidelines

## 7-Step Development Workflow

When implementing features or fixing bugs, follow this structured approach:

### Step 1: Understand Requirements
- Read the issue/request thoroughly
- Identify affected components and files
- Check existing tests and documentation in the area

### Step 2: Write Tests First
- Create or update tests that define expected behavior
- Tests should fail before implementation (TDD)
- Follow existing test patterns in the project

### Step 3: Implement
- Make minimal, focused changes
- Follow existing code conventions
- Keep changes reversible where possible

### Step 4: Run Tests
- Run targeted tests for the changed area
- Fix failures before proceeding

### Step 5: Fix Loop
- If tests fail, iterate: analyze → fix → retest
- Maximum 5 iterations before escalating
- Each iteration must try a different approach

### Step 6: Verify
- Run broader test suite for regression check
- Review changes for unintended side effects
- Capture evidence (screenshots, test output) if applicable

### Step 7: Commit & Document
- Write clear commit messages (conventional format)
- Update documentation if behavior changed
- Record learnings for future reference

## Key Principles

1. **Test before commit** — Never commit code that fails existing tests
2. **Minimal changes** — Change only what's needed for the task
3. **Evidence-based** — Verify with tests, not assumptions
4. **Reversible** — Prefer changes that can be easily undone
5. **Documented** — Leave breadcrumbs for the next developer (or session)

## When to Skip Steps

- **Trivial changes** (typos, comments): Steps 1-3 sufficient
- **Documentation only**: Skip testing steps
- **Emergency hotfixes**: Implement, test, commit — document after
