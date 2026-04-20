# Scope: global

# Design Principles

Universal design principles that apply to all code in this project, regardless of language or paradigm. Stack-specific rules extend these with framework-specific enforcement (e.g., `react-nextjs.md` enforces composition at the component boundary).

## Top-Level MUST NOTs

- MUST NOT duplicate knowledge — if a value, rule, or concept appears in two places, one MUST be derived from the other
- MUST NOT inline literal values that appear in more than one place or whose meaning is not obvious — extract to a named constant or enum
- MUST NOT build deep chains of knowledge (`a.b().c().d()`) across module boundaries — this couples callers to internal structure

## SOLID

Five object-oriented design principles (Robert C. Martin) that apply beyond strict OOP to any modular code:

- **Single Responsibility (SRP)** — each module/class/function MUST have exactly one reason to change. When a change request touches multiple unrelated sections of the same file, the file has multiple responsibilities
- **Open/Closed (OCP)** — code MUST be open for extension but closed for modification. Add behavior via new types/handlers/plugins, not by editing existing stable code paths
- **Liskov Substitution (LSP)** — subtypes MUST be substitutable for their base type without changing correctness. If a subclass throws exceptions the parent's contract doesn't declare, or strengthens preconditions beyond what the parent accepts, it violates LSP
- **Interface Segregation (ISP)** — clients MUST NOT be forced to depend on methods they don't use. Prefer many small interfaces over one large one
- **Dependency Inversion (DIP)** — high-level modules MUST NOT depend on low-level modules; both depend on abstractions. Inject dependencies via the constructor / function signature rather than reaching for globals

## DRY — Don't Repeat Yourself

Every piece of knowledge MUST have a single, authoritative representation in the system.

- Extract duplicated logic, constants, validation rules, SQL queries, API paths, and error messages to a single source
- Duplication of STRUCTURE (three classes that look similar but represent unrelated domains) is NOT the same as duplication of KNOWLEDGE — do not over-abstract
- The rule of three: tolerate two occurrences; on the third, extract

## No Magic Values (Constants & Enums)

A direct corollary of DRY and Meaningful Names: literal numbers, strings, and booleans that appear in multiple places or whose meaning is not obvious MUST be replaced with named constants or enums.

- Repeated literals → named constant (`MAX_RETRIES = 7`, not bare `7`)
- Closed set of valid values → typed enum / sealed type (not stringly-typed status fields like `"active" | "pending"`)
- Magic strings used as keys (routes, test IDs, event names, collection names, feature flags, i18n keys) → constants in a domain-specific module
- Place constants near their domain — route constants in `routes.ts`, not a catch-all `constants.ts`
- Exception: primitive "obvious" values in isolated contexts (`0`/`1`/`-1` for indexing/boundary checks), single-occurrence version literals

## Separation of Concerns

Divide a program into distinct sections so each addresses a separate concern. A module that mixes persistence, business logic, and presentation is a refactoring target.

- Persistence, domain logic, and presentation MUST live in separate modules — crossing these layers requires an explicit adapter
- HTTP / UI / transport concerns MUST NOT leak into business logic (no `HttpException` raised from a service; no DOM access from a domain model)
- Cross-cutting concerns (logging, auth, tracing) belong in middleware / decorators / interceptors — not duplicated in every handler

## Law of Demeter (Principle of Least Knowledge)

A unit MUST only talk to its immediate collaborators, not to strangers reached through chains. `order.customer.address.city` couples the caller to three classes' internal structure.

- Pass the data you need, not the object that contains it — `renderAddress(city)` over `renderAddress(order.customer.address)`
- Expose methods that do the work — `order.shippingCity()` instead of forcing callers to traverse
- Exception: fluent builders and query-chaining DSLs (`query.where().orderBy().limit()`) — these are designed for chaining

## Composition over Inheritance

Favor composing objects with behavior (strategy, delegate, plug-in) over deriving behavior through class hierarchies.

- Deep inheritance trees (>2 levels) are a refactoring signal — flatten into composition
- When a subclass overrides more than half of the parent's methods, it's not really an "is-a" — extract a shared interface and compose
- Mixins and traits are composition in disguise; prefer them over extending concrete classes
- Reserve inheritance for true polymorphic contracts (abstract base → concrete implementations)

## YAGNI & KISS (Cross-Reference)

KISS (rule 16), YAGNI (rule 21), and Measure-Before-You-Optimize (rule 22) are owned by `claude-behavior.md` — see those rules for the authoritative constraint.

## CRITICAL RULES

- MUST NOT allow a single class, module, or function to own more than one responsibility
- MUST NOT inline magic numbers or magic strings that appear more than once or whose meaning is non-obvious
- MUST NOT mix persistence, business logic, and presentation in a single module
- MUST NOT chain more than one `.` dereference across module boundaries — refactor to pass only what's needed
- MUST prefer composition over deep inheritance (>2 levels is a refactoring signal)
- MUST use typed enums / sealed types for closed sets of values — never stringly-typed categories
