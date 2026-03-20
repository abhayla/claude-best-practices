# Common Scenarios

### Scenario 1: First Run (No Custom Rules)

When `.pr-standards.yml` does not exist:

1. Apply all built-in default rules (Step 3)
2. Report results with a note: "Using built-in defaults. Create `.pr-standards.yml` to customize rules for your team."
3. Offer to generate a starter `.pr-standards.yml` based on the project's tech stack

### Scenario 2: Large Diff (500+ Changed Lines)

When the diff is large:

1. Note the size: "Large diff detected (X lines). Analysis may take longer."
2. Prioritize critical rules first — report critical violations immediately
3. Run warning and info rules after critical scan completes
4. Consider suggesting PR splitting (reference `/request-code-review` Step 1.3)

### Scenario 3: Only Test Files Changed

When only test files are modified:

1. Skip most code quality rules (debug statements in tests are sometimes acceptable)
2. Apply test-specific rules: no `@skip` without ticket, test naming conventions
3. Report with a note: "Only test files changed. Reduced rule set applied."

### Scenario 4: Configuration/Build Files Only

When only config files changed (`.yml`, `.json`, `.toml`, `Dockerfile`, etc.):

1. Apply security rules (no hardcoded secrets, no disabled security)
2. Skip code quality rules (no magic numbers, no empty catch, etc.)
3. Report with a note: "Configuration changes only. Security rules applied."

### Scenario 5: Migration Files

When database migration files are changed:

1. Apply security rules (no hardcoded secrets)
2. Flag irreversible operations: `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN ... NOT NULL` without default
3. Note: "Migration file detected. Verify rollback plan exists."

---

