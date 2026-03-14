---
name: react-native-e2e
description: >
  React Native E2E testing with Detox and visual regression with React Native Owl.
  Covers setup, flow writing, screenshot comparison, and CI integration.
  Use for end-to-end testing of React Native apps on Android and iOS.
allowed-tools: "Bash Read Grep Glob Write Edit"
triggers:
  - react native e2e
  - detox test
  - rn e2e
  - react native visual
argument-hint: "<test-file|feature-name|all> [--platform android|ios] [--visual]"
version: "1.0.0"
type: workflow
---

# React Native E2E Testing

Run and author E2E tests for React Native apps using Detox with visual regression via React Native Owl.

**Arguments:** $ARGUMENTS

> **Note:** For unit testing, component testing, and hook testing, see the `react-native-dev` skill (STEP 7: Testing) which covers Jest + React Native Testing Library patterns. This skill focuses exclusively on end-to-end and visual regression testing.

---

## STEP 1: Detox Setup

### Install

```bash
# Install Detox CLI and test runner
npm install -D detox @types/detox jest-circus
npm install -g detox-cli

# iOS: install applesimutils
brew tap wix/brew && brew install applesimutils
```

### Configuration (.detoxrc.js)

```javascript
module.exports = {
  testRunner: {
    args: { $0: 'jest', config: 'e2e/jest.config.js' },
    jest: { setupTimeout: 120000 },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/MyApp.app',
      build: 'xcodebuild -workspace ios/MyApp.xcworkspace -scheme MyApp -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'android.debug': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
      build: 'cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
      reversePorts: [8081],
    },
  },
  devices: {
    simulator: { type: 'ios.simulator', device: { type: 'iPhone 15' } },
    emulator: { type: 'android.emulator', device: { avdName: 'Pixel_7_API_34' } },
  },
  configurations: {
    'ios.sim.debug': { device: 'simulator', app: 'ios.debug' },
    'android.emu.debug': { device: 'emulator', app: 'android.debug' },
  },
};
```

### Build and Run

```bash
# Build app for testing
detox build --configuration android.emu.debug

# Run all E2E tests
detox test --configuration android.emu.debug

# Run specific test file
detox test --configuration ios.sim.debug e2e/login.test.js

# Run with retries for flaky tests
detox test --configuration android.emu.debug --retries 2
```

---

## STEP 2: Writing E2E Tests

### Login Flow

```javascript
describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should login successfully with valid credentials', async () => {
    await element(by.id('email-input')).typeText('test@example.com');
    await element(by.id('password-input')).typeText('Password123');
    await element(by.id('login-button')).tap();

    await waitFor(element(by.id('home-screen')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should show error for invalid credentials', async () => {
    await element(by.id('email-input')).typeText('wrong@example.com');
    await element(by.id('password-input')).typeText('wrong');
    await element(by.id('login-button')).tap();

    await expect(element(by.text('Invalid credentials'))).toBeVisible();
  });
});
```

### Navigation Flow

```javascript
describe('Bottom Tab Navigation', () => {
  beforeAll(async () => {
    await device.launchApp();
    // Login first
    await element(by.id('email-input')).typeText('test@example.com');
    await element(by.id('password-input')).typeText('Password123');
    await element(by.id('login-button')).tap();
    await waitFor(element(by.id('home-screen'))).toBeVisible().withTimeout(5000);
  });

  it('should navigate to settings', async () => {
    await element(by.id('tab-settings')).tap();
    await expect(element(by.id('settings-screen'))).toBeVisible();
  });

  it('should navigate back to home', async () => {
    await element(by.id('tab-home')).tap();
    await expect(element(by.id('home-screen'))).toBeVisible();
  });
});
```

### Scroll and List Interaction

```javascript
it('should scroll to item and tap it', async () => {
  await waitFor(element(by.id('list-item-25')))
    .toBeVisible()
    .whileElement(by.id('item-list'))
    .scroll(200, 'down');

  await element(by.id('list-item-25')).tap();
  await expect(element(by.id('detail-screen'))).toBeVisible();
});
```

### Selectors (priority order)

| Selector | Usage | Best For |
|----------|-------|----------|
| `by.id('testID')` | `element(by.id('login-btn'))` | Primary — most stable |
| `by.text('Submit')` | `element(by.text('Submit'))` | Static text buttons |
| `by.label('Close')` | `element(by.label('Close'))` | Accessibility labels |
| `by.type('RCTTextInput')` | `element(by.type('...'))` | Last resort only |

---

## STEP 3: Visual Regression with React Native Owl

React Native Owl captures screenshots on real emulators/simulators and compares against baselines.

### Setup

```bash
npm install -D react-native-owl
```

```javascript
// owl.config.js
module.exports = {
  android: {
    packageName: 'com.myapp',
    buildCommand: 'cd android && ./gradlew assembleDebug',
    binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
    device: 'Pixel_7_API_34',
  },
  ios: {
    scheme: 'MyApp',
    buildCommand: 'xcodebuild -workspace ios/MyApp.xcworkspace -scheme MyApp -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/MyApp.app',
    device: 'iPhone 15',
  },
  report: true,
};
```

### Writing Visual Tests

```javascript
// e2e/visual/login.owl.js
import { takeScreenshot, press, changeText } from 'react-native-owl';

describe('Login Screen - Visual', () => {
  it('matches baseline for empty state', async () => {
    const screen = await takeScreenshot('login-empty');
    // Automatically compared against baseline in __owl__/baseline/
  });

  it('matches baseline with filled form', async () => {
    await changeText('email-input', 'test@example.com');
    await changeText('password-input', 'Password123');
    const screen = await takeScreenshot('login-filled');
  });

  it('matches baseline for error state', async () => {
    await changeText('email-input', 'wrong@test.com');
    await changeText('password-input', 'x');
    await press('login-button');
    const screen = await takeScreenshot('login-error');
  });
});
```

### Running Visual Tests

```bash
# Run visual tests on Android
npx owl build --platform android
npx owl test --platform android

# Run on iOS
npx owl build --platform ios
npx owl test --platform ios

# Update baselines after intentional UI changes
npx owl test --platform android --update

# Baselines stored in: __owl__/baseline/{platform}/
# Diffs generated in: __owl__/diff/{platform}/
# Report at: __owl__/report/index.html
```

---

## STEP 4: CI Integration

```yaml
name: React Native E2E

on: [push, pull_request]

jobs:
  e2e-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci

      - name: Build for Detox
        run: detox build --configuration android.emu.debug

      - name: Run E2E tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 34
          arch: x86_64
          script: detox test --configuration android.emu.debug --retries 2

      - name: Run visual regression
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 34
          arch: x86_64
          script: npx owl build --platform android && npx owl test --platform android

      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: e2e-artifacts
          path: |
            artifacts/
            __owl__/diff/
            __owl__/report/
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `element not found` | Animation not settled | Use `waitFor().toBeVisible().withTimeout()` |
| Flaky tap on Android | Touch target too small | Increase touchable area or use `multiTap(1)` |
| App crashes on launch | Metro bundler not running | Add `--reuse` flag or build release |
| Visual diff on CI | Emulator rendering differs | Pin emulator image, use same API level |
| `device.launchApp` timeout | Emulator slow to boot | Increase `setupTimeout` in `.detoxrc.js` |
