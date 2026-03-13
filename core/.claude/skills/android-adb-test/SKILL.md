---
name: android-adb-test
description: >
  Android E2E testing via ADB (uiautomator dump, screencap, input tap).
  Use for testing app screens without Compose test framework, debugging emulator UI,
  or validating user flows manually.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[screen-name|flow-name|all]"
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

## Report

```
ADB Test Report:
  Screens tested: N
  Passed: X | Failed: Y
  Fixes applied: Z
  Duration: M minutes
```
