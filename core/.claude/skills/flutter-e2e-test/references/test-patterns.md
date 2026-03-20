# STEP 3: Test Patterns

### Login Flow

```dart
testWidgets('complete login flow', (tester) async {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  final loginRobot = LoginRobot(tester);
  await loginRobot.login(email: 'test@example.com', password: 'Passw0rd!');

  // Verify landed on home
  expect(find.bySemanticsLabel('Home screen'), findsOneWidget);
});
```

### Navigation Flow

```dart
testWidgets('bottom nav switches screens', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Navigate to settings
  await tester.tap(find.byKey(const Key('nav_settings')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('settings_screen')), findsOneWidget);

  // Navigate back to home
  await tester.tap(find.byKey(const Key('nav_home')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('home_screen')), findsOneWidget);
});
```

### Form Submission with Validation

```dart
testWidgets('form shows validation errors then submits', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Submit empty form — expect errors
  await tester.tap(find.byKey(const Key('submit_button')));
  await tester.pumpAndSettle();
  expect(find.text('Required field'), findsWidgets);

  // Fill valid data and submit
  await tester.enterText(find.byKey(const Key('name_field')), 'Jane Doe');
  await tester.enterText(find.byKey(const Key('email_field')), 'jane@test.com');
  await tester.tap(find.byKey(const Key('submit_button')));
  await tester.pumpAndSettle();
  expect(find.text('Success'), findsOneWidget);
});
```

### List Scrolling

```dart
testWidgets('scrolls to item and taps it', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  await tester.scrollUntilVisible(
    find.byKey(const Key('list_item_25')),
    300.0,
    scrollable: find.byType(Scrollable).first,
    maxScrolls: 50,
  );
  await tester.tap(find.byKey(const Key('list_item_25')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('detail_screen')), findsOneWidget);
});
```

### Error State Handling

```dart
testWidgets('displays error state and retries', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  // Set up mock to fail first, succeed on retry
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Verify error state is shown
  expect(find.bySemanticsLabel('Error message'), findsOneWidget);
  expect(find.byKey(const Key('retry_button')), findsOneWidget);

  // Tap retry
  await tester.tap(find.byKey(const Key('retry_button')));
  await tester.pumpAndSettle(const Duration(seconds: 5));
  expect(find.byKey(const Key('content_loaded')), findsOneWidget);
});
```

---

