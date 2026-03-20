# STEP 3: Widget Development

### GoRouter Navigation Setup

```dart
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isLoggedIn = authState.isAuthenticated;
      final isLoginRoute = state.matchedLocation == '/login';
      if (!isLoggedIn && !isLoginRoute) return '/login';
      if (isLoggedIn && isLoginRoute) return '/';
      return null;
    },
    routes: [
      ShellRoute(
        builder: (context, state, child) => AppScaffold(child: child),
        routes: [
          GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
          GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
        ],
      ),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(
        path: '/item/:id',
        builder: (_, state) => ItemScreen(id: state.pathParameters['id']!),
      ),
    ],
  );
});
```

### Navigation Methods

| Method | Effect | Use Case |
|--------|--------|----------|
| `context.go('/path')` | Replace stack | Tab switching, auth redirect |
| `context.push('/path')` | Push onto stack | Detail screens |
| `context.pop()` | Pop current | Back navigation |
| `context.pushReplacement('/path')` | Replace top | Post-login redirect |

### Material Design 3 Theme

```dart
class AppTheme {
  static ThemeData light() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4),
      brightness: Brightness.light,
    );
    return ThemeData(
      colorScheme: colorScheme,
      useMaterial3: true,
      appBarTheme: AppBarTheme(
        centerTitle: true,
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
      ),
      cardTheme: CardTheme(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        color: colorScheme.surfaceContainerLow,
      ),
    );
  }

  static ThemeData dark() {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4),
      brightness: Brightness.dark,
    );
    return ThemeData(colorScheme: colorScheme, useMaterial3: true);
  }
}
```

### Optimized Widget Pattern

```dart
class ItemCard extends StatelessWidget {
  const ItemCard({
    super.key,
    required this.title,
    required this.subtitle,
    this.onTap,
  });

  final String title;
  final String subtitle;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: ListTile(
        title: Text(title, style: theme.textTheme.titleMedium),
        subtitle: Text(subtitle, style: theme.textTheme.bodySmall),
        onTap: onTap,
      ),
    );
  }
}
```

### Responsive Layout

```dart
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.mobile,
    required this.tablet,
    this.desktop,
  });

  final Widget mobile;
  final Widget tablet;
  final Widget? desktop;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1200 && desktop != null) return desktop!;
        if (constraints.maxWidth >= 600) return tablet;
        return mobile;
      },
    );
  }
}
```

### Keys for Lists

```dart
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    final item = items[index];
    return ItemCard(
      key: ValueKey(item.id),  // MUST use key for list items
      title: item.title,
      subtitle: item.subtitle,
    );
  },
)
```

### Platform-Specific Widgets

```dart
Widget buildButton(BuildContext context) {
  if (Theme.of(context).platform == TargetPlatform.iOS) {
    return CupertinoButton(
      onPressed: _onPressed,
      child: const Text('Action'),
    );
  }
  return FilledButton(
    onPressed: _onPressed,
    child: const Text('Action'),
  );
}
```

---

