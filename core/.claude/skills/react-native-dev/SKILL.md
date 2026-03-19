---
name: react-native-dev
description: >
  React Native development workflow: project setup, functional components, hooks,
  React Navigation, state management (Zustand/Redux Toolkit), performance profiling
  (Hermes, Reanimated 3, FPS), platform-specific code, testing, CI/CD, version
  upgrades, brownfield migration, and debugging. Based on callstackincubator/agent-skills
  and community best practices.
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

### Functional Component Template

```tsx
import React, { useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';

interface ItemCardProps {
  title: string;
  subtitle: string;
  onPress?: () => void;
}

export const ItemCard: React.FC<ItemCardProps> = React.memo(({ title, subtitle, onPress }) => {
  const handlePress = useCallback(() => {
    onPress?.();
  }, [onPress]);

  return (
    <Pressable onPress={handlePress} style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.subtitle}>{subtitle}</Text>
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginVertical: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
```

### Hooks Reference

| Hook | Use Case | Performance Note |
|------|----------|------------------|
| `useState` | Local component state | Triggers re-render on change |
| `useEffect` | Side effects (API calls, subscriptions) | Always specify dependency array |
| `useCallback` | Memoize event handlers | Use when passing callbacks as props |
| `useMemo` | Memoize expensive computations | Use for derived data, not simple values |
| `useRef` | Mutable values, DOM refs | Does NOT trigger re-render |
| `useReducer` | Complex local state logic | Alternative to multiple `useState` |

### Optimized List Rendering

```tsx
import { FlatList, ListRenderItem } from 'react-native';

// GOOD: Extract renderItem with proper typing
const renderItem: ListRenderItem<Item> = useCallback(({ item }) => (
  <ItemCard
    key={item.id}
    title={item.title}
    subtitle={item.subtitle}
    onPress={() => onItemSelect(item.id)}
  />
), [onItemSelect]);

// GOOD: Extract keyExtractor
const keyExtractor = useCallback((item: Item) => item.id, []);

<FlatList
  data={items}
  renderItem={renderItem}
  keyExtractor={keyExtractor}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={5}
  removeClippedSubviews={true}
  getItemLayout={(_, index) => ({    // If fixed height, improves scroll perf
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })}
/>

// For large lists (1000+ items), prefer FlashList from Shopify
// yarn add @shopify/flash-list
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={renderItem}
  keyExtractor={keyExtractor}
  estimatedItemSize={80}
/>
```

### StyleSheet Best Practices

```tsx
// GOOD: Define styles outside component (created once)
const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  row: { flexDirection: 'row', alignItems: 'center' },
});

// BAD: Inline styles (new object every render)
// <View style={{ flex: 1, padding: 16 }}>

// Dynamic styles: use a factory or useMemo
const dynamicStyles = useMemo(() => ({
  container: { backgroundColor: isActive ? '#e0f0ff' : '#fff' },
}), [isActive]);
```

---

## STEP 3: Navigation

Configure React Navigation with typed routes and deep linking.

### Stack + Tab Navigator Setup

```tsx
// navigation/types.ts
export type RootStackParamList = {
  Main: undefined;
  ItemDetail: { id: string };
  Settings: undefined;
  Auth: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  Search: { query?: string };
  Profile: undefined;
};

// navigation/RootNavigator.tsx
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false }}>
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export function RootNavigator() {
  const isAuthenticated = useAuth();

  return (
    <NavigationContainer>
      <Stack.Navigator>
        {isAuthenticated ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
            <Stack.Screen name="ItemDetail" component={ItemDetailScreen} />
            <Stack.Screen name="Settings" component={SettingsScreen} />
          </>
        ) : (
          <Stack.Screen name="Auth" component={AuthScreen} options={{ headerShown: false }} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
```

### Typed Navigation Hooks

```tsx
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { RouteProp } from '@react-navigation/native';

// Typed navigation hook
type ItemDetailRouteProp = RouteProp<RootStackParamList, 'ItemDetail'>;
type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

function ItemDetailScreen() {
  const route = useRoute<ItemDetailRouteProp>();
  const navigation = useNavigation<NavigationProp>();
  const { id } = route.params;

  return <Text>Item {id}</Text>;
}
```

### Deep Linking Configuration

```tsx
const linking = {
  prefixes: ['myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Main: {
        screens: {
          Home: 'home',
          Search: 'search/:query?',
          Profile: 'profile',
        },
      },
      ItemDetail: 'item/:id',
      Auth: 'auth',
    },
  },
};

<NavigationContainer linking={linking} fallback={<LoadingScreen />}>
  {/* ... */}
</NavigationContainer>
```

### Drawer Navigator

```bash
yarn add @react-navigation/drawer react-native-gesture-handler
```

```tsx
import { createDrawerNavigator } from '@react-navigation/drawer';

const Drawer = createDrawerNavigator();

function AppDrawer() {
  return (
    <Drawer.Navigator>
      <Drawer.Screen name="Home" component={HomeScreen} />
      <Drawer.Screen name="Settings" component={SettingsScreen} />
    </Drawer.Navigator>
  );
}
```

---

## STEP 4: State Management

Choose the right state management approach based on complexity.

### Decision Guide

| Approach | When to Use |
|----------|-------------|
| `useState` / `useReducer` | Local component state only |
| Context API | Lightweight shared state (theme, locale, auth status) |
| Zustand | Medium complexity — most RN apps (recommended default) |
| Redux Toolkit | Large teams, complex state with middleware needs |

### Zustand (Recommended)

```tsx
// store/useAppStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface AppState {
  user: User | null;
  theme: 'light' | 'dark';
  setUser: (user: User | null) => void;
  toggleTheme: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      theme: 'light',
      setUser: (user) => set({ user }),
      toggleTheme: () => set((state) => ({
        theme: state.theme === 'light' ? 'dark' : 'light',
      })),
    }),
    {
      name: 'app-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Usage in component — only subscribes to what it reads
function UserBadge() {
  const user = useAppStore((state) => state.user); // Selective subscription
  if (!user) return null;
  return <Text>{user.name}</Text>;
}
```

### Redux Toolkit Pattern

```tsx
// store/slices/authSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.login(credentials);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: { user: null, status: 'idle', error: null } as AuthState,
  reducers: {
    logout: (state) => { state.user = null; state.status = 'idle'; },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => { state.status = 'loading'; })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
```

### Context API (Lightweight)

```tsx
// Use for values that change infrequently (theme, locale, auth status)
const ThemeContext = React.createContext<{ theme: Theme; toggle: () => void } | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(lightTheme);
  const toggle = useCallback(() => {
    setTheme((prev) => (prev === lightTheme ? darkTheme : lightTheme));
  }, []);

  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
```

---

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

### Animation Performance (Reanimated 3)

```tsx
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnUI,
} from 'react-native-reanimated';

function AnimatedCard() {
  const scale = useSharedValue(1);
  const opacity = useSharedValue(1);

  // Runs on UI thread — no JS thread blocking
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.95);
    opacity.value = withTiming(0.8, { duration: 100 });
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
    opacity.value = withTiming(1, { duration: 100 });
  };

  return (
    <Pressable onPressIn={handlePressIn} onPressOut={handlePressOut}>
      <Animated.View style={[styles.card, animatedStyle]}>
        <Text>Animated Card</Text>
      </Animated.View>
    </Pressable>
  );
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

## STEP 7: Testing

Test components, hooks, and integration flows.

### Jest + React Native Testing Library

```tsx
// components/ItemCard.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react-native';
import { ItemCard } from './ItemCard';

describe('ItemCard', () => {
  it('renders title and subtitle', () => {
    render(<ItemCard title="Test Title" subtitle="Test Sub" />);

    expect(screen.getByText('Test Title')).toBeTruthy();
    expect(screen.getByText('Test Sub')).toBeTruthy();
  });

  it('calls onPress when pressed', () => {
    const onPress = jest.fn();
    render(<ItemCard title="Tap Me" subtitle="Sub" onPress={onPress} />);

    fireEvent.press(screen.getByText('Tap Me'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('renders correctly without onPress', () => {
    const { toJSON } = render(<ItemCard title="Static" subtitle="Card" />);
    expect(toJSON()).toMatchSnapshot();
  });
});
```

### Hook Testing

```tsx
import { renderHook, act } from '@testing-library/react-native';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments count', () => {
    const { result } = renderHook(() => useCounter());

    act(() => { result.current.increment(); });
    expect(result.current.count).toBe(1);
  });
});
```

### Integration Test with Navigation

```tsx
import { NavigationContainer } from '@react-navigation/native';
import { render, fireEvent, waitFor } from '@testing-library/react-native';

function renderWithNavigation(component: React.ReactElement) {
  return render(
    <NavigationContainer>{component}</NavigationContainer>
  );
}

it('navigates to detail screen on item press', async () => {
  renderWithNavigation(<RootNavigator />);

  fireEvent.press(screen.getByText('First Item'));
  await waitFor(() => {
    expect(screen.getByText('Item Detail')).toBeTruthy();
  });
});
```

### Run Tests

```bash
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
