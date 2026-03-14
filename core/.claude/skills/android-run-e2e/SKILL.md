---
name: android-run-e2e
description: >
  Run Android E2E tests via Gradle (Espresso/Compose) or Maestro (cross-platform YAML flows)
  sequentially by feature group with auto-fix. Auto-delegates to /fix-loop on failure.
  Use for E2E regression testing on Android, iOS, React Native, or Flutter.
allowed-tools: "Bash Read Grep Glob Skill"
triggers:
  - android e2e
  - maestro test
  - mobile e2e
  - e2e test android
argument-hint: "[feature-group|all] [--maestro|--gradle]"
---

# Run Android E2E Tests by Feature Group

Run E2E tests organized by feature group with automatic fix delegation.

**Arguments:** $ARGUMENTS

---

## Feature Groups

Organize your E2E tests by feature area. Example groups:
- `auth` — Authentication and onboarding flows
- `home` — Main screen functionality
- `settings` — Settings and preferences
- `navigation` — Cross-screen navigation flows

## Execution

For each group:

1. Run the group's test class(es)
2. If failure → delegate to `/fix-loop` (max 3 retries per group)
3. If still failing → mark as FAILED, continue to next group
4. Track pass/fail per group

```bash
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class={test_class}
```

## Report

```
E2E Test Results:
  Groups: N total | X passed | Y failed
  Per group:
    auth: PASSED
    home: PASSED
    settings: FAILED (3 retries exhausted)
```

## Maestro E2E Testing (Cross-Platform)

Maestro is a declarative, YAML-based mobile E2E framework that works across Android, iOS, React Native, and Flutter without code changes.

### Setup

```bash
# Install Maestro
curl -Ls "https://get.maestro.mobile.dev" | bash

# Verify installation
maestro --version

# Start Android emulator (required)
emulator -avd <avd_name> -no-audio -no-boot-anim &
adb wait-for-device
```

### Flow File Structure

Organize flows by feature in `e2e/maestro/`:

```
e2e/maestro/
├── auth/
│   ├── login.yaml
│   ├── signup.yaml
│   └── forgot-password.yaml
├── home/
│   ├── home-feed.yaml
│   └── search.yaml
├── settings/
│   ├── profile-edit.yaml
│   └── preferences.yaml
├── navigation/
│   └── tab-navigation.yaml
└── config.yaml
```

### Writing Flows

```yaml
# e2e/maestro/auth/login.yaml
appId: com.example.app
---
- launchApp
- assertVisible: "Welcome"

# Enter credentials
- tapOn: "Email"
- inputText: "test@example.com"
- tapOn: "Password"
- inputText: "TestPassword123"

# Submit
- tapOn: "Sign In"

# Verify success
- assertVisible: "Home"
- assertNotVisible: "Error"
```

```yaml
# e2e/maestro/auth/login-visual.yaml
appId: com.example.app
---
- launchApp
- assertVisible: "Welcome"
- tapOn: "Email"
- inputText: "test@example.com"
- tapOn: "Password"
- inputText: "TestPassword123"
- tapOn: "Sign In"
- assertVisible: "Home"

# Visual regression check — autonomous pass/fail
- assertScreenshot:
    path: "baselines/home-after-login.png"
    thresholdPercentage: 95
    cropOn:
      id: "main_content"  # Ignore status bar clock/battery
```

### Common Actions

| Action | Syntax | Use For |
|--------|--------|---------|
| `tapOn` | `- tapOn: "Button Text"` | Tap buttons, links, elements |
| `inputText` | `- inputText: "value"` | Type into focused field |
| `assertVisible` | `- assertVisible: "Text"` | Verify element is displayed |
| `assertNotVisible` | `- assertNotVisible: "Error"` | Verify element is NOT shown |
| `scrollUntilVisible` | `- scrollUntilVisible: {element: "Text", direction: DOWN}` | Scroll to find element |
| `back` | `- back` | Press back button |
| `swipe` | `- swipe: {direction: LEFT, duration: 400}` | Swipe gesture |
| `waitForAnimationToEnd` | `- waitForAnimationToEnd` | Wait for transitions |
| `takeScreenshot` | `- takeScreenshot: "screenshot_name"` | Capture for visual regression |
| `runFlow` | `- runFlow: auth/login.yaml` | Reuse another flow |
| `repeat` | `- repeat: {times: 3, commands: [...]}` | Loop actions |
| `evalScript` | `- evalScript: \${output.field}` | Access JavaScript expressions |
| `assertScreenshot` | `- assertScreenshot: {path: "baseline.png", thresholdPercentage: 95}` | Visual regression assertion (autonomous pass/fail) |

### Selectors (priority order)

1. **Text content**: `- tapOn: "Sign In"` (preferred — closest to user intent)
2. **Test ID**: `- tapOn: {id: "login_button"}` (for dynamic text)
3. **Accessibility label**: `- tapOn: {accessibilityLabel: "Login"}` (for icons)
4. **Index**: `- tapOn: {index: 0, text: "Item"}` (for lists)

### Running Tests

```bash
# Run a single flow
maestro test e2e/maestro/auth/login.yaml

# Run all flows in a directory
maestro test e2e/maestro/

# Run with specific device
maestro test --device emulator-5554 e2e/maestro/

# Run with screenshots on failure
maestro test --debug-output=e2e/output e2e/maestro/

# Run in CI (headless)
maestro test --no-ansi e2e/maestro/ 2>&1 | tee maestro-results.txt
```

### CI Integration

```yaml
# GitHub Actions: Android Maestro E2E
maestro-e2e:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Android Emulator
      uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: 34
        target: google_apis
        arch: x86_64
        script: |
          curl -Ls "https://get.maestro.mobile.dev" | bash
          export PATH="$PATH:$HOME/.maestro/bin"
          ./gradlew :app:installDebug
          maestro test e2e/maestro/ --no-ansi --debug-output=e2e/output
    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: maestro-debug
        path: e2e/output/
```

---

## Execution

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
# Run tests with screenshot output
maestro test e2e/maestro/{group}/ --debug-output=e2e/output/{group}

# After each group, compare screenshots against baselines
# Use multimodal Read to view both baseline and current screenshot
# Report visual diffs as VISUAL_REGRESSION failures
```

## Report

```
E2E Test Results:
  Framework: Gradle (Espresso/Compose) + Maestro
  Groups: N total | X passed | Y failed | Z visual regressions
  Per group:
    auth (Maestro): PASSED
    home (Maestro): VISUAL_REGRESSION (home-feed.png differs from baseline)
    settings (Gradle): PASSED
    navigation (Maestro): FAILED (screenshot: e2e/output/navigation/)
  Visual Regression Summary:
    Baselines checked: N
    Matches: X
    Regressions: Y (list files)
    New screens (no baseline): Z
```

## Visual Regression Verification

Screenshots are NOT debug-only artifacts. They MUST be compared against committed baselines for autonomous pass/fail determination.

### Maestro Native Visual Assertion (Preferred)

Maestro's built-in `assertScreenshot` provides autonomous visual verification without LLM vision calls:

```yaml
# Autonomous visual assertion — fails the flow if screenshot differs from baseline
- assertScreenshot:
    path: "baselines/dashboard.png"      # Path to baseline image
    thresholdPercentage: 95              # 95% similarity required (default)
    cropOn:
      id: "main_content"                # Optional: compare only this element
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | required | Path to baseline screenshot |
| `thresholdPercentage` | 95 | Minimum similarity percentage (0-100) |
| `cropOn` | — | Selector to crop comparison area (ignore status bar, nav bar) |

**When to use which approach:**

| Approach | Use When | Speed | Reliability |
|----------|----------|-------|-------------|
| `assertScreenshot` (native) | Standard visual regression in CI | Fast (ms) | Deterministic |
| Multimodal Read comparison | Complex semantic analysis, design review | Slow (seconds) | AI-dependent |

Always prefer `assertScreenshot` for CI pipelines. Use multimodal comparison for design review or when semantic understanding is needed (e.g., "does this look like a login screen?").

**Baseline management:**
```bash
# First run generates baselines (test will fail — copy output to baselines/)
maestro test e2e/maestro/auth/ --debug-output=e2e/output/auth/

# Copy generated screenshots to baselines
cp e2e/output/auth/screenshots/*.png e2e/maestro/baselines/auth/

# Subsequent runs compare against baselines automatically
maestro test e2e/maestro/auth/  # Passes if within threshold
```

### Baseline Directory Structure

```
e2e/maestro/
  baselines/        # Committed to version control
    auth/
      login-complete.png
      signup-success.png
    home/
      home-feed.png
      search-results.png
  current/          # Generated during test run (gitignored)
    auth/
      login-complete.png
    home/
      home-feed.png
  diffs/            # Side-by-side comparison images (gitignored)
    home/
      home-feed-diff.png
```

Add to `.gitignore`:
```
e2e/maestro/current/
e2e/maestro/diffs/
```

### Capturing Screenshots in Flows

Add `takeScreenshot` commands at verification points in your Maestro flows:

```yaml
# e2e/maestro/auth/login.yaml
appId: com.example.app
---
- launchApp
- assertVisible: "Welcome"
- tapOn: "Email"
- inputText: "test@example.com"
- tapOn: "Password"
- inputText: "TestPassword123"
- tapOn: "Sign In"
- assertVisible: "Home"
- takeScreenshot: "login-complete"    # Captures to debug-output directory
```

The screenshot filename MUST match the corresponding baseline filename (without extension).

### Verification Workflow

After running each Maestro group, perform visual comparison:

1. **Locate screenshots** — Find all `.png` files in `e2e/output/{group}/`
2. **Copy to current/** — Move screenshots to `e2e/maestro/current/{group}/` for organized comparison
3. **Compare against baselines** — For each screenshot in `current/{group}/`:
   - Check if a baseline exists in `e2e/maestro/baselines/{group}/`
   - If baseline exists → use Claude's multimodal `Read` tool to view both images
   - Compare current vs baseline visually for layout shifts, missing elements, color changes, or content differences
   - Determine pass/fail based on whether the screens look functionally identical
4. **Report results** — Each screenshot gets one of three verdicts:
   - `MATCH` — Current matches baseline, no visual regression
   - `VISUAL_REGRESSION` — Current differs from baseline in a meaningful way
   - `NEW` — No baseline exists yet (not a failure, but flagged for review)

```bash
# Step 1: Run the group
maestro test e2e/maestro/{group}/ --debug-output=e2e/output/{group}

# Step 2: Copy screenshots to current/
mkdir -p e2e/maestro/current/{group}
cp e2e/output/{group}/*.png e2e/maestro/current/{group}/ 2>/dev/null || true

# Step 3: Compare each screenshot against its baseline
for screenshot in e2e/maestro/current/{group}/*.png; do
  name=$(basename "$screenshot")
  baseline="e2e/maestro/baselines/{group}/$name"
  if [ -f "$baseline" ]; then
    # Use Claude's multimodal Read to compare both images
    # Read baseline: e2e/maestro/baselines/{group}/$name
    # Read current:  e2e/maestro/current/{group}/$name
    # Verdict: MATCH or VISUAL_REGRESSION
    echo "Comparing $name against baseline..."
  else
    echo "NEW: No baseline for $name — flag for review"
  fi
done
```

### Multimodal Comparison Step

For each screenshot with a baseline, use Claude's `Read` tool to view both images:

1. `Read` the baseline image: `e2e/maestro/baselines/{group}/{name}.png`
2. `Read` the current image: `e2e/maestro/current/{group}/{name}.png`
3. Compare the two screenshots visually. Check for:
   - Layout shifts or element repositioning
   - Missing or added UI elements
   - Text content changes
   - Color or theme changes
   - Unexpected overlapping elements or clipping
4. If the screens look functionally identical → `MATCH`
5. If there are meaningful visual differences → `VISUAL_REGRESSION`
   - Describe what changed in the report

### Baseline Update Workflow

When visual changes are intentional (new feature, redesign), update baselines:

```bash
# Update all baselines from current screenshots
# Use --update-baselines flag with the E2E skill
# e.g.: /android-run-e2e all --maestro --update-baselines

# Manual update for a specific group:
mkdir -p e2e/maestro/baselines/{group}
cp e2e/maestro/current/{group}/*.png e2e/maestro/baselines/{group}/

# Update for all groups:
for group in e2e/maestro/current/*/; do
  group_name=$(basename "$group")
  mkdir -p "e2e/maestro/baselines/$group_name"
  cp "$group"*.png "e2e/maestro/baselines/$group_name/"
done

# Commit updated baselines
git add e2e/maestro/baselines/
git commit -m "chore: update visual regression baselines"
```

**When to update baselines:**
- After intentional UI changes (feature work, redesign)
- After theme or style system updates
- After upgrading UI component libraries
- NEVER update baselines to silence a regression without understanding the cause

### Integration with Execution Flow

When `--update-baselines` is passed:
1. Run all Maestro groups as normal
2. Instead of comparing screenshots, copy all captured screenshots to `e2e/maestro/baselines/{group}/`
3. Report which baselines were created or updated
4. Skip visual regression comparison (all screenshots become the new baselines)

When running normally (no `--update-baselines`):
1. Run each Maestro group
2. After each group completes, compare screenshots against baselines
3. Any `VISUAL_REGRESSION` verdict counts as a test failure for that group
4. `NEW` screenshots (no baseline) are warnings, not failures
5. Include visual regression details in the final report

## Notes

- Gradle E2E requires running emulator and backend
- Maestro requires emulator but NOT a compiled test APK (tests against installed app)
- Each group gets up to 3 fix-loop retries (Gradle) or 1 retry (Maestro)
- Failed groups don't block other groups from running
- Maestro flows are YAML-only — no code compilation, faster iteration
- Use Maestro for user-journey validation, Gradle/Espresso for framework-specific assertions
