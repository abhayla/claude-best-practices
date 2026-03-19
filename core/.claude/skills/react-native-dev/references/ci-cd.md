# CI/CD for React Native

Configure automated builds and delivery.

### GitHub Actions — Build & Test

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: yarn }
      - run: yarn install --frozen-lockfile
      - run: yarn lint
      - run: yarn typecheck
      - run: yarn test --coverage

  build-android:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: yarn }
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: 17 }
      - run: yarn install --frozen-lockfile
      - run: cd android && ./gradlew assembleRelease
      - uses: actions/upload-artifact@v4
        with:
          name: android-release
          path: android/app/build/outputs/apk/release/

  build-ios:
    runs-on: macos-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: yarn }
      - run: yarn install --frozen-lockfile
      - run: cd ios && pod install
      - run: |
          xcodebuild -workspace ios/MyApp.xcworkspace \
            -scheme MyApp -configuration Release \
            -sdk iphonesimulator -derivedDataPath build \
            -destination 'platform=iOS Simulator,name=iPhone 15'
```

### Fastlane Integration

```ruby
# ios/fastlane/Fastfile
default_platform(:ios)

platform :ios do
  desc "Build and upload to TestFlight"
  lane :beta do
    increment_build_number
    build_app(
      workspace: "MyApp.xcworkspace",
      scheme: "MyApp",
      export_method: "app-store"
    )
    upload_to_testflight(skip_waiting_for_build_processing: true)
  end
end

# android/fastlane/Fastfile
platform :android do
  desc "Build and upload to Play Store internal track"
  lane :beta do
    gradle(task: "clean bundleRelease")
    upload_to_play_store(track: "internal", aab: "app/build/outputs/bundle/release/app-release.aab")
  end
end
```

### Code Signing (iOS)

```bash
# Use match for team code signing
fastlane match init
fastlane match appstore   # For production
fastlane match development # For development
```
