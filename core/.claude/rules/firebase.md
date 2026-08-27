---
paths: ["**/firebase/**", "**/auth/**/*.ts", "**/auth/**/*.kt", "**/auth/**/*.dart", "**/auth/**/*.py"]
description: Firebase Auth, Firestore, and backend token verification patterns.
---

# Firebase Rules

## Initialization
- Always wrap `Firebase.initializeApp()` with a timeout (10s max) — hangs indefinitely on devices without internet
- Continue app launch even if Firebase init fails — degrade gracefully with offline functionality

## Phone OTP Auth Flow
- Handle all three verification callbacks: `codeSent`, `verificationCompleted` (auto-verify), `verificationFailed`
- Implement SMS auto-read where available (SmartAuth on Android, no equivalent on iOS)
- Never skip the `verificationFailed` callback — unhandled failures leave users stuck

## Token Exchange (Client → Backend)
- Exchange Firebase ID token for an app-specific JWT on the backend — never use the Firebase ID token directly for API authentication
- Store both access token and refresh token — use encrypted storage (EncryptedSharedPreferences, flutter_secure_storage) as primary, plain storage as fallback
- Implement token rotation with reuse detection on backend — revoke all tokens for user if a reused refresh token is detected

## Backend Token Verification
- Use `firebase_admin.auth.verify_id_token()` (Python) or `admin.auth().verifyIdToken()` (Node.js) — never manually decode JWT
- Set clock skew tolerance (60s) to handle minor time drift between client and server
- E2E test bypass: accept fake tokens gated by env var (`ENABLE_TEST_AUTH`) — exit process immediately if test auth is enabled in production

## Multi-Environment Config
- Separate `google-services.json` (Android) and `GoogleService-Info.plist` (iOS) per build flavor/scheme (`dev`/`prod`)
- Backend: use `FIREBASE_CREDENTIALS_PATH` env var — fall back to application default credentials for cloud environments
- Never commit Firebase service account keys — use environment variables or secret managers

## Firestore Conventions
- Collection names as constants in a dedicated class — never inline string literals
- Use subcollections for user-scoped data (e.g., `users/{uid}/preferences`) — never flatten into top-level collections
- `doc_to_dict()` helper: always inject document ID into the returned dictionary — Firestore snapshots don't include `id` in `data()`

## Security Rules
- Default deny: start with `allow read, write: if false;` then open specific paths
- Validate data types and required fields in write rules — never trust client-submitted data structure
- Use `request.auth.uid` for ownership checks — never rely on a `userId` field in the document
