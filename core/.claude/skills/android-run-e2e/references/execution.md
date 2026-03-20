# Execution

### Gradle-based E2E (Espresso/Compose)

For each feature group:

1. Run the group's test class(es)
2. If failure → delegate to `/fix-loop` (max 3 retries per group)
3. If still failing → mark as FAILED, continue to next group
4. Track pass/fail per group

```bash
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class={test_class}
```

### Maestro-based E2E

For each feature group:

1. Run the group's flow directory with screenshot capture
2. If failure → capture screenshots + debug output
3. Compare captured screenshots against baselines (see Visual Regression Verification)
4. If visual regression detected → mark as VISUAL_REGRESSION failure
5. Retry once (Maestro flows are deterministic)
6. If still failing → mark as FAILED, continue to next group
7. If `--update-baselines` flag is set → copy current screenshots to baselines instead of comparing

```bash
