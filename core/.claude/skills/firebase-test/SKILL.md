---
name: firebase-test
description: >
  Run and validate Firebase application tests across security rules, Cloud Functions,
  Auth triggers, and Test Lab. Manages Firebase Emulator Suite lifecycle, seeds test
  data, and produces structured JSON results. Invokes /fix-loop on failure and
  /learn-n-improve on success. Use when testing Firebase security rules, Cloud Functions, or Auth triggers.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<test-scope> [--rules|--functions|--auth|--emulator]"
version: "1.1.0"
---

# Firebase Test Runner

Run Firebase tests with emulator-backed isolation. Supports Firestore security rules,
Cloud Functions, Auth triggers, and Firebase Test Lab for mobile.

**CRITICAL: All tests MUST run against the Firebase Emulator Suite — never against
production or staging Firebase projects. Set `FIRESTORE_EMULATOR_HOST` and
`FIREBASE_AUTH_EMULATOR_HOST` environment variables before every test run.**

**Request:** $ARGUMENTS

---

## STEP 1: Detect Firebase Project Configuration

Locate and validate the Firebase project setup.

```bash
# Find firebase.json in the project
ls firebase.json 2>/dev/null || echo "ERROR: firebase.json not found at project root"
```

**Required files to check:**

| File | Purpose | Required |
|------|---------|----------|
| `firebase.json` | Emulator and service config | Yes |
| `.firebaserc` | Project aliases | Yes |
| `firestore.rules` | Firestore security rules | If Firestore used |
| `firestore.indexes.json` | Index definitions | If Firestore used |
| `functions/package.json` | Cloud Functions dependencies | If Functions used |

**Read `firebase.json`** and extract:
- Which emulators are configured (`emulators` key)
- Rules file paths (`firestore.rules`, `storage.rules`)
- Functions source directory (`functions.source`)
- Hosting configuration (if applicable)

If `firebase.json` is missing or incomplete, report the gap and stop.

---

## STEP 2: Firebase Emulator Suite Setup and Startup

Install and start the emulator suite for isolated testing.

```bash
# Install emulators if not already present
npx -y firebase-tools@latest setup:emulators:firestore
npx -y firebase-tools@latest setup:emulators:auth
npx -y firebase-tools@latest setup:emulators:functions
npx -y firebase-tools@latest setup:emulators:storage

# Start emulators in background with a known project ID
npx -y firebase-tools@latest emulators:start \
  --project <your-project-id> \
  --only firestore,auth,functions,storage \
  &

# Wait for emulators to be ready
echo "Waiting for emulators..."
timeout 30 bash -c 'until curl -s http://localhost:8080/ > /dev/null 2>&1; do sleep 1; done'
echo "Emulators ready."
```

**Set environment variables for all subsequent steps:**

```bash
export FIRESTORE_EMULATOR_HOST="localhost:8080"
export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099"
export FUNCTIONS_EMULATOR_HOST="localhost:5001"
export FIREBASE_STORAGE_EMULATOR_HOST="localhost:9199"
export GCLOUD_PROJECT="<your-project-id>"
```

**Verify emulator health** by hitting the Emulator UI endpoint:

```bash
curl -s http://localhost:4000 | head -c 200
```

If emulators fail to start, check port conflicts and `firebase.json` emulator config.

---

## STEP 3: Firestore Security Rules Testing

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

---

## STEP 4: Cloud Functions Unit Testing

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

---

## STEP 5: Auth Trigger Testing

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

---

## STEP 6: Firebase Test Lab Integration for Mobile

If the project contains Android (`build.gradle`, `build.gradle.kts`) or iOS (`*.xcodeproj`, `Podfile`) artifacts, run device tests via Firebase Test Lab.

**Detect mobile platform:**

```bash
# Android detection
ls app/build.gradle app/build.gradle.kts 2>/dev/null && echo "ANDROID_DETECTED"

# iOS detection
ls *.xcodeproj Podfile 2>/dev/null && echo "IOS_DETECTED"
```

**Android Test Lab:**

```bash
# Build test APKs
./gradlew :app:assembleDebug :app:assembleDebugAndroidTest

# Run instrumented tests on Test Lab
npx -y firebase-tools@latest test:android:run \
  --app app/build/outputs/apk/debug/app-debug.apk \
  --test app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk \
  --device model=Pixel2,version=30,locale=en,orientation=portrait \
  --results-dir test-lab-results \
  --timeout 10m
```

**iOS Test Lab:** Use `xcodebuild build-for-testing` to produce a test bundle, then
`npx -y firebase-tools@latest test:ios:run --test <path-to-test-zip> --device model=iphone13pro,version=15.7,locale=en,orientation=portrait`.

Skip this step if no mobile artifacts are detected.

---

## STEP 7: Test Data Seeding with Emulator

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

---

## STEP 8: Run Tests and Collect Results

Execute the test suite based on the `--scope` argument.

| Flag | Runs |
|------|------|
| `--rules` | Firestore security rules tests only |
| `--functions` | Cloud Functions unit tests only |
| `--auth` | Auth trigger tests only |
| `--emulator` | All emulator-backed tests (rules + functions + auth) |
| (no flag) | All detected test suites |

```bash
# Run all tests with coverage
npx jest --coverage --forceExit --json --outputFile=test-results/raw-output.json

# Or with mocha
npx mocha --recursive --reporter json --exit > test-results/raw-output.json
```

Capture exit code, stdout, and stderr for structured output in the next step.

---

## STEP 9: Write Structured JSON Output

Write results to `test-results/firebase-test.json` in the standard format.

```json
{
  "skill": "firebase-test",
  "timestamp": "2026-03-15T10:00:00Z",
  "result": "PASSED",
  "summary": {
    "total": 18,
    "passed": 17,
    "failed": 0,
    "skipped": 1,
    "flaky": 0
  },
  "quality_gate": "PASSED",
  "contract_check": "SKIPPED",
  "perf_baseline": "SKIPPED",
  "scopes_tested": ["rules", "functions", "auth"],
  "emulator_config": {
    "firestore_port": 8080,
    "auth_port": 9099,
    "functions_port": 5001,
    "project_id": "<your-project-id>"
  },
  "failures": [],
  "warnings": [],
  "duration_ms": 8500
}
```

**Failure entry example:**

```json
{
  "test": "unauthenticated user cannot write",
  "category": "RULES_VIOLATION",
  "file": "test/firestore-rules.test.js:45",
  "message": "Expected request to fail but it succeeded — security rule is too permissive",
  "confidence": "HIGH"
}
```

Ensure `test-results/` directory exists before writing:

```bash
mkdir -p test-results
```

---

## STEP 10: Tear Down Emulators

Stop all running emulators to free ports and resources.

```bash
# Find and kill emulator processes
npx -y firebase-tools@latest emulators:exec --only firestore,auth,functions,storage "echo done" 2>/dev/null

# Fallback: kill by port if emulators:exec is not applicable
lsof -ti:8080,9099,5001,9199,4000 | xargs kill -9 2>/dev/null || true
```

Verify ports are released and report final status with passed/failed/skipped counts.

---

## STEP 11: Auto-Fix and Learn (On Failure Only)

If tests failed in STEP 8, automatically invoke the fix-and-learn pipeline. Do NOT just report failures — fix them.

### 11a. Invoke Fix-Loop

```
Skill("fix-loop", args="<failure_output>\n\nretest_command: npx jest {test_scope} --forceExit")
```

Or for mocha:
```
Skill("fix-loop", args="<failure_output>\n\nretest_command: npx mocha {test_scope} --exit")
```

### 11b. Capture Learnings (On Fix Success)

If `/fix-loop` reports `result: PASSED` or `result: FIXED`:

```
Skill("learn-n-improve", args="session")
```

### 11c. Escalation (On Fix Failure)

If `/fix-loop` exhausts 5 iterations without success:
- Report the failure to the user
- Suggest `/systematic-debugging` for deeper investigation
- Do NOT silently continue

### Skip Conditions

Do NOT auto-invoke fix-loop if:
- Emulators failed to start (environment error — fix emulator setup first)
- `firebase.json` is missing or misconfigured
- The failure is a security rules test that correctly rejects access (that's the test working as intended)

---

## CRITICAL RULES

### MUST DO

- MUST run all tests against the Firebase Emulator Suite, never against live projects
- MUST invoke `/fix-loop` on test failure — do not just report failures
- MUST set `FIRESTORE_EMULATOR_HOST` and `FIREBASE_AUTH_EMULATOR_HOST` before test execution
- MUST clear Firestore data between test suites using `testEnv.clearFirestore()` or the REST endpoint
- MUST tear down emulators after test completion (Step 10), even on failure
- MUST write structured JSON output to `test-results/firebase-test.json`
- MUST use `--forceExit` (Jest) or `--exit` (Mocha) to prevent hanging test processes
- MUST check emulator health before running tests — fail fast if emulators are not responding
- MUST use `<your-project-id>`, `<your-collection>`, and similar placeholders instead of real project names

### MUST NOT DO

- MUST NOT run tests against production or staging Firebase projects
- MUST NOT commit service account keys or credentials to version control
- MUST NOT hardcode port numbers — read them from `firebase.json` emulator config when possible
- MUST NOT skip emulator teardown — leaked emulator processes cause port conflicts on subsequent runs
- MUST NOT use `firebase-admin` `initializeApp()` without pointing to the emulator (it defaults to production)
- MUST NOT seed test data with user PII — use synthetic placeholder data only
- MUST NOT leave emulator export directories (`test-data-seed/`) in the committed codebase unless intentional
