# 9.4 Signing Key Management

### 9.4 Signing Key Management

| Item | Storage | Access |
|------|---------|--------|
| Android keystore (`.jks`) | CI secrets (base64 encoded) | Decode at build time, delete after |
| Play Store service account JSON | CI secrets | Upload only, no read access to store |
| iOS distribution certificate | Match (Fastlane) or manual in CI | Stored in encrypted git repo or CI secrets |
| iOS provisioning profiles | Match (Fastlane) auto-manages | Synced from Apple Developer Portal |

**Critical rules:**
- NEVER commit keystores or signing keys to git
- MUST use Play App Signing (Google manages upload key → signing key)
- MUST back up keystores separately — lost keystore = cannot update app
- Use Fastlane `match` for iOS to share signing identities across team

