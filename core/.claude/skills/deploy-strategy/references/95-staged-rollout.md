# 9.5 Staged Rollout

### 9.5 Staged Rollout

| Track/Phase | Audience | Purpose |
|-------------|----------|---------|
| Internal (Android) / TestFlight (iOS) | Team only | Smoke testing |
| Closed beta / TestFlight external | Selected users | Beta testing |
| Open beta / Public TestFlight | Opt-in users | Pre-release validation |
| Production 10% → 50% → 100% | Staged | Gradual rollout with crash monitoring |

Monitor crash rate (Firebase Crashlytics / Sentry) at each rollout stage. Halt rollout if crash rate exceeds baseline by >2x.

---

