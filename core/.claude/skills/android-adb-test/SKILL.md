---
name: android-adb-test
description: >
  Run Android E2E tests via ADB using uiautomator dump, screencap, and input tap.
  Use when testing app screens without the Compose test framework, debugging emulator UI,
  or validating user flows manually.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[screen-name|flow-name|all]"
version: "1.0.0"
type: reference
---

# ADB Manual E2E Testing

Test app screens via ADB commands — uiautomator dump, screencap, input tap.

**Target:** $ARGUMENTS

---

## Prerequisites

1. **Emulator running:** `adb devices` should show a device
2. **App installed:** Build and install debug APK
3. **Backend running** (if testing API-connected screens)

## ADB Patterns

| Pattern | Command |
|---------|---------|
| UI Dump | `adb exec-out uiautomator dump /dev/tty` |
| Screenshot | `adb exec-out screencap -p > screenshot.png` |
| Tap | `adb shell input tap X Y` |
| Text Input | `adb shell input text "hello"` |
| Back | `adb shell input keyevent BACK` |
| Launch App | `adb shell am start -n PACKAGE/ACTIVITY` |

## Testing Process

For each screen:

1. **Navigate** to the screen via ADB taps
2. **Dump UI** to verify expected elements are present
3. **Interact** with key elements (tap buttons, enter text)
4. **Screenshot** after interaction
5. **Verify** expected state changes occurred

## Important Notes

- Compose `testTag()` values do NOT appear in uiautomator XML
- Search by: `text`, `content-desc`, `resource-id`, `bounds` instead
- ExposedDropdownMenu popups cannot be interacted with via ADB
- Use backend API to set values that can't be set through UI

## Emulator Setup & Profiling

### Create and Manage Emulators

```bash
# List available system images
sdkmanager --list | grep "system-images"

# Create AVD
avdmanager create avd -n test_device -k "system-images;android-34;google_apis;x86_64" -d pixel_6

# Start with cold boot (no snapshot)
emulator -avd test_device -no-snapshot-load

# Start with snapshot (fast boot)
emulator -avd test_device

# Save snapshot
adb emu avd snapshot save clean_state

# Load snapshot
adb emu avd snapshot load clean_state
```

### Logcat Filtering

```bash
# Filter by app package
adb logcat --pid=$(adb shell pidof com.app.package)

# Filter by tag and priority
adb logcat -s MyTag:D ActivityManager:I

# Clear and capture fresh logs
adb logcat -c && adb logcat -v time > logcat.txt
```

### Performance Profiling

```bash
# Record Perfetto trace (10 seconds)
adb shell perfetto -o /data/misc/perfetto-traces/trace.pb -t 10s sched freq idle am wm gfx view

# Pull trace for analysis
adb pull /data/misc/perfetto-traces/trace.pb ./trace.pb

# Open in ui.perfetto.dev or Android Studio Profiler
```

### App Startup Timing

```bash
# Cold start timing
adb shell am force-stop com.app.package
adb shell am start-activity -W -S com.app.package/.MainActivity

# Output includes: TotalTime (ms) — the metric that matters
```

## Monkey Testing (Autonomous Crash Detection)

Use Android's built-in `monkey` tool to send random UI events and detect crashes/ANRs without writing test code.

### Basic Crash Detection

```bash
# Send 1000 random events to the app (touches, gestures, system keys)
adb shell monkey -p com.example.app -v 1000 --throttle 100 \
  --pct-touch 40 --pct-motion 25 --pct-nav 15 \
  --pct-syskeys 5 --pct-appswitch 10 --pct-anyevent 5 \
  --kill-process-after-error 2>&1 | tee monkey_log.txt

# Check for crashes and ANRs
grep -E "CRASH|ANR|Exception|FATAL" monkey_log.txt
echo "Exit code: $?"  # Non-zero = crash detected
```

### Event Distribution

| Parameter | Default | Recommended | Description |
|-----------|---------|-------------|-------------|
| `--pct-touch` | — | 40% | Tap events |
| `--pct-motion` | — | 25% | Drag/swipe gestures |
| `--pct-nav` | — | 15% | Navigation (back, menu) |
| `--pct-syskeys` | — | 5% | System keys (home, volume) |
| `--pct-appswitch` | — | 10% | Activity switches |
| `--pct-anyevent` | — | 5% | Other events |
| `--throttle` | 0 | 100 | Delay between events (ms) |

### Reproducible Runs

```bash
# Use a fixed seed for deterministic reproduction
adb shell monkey -p com.example.app -s 42 -v 5000 --throttle 100 \
  --kill-process-after-error 2>&1 | tee monkey_seed42.txt

# If crash found, replay with same seed to reproduce
adb shell monkey -p com.example.app -s 42 -v 5000 --throttle 100
```

### CI Integration

```bash
# Run monkey test, fail CI if crash detected
adb shell monkey -p com.example.app -s $RANDOM_SEED -v 2000 \
  --throttle 50 --kill-process-after-error 2>&1 | tee monkey_ci.txt

CRASHES=$(grep -c "CRASH\|ANR\|FATAL" monkey_ci.txt || true)
if [ "$CRASHES" -gt 0 ]; then
  echo "FAILED: $CRASHES crash(es) detected"
  # Capture logcat for debugging
  adb logcat -d > crash_logcat.txt
  exit 1
fi
echo "PASSED: No crashes in 2000 events"
```

### Extended Stress Test

```bash
# Long-running stability test (10000 events, ~15 minutes)
adb shell monkey -p com.example.app -s 12345 -v 10000 \
  --throttle 200 \
  --pct-touch 35 --pct-motion 20 --pct-nav 20 \
  --pct-syskeys 5 --pct-appswitch 15 --pct-anyevent 5 \
  --ignore-timeouts --ignore-security-exceptions \
  --kill-process-after-error 2>&1 | tee monkey_stress.txt

# Parse results
EVENTS=$(grep "Events injected:" monkey_stress.txt | awk '{print $3}')
CRASHES=$(grep -c "CRASH\|ANR" monkey_stress.txt || true)
echo "Stability: $EVENTS events, $CRASHES crashes"
```

## Report

```
ADB Test Report:
  Screens tested: N
  Passed: X | Failed: Y
  Fixes applied: Z
  Duration: M minutes
```
