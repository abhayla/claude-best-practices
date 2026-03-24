# STEP N: Action Verb + Object

### N.1 Sub-step Title

1. Specific instruction with concrete action
2. Another specific instruction
3. Expected outcome or decision point

### N.2 Another Sub-step

| Situation | Action |
|-----------|--------|
| Happy path | Do X |
| Error case | Do Y instead |
| Edge case | Ask user for clarification |
```

#### Recommended Step Count

| Skill Type | Steps | Reasoning |
|------------|-------|-----------|
| Simple workflow | 3-5 | Focused task, minimal branching |
| Standard workflow | 5-8 | Most skills fall here |
| Complex workflow | 8-10 | Multi-phase with verification |
| Too many | >10 | Split into multiple skills or use subagent delegation |

### 2.4 Add Tables for Decision Logic

When a step has conditional behavior, use a table instead of nested if-else prose:

```markdown
| Condition | Action | Next Step |
|-----------|--------|-----------|
| All tests pass | Report success | Step 6 |
| 1-2 tests fail | Attempt auto-fix | Step 5 |
| >2 tests fail | Escalate to user | STOP |
| Build error | Check dependencies first | Step 4.2 |
```

Tables are faster for Claude to parse than nested bullet points and reduce errors in conditional logic.

### 2.5 Add Code Block Templates

When a step produces output or requires specific formatting, include a template:

```markdown
Output the results in this format:
\```
Analysis Results:
  Files scanned: {count}
  Issues found: {count}
  Severity breakdown:
    Critical: {n}
    Warning: {n}
    Info: {n}
\```
```

### 2.6 Write MUST DO / MUST NOT DO Sections

Every skill ends with explicit behavioral boundaries. These are the guardrails that prevent the skill from going off-track.

```markdown
