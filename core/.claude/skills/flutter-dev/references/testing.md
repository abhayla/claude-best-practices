# STEP 4: Testing

### Widget Test

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  group('ItemCard', () {
    testWidgets('renders title and subtitle', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ItemCard(title: 'Test Title', subtitle: 'Test Sub'),
          ),
        ),
      );

      expect(find.text('Test Title'), findsOneWidget);
      expect(find.text('Test Sub'), findsOneWidget);
    });

    testWidgets('calls onTap when tapped', (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ItemCard(
              title: 'Tap Me',
              subtitle: 'Sub',
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Tap Me'));
      await tester.pumpAndSettle();
      expect(tapped, isTrue);
    });
  });
}
```

### Provider/Notifier Unit Test

```dart
void main() {
  test('TodoList adds and fetches todos', () async {
    final container = ProviderContainer(
      overrides: [
        todoRepositoryProvider.overrideWithValue(MockTodoRepository()),
      ],
    );
    addTearDown(container.dispose);

    final notifier = container.read(todoListProvider.notifier);
    await notifier.addTodo(Todo(id: '1', title: 'Test'));

    final todos = await container.read(todoListProvider.future);
    expect(todos, hasLength(1));
  });
}
```

### BLoC Test

```dart
import 'package:bloc_test/bloc_test.dart';

void main() {
  blocTest<AuthBloc, AuthState>(
    'emits [AuthLoading, AuthAuthenticated] on successful login',
    build: () => AuthBloc(MockAuthRepository()),
    act: (bloc) => bloc.add(
      LoginRequested(email: 'a@b.com', password: 'pass'),
    ),
    expect: () => [isA<AuthLoading>(), isA<AuthAuthenticated>()],
  );
}
```

### Integration Test

```dart
// integration_test/app_test.dart
import 'package:integration_test/integration_test.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('full login flow', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MyApp()));
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('email_field')), 'user@test.com');
    await tester.enterText(find.byKey(const Key('password_field')), 'password');
    await tester.tap(find.byKey(const Key('login_button')));
    await tester.pumpAndSettle();

    expect(find.text('Home'), findsOneWidget);
  });
}
```

### Run Tests

```bash
