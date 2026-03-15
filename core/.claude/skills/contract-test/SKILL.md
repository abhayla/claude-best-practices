---
name: contract-test
description: >
  Implement consumer-driven contract testing with Pact. Write consumer contract
  tests, generate Pact files, run provider verification, integrate with a Pact
  broker, and set up CI gates with can-i-deploy. Supports Pact-JS, Pact-Python,
  and Pact-JVM.
triggers:
  - contract-test
  - pact
  - consumer-driven
  - cdc-test
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<consumer-name> <provider-name> [language: js|python|jvm] [broker-url]"
version: "1.1.0"
type: workflow
---

# Consumer-Driven Contract Testing with Pact

Set up contract testing between API consumers and providers using the Pact framework.

**Request:** $ARGUMENTS

---

## STEP 1: Identify Consumers and Providers

1. Map the service dependency graph:
   - Which services CALL APIs (consumers)?
   - Which services EXPOSE APIs (providers)?
2. For each consumer-provider pair, identify the interactions to cover:
   - HTTP endpoints (method, path, headers, request body, response body)
   - Message-based interactions (event schemas, queue contracts)
3. Check for existing contract tests or Pact files (`pacts/`, `*.pact.json`)
4. Determine the language/framework for each service to select the correct Pact library

### Language Selection

| Service Language | Pact Library | Install Command |
|-----------------|-------------|-----------------|
| JavaScript/TypeScript | `@pact-foundation/pact` | `npm install --save-dev @pact-foundation/pact` |
| Python | `pact-python` | `pip install pact-python` |
| Java/Kotlin | `pact-jvm` | Add `au.com.dius.pact.consumer:junit5` to Gradle/Maven |

---

## STEP 2: Write Consumer Contract Tests

Consumer tests define the EXPECTED interactions from the consumer's perspective. Each test declares what the consumer sends and what it expects back.

### Pact-JS (JavaScript/TypeScript)

```javascript
import { PactV4 } from '@pact-foundation/pact';

const provider = new PactV4({
  consumer: 'OrderService',
  provider: 'InventoryService',
  dir: './pacts',         // output directory for Pact files
  logLevel: 'warn',
});

describe('Inventory API contract', () => {
  it('returns stock level for a valid product', async () => {
    await provider
      .addInteraction()
      .given('product ABC-123 exists with stock 50')
      .uponReceiving('a request for product stock level')
      .withRequest('GET', '/api/products/ABC-123/stock', (builder) => {
        builder.headers({ Accept: 'application/json' });
      })
      .willRespondWith(200, (builder) => {
        builder.headers({ 'Content-Type': 'application/json' });
        builder.jsonBody({
          productId: 'ABC-123',
          stock: 50,
          updatedAt: provider.like('2025-01-15T10:00:00Z'),
        });
      })
      .executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/api/products/ABC-123/stock`,
          { headers: { Accept: 'application/json' } }
        );
        const body = await response.json();
        expect(response.status).toBe(200);
        expect(body.productId).toBe('ABC-123');
        expect(body.stock).toBe(50);
      });
  });
});
```

### Pact-Python

```python
import pytest
from pact import Consumer, Provider

@pytest.fixture
def pact():
    pact = Consumer('OrderService').has_pact_with(
        Provider('InventoryService'),
        pact_dir='./pacts',
    )
    pact.start_service()
    yield pact
    pact.stop_service()
    pact.verify()

def test_get_stock_level(pact):
    expected = {'productId': 'ABC-123', 'stock': 50}

    (pact
     .given('product ABC-123 exists with stock 50')
     .upon_receiving('a request for product stock level')
     .with_request('GET', '/api/products/ABC-123/stock')
     .will_respond_with(200, body=expected))

    # Call the consumer code against the mock
    result = get_stock('ABC-123', base_url=pact.uri)
    assert result['stock'] == 50
```

### Pact-JVM (JUnit 5)

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "InventoryService", port = "8080")
class InventoryContractTest {

    @Pact(consumer = "OrderService")
    V4Pact stockLevelPact(PactDslWithProvider builder) {
        return builder
            .given("product ABC-123 exists with stock 50")
            .uponReceiving("a request for product stock level")
            .method("GET")
            .path("/api/products/ABC-123/stock")
            .willRespondWith()
            .status(200)
            .body(newJsonBody(body -> {
                body.stringValue("productId", "ABC-123");
                body.integerType("stock", 50);
            }).toString())
            .toPact(V4Pact.class);
    }

    @Test
    @PactTestFor(pactMethod = "stockLevelPact")
    void verifiesStockLevel(MockServer mockServer) {
        var client = new InventoryClient(mockServer.getUrl());
        var stock = client.getStock("ABC-123");
        assertThat(stock.getQuantity()).isEqualTo(50);
    }
}
```

### Pact Matchers

Use matchers instead of exact values to make contracts flexible:

| Matcher | Purpose | Example |
|---------|---------|---------|
| `like(value)` | Match type, not exact value | `like(42)` matches any integer |
| `eachLike(example)` | Array where each element matches type | `eachLike({id: 1})` |
| `regex(pattern, example)` | Match against regex | `regex('\\d{4}-\\d{2}', '2025-01')` |
| `datetime(format, example)` | ISO date/time matching | `datetime('yyyy-MM-dd')` |
| `integer()` / `decimal()` | Numeric type matching | Matches any int/float |

---

## STEP 3: Generate Pact Files

After consumer tests pass, Pact files are written to the configured output directory.

1. Run consumer tests:
   ```bash
   # JS
   npm test -- --testPathPattern=pact

   # Python
   pytest tests/pact/ -v

   # JVM
   ./gradlew test --tests '*ContractTest'
   ```

2. Verify Pact files were generated:
   ```bash
   ls pacts/
   # Expected: OrderService-InventoryService.json
   ```

3. Inspect the generated Pact file to confirm interactions look correct:
   ```bash
   cat pacts/OrderService-InventoryService.json | python -m json.tool
   ```

Each Pact file contains the consumer name, provider name, and all declared interactions with request/response pairs.

---

## STEP 4: Run Provider Verification

Provider verification replays the consumer's expected interactions against the real provider and checks that responses match.

### Provider State Setup

The provider must handle `given(...)` states declared in consumer tests. Implement a state handler that sets up test data before each interaction:

```javascript
// Pact-JS provider verification
const { Verifier } = require('@pact-foundation/pact');

new Verifier({
  providerBaseUrl: 'http://localhost:3000',
  pactUrls: ['./pacts/OrderService-InventoryService.json'],
  // OR fetch from broker:
  // pactBrokerUrl: 'https://pact-broker.example.com',
  // providerName: 'InventoryService',
  stateHandlers: {
    'product ABC-123 exists with stock 50': async () => {
      await db.products.upsert({ id: 'ABC-123', stock: 50 });
    },
    null: async () => {
      // Default state — clean slate
      await db.products.deleteAll();
    },
  },
}).verifyProvider();
```

```python
# Pact-Python provider verification
# Run via CLI:
# pact-verifier --provider-base-url=http://localhost:3000 \
#   --pact-url=./pacts/OrderService-InventoryService.json \
#   --provider-states-setup-url=http://localhost:3000/_pact/state
```

```java
// Pact-JVM provider verification
@Provider("InventoryService")
@PactFolder("pacts")
class InventoryProviderTest {

    @State("product ABC-123 exists with stock 50")
    void setupProduct() {
        repository.save(new Product("ABC-123", 50));
    }

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.verifyInteraction();
    }
}
```

### Verification Checklist

| Check | Status |
|-------|--------|
| Provider starts and is accessible | |
| All provider states have handlers | |
| All interactions pass verification | |
| Response status codes match | |
| Response body structure matches (types, not exact values) | |

---

## STEP 5: Set Up Pact Broker (Optional)

A Pact broker centralizes contract storage, tracks versions, and enables the `can-i-deploy` workflow.

### Options

| Broker | Setup | Cost |
|--------|-------|------|
| Pactflow (SaaS) | Sign up at pactflow.io | Free tier available |
| Self-hosted | Docker: `pactfoundation/pact-broker` | Infrastructure cost |

### Publishing Pacts to the Broker

```bash
# Pact-JS / Pact-Python CLI
pact-broker publish ./pacts \
  --consumer-app-version=$(git rev-parse --short HEAD) \
  --branch=$(git branch --show-current) \
  --broker-base-url=https://pact-broker.example.com \
  --broker-token=$PACT_BROKER_TOKEN
```

### Verifying from the Broker

```bash
# Provider pulls consumer pacts from the broker
pact-verifier \
  --provider-base-url=http://localhost:3000 \
  --pact-broker-url=https://pact-broker.example.com \
  --provider=InventoryService \
  --provider-app-version=$(git rev-parse --short HEAD) \
  --publish-verification-results
```

---

## STEP 6: CI Integration

### can-i-deploy Workflow

The `can-i-deploy` check queries the broker to determine if a version is safe to deploy based on verified contracts.

```yaml
# GitHub Actions example
jobs:
  contract-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run consumer contract tests
        run: npm test -- --testPathPattern=pact

      - name: Publish pacts to broker
        run: |
          npx pact-broker publish ./pacts \
            --consumer-app-version=${{ github.sha }} \
            --branch=${{ github.ref_name }} \
            --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
            --broker-token=${{ secrets.PACT_BROKER_TOKEN }}

      - name: Can I deploy?
        run: |
          npx pact-broker can-i-deploy \
            --pacticipant=OrderService \
            --version=${{ github.sha }} \
            --to-environment=production \
            --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
            --broker-token=${{ secrets.PACT_BROKER_TOKEN }}
```

### Pipeline Flow

```
Consumer CI:  test → publish pact → can-i-deploy → deploy
Provider CI:  test → verify pacts → publish results → can-i-deploy → deploy
```

Both consumer and provider MUST pass `can-i-deploy` before deploying to any shared environment.

---

## STEP 6.5: Update Downstream Mocks

After provider verification (STEP 4), if verification reveals changed response shapes — new fields, removed fields, or type changes — consumer test mocks will be stale. This step identifies and flags those mocks for update.

### 6.5.1 Detect Changed Response Shapes

Compare the current Pact file against the previous version to identify response shape changes:

```bash
# Compare current vs previous Pact file (if version-controlled)
git diff origin/main -- pacts/*.json | grep -E '^\+.*"body"|^\-.*"body"'

# Or compare against the broker's last verified version
pact-broker describe-version \
  --pacticipant=<provider-name> \
  --version=$(git rev-parse --short HEAD~1) \
  --broker-base-url=$PACT_BROKER_URL 2>/dev/null
```

If provider verification failed or passed with warnings about changed fields, extract the list of affected endpoints and changed fields from the verification output.

### 6.5.2 Scan Consumer Tests for Stale Mocks

For each endpoint with a changed response shape, search consumer test files for mocks of the same endpoint:

**Python:**
```bash
# Find mock definitions that reference the changed endpoint path
grep -rn "mock.*<endpoint-path>\|patch.*<endpoint-path>\|responses\.add.*<endpoint-path>\|return_value.*<field-name>" tests/ 2>/dev/null
```

**JavaScript/TypeScript:**
```bash
# Find mock/stub definitions referencing the changed endpoint
grep -rn "mockResolvedValue\|nock.*<endpoint-path>\|msw.*<endpoint-path>\|jest\.fn.*<field-name>\|vi\.fn.*<field-name>" tests/ __tests__/ 2>/dev/null
```

**Java/Kotlin:**
```bash
# Find Mockito/WireMock stubs referencing the changed endpoint
grep -rn "when(.*<endpoint-path>\|stubFor.*<endpoint-path>\|willReturn.*<field-name>" src/test/ 2>/dev/null
```

### 6.5.3 Generate Mock Update Checklist

For each stale mock found, produce a checklist entry:

```markdown
## Stale Mock Checklist

Provider `<provider-name>` verification revealed changed response shapes.
The following consumer mocks reference affected endpoints and may need updates:

| Consumer | Test File | Line | Endpoint | Stale Field(s) | Action |
|----------|-----------|------|----------|-----------------|--------|
| <consumer-name> | tests/unit/test_inventory_client.py | 34 | GET /api/products/:id/stock | `updatedAt` (type changed) | Update mock return value |
| <consumer-name> | tests/unit/test_order_service.py | 78 | POST /api/orders | `discount` (field added) | Add field to mock response |
| <consumer-name> | __tests__/api/inventory.test.ts | 22 | GET /api/products/:id/stock | `warehouse` (field removed) | Remove field from mock |

### How to Update

1. Open each flagged test file
2. Locate the mock definition at the specified line
3. Update the mock return value / response body to match the new contract shape
4. Re-run consumer tests to verify mocks are consistent
5. Re-run consumer contract tests to regenerate Pact files with updated expectations
```

### 6.5.4 Automated Validation

After updating mocks, verify consistency:

```bash
# Re-run consumer unit tests (mocks should match new shapes)
# Python
pytest tests/unit/ -v -k "<consumer-module>"

# JavaScript
npx jest --testPathPattern="<consumer-module>"

# Re-run consumer contract tests to regenerate Pact files
pytest tests/pact/ -v
# or
npm test -- --testPathPattern=pact
```

If consumer unit tests fail after mock updates, the consumer code itself may need updating to handle the new response shape.

---

## Contract Evolution: Handling Breaking Changes

### Non-Breaking Changes (Safe)

| Change | Why Safe |
|--------|----------|
| Add a new optional field to response | Existing consumers ignore unknown fields |
| Add a new endpoint | No consumer depends on it yet |
| Widen an accepted input type | Existing inputs still valid |

### Breaking Changes (Require Coordination)

| Change | Migration Path |
|--------|---------------|
| Remove a response field | 1. Deprecate field, 2. Update all consumers, 3. Remove field |
| Rename an endpoint | 1. Add new endpoint, 2. Migrate consumers, 3. Remove old endpoint |
| Change field type | 1. Add new field with new type, 2. Migrate consumers, 3. Remove old field |
| Remove an endpoint | 1. Verify no consumer pacts reference it, 2. Remove |

### Versioning Strategy

- Tag every Pact with the git SHA and branch name
- Use broker environments (`dev`, `staging`, `production`) to track deployed versions
- Use `record-deployment` / `record-release` to tell the broker what is deployed where

---

## MUST DO

- Write consumer tests FIRST, before provider verification — the consumer defines the contract
- Use Pact matchers (`like`, `eachLike`, `regex`) instead of exact values for flexible contracts
- Implement provider state handlers for EVERY `given(...)` clause in consumer tests
- Tag pacts with git SHA and branch for traceability
- Run `can-i-deploy` in CI before deploying to shared environments
- Keep consumer tests focused on the contract (request/response shape), not business logic
- Clean up obsolete interactions when consumer no longer uses an endpoint
- Verify provider against ALL consumers, not just one
- Publish verification results back to the broker so `can-i-deploy` has complete data
- Run provider verification against a real (or near-real) instance, not mocked internals

## MUST NOT DO

- MUST NOT use contract tests as a replacement for integration or E2E tests — they verify schema compatibility, not functional correctness
- MUST NOT hardcode exact values in contracts where type matching suffices — use `like()` matchers instead
- MUST NOT let the provider team write consumer tests — consumers own their contracts
- MUST NOT skip provider state setup — missing states cause false verification failures
- MUST NOT deploy without running `can-i-deploy` when using a broker
- MUST NOT modify generated Pact JSON files by hand — regenerate by updating and re-running consumer tests
- MUST NOT couple contract tests to internal implementation details of either service
- MUST NOT ignore verification failures — a failing contract means a real integration risk
- MUST NOT use `can-i-deploy` without publishing verification results from the provider side
- MUST NOT treat contract tests as optional — if two services communicate, they need a contract

---

## SPEC-AS-CONTRACT TESTING (Specmatic)

Specmatic uses OpenAPI/AsyncAPI specs as executable contracts — zero test code needed.

### How It Works

The API specification IS the contract. No separate contract language, no consumer/provider test code.

```bash
# Install Specmatic
npm install -g specmatic
# or
brew install specmatic

# Run contract tests against your API (reads OpenAPI spec)
specmatic test --contract openapi.yaml --host localhost --port 8000

# Generate stub server from spec (for consumer testing)
specmatic stub --contract openapi.yaml --port 9000
```

### Auto-Generated Tests

Specmatic reads your OpenAPI spec and automatically generates:
- **Positive tests** — valid requests for every endpoint/method/parameter combination
- **Negative tests** — invalid types, missing required fields, boundary values
- **Auth tests** — requests with/without required auth headers

```yaml
# openapi.yaml — this IS your contract
openapi: 3.0.0
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

# Specmatic auto-generates tests for:
# - GET /users/123 → expects 200 with User schema
# - GET /users/abc → expects 400 (id must be integer)
# - GET /users/ → expects 404 or 400 (missing required param)
```

### CI Integration

```yaml
# GitHub Actions
contract-test:
  steps:
    - run: specmatic test --contract openapi.yaml --host localhost --port 8000
    - run: specmatic backward-compatibility-check --contract openapi.yaml
```

### When to Use Specmatic vs Pact

| Criteria | Specmatic | Pact |
|----------|-----------|------|
| Contract source | OpenAPI/AsyncAPI spec | Consumer-generated expectations |
| Test code needed | None | Yes (consumer + provider) |
| Supports | REST, gRPC, GraphQL, Kafka | REST, GraphQL, messages |
| Breaking change detection | Built-in backward compatibility check | Via Pact broker `can-i-deploy` |
| Best for | API-first teams with maintained specs | Teams without formal API specs |

---

## GRAPHQL SCHEMA VERIFICATION

### GraphQL Inspector — CI Breaking Change Detection

Automatically detect breaking changes in GraphQL schemas on every PR:

```bash
# Install
npm install -g @graphql-inspector/cli

# Compare schemas (local files)
graphql-inspector diff old-schema.graphql new-schema.graphql

# Compare against a remote endpoint
graphql-inspector diff https://api.example.com/graphql new-schema.graphql

# Lint schema for best practices
graphql-inspector lint schema.graphql

# Validate operations against schema
graphql-inspector validate "src/**/*.graphql" schema.graphql
```

### Breaking vs Non-Breaking Changes

| Change | Breaking | Why |
|--------|----------|-----|
| Remove field | Yes | Existing queries will fail |
| Remove type | Yes | Dependent queries/mutations break |
| Change field type | Yes | Client deserialization breaks |
| Add optional field | No | Existing queries unaffected |
| Add new type | No | No existing queries reference it |
| Deprecate field | No | Field still works, warns consumers |
| Add required argument | Yes | Existing mutations missing the arg |

### CI Integration

```yaml
graphql-check:
  steps:
    - run: |
        graphql-inspector diff \
          "git:origin/main:schema.graphql" \
          "schema.graphql" \
          --rule suppressRemovalOfDeprecatedField
```

---

## GRPC PROTOBUF VERIFICATION

### buf — Lint and Breaking Change Detection

```bash
# Install buf
brew install bufbuild/buf/buf

# Lint proto files for style and correctness
buf lint

# Check for breaking changes against the main branch
buf breaking --against '.git#branch=main'

# Generate code (replaces protoc)
buf generate
```

### buf.yaml Configuration

```yaml
version: v2
lint:
  use:
    - DEFAULT          # Standard lint rules
    - COMMENTS         # Require comments on services/messages
  except:
    - PACKAGE_VERSION_SUFFIX  # Allow unversioned packages
breaking:
  use:
    - FILE             # Detect breaking changes per file
```

### Breaking Change Rules

| Change | Breaking | Safe Alternative |
|--------|----------|-----------------|
| Remove field | Yes | Mark as reserved, keep field number |
| Rename field | Yes | Add new field, deprecate old |
| Change field type | Yes | Add new field with new type |
| Change field number | Yes | Never reuse field numbers |
| Remove service/RPC | Yes | Deprecate first, remove in next major |
| Add required field | Yes (proto3: all optional) | All fields optional in proto3 |

### CI Integration

```yaml
proto-check:
  steps:
    - uses: bufbuild/buf-setup-action@v1
    - run: buf lint
    - run: buf breaking --against 'https://github.com/$REPO.git#branch=main'
```

---

## EVENT-DRIVEN CONTRACT TESTING

### Pact for Async Messages

Test that producers emit events matching consumer expectations:

```python
# Consumer: define expected message format
@message_handler("UserCreated")
def handle_user_created(message):
    assert "userId" in message
    assert "email" in message
    assert isinstance(message["timestamp"], str)

# Provider: verify messages match consumer expectations
pact_verifier.verify_with_broker(
    provider_name="user-service",
    provider_version=git_version,
    consumer_version_selectors=[{"mainBranch": True}],
    message_providers={
        "UserCreated": lambda: {
            "userId": "123",
            "email": "test@example.com",
            "timestamp": "2026-03-14T10:00:00Z"
        }
    }
)
```

### Specmatic + AsyncAPI for Kafka

```yaml
# asyncapi.yaml — contract for Kafka topics
asyncapi: 2.6.0
channels:
  user.created:
    publish:
      message:
        payload:
          type: object
          required: [userId, email]
          properties:
            userId: { type: string }
            email: { type: string, format: email }
```

```bash
# Validate Kafka messages against AsyncAPI spec
specmatic test --contract asyncapi.yaml --kafka-bootstrap-servers localhost:9092
```

### Event Replay and Idempotency Testing

```python
# Test idempotency: replay same event twice, verify no duplicate side effects
async def test_event_idempotency():
    event = {"userId": "123", "email": "test@example.com", "eventId": "evt-001"}

    await handler.process(event)  # First processing
    count_after_first = await db.users.count()

    await handler.process(event)  # Replay same event
    count_after_replay = await db.users.count()

    assert count_after_first == count_after_replay, "Event processed twice — not idempotent"
```

### Message Isolation in Shared Environments

When testing against shared Kafka/SQS brokers, isolate messages per test:

- Use unique topic suffixes per test run: `user.created.test-{uuid}`
- Use message headers with test correlation IDs
- Filter consumers to only process messages from current test run
- Clean up test topics after test suite completes
