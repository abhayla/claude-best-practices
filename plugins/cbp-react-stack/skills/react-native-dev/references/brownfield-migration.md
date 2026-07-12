# Brownfield Migration

Integrate React Native into existing native iOS/Android apps.

### iOS Integration

```ruby
# In existing iOS project Podfile
require_relative '../node_modules/react-native/scripts/react_native_pods'

target 'ExistingApp' do
  use_react_native!(path: '../node_modules/react-native')
end
```

```swift
// AppDelegate or SceneDelegate — present RN view
import React

func showReactNativeView() {
    let bundleURL = RCTBundleURLProvider.sharedSettings().jsBundleURL(
        forBundleRoot: "index",
        fallbackResource: nil
    )
    let rootView = RCTRootView(
        bundleURL: bundleURL!,
        moduleName: "MyRNModule",
        initialProperties: ["screenId": "settings"],
        launchOptions: nil
    )
    let vc = UIViewController()
    vc.view = rootView
    present(vc, animated: true)
}
```

### Android Integration

```kotlin
// In existing Activity or Fragment
class ReactNativeActivity : ReactActivity() {
    override fun getMainComponentName(): String = "MyRNModule"

    override fun createReactActivityDelegate(): ReactActivityDelegate {
        return DefaultReactActivityDelegate(this, mainComponentName)
    }
}
```

```gradle
// android/app/build.gradle — add RN dependency
dependencies {
    implementation project(':ReactAndroid')
    implementation("com.facebook.react:hermes-android")
}
```

### Native Module Bridge (communicate between native and RN)

```tsx
// TypeScript side
import { NativeModules, NativeEventEmitter } from 'react-native';

const { AnalyticsModule } = NativeModules;
const analyticsEmitter = new NativeEventEmitter(AnalyticsModule);

// Call native method
AnalyticsModule.trackEvent('screen_view', { screen: 'home' });

// Listen for native events
const subscription = analyticsEmitter.addListener('onAnalyticsReady', (data) => {
  console.log('Analytics ready:', data);
});

// Clean up
subscription.remove();
```

### Module Federation Strategy

1. **Start small** — migrate one screen or feature at a time
2. **Shared navigation** — use deep links to transition between native and RN screens
3. **Shared state** — pass initial props from native; use native modules for ongoing communication
4. **Independent builds** — bundle RN separately, load at runtime in the native app
5. **Feature flags** — gate RN screens behind flags for gradual rollout
