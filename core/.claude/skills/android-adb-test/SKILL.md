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

## Report

```
ADB Test Report:
  Screens tested: N
  Passed: X | Failed: Y
  Fixes applied: Z
  Duration: M minutes
```
