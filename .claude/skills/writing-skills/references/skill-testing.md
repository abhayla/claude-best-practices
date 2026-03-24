# STEP 6: Skill Testing

### 6.1 Define Test Scenarios

Create 5 scenarios for every skill: 3 happy-path + 2 edge-case.

#### Happy Path Tests (3 required)

```
Scenario 1: Standard use case
  Input: <typical argument the user would provide>
  Expected behavior:
    - Step 1 completes: <specific observable outcome>
    - Step 2 completes: <specific observable outcome>
    - ...
    - Final output: <what the user sees>
  Success criteria: <measurable result>

Scenario 2: Alternate valid input
  Input: <different but valid argument — tests a secondary path>
  Success criteria: <correct output for this variation>

Scenario 3: Minimal valid input
  Input: <the simplest valid argument — tests the base case>
  Success criteria: <correct output, no unnecessary steps triggered>
```

#### Edge Case Tests (2 required)

Test against these categories — pick the 2 most relevant to the skill's domain:

| Category | Example Input | What It Tests |
|---|---|---|
| Empty/missing input | `""`, no argument, null | Graceful handling of absent data |
| Boundary values | Very long string, max-size file, 0, -1 | Limits and overflow behavior |
| Special characters | Paths with spaces, unicode, `../` | Injection and encoding resilience |
| Conflicting state | File already exists, resource locked, stale cache | Idempotency and conflict resolution |
| Interrupted execution | Network timeout, missing dependency, permission denied | Partial failure and cleanup behavior |
| Concurrent invocation | Skill invoked twice on same target | Race conditions and state corruption |

```
Edge Case 1: <chosen category>
  Input: <specific edge case argument>
  Expected behavior:
    - Skill handles gracefully without crashing
    - User receives clear feedback if input is invalid
    - No partial/corrupted state left behind
  Success criteria: <no errors, appropriate fallback behavior>

Edge Case 2: <chosen category>
  Input: <specific edge case argument>
  Expected behavior:
    - <describe expected graceful handling>
  Success criteria: <measurable result>
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

### 6.3 Stress Testing (Pre-Promotion Gate)

Before promoting a skill to the hub, stress test it with adversarial inputs designed to break it. This goes beyond the 5 validation scenarios — the goal is to find where the skill **fails or degrades**, not confirm it works.

#### Invoking the Stress Test

Use this prompt to run the stress test. The `<role>` tag sets an adversarial mindset — Claude will actively try to break the skill rather than validate it.

```markdown
<role>
Act as a Claude skill QA engineer who breaks prompts on purpose
to find every hidden failure point.
</role>

<task>
Take the skill at `[path/to/SKILL.md]` and deliberately test it
against inputs designed to make it fail.
</task>

<steps>
1. Read the target skill and identify its input types, steps, and constraints
2. Generate 10 adversarial inputs from the categories below — pick the
   ones most realistic for this skill's domain
3. Run each input against the skill and document exactly where it breaks
   or degrades — which step fails, what output is wrong, what state is left
4. Score each failure by severity (CRITICAL / MAJOR / MINOR / PASS)
5. Deliver the ranked stress test report BEFORE suggesting any fixes
</steps>

<rules>
- Stress test first — never assume a skill is production-ready without breaking it
- Adversarial inputs MUST be realistic — inputs a real user might plausibly provide,
  not absurd edge cases that will never occur
- Every failure MUST be scored, not just listed — severity determines fix priority
- Report findings BEFORE touching the skill — diagnose before prescribing
</rules>

<output>
Adversarial Input Set → Failure Log → Severity Rankings → Stress Test Score
</output>
```

#### Adversarial Input Categories

Generate 10 inputs from these categories — prioritize the ones most realistic for the skill's domain:

| # | Category | Example Input | What It Exposes |
|---|---|---|---|
| 1 | Ambiguous request | Input that could trigger 2+ different steps | Routing/classification failures |
| 2 | Off-topic query | Valid request but outside skill's scope | Missing scope guard — skill proceeds when it should reject |
| 3 | Conflicting constraints | Input with contradictory requirements | Silent data loss or arbitrary tiebreaking |
| 4 | Oversized input | Very long argument, huge file, 100+ items | Truncation, timeout, or degraded output quality |
| 5 | Minimal/empty input | `""`, whitespace-only, no argument | Crash or proceeding with null data |
| 6 | Partial prerequisite | One of N required files exists, others missing | Partial execution leaving broken state |
| 7 | Repeated invocation | Run the skill twice on the same target | Duplicate output, state corruption, or overwrite |
| 8 | Malformed format | Wrong file type, invalid JSON, typos in flags | Unhelpful error or silent wrong behavior |
| 9 | Stale context | Outdated input that no longer matches current state | Acting on stale data without detecting drift |
| 10 | Adversarial phrasing | Same intent worded to confuse trigger matching | Trigger misfire or skill not activating |

#### Failure Log Format

For each adversarial input, document the result:

```
Adversarial Input #N: <category> — <specific input>
  Step where failure occurred: <Step N.M or "trigger phase">
  Result: <what actually happened>
  Expected: <what should have happened>
  State left behind: <clean | partial | corrupted>
  Severity: <CRITICAL | MAJOR | MINOR | PASS>
```

#### Severity Scoring

| Severity | Definition | Example |
|---|---|---|
| CRITICAL | Complete breakdown — wrong output, data loss, or unrecoverable state | Skill overwrites user file without confirmation on repeated invocation |
| MAJOR | Significant degradation — output is partial, misleading, or requires manual cleanup | Skill proceeds with stale data and produces outdated recommendations |
| MINOR | Cosmetic or minor — output is correct but formatting is off, or error message is vague | Empty input produces "Error" instead of "Please provide a skill name" |
| PASS | Handled correctly — skill rejects, recovers, or produces correct output | Off-topic query correctly rejected with helpful redirect |

#### Stress Test Report Format

The report MUST be delivered before any fixes are suggested:

```
## Stress Test Report: <skill-name>

### Summary
- Inputs tested: 10
- PASS: N | MINOR: N | MAJOR: N | CRITICAL: N
- Stress Test Score: (PASS count / 10) × 100 = N%

### Ranked Failures (highest severity first)

1. **CRITICAL** — #6 Partial prerequisite: <details>
2. **MAJOR** — #3 Conflicting constraints: <details>
3. **MINOR** — #5 Minimal input: <details>

### Verdict
- 90-100% → Production-ready — promote to hub
- 70-89%  → Fix CRITICAL/MAJOR items before promotion
- 50-69%  → Significant rework needed — revisit failure mode analysis (Step 2.3)
- <50%    → Fundamental design issue — reconsider skill scope and constraints
```

#### When to Run

| Trigger | Required? |
|---|---|
| Before hub promotion (Step 7) | MUST — no skill enters the hub without stress testing |
| After major version bump | MUST — new steps or output changes may introduce regressions |
| After user-reported failures | SHOULD — add the failing input to the adversarial set |
| Quarterly for high-usage skills | SHOULD — context drift can degrade skills over time |

### 6.4 Regression Indicators

After the skill is in use, watch for these signs it needs revision:

| Signal | Meaning | Action |
|--------|---------|--------|
| Users rephrase and re-invoke | Triggers are too narrow | Add more natural language triggers |
| Skill activates for unrelated requests | Triggers are too broad | Make triggers more specific |
| Users skip steps manually | Steps are unnecessary or in wrong order | Restructure |
| Users always modify the output | Output format does not match needs | Update templates |
| Errors in later steps | Earlier steps missed validation | Add prerequisite checks |

---
