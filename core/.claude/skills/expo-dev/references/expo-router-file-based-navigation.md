# STEP 2: Expo Router — File-Based Navigation

### Route Conventions

| File Pattern | URL | Purpose |
|---|---|---|
| `app/index.tsx` | `/` | Home route |
| `app/settings.tsx` | `/settings` | Static route |
| `app/users/[id].tsx` | `/users/123` | Dynamic route |
| `app/docs/[...slug].tsx` | `/docs/a/b/c` | Catch-all route |
| `app/(auth)/login.tsx` | `/login` | Group (no URL segment) |
| `app/_layout.tsx` | — | Layout wrapper |
| `app/+not-found.tsx` | — | 404 handler |

### Layouts (`_layout.tsx`)

Every directory can have a layout that wraps its routes:

```tsx
// app/_layout.tsx — Root layout
import { Stack } from "expo-router/stack";

export default function RootLayout() {
  return <Stack />;
}
```

### Groups (Parentheses)

Groups organize routes without affecting URLs:

```
app/
  (auth)/
    login.tsx       # URL: /login
    register.tsx    # URL: /register
  (main)/
    index.tsx       # URL: /
    profile.tsx     # URL: /profile
```

### Navigation Methods

```tsx
import { Link, router } from "expo-router";

// Declarative — use in JSX
<Link href="/settings">Settings</Link>
<Link href="/users/42" asChild>
  <Pressable><Text>User 42</Text></Pressable>
</Link>

// Imperative — use in callbacks
router.push("/settings");        // Push onto stack
router.replace("/home");         // Replace current
router.back();                   // Go back
router.navigate("/settings");    // Navigate (deduplicates)
```

### Dynamic Route Parameters

```tsx
import { useLocalSearchParams } from "expo-router";

export default function UserPage() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <Text>User {id}</Text>;
}
```

### Tabs with NativeTabs (SDK 54+)

Prefer `NativeTabs` for platform-native tab bars:

```tsx
// app/_layout.tsx
import { NativeTabs } from "expo-router/unstable-native-tabs";

export default function Layout() {
  return (
    <NativeTabs>
      <NativeTabs.Trigger name="(home)">
        <NativeTabs.Trigger.Icon sf="house.fill" md="home" />
        <NativeTabs.Trigger.Label>Home</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(settings)">
        <NativeTabs.Trigger.Icon sf="gear" md="settings" />
        <NativeTabs.Trigger.Label>Settings</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
```

Nest a Stack inside each tab for headers:

```tsx
// app/(home)/_layout.tsx
import { Stack } from "expo-router/stack";

export default function HomeStack() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: "Home", headerLargeTitle: true }} />
      <Stack.Screen name="details" options={{ title: "Details" }} />
    </Stack>
  );
}
```

### Stack Navigation

```tsx
// app/(main)/_layout.tsx
import { Stack } from "expo-router/stack";

export default function MainStack() {
  return (
    <Stack screenOptions={{
      headerTransparent: true,
      headerBlurEffect: "regular",
      headerBackButtonDisplayMode: "minimal",
    }}>
      <Stack.Screen name="index" options={{ title: "Home" }} />
      <Stack.Screen name="modal" options={{ presentation: "modal" }} />
      <Stack.Screen name="sheet" options={{
        presentation: "formSheet",
        sheetGrabberVisible: true,
        sheetAllowedDetents: [0.5, 1.0],
      }} />
    </Stack>
  );
}
```

### Deep Linking and Universal Links

Configure the scheme in `app.json`:

```json
{
  "expo": {
    "scheme": "myapp",
    "ios": {
      "associatedDomains": ["applinks:example.com"]
    },
    "android": {
      "intentFilters": [{
        "action": "VIEW",
        "autoVerify": true,
        "data": [{ "scheme": "https", "host": "example.com", "pathPrefix": "/" }],
        "category": ["BROWSABLE", "DEFAULT"]
      }]
    }
  }
}
```

Expo Router automatically maps deep link paths to file routes.

### Typed Routes

Enable in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

Expo Router generates types automatically — use typed `href` props for compile-time route safety.

---

