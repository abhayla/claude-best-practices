# STEP 3: Navigation

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

