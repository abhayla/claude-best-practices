# STEP 6: Platform-Specific Code

### Platform.OS Branching

```tsx
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  shadow: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
    },
    android: {
      elevation: 4,
    },
    default: {},
  }),
  header: {
    paddingTop: Platform.OS === 'ios' ? 44 : 0,
  },
});
```

### Platform-Specific File Extensions

```
components/
  Camera.tsx            # Shared interface/types
  Camera.ios.tsx        # iOS implementation (AVFoundation)
  Camera.android.tsx    # Android implementation (CameraX)
```

Metro automatically resolves `.ios.tsx` / `.android.tsx` at build time.

### Native Modules (Turbo Modules)

```tsx
// For performance-critical native code, create Turbo Modules (New Architecture)
import { TurboModuleRegistry } from 'react-native';

interface CryptoSpec extends TurboModule {
  hash(input: string, algorithm: string): Promise<string>;
}

export default TurboModuleRegistry.getEnforcing<CryptoSpec>('CryptoModule');
```

### Conditional Feature Detection

```tsx
import { Platform, UIManager } from 'react-native';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}
```

---

