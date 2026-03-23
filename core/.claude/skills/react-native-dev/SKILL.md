---
name: react-native-dev
description: >
  Build React Native applications covering project setup, functional components, hooks,
  React Navigation, state management (Zustand/Redux Toolkit), performance profiling
  (Hermes, Reanimated 3, FPS), platform-specific code, testing, CI/CD, version
  upgrades, brownfield migration, and debugging. Use when developing, optimizing,
  or upgrading React Native apps.
triggers: "react native, react-native, expo, metro, react navigation, hermes, flipper, brownfield"
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<feature-description or 'setup' or 'test' or 'optimize' or 'upgrade' or 'brownfield'>"
version: "1.0.1"
type: workflow
---

# React Native Development

Build production-grade React Native applications with robust architecture, native performance, and cross-platform reliability.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup

Scaffold or verify the React Native project structure.

### Initialize Project

```bash
# New project with React Native CLI
npx @react-native-community/cli init MyApp --pm yarn

# Or with Expo (managed workflow)
npx create-expo-app MyApp --template expo-template-blank-typescript

# Verify setup
cd MyApp && npx react-native run-ios   # or run-android
```

### Directory Structure

```
src/
  api/                  # API clients, request/response types
  assets/               # Images, fonts, static resources
  components/           # Shared reusable components
    Button/
      Button.tsx
      Button.test.tsx
      Button.styles.ts
  features/             # Feature-based modules
    auth/
      screens/          # Screen components
      hooks/            # Feature-specific hooks
      components/       # Feature-specific components
      types.ts
    home/
      screens/
      hooks/
      components/
  hooks/                # Shared custom hooks
  navigation/           # React Navigation config
    RootNavigator.tsx
    types.ts            # Typed route params
  services/             # Business logic, native module wrappers
  store/                # Global state (Zustand/Redux)
  theme/                # Colors, spacing, typography tokens
  utils/                # Pure utility functions
  App.tsx               # Root component
index.js                # Entry point
```

### Metro Bundler Configuration

```js
// metro.config.js
const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

const defaultConfig = getDefaultConfig(__dirname);

const config = {
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true, // Improves startup time
      },
    }),
  },
  resolver: {
    // Add any custom asset extensions
    assetExts: [...defaultConfig.resolver.assetExts, 'lottie'],
    sourceExts: [...defaultConfig.resolver.sourceExts, 'cjs'],
  },
};

module.exports = mergeConfig(defaultConfig, config);
```

### Essential Dependencies

```bash
# Navigation
yarn add @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs
yarn add react-native-screens react-native-safe-area-context

# State management
yarn add zustand                      # Lightweight (preferred)
# OR
yarn add @reduxjs/toolkit react-redux # Full-featured

# Animations
yarn add react-native-reanimated

# Async storage
yarn add @react-native-async-storage/async-storage

# Networking
yarn add axios                        # OR use fetch with interceptors

# Dev dependencies
yarn add -D @testing-library/react-native jest @types/react @types/react-native
```

### Verify Setup

```bash
# iOS
cd ios && pod install && cd ..
npx react-native run-ios

# Android
npx react-native run-android

# TypeScript check
npx tsc --noEmit

# Lint
npx eslint src/ --ext .ts,.tsx
```

Fix all TypeScript and lint issues before proceeding.

---

## STEP 2: Core Patterns

Use functional components with hooks exclusively. Class components are legacy.


**Read:** `references/core-patterns.md` for detailed step 2: core patterns reference material.

## STEP 3: Navigation

Configure React Navigation with typed routes and deep linking.


**Read:** `references/navigation.md` for detailed step 3: navigation reference material.

## STEP 4: State Management

Choose the right state management approach based on complexity.


**Read:** `references/state-management.md` for detailed step 4: state management reference material.

## STEP 5: Performance Profiling

Profile and optimize for consistent 60 FPS. Follow the cycle: **Measure > Optimize > Re-measure > Validate**.

### JS Thread Monitoring

```bash
# Open React Native DevTools (press 'j' in Metro terminal)
# Or shake device > "Open DevTools"

# Enable performance monitor overlay (shows JS/UI FPS)
# In-app: shake device > "Show Perf Monitor"
```

### FPS Tracking

```tsx
// Programmatic FPS monitoring
import { PerformanceObserver } from 'react-native-performance';

// React DevTools Profiler for component render timing
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
) {
  if (actualDuration > 16) {
    console.warn(`Slow render: ${id} took ${actualDuration.toFixed(1)}ms (${phase})`);
  }
}

<Profiler id="ItemList" onRender={onRenderCallback}>
  <ItemList />
</Profiler>
```

### Re-render Detection

```tsx
// Option 1: React DevTools Profiler — "Highlight updates when components render"
// Option 2: React Compiler (RN 0.76+) — automatic memoization, eliminates manual memo/useCallback
// Option 3: why-did-you-render (development only)
// yarn add -D @welldone-software/why-did-you-render

// wdyr.ts (import before App)
import React from 'react';
if (__DEV__) {
  const whyDidYouRender = require('@welldone-software/why-did-you-render');
  whyDidYouRender(React, { trackAllPureComponents: true });
}
```

### Memory Profiling

```bash
# iOS: Xcode > Debug > Debug Workflow > Capture GPU Frame
# Android: Android Studio > Profiler > Memory

# JS heap snapshots via Hermes
adb shell am broadcast -a com.facebook.react.HeapCapture
# Or use Chrome DevTools with Hermes debugging
```

### Hermes Engine Optimization

```js
// metro.config.js — enable inline requires for faster startup
module.exports = {
  transformer: {
    getTransformOptions: async () => ({
      transform: { inlineRequires: true },
    }),
  },
};

// android/app/build.gradle — ensure Hermes is enabled
project.ext.react = [
    enableHermes: true,  // Default since RN 0.70
]

// Disable bundle compression on Android for Hermes mmap optimization
// android/app/build.gradle
android {
    packagingOptions {
        jniLibs { useLegacyPackaging = true }
    }
}
```

### Performance Metrics Targets

| Metric | Target | Red Flag |
|--------|--------|----------|
| JS FPS | 60 | <45 sustained |
| UI FPS | 60 | <50 sustained |
| TTI (cold start) | <2s | >4s |
| JS bundle size | <1.5 MB | >3 MB |
| Memory (JS heap) | Stable | Monotonic increase |
| Frame build time | <16ms | >16ms consistently |
| List scroll FPS | 60 | Visible jank on scroll |

---

## STEP 6: Platform-Specific Code

Write cross-platform code with targeted platform overrides.


**Read:** `references/platform-specific-code.md` for detailed step 6: platform-specific code reference material.

## STEP 7: Testing

Test components, hooks, and integration flows.


**Read:** `references/testing.md` for detailed step 7: testing reference material.

# All tests
yarn test

# Watch mode
yarn test --watch

# With coverage
yarn test --coverage

# Single file
yarn test src/components/ItemCard.test.tsx

# Update snapshots
yarn test -u
```

---

## STEP 8: CI/CD

> **Reference:** See [references/ci-cd.md](references/ci-cd.md) for full details.

---

## STEP 9: Version Upgrades

Guided React Native version migration.

### Upgrade Workflow

```bash
# 1. Check current version
npx react-native --version
cat node_modules/react-native/package.json | grep '"version"'

# 2. Use the upgrade helper for a diff of changes
# Visit: https://react-native-community.github.io/upgrade-helper/
# Select current version -> target version

# 3. Apply upgrade
npx react-native upgrade
# OR for more control:
yarn add react-native@<target-version>

# 4. Reinstall pods
cd ios && pod install --repo-update && cd ..

# 5. Clean build caches
cd android && ./gradlew clean && cd ..
rm -rf ios/build
watchman watch-del-all
yarn start --reset-cache

# 6. Verify
npx react-native run-ios
npx react-native run-android
yarn test
```

### Breaking Change Detection

Before upgrading, check for:

1. **Native dependency compatibility** — verify each native module supports the target RN version
2. **New Architecture migration** — RN 0.76+ defaults to New Architecture (Fabric + Turbo Modules)
3. **Hermes changes** — Hermes is default since 0.70; check for bytecode version changes
4. **Metro config changes** — `metro.config.js` format may change between versions
5. **Gradle/CocoaPods version requirements** — check minimum versions

```bash
# Check native module compatibility
npx react-native-doctor

# Verify all dependencies support new RN version
yarn outdated
```

---

## STEP 10: Brownfield Migration

> **Reference:** See [references/brownfield-migration.md](references/brownfield-migration.md) for full details.

---

## STEP 11: Debugging

> **Reference:** See [references/debugging.md](references/debugging.md) for full details.

---

## CRITICAL RULES

### MUST DO

- Use functional components with hooks exclusively — no class components for new code
- Define `StyleSheet.create()` outside the component body (created once, reused)
- Specify dependency arrays on every `useEffect`, `useCallback`, and `useMemo`
- Use `FlatList` or `FlashList` for scrollable lists — never `ScrollView` with mapped children for dynamic data
- Type all navigation routes using `ParamList` types
- Clean up subscriptions, timers, and listeners in `useEffect` return functions
- Profile with React DevTools Profiler before declaring performance acceptable
- Run `npx tsc --noEmit` and lint checks before every commit
- Use `react-native-reanimated` for animations — runs on UI thread, not JS thread
- Test on both iOS and Android before shipping
- Use Hermes as the JS engine (default since RN 0.70)
- Follow the Measure > Optimize > Re-measure > Validate cycle for performance work

### MUST NOT DO

- Use inline styles — use `StyleSheet.create()` instead (inline creates new objects every render)
- Skip `keyExtractor` on `FlatList` — use stable unique IDs, not array indices
- Block the JS thread with synchronous heavy computation — use `InteractionManager` or offload to native
- Use `Animated` from `react-native` for complex animations — use `react-native-reanimated` instead
- Import from barrel files (`index.ts` re-exports) — import directly from source modules to enable tree shaking
- Store sensitive data in `AsyncStorage` — use `react-native-keychain` or platform Keystore/Keychain
- Ignore TypeScript errors with `@ts-ignore` — fix the types or use `@ts-expect-error` with a comment
- Mutate state directly — always use setter functions from `useState` or dispatch actions
- Use `console.log` in production builds — strip with `babel-plugin-transform-remove-console`
- Commit code with lint warnings or TypeScript errors
