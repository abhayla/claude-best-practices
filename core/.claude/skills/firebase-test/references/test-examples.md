# Firebase Test Examples

Reference material for Steps 3, 4, 5, and 7 of the firebase-test skill.

## Firestore Security Rules Testing (Step 3)

Test Firestore security rules using `@firebase/rules-unit-testing`.

```javascript
// Example: test/firestore-rules.test.js
const {
  initializeTestEnvironment,
  assertSucceeds,
  assertFails,
} = require("@firebase/rules-unit-testing");
const { readFileSync } = require("fs");

let testEnv;

beforeAll(async () => {
  testEnv = await initializeTestEnvironment({
    projectId: "<your-project-id>",
    firestore: {
      rules: readFileSync("firestore.rules", "utf8"),
      host: "localhost",
      port: 8080,
    },
  });
});

afterEach(async () => {
  await testEnv.clearFirestore();
});

afterAll(async () => {
  await testEnv.cleanup();
});

// Test: authenticated user can read their own document
test("user can read own profile", async () => {
  const userContext = testEnv.authenticatedContext("user-123", {
    email: "user@example.com",
  });
  const db = userContext.firestore();
  await assertSucceeds(
    db.collection("<your-collection>").doc("user-123").get()
  );
});

// Test: unauthenticated user cannot write
test("unauthenticated user cannot write", async () => {
  const unauthed = testEnv.unauthenticatedContext();
  const db = unauthed.firestore();
  await assertFails(
    db.collection("<your-collection>").doc("any-doc").set({ data: "value" })
  );
});

// Test: user cannot read another user's private data
test("user cannot read other user profile", async () => {
  const userContext = testEnv.authenticatedContext("user-123");
  const db = userContext.firestore();
  await assertFails(
    db.collection("<your-collection>").doc("user-456").get()
  );
});
```

**Run rules tests:**

```bash
npx jest test/firestore-rules.test.js --forceExit
# or
npx mocha test/firestore-rules.test.js --exit
```

## Cloud Functions Unit Testing (Step 4)

Test Cloud Functions in isolation using `firebase-functions-test`.

```javascript
// Example: functions/test/my-function.test.js
const functionsTest = require("firebase-functions-test")({
  projectId: "<your-project-id>",
}, "./service-account-key-test.json"); // use a test-only service account or omit for offline

const admin = require("firebase-admin");

// Import the function under test
const { myFunction } = require("../index");

afterAll(() => {
  functionsTest.cleanup();
});

// Test an HTTP function
test("HTTP function returns expected response", async () => {
  const req = { query: { name: "test" } };
  const res = {
    status: jest.fn().mockReturnThis(),
    json: jest.fn(),
  };

  await myFunction(req, res);

  expect(res.status).toHaveBeenCalledWith(200);
  expect(res.json).toHaveBeenCalledWith(
    expect.objectContaining({ message: expect.any(String) })
  );
});

// Test a Firestore-triggered function
test("Firestore trigger processes document", async () => {
  const snap = functionsTest.firestore.makeDocumentSnapshot(
    { name: "test-item", status: "pending" },
    "<your-collection>/doc-123"
  );

  const wrapped = functionsTest.wrap(myFunction);
  await wrapped(snap);

  // Verify side effects (e.g., another document was updated)
  const result = await admin
    .firestore()
    .collection("<your-collection>")
    .doc("doc-123")
    .get();
  expect(result.data().status).toBe("processed");
});
```

**Run function tests:**

```bash
cd functions && npm test && cd ..
```

## Auth Trigger Testing (Step 5)

Test Authentication triggers by simulating user lifecycle events.

```javascript
// Example: functions/test/auth-triggers.test.js
const functionsTest = require("firebase-functions-test")({
  projectId: "<your-project-id>",
});

const { onUserCreated, onUserDeleted } = require("../index");

afterAll(() => {
  functionsTest.cleanup();
});

// Test user creation trigger
test("new user trigger creates profile document", async () => {
  const userRecord = functionsTest.auth.makeUserRecord({
    uid: "test-user-789",
    email: "newuser@example.com",
    displayName: "New User",
  });

  const wrapped = functionsTest.wrap(onUserCreated);
  await wrapped(userRecord);

  // Verify a profile document was created in Firestore
  const admin = require("firebase-admin");
  const profile = await admin
    .firestore()
    .collection("profiles")
    .doc("test-user-789")
    .get();
  expect(profile.exists).toBe(true);
  expect(profile.data().email).toBe("newuser@example.com");
});

// Test user deletion trigger
test("user deletion trigger cleans up data", async () => {
  const userRecord = functionsTest.auth.makeUserRecord({
    uid: "test-user-789",
    email: "deleted@example.com",
  });

  const wrapped = functionsTest.wrap(onUserDeleted);
  await wrapped(userRecord);
});
```

## Test Data Seeding with Emulator (Step 7)

Seed and manage test data for reproducible test runs.

**Export current emulator state (for reuse):**

```bash
npx -y firebase-tools@latest emulators:export ./test-data-seed --force
```

**Import seed data before test runs:**

```bash
npx -y firebase-tools@latest emulators:start \
  --project <your-project-id> \
  --import ./test-data-seed \
  --only firestore,auth \
  &
```

**Programmatic seeding via Admin SDK:**

```javascript
const admin = require("firebase-admin");

async function seedTestData() {
  const db = admin.firestore();
  const batch = db.batch();

  // Seed a collection with test documents
  const testDocs = [
    { id: "doc-1", name: "Item A", status: "active" },
    { id: "doc-2", name: "Item B", status: "archived" },
    { id: "doc-3", name: "Item C", status: "active" },
  ];

  for (const doc of testDocs) {
    batch.set(db.collection("<your-collection>").doc(doc.id), doc);
  }

  await batch.commit();
  console.log(`Seeded ${testDocs.length} documents`);
}
```

**Clear data between test suites:**

```bash
curl -X DELETE "http://localhost:8080/emulator/v1/projects/<your-project-id>/databases/(default)/documents"
```
