# STEP 3: Generate Pact Files

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

