---
name: integration-test
description: >
  Reference guide for integration testing patterns across service boundaries.
  Covers database, cache, queue, and external API integrations with real
  dependencies using testcontainers, fixture strategies, and CI configuration.
  Use when writing or reviewing tests that cross service boundaries.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "<integration-type> [language: python|typescript]"
version: "1.0.0"
triggers:
  - integration-test
  - testcontainers
  - database-test
  - service-test
---

# Integration Test Patterns Reference

Patterns for testing across service boundaries with real dependencies. All examples
provide both Python (pytest) and TypeScript (Vitest/Jest) implementations.

**Request:** $ARGUMENTS

---

## Service-to-Database

Test repository/DAO layers against real database engines to catch SQL dialect issues,
constraint violations, and transaction behavior that in-memory fakes miss.

### Transaction Rollback Pattern

Wrap each test in a transaction that rolls back, keeping the database clean.

**Python (pytest + SQLAlchemy):**

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

def test_create_user_persists(db_session):
    repo = UserRepository(db_session)
    user = repo.create(name="Alice", email="alice@test.com")
    assert repo.find_by_id(user.id).email == "alice@test.com"
```

**TypeScript (Vitest + Knex):**

```typescript
const db = knex({ client: "pg", connection: process.env.TEST_DATABASE_URL });

describe("UserRepository", () => {
  beforeEach(() => db.raw("BEGIN"));
  afterEach(() => db.raw("ROLLBACK"));

  it("persists and retrieves a user", async () => {
    const [user] = await db("users")
      .insert({ name: "Alice", email: "alice@test.com" })
      .returning("*");
    const found = await db("users").where({ id: user.id }).first();
    expect(found.email).toBe("alice@test.com");
  });
});
```

### In-Memory vs Containers

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| SQLite in-memory | Fast, no setup | Missing Postgres/MySQL features | Simple CRUD, unit-adjacent |
| Testcontainers | Real engine, full fidelity | Slower startup, needs Docker | CI, complex queries |
| Shared test DB | No container overhead | State leaks between runs | Local dev with discipline |

---

## Service-to-Cache

Verify cache read/write/invalidation behavior against a real cache backend.

**Python (pytest + redis-py):**

```python
@pytest.fixture
def cache(redis_container):
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True,
    )
    yield client
    client.flushdb()

def test_cache_hit(cache):
    cache.set("user:42", '{"name": "Alice"}', ex=300)
    assert cache.get("user:42") == '{"name": "Alice"}'

def test_cache_invalidation(cache):
    cache.set("user:42", '{"name": "Alice"}')
    cache.delete("user:42")
    assert cache.get("user:42") is None
```

**TypeScript (Vitest + ioredis):**

```typescript
let redis: Redis;
beforeAll(() => { redis = new Redis({ host: "localhost", port: Number(process.env.REDIS_PORT) }); });
afterEach(() => redis.flushdb());
afterAll(() => redis.quit());

it("returns cached value on hit", async () => {
  await redis.set("user:42", JSON.stringify({ name: "Alice" }), "EX", 300);
  const result = await redis.get("user:42");
  expect(JSON.parse(result!)).toEqual({ name: "Alice" });
});
```

---

## Service-to-Queue

Test message publish/consume cycles against real brokers to verify serialization,
routing, and acknowledgment.

**Python (pytest + pika for RabbitMQ):**

```python
@pytest.fixture
def rabbit_channel(rabbitmq_container):
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=rabbitmq_container.get_container_host_ip(),
        port=int(rabbitmq_container.get_exposed_port(5672)),
    ))
    channel = connection.channel()
    channel.queue_declare(queue="test_queue", durable=False)
    yield channel
    connection.close()

def test_publish_and_consume(rabbit_channel):
    body = json.dumps({"event": "user.created", "user_id": 42})
    rabbit_channel.basic_publish(exchange="", routing_key="test_queue", body=body)
    method, _, received = rabbit_channel.basic_get(queue="test_queue")
    assert json.loads(received) == {"event": "user.created", "user_id": 42}
```

**TypeScript (Vitest + amqplib):**

```typescript
let connection: amqp.Connection;
let channel: amqp.Channel;

beforeAll(async () => {
  connection = await amqp.connect(process.env.RABBITMQ_URL!);
  channel = await connection.createChannel();
  await channel.assertQueue("test_queue", { durable: false });
});
afterAll(async () => { await channel.close(); await connection.close(); });

it("publishes and consumes a message", async () => {
  const payload = { event: "user.created", userId: 42 };
  channel.sendToQueue("test_queue", Buffer.from(JSON.stringify(payload)));
  const msg = await channel.get("test_queue");
  expect(JSON.parse(msg!.content.toString())).toEqual(payload);
  channel.ack(msg!);
});
```

---

## Service-to-External API

Test HTTP clients against recorded or stubbed responses to avoid hitting real services in CI.

### VCR / Cassette Pattern

Record real HTTP interactions once, replay in subsequent runs.

**Python (vcrpy):**

```python
@vcr.use_cassette("tests/cassettes/github_user.yaml", record_mode="once")
def test_fetch_github_user():
    response = requests.get("https://api.github.com/users/octocat")
    assert response.status_code == 200
    assert response.json()["login"] == "octocat"
```

**TypeScript (nock):**

```typescript
afterEach(() => nock.cleanAll());

it("fetches user profile", async () => {
  nock("https://api.github.com")
    .get("/users/octocat")
    .reply(200, { login: "octocat", id: 1 });
  const response = await axios.get("https://api.github.com/users/octocat");
  expect(response.data.login).toBe("octocat");
});

it("handles rate limiting", async () => {
  nock("https://api.github.com")
    .get("/users/octocat")
    .reply(429, { message: "rate limit exceeded" });
  await expect(axios.get("https://api.github.com/users/octocat")).rejects.toThrow();
});
```

### WireMock Pattern

Use a WireMock container for complex multi-request scenarios:

```python
WIREMOCK = f"http://{container.get_container_host_ip()}:{container.get_exposed_port(8080)}"
requests.post(f"{WIREMOCK}/__admin/mappings", json={
    "request": {"method": "GET", "urlPath": "/api/v1/orders/123"},
    "response": {"status": 200, "jsonBody": {"id": 123, "status": "shipped"}},
})
assert requests.get(f"{WIREMOCK}/api/v1/orders/123").json()["status"] == "shipped"
```

---

## Database Fixtures

### Seeding Strategies

| Strategy | When to Use | Trade-offs |
|----------|-------------|------------|
| Factory functions | Default choice | Explicit, composable, no hidden state |
| SQL seed files | Shared read-only reference data | Fast load, hard to maintain |
| ORM fixtures | Framework-integrated projects | Coupled to ORM, can be slow |
| Snapshot restore | Large datasets needed | Fast restore, complex setup |

### Factory-Based Seeding

**Python (factory_boy):**

```python
class UserFactory(factory.Factory):
    class Meta:
        model = User
    name = factory.Sequence(lambda n: f"user-{n}")
    email = factory.LazyAttribute(lambda o: f"{o.name}@test.com")

class OrderFactory(factory.Factory):
    class Meta:
        model = Order
    user = factory.SubFactory(UserFactory)
    total = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    status = "pending"

def test_active_user_orders(db_session):
    user = UserFactory(is_active=True)
    OrderFactory.create_batch(3, user=user)
    assert len(get_active_user_orders(db_session, user.id)) == 3
```

**TypeScript (fishery):**

```typescript
const userFactory = Factory.define<User>(({ sequence }) => ({
  id: sequence,
  name: `user-${sequence}`,
  email: `user-${sequence}@test.com`,
}));

it("lists orders for active users", async () => {
  const user = userFactory.build({ name: "Alice" });
  // insert user and orders into test DB...
  expect(await orderService.getByUserId(user.id)).toHaveLength(3);
});
```

---

## Testcontainers

Docker-based throwaway instances of real dependencies.

**Python (testcontainers-python):**

```python
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.kafka import KafkaContainer

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as r:
        yield r

@pytest.fixture(scope="session")
def kafka_container():
    with KafkaContainer("confluentinc/cp-kafka:7.6.0") as kafka:
        yield kafka
```

**TypeScript (testcontainers-node):**

```typescript
import { PostgreSqlContainer } from "@testcontainers/postgresql";
import { RedisContainer } from "@testcontainers/redis";

let pgContainer: StartedPostgreSqlContainer;
let redisContainer: StartedRedisContainer;

beforeAll(async () => {
  pgContainer = await new PostgreSqlContainer("postgres:16-alpine").start();
  redisContainer = await new RedisContainer("redis:7-alpine").start();
}, 60_000);

afterAll(async () => {
  await pgContainer.stop();
  await redisContainer.stop();
});
```

### Container Lifecycle Scopes

| Scope | Lifecycle | Use When |
|-------|-----------|----------|
| Per-test | Start/stop each test | Tests mutate state, need full isolation |
| Per-module | Start once per test file | Tests use transaction rollback for cleanup |
| Per-session | Start once for entire suite | Read-heavy tests, immutable reference data |

Prefer **per-session** containers with **per-test transaction rollback**.

---

## Test Isolation

### Cleanup Strategies

| Strategy | Speed | Isolation | Best For |
|----------|-------|-----------|----------|
| Transaction rollback | Fast | High | Most integration tests |
| TRUNCATE tables | Medium | High | Tests needing committed data |
| Drop + recreate schema | Slow | Complete | Migration tests |
| Fresh container | Slowest | Complete | DDL tests, destructive operations |

**Auto-rollback fixture (Python):**

```python
@pytest.fixture(autouse=True)
def transactional_test(db_session):
    yield
    db_session.rollback()
```

**Per-test container for DDL tests:**

```python
@pytest.fixture
def fresh_postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg
```

### State Leak Checklist

- Reset auto-increment sequences if tests assert on IDs
- Clear application-level caches between tests
- Flush Redis/Memcached in `afterEach` / teardown
- Reset queue consumer offsets
- Restore mocked clocks and environment variables

---

## CI Considerations

### GitHub Actions Service Containers

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: --health-cmd="pg_isready" --health-interval=10s --health-timeout=5s --health-retries=5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: --health-cmd="redis-cli ping"
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: pytest tests/integration/ -v  # or: npx vitest run tests/integration/
```

### Testcontainers in CI

On GitHub Actions `ubuntu-latest`, Docker is pre-installed -- testcontainers work
out of the box. For other CI providers, ensure the Docker daemon is accessible.

### Parallelism

- Append worker ID to database name for parallel workers
- Limit parallelism: `--maxWorkers=2` (Jest/Vitest) or `-n 2` (pytest-xdist)

```python
@pytest.fixture(scope="session")
def db_name(worker_id):
    return f"test_db_{worker_id}"
```

---

## MUST DO

- Use real database engines (via testcontainers or service containers) for integration tests
- Isolate each test with transaction rollback or container-level reset
- Set container startup timeouts in CI (60s+) to avoid flaky failures
- Use factory functions for test data instead of shared SQL fixtures
- Flush caches and queues in teardown to prevent cross-test contamination
- Pin container image tags to specific versions (e.g., `postgres:16-alpine`)
- Run integration tests in a separate CI job from unit tests for faster feedback

## MUST NOT DO

- MUST NOT mock the database in integration tests -- the goal is to test real interactions
- MUST NOT share mutable state across tests without explicit cleanup
- MUST NOT use `latest` tags for container images -- builds become non-reproducible
- MUST NOT hardcode connection strings -- use environment variables (`$DATABASE_URL`, `$REDIS_URL`)
- MUST NOT run integration tests synchronously if the suite exceeds 5 minutes -- parallelize
- MUST NOT skip integration tests locally -- run a subset before pushing
- MUST NOT leave containers running after tests -- use context managers or `afterAll`
