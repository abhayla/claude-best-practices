---
name: expo-dev
description: >
  Build and deploy React Native apps with Expo including project setup, Expo Router
  navigation, EAS Build/Submit/Update, SDK upgrades, and push notifications. Use when
  building, deploying, or maintaining Expo-based mobile applications.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "expo, expo router, expo sdk, eas build, eas submit, app store deploy, expo upgrade"
argument-hint: "<feature-description or 'setup' or 'deploy' or 'upgrade' or 'navigate'>"
version: "1.0.0"
type: workflow
---

# Expo Development

Build, deploy, and maintain React Native applications with Expo SDK, Expo Router, and EAS.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup

Scaffold or verify an Expo project.


**Read:** `references/project-setup.md` for detailed step 1: project setup reference material.

# Set secrets for EAS builds (not committed to source)
eas secret:create --name API_KEY --value "sk-..." --scope project
eas secret:list
```

### Verify Setup

```bash
npx expo start        # Try Expo Go first
npx expo-doctor       # Diagnose issues
```

---

## STEP 2: Expo Router — File-Based Navigation

Routes live in the `app/` directory. Every file exports a default React component.


**Read:** `references/expo-router-file-based-navigation.md` for detailed step 2: expo router — file-based navigation reference material.

## STEP 3: UI Patterns


**Read:** `references/ui-patterns.md` for detailed step 3: ui patterns reference material.

## STEP 4: State Management and Storage


**Read:** `references/state-management-and-storage.md` for detailed step 4: state management and storage reference material.

## STEP 5: EAS Build and Submit

### Install EAS CLI

```bash
npm install -g eas-cli
eas login
npx eas-cli@latest init
```

### eas.json Configuration

```json
{
  "cli": {
    "version": ">= 16.0.1",
    "appVersionSource": "remote"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": { "simulator": true }
    },
    "production": {
      "autoIncrement": true,
      "ios": { "resourceClass": "m-medium" }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "your@email.com",
        "ascAppId": "1234567890"
      },
      "android": {
        "serviceAccountKeyPath": "./google-service-account.json",
        "track": "internal"
      }
    }
  }
}
```

### Build Commands

```bash
# Development build (custom dev client)
npx eas-cli@latest build -p ios --profile development
npx eas-cli@latest build -p android --profile development

# Preview (internal distribution)
npx eas-cli@latest build --profile preview

# Production
npx eas-cli@latest build -p ios --profile production
npx eas-cli@latest build -p android --profile production
```

### Submit to App Stores

```bash
# iOS: Build + submit to App Store Connect
npx eas-cli@latest build -p ios --profile production --submit

# Android: Build + submit to Play Store
npx eas-cli@latest build -p android --profile production --submit

# Submit an existing build
npx eas-cli@latest submit -p ios --latest
npx eas-cli@latest submit -p android --latest
```

### Credentials Management

```bash
eas credentials                    # Interactive credential manager
eas credentials --platform ios     # iOS certificates and provisioning profiles
eas credentials --platform android # Android keystore management
```

### Over-the-Air Updates (expo-updates)

```bash
# Publish an update to a branch
npx eas-cli@latest update --branch production --message "Fix login bug"

# Publish to preview
npx eas-cli@latest update --branch preview --message "New feature"

# Check update status
npx eas-cli@latest update:list
```

Configure update checking in app code:

```tsx
import * as Updates from "expo-updates";

async function checkForUpdates() {
  const update = await Updates.checkForUpdateAsync();
  if (update.isAvailable) {
    await Updates.fetchUpdateAsync();
    await Updates.reloadAsync();
  }
}
```

### EAS Workflows (CI/CD)

```yaml
# .eas/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

jobs:
  build-ios:
    type: build
    params:
      platform: ios
      profile: production

  submit-ios:
    type: submit
    needs: [build-ios]
    params:
      platform: ios
      profile: production

  build-android:
    type: build
    params:
      platform: android
      profile: production

  submit-android:
    type: submit
    needs: [build-android]
    params:
      platform: android
      profile: production
```

### Version Management

```bash
eas build:version:get                        # Check current versions
eas build:version:set -p ios --build-number 42  # Set manually
```

With `"appVersionSource": "remote"` in eas.json, version numbers auto-increment.

---

## STEP 6: SDK Upgrades

### Upgrade Process

```bash
# 1. Upgrade Expo SDK
npx expo install expo@latest

# 2. Fix all dependency versions
npx expo install --fix

# 3. Run diagnostics
npx expo-doctor

# 4. Clear caches and reinstall
rm -rf node_modules .expo
npm install
npx expo start --clear
```

### For Bare Workflow (ios/ and android/ directories exist)

```bash
# Regenerate native projects
npx expo prebuild --clean

# iOS: reinstall pods
cd ios && pod install --repo-update && cd ..

# Android: clean Gradle
cd android && ./gradlew clean && cd ..
```

If `ios/` and `android/` directories do NOT exist, the project uses Continuous Native Generation (CNG) — skip native rebuild steps.

### Breaking Changes Checklist

- [ ] Read release notes at https://expo.dev/changelog
- [ ] Check for removed APIs and update import paths
- [ ] Test camera, audio, video, and location features
- [ ] Verify navigation works correctly
- [ ] Review and remove outdated `expo.install.exclude` entries in package.json
- [ ] Remove outdated patches from `patches/` directory
- [ ] Run full test suite

### Deprecated Packages — Replace Immediately

| Old Package | Replacement |
|---|---|
| `expo-av` | `expo-audio` and `expo-video` |
| `expo-permissions` | Individual package permission APIs |
| `@expo/vector-icons` | `expo-symbols` or `expo-image` with `source="sf:name"` |
| `AsyncStorage` | `expo-sqlite/localStorage/install` |
| `expo-app-loading` | `expo-splash-screen` |
| `expo-linear-gradient` | `experimental_backgroundImage` + CSS gradients |

### Housekeeping After Upgrade

- Delete `sdkVersion` from `app.json` — let Expo manage it
- Remove implicit packages from `package.json`: `@babel/core`, `babel-preset-expo`, `expo-constants`
- Delete `babel.config.js` if it only contains `babel-preset-expo`
- Delete `metro.config.js` if it only contains Expo defaults
- Enable React Compiler in SDK 54+: `"experiments": { "reactCompiler": true }` in app.json
- SDK 53+: `autoprefixer` is no longer needed — remove from dependencies and PostCSS config
- SDK 53+: New Architecture is on by default — remove `"newArchEnabled": true` from app.json
- SDK 54+: `react-native-worklets` is required for `react-native-reanimated`

---

## STEP 7: Push Notifications


**Read:** `references/push-notifications.md` for detailed step 7: push notifications reference material.

## Common Expo Packages

| Package | Purpose | Install |
|---|---|---|
| `expo-camera` | Camera access and barcode scanning | `npx expo install expo-camera` |
| `expo-image-picker` | Select images/videos from library or camera | `npx expo install expo-image-picker` |
| `expo-location` | GPS and geocoding | `npx expo install expo-location` |
| `expo-file-system` | File read/write/download | `npx expo install expo-file-system` |
| `expo-audio` | Audio playback and recording | `npx expo install expo-audio` |
| `expo-video` | Video playback | `npx expo install expo-video` |
| `expo-haptics` | Haptic feedback (iOS) | `npx expo install expo-haptics` |
| `expo-image` | Optimized image component | `npx expo install expo-image` |
| `expo-notifications` | Push and local notifications | `npx expo install expo-notifications` |
| `expo-secure-store` | Encrypted key-value storage | `npx expo install expo-secure-store` |
| `expo-sqlite` | Local SQLite database | `npx expo install expo-sqlite` |
| `expo-splash-screen` | Splash screen control | `npx expo install expo-splash-screen` |

Always install with `npx expo install` — it resolves the correct version for your SDK.

---

## CRITICAL RULES

### MUST DO

- Use `npx expo install` for all package installations — ensures SDK-compatible versions
- Use `contentInsetAdjustmentBehavior="automatic"` on ScrollView/FlatList instead of SafeAreaView
- Use `_layout.tsx` files to define navigation stacks and tabs
- Ensure the app always has a route matching `/` so the app is never blank
- Use `expo-audio` and `expo-video` instead of `expo-av`
- Use `expo-image` instead of the intrinsic `<img>` element
- Use kebab-case for filenames (e.g., `comment-card.tsx`)
- Try Expo Go first before creating custom dev client builds
- Use `process.env.EXPO_OS` instead of `Platform.OS`
- Handle all async states (loading, error, success) in the UI
- Run `npx expo-doctor` after dependency changes
- Nest Stacks inside tabs for navigation headers — NativeTabs do not render headers
- Use `eas credentials` to manage signing certificates — do not manage manually

### MUST NOT DO

- Co-locate components, types, or utilities in the `app/` directory — only route and layout files belong there
- Use deprecated packages (`expo-av`, `expo-permissions`, `AsyncStorage`, `expo-app-loading`) — use their replacements
- Use `StyleSheet.create` for one-off styles — use inline styles instead
- Use `SafeAreaView` from React Native — use `react-native-safe-area-context` or `contentInsetAdjustmentBehavior`
- Use `Dimensions.get()` — use `useWindowDimensions` instead
- Use legacy React Native shadow or elevation props — use `boxShadow` style
- Use `Platform.OS` — use `process.env.EXPO_OS` instead
- Hardcode API keys in source — use EAS secrets or `.env` with `expo-constants`
- Skip `npx expo install --fix` after SDK upgrades — dependency mismatches cause silent failures
- Use CSS or Tailwind class-based styling (unless explicitly configured with NativeWind)
- Dynamically add/remove tabs at runtime — this remounts the navigator and loses state

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---|---|---|
| `npx expo start` fails with dependency errors | SDK version mismatch in packages | Run `npx expo install --fix` then `npx expo-doctor` |
| Metro bundler crashes or hangs | Stale cache or corrupted node_modules | `rm -rf node_modules .expo && npm install && npx expo start --clear` |
| Native module not found in Expo Go | Package requires custom native code | Create dev client: `npx eas-cli@latest build -p ios --profile development` |
| EAS build fails on credentials | Missing or expired certificates | Run `eas credentials` to regenerate; for iOS use `eas credentials --platform ios` |
| OTA update not applying | Branch mismatch or runtime version conflict | Verify `eas update:list`; ensure `runtimeVersion` in app.json matches the build |
| `expo-notifications` token is undefined | Running on simulator or missing permissions | Test on physical device; check `Device.isDevice` before requesting token |
| iOS build rejected by App Store | Missing privacy descriptions or invalid icons | Add `NSCameraUsageDescription` etc. in `app.json` `ios.infoPlist`; verify icon is 1024x1024 with no alpha |
| Android build fails on Gradle | Outdated Gradle cache or JDK mismatch | `cd android && ./gradlew clean`; ensure JDK 17 is installed |
| Tab icons not showing on Android | Missing `md` prop on NativeTabs.Trigger.Icon | Add Material Symbol name: `<NativeTabs.Trigger.Icon sf="house.fill" md="home" />` |
| Headers missing in tabbed app | Using NativeTabs without nested Stack | Add a `<Stack>` layout inside each tab group directory |
| `RenderFlex overflowed` | Content exceeds screen bounds | Wrap in `ScrollView` with `contentInsetAdjustmentBehavior="automatic"` |
| Deep links not opening the app | Missing scheme or intent filter config | Verify `scheme` in app.json; for universal links check `associatedDomains` config |
