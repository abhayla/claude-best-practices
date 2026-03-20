# STEP 6: Compose Navigation

### Route Definitions

```kotlin
@Serializable object Home
@Serializable object Settings
@Serializable data class Profile(val userId: String)
@Serializable data class ItemDetail(val itemId: Int, val title: String)
```

### NavHost Setup

```kotlin
@Composable
fun AppNavHost(
    navController: NavHostController = rememberNavController(),
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Home,
        modifier = modifier
    ) {
        composable<Home> {
            HomeScreen(onNavigateToProfile = { userId ->
                navController.navigate(Profile(userId))
            })
        }
        composable<Profile> { backStackEntry ->
            val profile: Profile = backStackEntry.toRoute()
            ProfileScreen(userId = profile.userId)
        }
        composable<ItemDetail> { backStackEntry ->
            val detail: ItemDetail = backStackEntry.toRoute()
            ItemDetailScreen(itemId = detail.itemId, title = detail.title)
        }
    }
}
```

### Argument Handling in ViewModels

```kotlin
@HiltViewModel
class ProfileViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val route = savedStateHandle.toRoute<Profile>()
    val userId = route.userId
}
```

### Bottom Navigation

```kotlin
@Composable
fun MainScreen() {
    val navController = rememberNavController()
    Scaffold(
        bottomBar = {
            NavigationBar {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentDestination = navBackStackEntry?.destination

                NavigationBarItem(
                    icon = { Icon(Icons.Default.Home, contentDescription = "Home") },
                    label = { Text("Home") },
                    selected = currentDestination?.hasRoute<Home>() == true,
                    onClick = {
                        navController.navigate(Home) {
                            popUpTo(navController.graph.findStartDestination().id) {
                                saveState = true
                            }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    ) { padding ->
        AppNavHost(navController = navController, modifier = Modifier.padding(padding))
    }
}
```

### Deep Links

```kotlin
composable<Profile>(
    deepLinks = listOf(navDeepLink<Profile>(basePath = "https://example.com/profile"))
) { backStackEntry ->
    val profile: Profile = backStackEntry.toRoute()
    ProfileScreen(userId = profile.userId)
}
```

Declare in `AndroidManifest.xml`:

```xml
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" android:host="example.com" android:pathPrefix="/profile" />
    </intent-filter>
</activity>
```

### Nested Graphs

```kotlin
NavHost(navController = navController, startDestination = Home) {
    composable<Home> { HomeScreen() }

    navigation<AuthGraph>(startDestination = Login) {
        composable<Login> {
            LoginScreen(onLoginSuccess = {
                navController.navigate(Home) {
                    popUpTo<AuthGraph> { inclusive = true }
                }
            })
        }
        composable<Register> { RegisterScreen() }
    }
}

@Serializable object AuthGraph
@Serializable object Login
@Serializable object Register
```

### Dialog Navigation

Use `dialog()` for declarative dialog routing instead of imperative show/hide:

```kotlin
@Serializable data class ConfirmDelete(val itemId: String)

NavHost(navController, startDestination = Home) {
    composable<Home> { /* ... */ }
    dialog<ConfirmDelete> { backStackEntry ->
        val route = backStackEntry.toRoute<ConfirmDelete>()
        ConfirmDeleteDialog(
            itemId = route.itemId,
            onConfirm = { navController.popBackStack() },
            onDismiss = { navController.popBackStack() }
        )
    }
}
```

### Adaptive NavigationSuiteScaffold

Use `NavigationSuiteScaffold` for responsive navigation (bottom bar on phones, rail on tablets):

```kotlin
@Composable
fun AdaptiveApp() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    NavigationSuiteScaffold(
        navigationSuiteItems = {
            item(
                icon = { Icon(Icons.Default.Home, contentDescription = "Home") },
                label = { Text("Home") },
                selected = currentDestination?.hasRoute<Home>() == true,
                onClick = { navController.navigate(Home) }
            )
            item(
                icon = { Icon(Icons.Default.Settings, contentDescription = "Settings") },
                label = { Text("Settings") },
                selected = currentDestination?.hasRoute<Settings>() == true,
                onClick = { navController.navigate(Settings) }
            )
        }
    ) {
        AppNavHost(navController = navController)
    }
}
```

---

