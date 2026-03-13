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
