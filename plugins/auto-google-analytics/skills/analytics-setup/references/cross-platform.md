# Cross-Platform Analytics — mobile & desktop (same GA4 backend)

The main `analytics-setup` workflow is web (GA4 via GTM). A non-web app the
project ships sends to the **same GA4 property family** so web + app behavior is
unified in one place. Sources verified against official Google/Firebase docs
2026-06-25. Use this reference when STEP 1 detects a mobile or desktop project.

## Mobile apps → Firebase Analytics

Firebase Analytics and GA4 share one backend: each app is registered as a
**data stream** inside a GA4 property (link the Firebase project to GA4 in the
Firebase console — Project Settings → Integrations → Google Analytics; without
the link, app events never reach GA4).

| Platform | Package | Setup |
|---|---|---|
| Flutter | `firebase_analytics` (pub.dev, first-party) | `flutter pub add firebase_analytics`; FlutterFire CLI generates `firebase_options.dart` |
| React Native | `@react-native-firebase/analytics` (community std; no Google first-party RN SDK) | needs `@react-native-firebase/app` + `AsyncStorage` for session persistence |
| Android native | `com.google.firebase:firebase-analytics` (Gradle) | needs `google-services.json` |

- **Auto-collected:** `first_open`, `screen_view`, `session_start`, in-app
  purchases — no code. **Custom events:** `FirebaseAnalytics.instance.logEvent(name, parameters)`
  (Flutter) / `logEvent(...)` equivalents — `snake_case`, same naming convention as web.
- **Consent (GDPR/DPDP):** `FirebaseAnalytics.instance.setConsent({...})` (Flutter) /
  `setConsent(...)` (Android) — the mobile analog of web Consent Mode v2.

## Desktop / Electron / Windows → GA4 Measurement Protocol

No gtag/Firebase SDK path — send events over HTTPS POST to the Measurement Protocol.

```
POST https://www.google-analytics.com/mp/collect?measurement_id=G-XXXX&api_secret=SECRET
Content-Type: application/json
{ "client_id": "PERSISTED_UUID_PER_INSTALL",
  "events": [ { "name": "app_open", "params": { "engagement_time_msec": 100 } } ] }
```

- **`api_secret` MUST stay server-side** — never embed it in an Electron renderer
  (DevTools-readable). Send from the main process, or proxy through a small
  backend (Cloudflare Worker / Vercel Edge Function). Exposed = anyone can spam
  the property. (EU endpoint: `https://region1.google-analytics.com/mp/collect`.)
- **`client_id`:** generate a UUID v4 on first launch, persist to
  `app.getPath('userData')` (Electron) — the stable anonymous device identifier.
- The Measurement Protocol **supplements** SDK collection; some GA4 features
  (user-lifetime, certain attribution) are weaker than the full gtag/Firebase path.

## YAGNI note

These procedures are documented and ready, but the hub does NOT ship heavy
per-platform tooling (a code module, a provisioning skill) speculatively — build
that when a concrete mobile/Windows app actually needs it (`rule-curation.md`:
reactive, not speculative). For a web project, ignore this file.
