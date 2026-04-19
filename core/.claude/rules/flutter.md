---
globs: ["**/lib/**/*.dart"]
description: Flutter/Dart development patterns and conventions.
---

# Flutter Rules

## Implementation Order
Always implement domain → data → presentation. Never start with UI.

## State Management (Riverpod)
- One `NotifierProvider` with a single state class per feature
- Declare all providers in a per-feature `providers.dart` — single source of truth
- Use `copyWith()` for state transitions — never mutate state directly
- Use `.select()` for selective rebuilds — never watch entire state when only one field is needed
- Handle all `AsyncValue` states (`data`, `loading`, `error`) — never ignore error state

## Generated Code
- Never edit `*.g.dart`, `*.freezed.dart`, or `*.drift.dart` files
- After modifying annotated classes: `dart run build_runner build --delete-conflicting-outputs`
- Freezed 3.x: use `abstract class` with `_$Mixin` — custom methods go in extensions, not the class body

## GoRouter Navigation
- Define route paths as static constants in `AppRoutes` — never inline string literals
- Use `refreshListenable` tied to auth state for reactive redirects
- Pass data via `state.extra` with a cache wrapper — `extra` becomes `null` on GoRouter rebuild

## Offline-First (Drift)
- Write to local Drift database first, enqueue sync operation, sync to server in background
- One `DatabaseAccessor` DAO per feature — never query `AppDatabase` directly from widgets
- Override `databaseProvider` in `ProviderScope` — default provider must throw `UnimplementedError`
- Include `MigrationStrategy` with explicit `onUpgrade` handling for schema versioning

## Widget Conventions
- `const` constructors on all widgets with no runtime parameters
- `ValueKey` on every list item — missing keys cause state loss on reorder
- `RepaintBoundary` around expensive paint operations (charts, custom painters)
- Use `compute()` or `Isolate` for CPU-intensive work — never block the UI thread

## Testing
- Never use `pumpAndSettle()` with infinite animations (shimmer, pulsing) — use `pump(Duration)` instead
- Override providers in `ProviderContainer` for unit tests — never depend on real implementations
- Use `IntegrationTestWidgetsFlutterBinding` for E2E tests

## Firebase Init
- Always wrap `Firebase.initializeApp()` with a timeout (10s) — hangs indefinitely without internet
- Continue app launch even if Firebase init fails — degrade gracefully
