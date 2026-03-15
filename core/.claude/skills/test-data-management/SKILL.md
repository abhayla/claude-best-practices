---
name: test-data-management
description: >
  Manage test data across Python and TypeScript projects using factories, fakers, seeders,
  builders, and fixtures. Use when setting up test infrastructure, improving test data quality,
  or eliminating brittle hardcoded test data.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "<test-data-concern> [language]"
version: "1.0.0"
triggers:
  - test data
  - factory
  - faker
  - seed data
  - test fixtures
  - factory boy
  - fishery
---

# Test Data Management Reference

Patterns for creating, managing, and maintaining test data in Python and TypeScript.

**Request:** $ARGUMENTS

---

## Factory Pattern

Factories produce test objects with sensible defaults that can be selectively overridden.

### Python — Factory Boy

```python
import factory
from <your_app>.models import User, Order

class UserFactory(factory.Factory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    role = "member"
    is_active = True
    class Params:
        admin = factory.Trait(role="admin", is_active=True)

class OrderFactory(factory.Factory):
    class Meta:
        model = Order
    user = factory.SubFactory(UserFactory)
    total = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    status = "pending"

# Usage: UserFactory(), UserFactory(admin=True), UserFactory(email="x@test.com")
```

### TypeScript — Fishery

```typescript
import { Factory } from "fishery";

const userFactory = Factory.define<User>(({ sequence, params }) => ({
  id: sequence,
  username: `user_${sequence}`,
  email: params.email ?? `user_${sequence}@example.com`,
  role: "member",
  isActive: true,
}));

// Usage: userFactory.build(), userFactory.build({ role: "admin" }), userFactory.buildList(5)
```

### Plain Factory Functions (No Library)

```python
def make_user(**overrides):
    defaults = {"username": "testuser", "email": "test@example.com", "role": "member"}
    return {**defaults, **overrides}
```

```typescript
function makeUser(overrides: Partial<User> = {}): User {
  return { id: 1, username: "testuser", email: "test@example.com", role: "member", ...overrides };
}
```

---

## Fake Data Generation

Use faker libraries to generate realistic synthetic data. Always seed for reproducibility.

### Python — Faker

```python
from faker import Faker
fake = Faker()
Faker.seed(42)  # deterministic across runs

name = fake.name()           # realistic name
email = fake.email()         # realistic email
fake_de = Faker("de_DE")    # locale-specific

# With Factory Boy
class UserFactory(factory.Factory):
    class Meta:
        model = User
    name = factory.Faker("name")
    email = factory.Faker("email")
```

### TypeScript — @faker-js/faker

```typescript
import { faker } from "@faker-js/faker";
faker.seed(42); // deterministic across runs

const name = faker.person.fullName();
const email = faker.internet.email();

// Locale-specific
import { fakerDE } from "@faker-js/faker";
const germanName = fakerDE.person.fullName();
```

### Global Seed Setup

```python
# conftest.py — auto-seed for all tests
@pytest.fixture(autouse=True)
def seed_faker():
    Faker.seed(12345)
```

```typescript
// Jest/Vitest global setup
import { faker } from "@faker-js/faker";
faker.seed(12345);
```

---

## Database Seeding

### Idempotent Seeds

Seeds MUST be idempotent — running twice produces the same result, not duplicates.

```python
def seed_roles(session):
    for role_data in ROLES:
        existing = session.query(Role).filter_by(name=role_data["name"]).first()
        if existing:
            existing.permissions = role_data["permissions"]  # update
        else:
            session.add(Role(**role_data))                   # insert
    session.commit()
```

```typescript
async function seedRoles() {
  for (const role of ROLES) {
    await db.role.upsert({
      where: { name: role.name },
      update: { permissions: role.permissions },
      create: role,
    });
  }
}
```

### Environment-Specific Seeds

```python
def run_seeds():
    seed_roles()          # always needed
    env = os.getenv("APP_ENV", "development")
    if env in ("development", "test"):
        seed_test_users() # fake users for dev/test only
    if env == "test":
        seed_edge_cases() # boundary data for assertions
```

---

## Builder Pattern

Use fluent builders when test objects have complex relationships or many optional fields.

```python
class OrderBuilder:
    def __init__(self):
        self._user, self._items, self._status, self._discount = None, [], "pending", 0.0

    def with_user(self, user):       self._user = user; return self
    def with_item(self, name, price, qty=1):
        self._items.append({"name": name, "price": price, "qty": qty}); return self
    def with_status(self, s):        self._status = s; return self
    def with_discount(self, pct):    self._discount = pct; return self

    def build(self):
        total = sum(i["price"] * i["qty"] for i in self._items) * (1 - self._discount)
        return Order(user=self._user or make_user(), items=self._items,
                     total=total, status=self._status)

# Usage
order = (OrderBuilder()
    .with_user(make_user(role="member"))
    .with_item("Widget", 9.99, qty=2)
    .with_discount(0.1)
    .with_status("confirmed")
    .build())
```

```typescript
class OrderBuilder {
  private user?: User;
  private items: OrderItem[] = [];
  private status = "pending";
  private discount = 0;

  withUser(user: User): this       { this.user = user; return this; }
  withItem(name: string, price: number, qty = 1): this {
    this.items.push({ name, price, qty }); return this;
  }
  withStatus(s: string): this      { this.status = s; return this; }
  withDiscount(pct: number): this  { this.discount = pct; return this; }

  build(): Order {
    const total = this.items.reduce((s, i) => s + i.price * i.qty, 0) * (1 - this.discount);
    return { user: this.user ?? makeUser(), items: this.items, total, status: this.status };
  }
}
```

---

## Fixture Files

For static reference data, load from JSON or YAML files.

### Organization Convention

```
tests/fixtures/
  users.json                  # entity fixtures
  products.json
  responses/                  # API response mocks
    get-user-200.json
    error-422.json
  snapshots/                  # expected output snapshots
    report-summary.json
```

### Loading Fixtures

```python
FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / name
    with open(path) as f:
        return yaml.safe_load(f) if path.suffix in (".yaml", ".yml") else json.load(f)
```

```typescript
const FIXTURES_DIR = join(__dirname, "fixtures");
function loadFixture<T>(name: string): T {
  return JSON.parse(readFileSync(join(FIXTURES_DIR, name), "utf-8")) as T;
}
```

Keep fixtures small and single-purpose. Use factories for dynamic data, fixtures only for
static reference shapes. Version fixtures alongside tests in the same PR.

---

## Anonymized Production Data

Strategies for using production-like data safely.

### PII Masking

```python
import hashlib
from faker import Faker

def anonymize_record(record: dict) -> dict:
    local, _ = record["email"].split("@")
    hashed = hashlib.sha256(local.encode()).hexdigest()[:8]
    fake = Faker(); Faker.seed(hash(record["name"]) % (2**32))
    return {**record,
        "email": f"{hashed}@example.com",
        "name": fake.name(),
        "phone": record.get("phone", "000-0000")[:3] + "****",
        "ssn": None, "address": None,
    }
```

### Data Subsetting

Extract a representative subset rather than copying full production data. Use `ORDER BY RANDOM() LIMIT N` or equivalent, then pull related records via joins.

### Safety Checklist

| Check | Action |
|-------|--------|
| PII fields identified | Map all columns containing personal data |
| Masking applied | Every PII field transformed or nulled |
| Referential integrity | Foreign keys still valid after masking |
| No real credentials | API keys, tokens, passwords all replaced |

---

## Test Data Lifecycle

### Transaction Rollback (Preferred)

Wrap each test in a transaction that rolls back. Fastest isolation — no truncation needed.

```python
@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

```typescript
let trx: Transaction;
beforeEach(async () => { trx = await db.transaction(); });
afterEach(async () => { await trx.rollback(); });
```

### Snapshot Restore

For suites needing a known database state, dump a baseline with `pg_dump` (or equivalent)
and restore before each suite run with `pg_restore --clean --if-exists`.

### Isolation Strategy Comparison

| Strategy | Speed | Isolation | Best For |
|----------|-------|-----------|----------|
| Transaction rollback | Fast | High | Unit/integration tests |
| Table truncation | Medium | High | Tests needing committed data |
| Separate database | Slow | Complete | Parallel test workers |
| In-memory database | Fastest | Complete | Pure unit tests (SQLite) |

---

## Anti-Patterns

**Hardcoded test data** — Magic values with no context make tests fragile and unreadable.
Use factories with meaningful overrides instead.

```python
# BAD
order = Order(user_id=42, items=[{"id": 7, "price": 19.99}], discount=0.1)
# GOOD
order = OrderFactory(items=[make_item(price=19.99)], discount=0.1)
```

**Shared mutable fixtures** — Module-level mutable collections cause order-dependent failures.
Create fresh data per test or use immutable shared fixtures.

**Test data coupling** — Tests that depend on data created by other tests break in isolation.
Each test must set up its own data and assert against it.

**Over-specified test data** — Specifying irrelevant fields obscures what the test checks.
Only set fields relevant to the assertion; let factories handle the rest.

---

## MUST DO

- Use factories or builder patterns instead of raw constructors in tests
- Seed faker with a fixed value for deterministic test runs
- Make seed scripts idempotent (use upsert, not insert)
- Wrap database tests in transactions that roll back after each test
- Keep fixture files small and single-purpose
- Anonymize all PII before using production-derived data in tests
- Create fresh test data per test or use immutable shared fixtures
- Document what each fixture represents and when to use it

## MUST NOT DO

- MUST NOT hardcode magic numbers or IDs in test assertions without explanation
- MUST NOT share mutable state between tests (lists, dicts, database rows)
- MUST NOT rely on test execution order for data availability
- MUST NOT use real production data (emails, names, credentials) in test fixtures
- MUST NOT seed the same data in every test file — centralize in conftest/setup files
- MUST NOT skip cleanup — leaked test data causes cascading failures in other tests
- MUST NOT use `random()` without a seed — non-deterministic tests are flaky tests
- MUST NOT store large binary fixtures in version control — use generation scripts instead
