# 9.3 Versioning Strategy

### 9.3 Versioning Strategy

| Platform | Version Field | Auto-Increment | Example |
|----------|--------------|----------------|---------|
| Android | `versionCode` (int) + `versionName` (string) | CI build number for versionCode | `versionCode=142`, `versionName="2.3.1"` |
| iOS | `CFBundleVersion` (build) + `CFBundleShortVersionString` (marketing) | CI build number for CFBundleVersion | `1.2.3 (142)` |

```kotlin
// build.gradle.kts — auto-increment versionCode from CI
android {
    defaultConfig {
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "2.3.1"
    }
}
```

