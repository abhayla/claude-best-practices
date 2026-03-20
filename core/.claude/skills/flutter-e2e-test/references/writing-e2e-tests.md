# STEP 2: Writing E2E Tests

### Finding Elements by Semantics (Self-Healing)

Use semantic labels and keys instead of text or widget type. Semantic finders survive UI refactors because they bind to meaning, not structure.

```dart
// GOOD: Semantic-based — survives widget type changes
find.bySemanticsLabel('Email input');
find.bySemanticsLabel(RegExp(r'Submit'));
find.byKey(const Key('login_button'));

// BAD: Brittle — breaks when text or widget type changes
find.text('Submit');
find.byType(ElevatedButton);
```

### Annotating Widgets for Testability

```dart
Semantics(
  label: 'Email input',
  child: TextField(
    key: const Key('email_field'),
    decoration: const InputDecoration(labelText: 'Email'),
  ),
)
```

### Core Interactions

```dart
// Tap
await tester.tap(find.byKey(const Key('login_button')));
await tester.pumpAndSettle();

// Enter text
await tester.enterText(find.byKey(const Key('email_field')), 'user@test.com');

// Scroll until visible
await tester.scrollUntilVisible(
  find.byKey(const Key('item_42')),
  200.0,  // scroll delta
  scrollable: find.byType(Scrollable),
);

// Swipe / drag
await tester.drag(find.byKey(const Key('dismissible_card')), const Offset(-300, 0));
await tester.pumpAndSettle();

// Long press
await tester.longPress(find.bySemanticsLabel('Context menu target'));
await tester.pumpAndSettle();
```

### Batch Operations (Token Efficiency)

Group 5+ sequential actions into helper methods to reduce token usage and improve readability.

```dart
/// Robot pattern: batch login actions into a single call
class LoginRobot {
  final WidgetTester tester;
  const LoginRobot(this.tester);

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await tester.enterText(find.byKey(const Key('email_field')), email);
    await tester.enterText(find.byKey(const Key('password_field')), password);
    await tester.tap(find.byKey(const Key('login_button')));
    await tester.pumpAndSettle(const Duration(seconds: 3));
    expect(find.byKey(const Key('home_screen')), findsOneWidget);
  }
}
```

### MCP-Based Semantic Element Recognition

When using MCP tools that expose the accessibility tree, query elements by their semantic role rather than coordinates or indices.

```dart
// Accessibility tree approach: query by role + label
// The MCP server exposes the Flutter accessibility tree as a structured object.
// Use SemanticsNode queries to locate elements by role, label, and value.

import 'package:flutter/rendering.dart';

SemanticsNode findNodeByLabel(SemanticsNode root, String label) {
  if (root.label == label) return root;
  for (final child in root.debugListChildrenInOrder(DebugSemanticsDumpOrder.traversalOrder)) {
    final result = findNodeByLabel(child, label);
    if (result.label == label) return result;
  }
  throw StateError('No SemanticsNode with label "$label"');
}
```

---

