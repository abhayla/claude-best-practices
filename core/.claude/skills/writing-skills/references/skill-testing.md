# STEP 6: Skill Testing

### 6.1 Define Test Scenarios

Create three scenarios for every skill:

#### Happy Path Test

```
Scenario: Standard use case
  Input: <typical argument the user would provide>
  Expected behavior:
    - Step 1 completes: <specific observable outcome>
    - Step 2 completes: <specific observable outcome>
    - ...
    - Final output: <what the user sees>
  Success criteria: <measurable result>
```

#### Edge Case Test

```
Scenario: Unusual but valid input
  Input: <edge case argument — empty string, very long input, special characters>
  Expected behavior:
    - Skill handles gracefully without crashing
    - User receives clear feedback if input is invalid
  Success criteria: <no errors, appropriate fallback behavior>
```

#### Error Case Test

```
Scenario: Invalid input or failed prerequisite
  Input: <missing argument, wrong format, or broken environment>
  Expected behavior:
    - Skill detects the problem in Step 1 or Step 2
    - User receives actionable error message
    - Skill does NOT proceed with partial/broken state
  Success criteria: <clear error message, no side effects>
```

### 6.2 Manual Testing Procedure

To test a skill after creation:

1. Open a new Claude Code session (fresh context)
2. Invoke the skill with each test scenario input
3. Verify each step produces the expected outcome
4. Check that MUST DO rules are followed
5. Deliberately trigger a MUST NOT DO rule and verify it is respected
6. Test with both slash command triggers and natural language triggers

### 6.3 Regression Indicators

After the skill is in use, watch for these signs it needs revision:

| Signal | Meaning | Action |
|--------|---------|--------|
| Users rephrase and re-invoke | Triggers are too narrow | Add more natural language triggers |
| Skill activates for unrelated requests | Triggers are too broad | Make triggers more specific |
| Users skip steps manually | Steps are unnecessary or in wrong order | Restructure |
| Users always modify the output | Output format does not match needs | Update templates |
| Errors in later steps | Earlier steps missed validation | Add prerequisite checks |

---

