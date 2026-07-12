# STEP 1: Reproduce the Failure

### 1.1 Understand the Report

Gather essential information about the failure:

| Element | Source | Example |
|---------|--------|---------|
| **Symptom** | Error message, user report, failing test | `TypeError: Cannot read properties of undefined` |
| **Context** | When/where it happens | "Happens on login when email contains a `+` sign" |
| **Expected behavior** | What should happen instead | "User should be logged in successfully" |
| **Frequency** | Always, intermittent, or one-time | "Every time with `+` in email, never without" |
| **Environment** | OS, runtime version, config | "Python 3.11, production database, DEBUG=false" |

If any of these are missing, ask the user before proceeding. Debugging without a clear symptom description wastes time.

### 1.2 Create a Minimal Reproduction

Build the simplest possible case that triggers the failure:

1. **Start with the reported reproduction steps** — run them exactly as described
2. **Verify the failure occurs** — you must see the actual error yourself
3. **Record the exact command and output** — this becomes your baseline

```bash
