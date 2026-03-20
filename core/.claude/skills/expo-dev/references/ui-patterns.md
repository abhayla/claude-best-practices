# STEP 3: UI Patterns

### ScrollView as Root

Every Stack screen should start with a ScrollView:

```tsx
import { ScrollView, Text } from "react-native";
import { Stack } from "expo-router";

export default function HomeScreen() {
  return (
    <>
      <Stack.Screen options={{ title: "Home" }} />
      <ScrollView contentInsetAdjustmentBehavior="automatic">
        <Text>Content here</Text>
      </ScrollView>
    </>
  );
}
```

Use `contentInsetAdjustmentBehavior="automatic"` on ScrollView, FlatList, and SectionList instead of wrapping in SafeAreaView.

### Splash Screen

```tsx
import * as SplashScreen from "expo-splash-screen";
import { useEffect } from "react";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [loaded] = useFonts({ Inter: require("./assets/Inter.ttf") });

  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);

  if (!loaded) return null;
  return <Stack />;
}
```

### App Icons

- **iOS**: Provide a 1024x1024 `icon.png` in `app.json` `expo.icon`
- **Android Adaptive Icons**: Provide `foregroundImage` (1024x1024 with padding) in `expo.android.adaptiveIcon`
- Use `npx expo customize` to generate platform-specific icon variants

### Styling Rules

- Use inline styles (not `StyleSheet.create`) unless reusing styles
- Prefer `flex` and `gap` over margin/padding
- Use `{ borderCurve: "continuous" }` for rounded corners
- Use `boxShadow` style prop — NEVER legacy React Native shadow/elevation
- Use `process.env.EXPO_OS` instead of `Platform.OS`
- Use `useWindowDimensions` instead of `Dimensions.get()`

---

