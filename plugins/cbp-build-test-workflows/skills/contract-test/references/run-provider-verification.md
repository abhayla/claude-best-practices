# STEP 4: Run Provider Verification

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
