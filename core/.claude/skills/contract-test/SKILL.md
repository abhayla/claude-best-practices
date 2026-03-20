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

## STEP 2: Write Consumer Contract Tests

Consumer tests define the EXPECTED interactions from the consumer's perspective. Each test declares what the consumer sends and what it expects back.


**Read:** `references/write-consumer-contract-tests.md` for detailed step 2: write consumer contract tests reference material.

## STEP 3: Generate Pact Files

**Read:** `references/generate-pact-files.md` for detailed step 3: generate pact files reference material.

## STEP 4: Run Provider Verification

Provider verification replays the consumer's expected interactions against the real provider and checks that responses match.


**Read:** `references/run-provider-verification.md` for detailed step 4: run provider verification reference material.

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


**Read:** `references/contract-evolution-handling-breaking-changes.md` for detailed contract evolution: handling breaking changes reference material.

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
