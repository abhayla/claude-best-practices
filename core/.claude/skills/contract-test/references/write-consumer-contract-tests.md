# STEP 2: Write Consumer Contract Tests

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

