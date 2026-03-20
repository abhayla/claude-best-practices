# STEP 5: Monkey / Fuzz Testing

## STEP 5: Monkey / Fuzz Testing

Randomly interact with the app to discover crashes and unhandled exceptions.

```dart
testWidgets('monkey test — random interactions for 60s', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  final random = Random(42); // Deterministic seed for reproducibility
  final stopwatch = Stopwatch()..start();
  var actions = 0;

  while (stopwatch.elapsed < const Duration(seconds: 60)) {
    try {
      final size = tester.view.physicalSize / tester.view.devicePixelRatio;
      final x = random.nextDouble() * size.width;
      final y = random.nextDouble() * size.height;

      switch (random.nextInt(4)) {
        case 0: // Tap at random location
          await tester.tapAt(Offset(x, y));
          break;
        case 1: // Drag gesture
          await tester.dragFrom(Offset(x, y), Offset(
            (random.nextDouble() - 0.5) * 200,
            (random.nextDouble() - 0.5) * 200,
          ));
          break;
        case 2: // Enter text if text field focused
          await tester.enterText(find.byType(EditableText).first, 'fuzz${random.nextInt(999)}');
          break;
        case 3: // Back navigation
          final backButton = find.byTooltip('Back');
          if (backButton.evaluate().isNotEmpty) {
            await tester.tap(backButton);
          }
          break;
      }
      await tester.pumpAndSettle(const Duration(milliseconds: 100));
      actions++;
    } catch (e) {
      // Log but continue — monkey testing should be resilient
      debugPrint('Monkey action $actions failed: $e');
      await tester.pumpAndSettle();
    }
  }

  debugPrint('Monkey test completed: $actions actions in ${stopwatch.elapsed}');
});
```

---

