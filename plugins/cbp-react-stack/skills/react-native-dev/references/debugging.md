# Debugging and Troubleshooting

Use the right tool for each debugging scenario.

## Debugging Tools

### Flipper

```bash
# Flipper is deprecated in RN 0.74+. Use React Native DevTools instead.
# For older projects: download from https://fbflipper.com/
# Flipper plugins: Network, Layout Inspector, Databases, Shared Preferences
```

### React Native DevTools (RN 0.76+)

```bash
# Press 'j' in Metro terminal to open DevTools
# Or shake device > "Open DevTools"

# Features:
# - Component tree inspection
# - Profiler for render performance
# - Network request inspection
# - Console logs
```

### Hermes Debugger

```bash
# Chrome DevTools with Hermes
# 1. Run app in debug mode
npx react-native start

# 2. Open chrome://inspect in Chrome
# 3. Click "inspect" on the Hermes target
# 4. Use Sources, Console, Memory, Performance tabs
```

### LogBox Configuration

```tsx
import { LogBox } from 'react-native';

// Ignore specific warnings (use sparingly)
LogBox.ignoreLogs([
  'ViewPropTypes will be removed',   // Known third-party lib warning
  'Require cycle:',                   // Investigate but may be benign
]);

// Never ignore all logs in development — fix the root cause instead
```

### Common Debug Commands

```bash
# Clear all caches
watchman watch-del-all
rm -rf node_modules && yarn install
cd ios && pod install && cd ..
yarn start --reset-cache

# Android: reverse port for device debugging
adb reverse tcp:8081 tcp:8081

# iOS: reset simulator
xcrun simctl erase all

# Check running Metro processes
lsof -i :8081
```

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| Metro bundler fails to start | Port 8081 in use or cache corruption | `lsof -i :8081` to find process; `yarn start --reset-cache` |
| `Unable to resolve module` | Missing dependency or incorrect import path | `yarn install`; check for typos; verify file exists |
| iOS build fails: `pod install` errors | CocoaPods cache stale or version mismatch | `cd ios && pod deintegrate && pod install --repo-update` |
| Android build fails: Gradle errors | JDK version mismatch or cache corruption | Verify JDK 17; `cd android && ./gradlew clean` |
| Red screen: `TypeError: undefined is not an object` | Accessing property on null/undefined | Add null checks; verify API response shape |
| Bridge errors: `Invariant Violation` | Native module not linked or misconfigured | `npx react-native link`; verify `pod install`; rebuild |
| JS thread blocked (FPS drops) | Heavy computation on JS thread | Move to `InteractionManager.runAfterInteractions()` or use Reanimated worklets |
| Memory leak: app grows over time | Uncleared subscriptions, listeners, or timers | Clean up in `useEffect` return; profile with Hermes heap snapshots |
| `ENOSPC: System limit for file watchers reached` | Linux/WSL file watcher limit | `echo fs.inotify.max_user_watches=524288 \| sudo tee -a /etc/sysctl.conf && sudo sysctl -p` |
| Hot reload not reflecting changes | Metro cache stale or module caching issue | `yarn start --reset-cache`; for persistent issues, cold restart |
| Reanimated crash on startup | Babel plugin not configured | Add `react-native-reanimated/plugin` as last item in `babel.config.js` plugins |
| `com.facebook.react.bridge.ReadableNativeMap cannot be cast` | Incorrect data type passed over bridge | Verify native module parameter types match JS-side types |
