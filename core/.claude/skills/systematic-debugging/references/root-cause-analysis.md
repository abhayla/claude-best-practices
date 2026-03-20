# STEP 5: Root Cause Analysis

### 5.1 Trace the Causal Chain

Build the chain from symptom back to cause:

```
Causal Chain:
  SYMPTOM: {what the user sees}
    caused by: {proximate cause — the immediate trigger}
      caused by: {intermediate cause}
        caused by: {root cause — the fundamental issue}
```

Example:
```
Causal Chain:
  SYMPTOM: "500 Internal Server Error on login"
    caused by: NullPointerException in UserService.authenticate()
      caused by: user.getProfile() returns null
        caused by: Profile table migration was not run in production
          ROOT CAUSE: Deployment script skips migrations when DB_MIGRATE=false
```

### 5.2 Distinguish Root Cause from Proximate Cause

| Level | Example | Fix Quality |
|-------|---------|-------------|
| **Symptom** | "Page shows 500 error" | Useless — just hides the error |
| **Proximate cause** | "Null pointer in line 42" | Fragile — adds a null check but doesn't prevent null |
| **Root cause** | "Migration not run in prod" | Durable — fixes the deployment pipeline |
| **Systemic cause** | "No migration check in deploy" | Best — adds a deployment safeguard |

Always fix at the root cause level or deeper. Fixing the proximate cause creates a band-aid that will fail again in a different way.

### 5.3 The "Five Whys" Technique

When the root cause is not obvious, ask "why" iteratively:

1. **Why** did the server return a 500 error? Because `authenticate()` threw a NullPointerException.
2. **Why** did it throw NPE? Because `user.getProfile()` returned null.
3. **Why** did it return null? Because the profile row does not exist in the database.
4. **Why** does the row not exist? Because the migration that creates the profiles table was not run.
5. **Why** was the migration not run? Because `DB_MIGRATE` is set to `false` in the production deploy config.

The root cause is at level 4 or 5 — not level 1 or 2.

### 5.4 Verify the Root Cause

Before writing a fix, confirm the root cause by predicting behavior:

1. **Predict** — "If my root cause analysis is correct, then {changing X} should {produce Y}"
2. **Test the prediction** — Make the predicted change and verify the predicted outcome
3. **Confirm** — If the prediction holds, you have found the root cause
4. **Refute** — If the prediction fails, your root cause analysis is wrong — return to Step 3

Example:
- Prediction: "If the root cause is the missing migration, then running the migration should fix the login error"
- Test: Run the migration in a test environment and attempt login
- Result: Login succeeds — root cause confirmed

---

