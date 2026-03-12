---
name: firebase-dev
description: >
  Core Firebase development: project setup, CLI, Authentication (providers, tokens,
  security rules, web SDK), and Firestore (provisioning, security rules, CRUD,
  transactions, realtime listeners, indexes). Use when building Firebase-backed apps.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<what to set up or implement — e.g. 'add Google auth' or 'create Firestore rules for user posts'>"
---

# Firebase Core Development

Reference for Firebase project setup, Authentication, and Firestore.

**Request:** $ARGUMENTS

---

## Project Setup & CLI

| Detail | Value |
|--------|-------|
| CLI install | `npm install -g firebase-tools` |
| Login | `npx -y firebase-tools@latest login` |
| Create project | `npx -y firebase-tools@latest projects:create` |
| Init services | `npx -y firebase-tools@latest init` |
| Node.js | v20+ required |

### Web SDK Initialization

```javascript
import { initializeApp } from "firebase/app";

// If running in Firebase App Hosting, skip config:
// const app = initializeApp();

const firebaseConfig = {
  // Get values: npx -y firebase-tools@latest apps:sdkconfig <platform> <app-id>
};

const app = initializeApp(firebaseConfig);
```

### Key Files

| File | Purpose |
|------|---------|
| `firebase.json` | CLI configuration (services, rules paths, hosting) |
| `.firebaserc` | Project aliases |
| `firestore.rules` | Firestore security rules |
| `firestore.indexes.json` | Firestore index definitions |

---

## Authentication

### Supported Providers

| Provider | Module |
|----------|--------|
| Email/Password | `createUserWithEmailAndPassword`, `signInWithEmailAndPassword` |
| Google | `GoogleAuthProvider` + `signInWithPopup` |
| Facebook | `FacebookAuthProvider` + `signInWithPopup` |
| Apple | `OAuthProvider('apple.com')` + `signInWithPopup` |
| Twitter | `TwitterAuthProvider` + `signInWithPopup` |
| GitHub | `GithubAuthProvider` + `signInWithPopup` |
| Microsoft | `OAuthProvider('microsoft.com')` + `signInWithPopup` |
| Anonymous | `signInAnonymously` |

Google Sign-In is the recommended default provider.

### Auth SDK Setup

```javascript
import { getAuth, connectAuthEmulator } from "firebase/auth";

const auth = getAuth(app);

// Connect to emulator in development
if (location.hostname === "localhost") {
  connectAuthEmulator(auth, "http://localhost:9099");
}
```

### Email/Password Sign-Up

```javascript
import { getAuth, createUserWithEmailAndPassword } from "firebase/auth";

const auth = getAuth();
createUserWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    const user = userCredential.user;
  })
  .catch((error) => {
    console.error(error.code, error.message);
  });
```

### OAuth Sign-In (Google Example)

```javascript
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";

const auth = getAuth();
const provider = new GoogleAuthProvider();

signInWithPopup(auth, provider)
  .then((result) => {
    const credential = GoogleAuthProvider.credentialFromResult(result);
    const token = credential.accessToken;
    const user = result.user;
  })
  .catch((error) => {
    console.error(error.code, error.message);
  });
```

### Anonymous Auth (Guest Accounts)

```javascript
import { getAuth, signInAnonymously, onAuthStateChanged } from "firebase/auth";

const auth = getAuth();
signInAnonymously(auth)
  .then(() => { /* signed in */ })
  .catch((error) => { console.error(error.code, error.message); });

// Monitor auth state
onAuthStateChanged(auth, (user) => {
  if (user) {
    const uid = user.uid;
    const isAnonymous = user.isAnonymous;
  }
});
```

### Sign Out

```javascript
import { getAuth, signOut } from "firebase/auth";

const auth = getAuth();
signOut(auth).then(() => { /* signed out */ });
```

### User Properties

| Property | Description |
|----------|-------------|
| `uid` | Unique identifier |
| `email` | Email address (if available) |
| `displayName` | Display name (if available) |
| `photoURL` | Profile photo URL (if available) |
| `emailVerified` | Whether email is verified |
| `isAnonymous` | Whether user is anonymous |

### Tokens

- **ID Token**: Short-lived JWT (1 hour), verifies identity for Firebase services
- **Refresh Token**: Long-lived, used to obtain new ID tokens automatically

---

## Firestore

### Provisioning

Create these files manually (do NOT use `firebase init` which requires interactive input):

**firebase.json:**
```json
{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  }
}
```

For a named database:
```json
{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json",
    "database": "my-database-id",
    "location": "us-central1"
  }
}
```

**firestore.rules** (locked-down starting point):
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

**firestore.indexes.json:**
```json
{
  "indexes": [],
  "fieldOverrides": []
}
```

### Firestore SDK Setup

```javascript
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

// Connect to emulator in development
if (location.hostname === "localhost") {
  connectFirestoreEmulator(db, "localhost", 8080);
}
```

### Write Operations

```javascript
import { doc, setDoc, addDoc, updateDoc, collection } from "firebase/firestore";

// Set (create or overwrite)
await setDoc(doc(db, "cities", "LA"), {
  name: "Los Angeles", state: "CA", country: "USA"
});

// Set with merge (partial update, creates if missing)
await setDoc(doc(db, "cities", "LA"), { population: 3900000 }, { merge: true });

// Add with auto-generated ID
const docRef = await addDoc(collection(db, "cities"), {
  name: "Tokyo", country: "Japan"
});

// Update specific fields (fails if doc doesn't exist)
await updateDoc(doc(db, "cities", "LA"), { capital: true });
```

### Transactions

```javascript
import { runTransaction, doc } from "firebase/firestore";

const sfDocRef = doc(db, "cities", "SF");
await runTransaction(db, async (transaction) => {
  const sfDoc = await transaction.get(sfDocRef);
  if (!sfDoc.exists()) throw "Document does not exist!";
  const newPop = sfDoc.data().population + 1;
  transaction.update(sfDocRef, { population: newPop });
});
```

### Read Operations

```javascript
import { doc, getDoc, getDocs, collection } from "firebase/firestore";

// Single document
const docSnap = await getDoc(doc(db, "cities", "SF"));
if (docSnap.exists()) console.log(docSnap.data());

// All documents in a collection
const querySnapshot = await getDocs(collection(db, "cities"));
querySnapshot.forEach((doc) => console.log(doc.id, doc.data()));
```

### Queries with Filters

```javascript
import { collection, query, where, orderBy, limit, getDocs } from "firebase/firestore";

const q = query(
  collection(db, "cities"),
  where("state", "==", "CA"),
  where("population", ">", 100000),
  orderBy("population", "desc"),
  limit(10)
);
const querySnapshot = await getDocs(q);
```

### Realtime Listeners

```javascript
import { doc, onSnapshot, collection, query, where } from "firebase/firestore";

// Listen to a single document
const unsubDoc = onSnapshot(doc(db, "cities", "SF"), (doc) => {
  console.log("Current data:", doc.data());
});

// Listen to a query
const q = query(collection(db, "cities"), where("state", "==", "CA"));
const unsubQuery = onSnapshot(q, (querySnapshot) => {
  querySnapshot.forEach((doc) => console.log(doc.data()));
});

// Unsubscribe when done
unsubDoc();
unsubQuery();
```

### Security Rules

#### Structure

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Rules go here
  }
}
```

#### Common Patterns

```
// Auth required
match /{document=**} {
  allow read, write: if request.auth != null;
}

// User-specific data
match /users/{userId} {
  allow read, write: if request.auth != null && request.auth.uid == userId;
}

// Verified email only
match /some_collection/{document} {
  allow read: if request.auth != null
              && request.auth.email_verified
              && request.auth.email.endsWith('@example.com');
}

// Data validation on create
match /users/{userId} {
  allow create: if request.auth.uid == userId
                && request.resource.data.email is string
                && request.resource.data.createdAt == request.time;
}
```

#### Granular Operations

| Read | Write |
|------|-------|
| `get` (single doc) | `create` (new doc) |
| `list` (queries) | `update` (existing doc) |
| | `delete` (remove doc) |

#### Hierarchical Rules

Rules do NOT cascade to subcollections. Match subcollections explicitly:

```
match /cities/{city} {
  allow read: if true;
  match /landmarks/{landmark} {
    allow read: if true;
  }
}
```

Use `{document=**}` for recursive wildcard matching across all subcollections.

### Indexes

| Type | Created Automatically? | Supports |
|------|----------------------|----------|
| Single-field | Yes | Simple equality (`==`), single range/sort |
| Composite | No (must define manually) | Multi-field filter/sort |

If a query requires a missing composite index, the SDK error message includes a direct link to create it in the Firebase Console.

**firestore.indexes.json example:**
```json
{
  "indexes": [
    {
      "collectionGroup": "cities",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "state", "order": "ASCENDING" },
        { "fieldPath": "population", "order": "DESCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

Deploy indexes: `npx -y firebase-tools@latest deploy --only firestore:indexes`

---

## Security Best Practices

1. **Start locked down** -- Begin with `allow read, write: if false` and open access incrementally
2. **Never use test mode in production** -- `allow read, write: if true` is for prototyping only
3. **Validate all writes** -- Check `request.resource.data` fields in create/update rules
4. **Use granular operations** -- Prefer `create`/`update`/`delete` over blanket `write`
5. **Scope user data** -- Match `request.auth.uid` against document path or field
6. **Test rules** -- Use the Firebase Emulator Suite to test rules before deploying

## Common Anti-Patterns

| Anti-Pattern | Use Instead |
|-------------|-------------|
| `allow write: if true` in production | Scoped rules with auth checks |
| Trusting client-set `uid` fields | Compare against `request.auth.uid` |
| Missing subcollection rules | Explicit match blocks for each subcollection |
| No data validation on writes | `request.resource.data` field checks |
| Hardcoded credentials in client code | Environment variables or Firebase config |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Check security rules match the path and operation |
| Missing index error | Follow the link in the error to create the composite index |
| Emulator not connecting | Verify emulator is running and port matches |
| Auth state not persisting | Check `setPersistence()` configuration |
| Stale data | Ensure listeners are properly set up, check network |

## References

- Firebase CLI: https://firebase.google.com/docs/cli
- Firebase Auth: https://firebase.google.com/docs/auth
- Firestore: https://firebase.google.com/docs/firestore
- Security Rules: https://firebase.google.com/docs/firestore/security/get-started
- Firebase Emulator Suite: https://firebase.google.com/docs/emulator-suite
