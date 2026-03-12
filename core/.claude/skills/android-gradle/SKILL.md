---
name: android-gradle
description: >
  Gradle convention plugins, version catalogs, and build performance optimization for Android projects.
  Use when setting up build-logic/, configuring libs.versions.toml, debugging slow builds,
  enabling Configuration Cache, migrating kapt to KSP, or optimizing CI/CD build pipelines.
triggers: "gradle, build-logic, convention plugin, build performance, gradle optimization, version catalog, libs.versions.toml"
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<task-description or 'setup' or 'optimize' or 'diagnose'>"
---

# Android Gradle Build System

Configure scalable, maintainable Gradle builds for Android projects using Convention Plugins, Version Catalogs, and 12 proven performance optimization patterns.

**Request:** $ARGUMENTS

---

## STEP 1: Convention Plugins (build-logic/)

Centralize build configuration in a composite build so module-level `build.gradle.kts` files stay minimal.

### Project Structure

```
root/
├── build-logic/
│   ├── convention/
│   │   ├── src/main/kotlin/
│   │   │   ├── AndroidApplicationConventionPlugin.kt
│   │   │   ├── AndroidLibraryConventionPlugin.kt
│   │   │   ├── ComposeConventionPlugin.kt
│   │   │   ├── AndroidFeatureConventionPlugin.kt
│   │   │   └── AndroidHiltConventionPlugin.kt
│   │   └── build.gradle.kts
│   ├── build.gradle.kts
│   └── settings.gradle.kts
├── gradle/
│   └── libs.versions.toml
├── app/
│   └── build.gradle.kts
└── settings.gradle.kts
```

### Root settings.gradle.kts

Include `build-logic` as a composite build for plugin management:

```kotlin
// settings.gradle.kts
pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
```

### Convention Plugin Class

```kotlin
// build-logic/convention/src/main/kotlin/AndroidApplicationConventionPlugin.kt
import com.android.build.api.dsl.ApplicationExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<ApplicationExtension> {
                compileSdk = 35
                defaultConfig {
                    targetSdk = 35
                    minSdk = 26
                }
                compileOptions {
                    sourceCompatibility = JavaVersion.VERSION_17
                    targetCompatibility = JavaVersion.VERSION_17
                }
            }
        }
    }
}
```

### AndroidLibraryConventionPlugin

```kotlin
// build-logic/convention/src/main/kotlin/AndroidLibraryConventionPlugin.kt
import com.android.build.gradle.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                compileSdk = 35
                defaultConfig.minSdk = 26
                compileOptions {
                    sourceCompatibility = JavaVersion.VERSION_17
                    targetCompatibility = JavaVersion.VERSION_17
                }
            }
        }
    }
}
```

### ComposeConventionPlugin

```kotlin
// build-logic/convention/src/main/kotlin/ComposeConventionPlugin.kt
import com.android.build.api.dsl.CommonExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class ComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("org.jetbrains.kotlin.plugin.compose")
            }

            extensions.configure<CommonExtension<*, *, *, *, *, *>> {
                buildFeatures.compose = true
            }
        }
    }
}
```

### Register Plugins in build-logic/convention/build.gradle.kts

```kotlin
// build-logic/convention/build.gradle.kts
plugins {
    `kotlin-dsl`
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "myapp.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
        register("androidLibrary") {
            id = "myapp.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("androidCompose") {
            id = "myapp.android.compose"
            implementationClass = "ComposeConventionPlugin"
        }
        register("androidFeature") {
            id = "myapp.android.feature"
            implementationClass = "AndroidFeatureConventionPlugin"
        }
        register("androidHilt") {
            id = "myapp.android.hilt"
            implementationClass = "AndroidHiltConventionPlugin"
        }
    }
}
```

### Apply Convention Plugins in Modules

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.myapp.android.application)
    alias(libs.plugins.myapp.android.compose)
}

android {
    namespace = "com.example.myapp"
    defaultConfig {
        applicationId = "com.example.myapp"
        versionCode = 1
        versionName = "1.0"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.bundles.compose)
}
```

---

## STEP 2: Version Catalog (libs.versions.toml)

Define all dependency versions in a single source of truth at `gradle/libs.versions.toml`.

### Structure

```toml
# gradle/libs.versions.toml

[versions]
androidGradlePlugin = "8.7.3"
kotlin = "2.1.0"
composeBom = "2025.01.01"
hilt = "2.53.1"
room = "2.6.1"
coroutines = "1.9.0"
ksp = "2.1.0-1.0.29"

[libraries]
# AndroidX
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version = "1.15.0" }
androidx-lifecycle-runtime-compose = { group = "androidx.lifecycle", name = "lifecycle-runtime-compose", version = "2.8.7" }
androidx-activity-compose = { group = "androidx.activity", name = "activity-compose", version = "1.9.3" }

# Compose (BOM-managed)
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-compose-ui = { group = "androidx.compose.ui", name = "ui" }
androidx-compose-material3 = { group = "androidx.compose.material3", name = "material3" }
androidx-compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview" }

# Hilt
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }

# Room
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
room-compiler = { group = "androidx.room", name = "room-compiler", version.ref = "room" }
room-ktx = { group = "androidx.room", name = "room-ktx", version.ref = "room" }

# Build-logic dependencies (for convention plugins)
android-gradlePlugin = { group = "com.android.tools.build", name = "gradle", version.ref = "androidGradlePlugin" }
kotlin-gradlePlugin = { group = "org.jetbrains.kotlin", name = "kotlin-gradle-plugin", version.ref = "kotlin" }
compose-gradlePlugin = { group = "org.jetbrains.kotlin", name = "compose-compiler-gradle-plugin", version.ref = "kotlin" }

[bundles]
compose = ["androidx-compose-ui", "androidx-compose-material3", "androidx-compose-ui-tooling-preview", "androidx-activity-compose"]
room = ["room-runtime", "room-ktx"]

[plugins]
android-application = { id = "com.android.application", version.ref = "androidGradlePlugin" }
android-library = { id = "com.android.library", version.ref = "androidGradlePlugin" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
# Convention plugins (version = "unspecified" since they are local)
myapp-android-application = { id = "myapp.android.application", version = "unspecified" }
myapp-android-library = { id = "myapp.android.library", version = "unspecified" }
myapp-android-compose = { id = "myapp.android.compose", version = "unspecified" }
```

### Referencing in build.gradle.kts

```kotlin
// Libraries
implementation(libs.androidx.core.ktx)
implementation(platform(libs.androidx.compose.bom))
implementation(libs.bundles.compose)

// Annotation processors
ksp(libs.hilt.compiler)
ksp(libs.room.compiler)

// Plugins
plugins {
    alias(libs.plugins.myapp.android.application)
}
```

---

## STEP 3: Build Performance Optimization

Apply these 12 optimization patterns. Change one at a time and measure the impact.

### Workflow

1. **Measure Baseline** -- Clean build + incremental build times
2. **Generate Build Scan** -- `./gradlew assembleDebug --scan`
3. **Identify Phase** -- Configuration? Execution? Dependency resolution?
4. **Apply ONE optimization** -- Do not batch changes
5. **Measure Improvement** -- Compare against baseline
6. **Verify in Build Scan** -- Visual confirmation

### Build Phases

| Phase | What Happens | Common Issues |
|-------|-------------|---------------|
| **Initialization** | `settings.gradle.kts` evaluated | Too many `include()` statements |
| **Configuration** | All `build.gradle.kts` files evaluated | Expensive plugins, eager task creation |
| **Execution** | Tasks run based on inputs/outputs | Cache misses, non-incremental tasks |

### 1. Configuration Cache

Caches configuration phase across builds (AGP 8.0+):

```properties
# gradle.properties
org.gradle.configuration-cache=true
org.gradle.configuration-cache.problems=warn
```

### 2. Build Cache

Reuses task outputs across builds and machines:

```properties
# gradle.properties
org.gradle.caching=true
```

### 3. Parallel Execution

Build independent modules simultaneously:

```properties
# gradle.properties
org.gradle.parallel=true
```

### 4. JVM Heap

Allocate more memory for large projects:

```properties
# gradle.properties
org.gradle.jvmargs=-Xmx4g -XX:+UseParallelGC
```

### 5. Non-Transitive R Classes

Reduces R class size and compilation (AGP 8.0+ default):

```properties
# gradle.properties
android.nonTransitiveRClass=true
```

### 6. Migrate kapt to KSP (2x Faster)

```kotlin
// Before (slow)
kapt("com.google.dagger:hilt-compiler:2.53.1")

// After (fast)
ksp("com.google.dagger:hilt-compiler:2.53.1")
```

### 7. Avoid Dynamic Dependencies

Pin dependency versions:

```kotlin
// BAD: Forces resolution every build
implementation("com.example:lib:+")
implementation("com.example:lib:1.0.+")

// GOOD: Fixed version
implementation("com.example:lib:1.2.3")
```

### 8. Optimize Repository Order

Put most-used repositories first:

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        google()        // First: Android dependencies
        mavenCentral()  // Second: Most libraries
        // Third-party repos last
    }
}
```

### 9. includeBuild for Local Modules

Composite builds are faster than `project()` for large monorepos:

```kotlin
// settings.gradle.kts
includeBuild("shared-library") {
    dependencySubstitution {
        substitute(module("com.example:shared")).using(project(":"))
    }
}
```

### 10. Incremental Annotation Processing

```properties
# gradle.properties
kapt.incremental.apt=true
kapt.use.worker.api=true
```

### 11. Lazy Task Configuration

Use `register()` instead of `create()`:

```kotlin
// BAD: Eagerly configured (runs during configuration phase)
tasks.create("myTask") { ... }

// GOOD: Lazily configured (runs only when needed)
tasks.register("myTask") { ... }
```

### 12. Avoid Configuration-Time I/O

Do not read files or make network calls during configuration:

```kotlin
// BAD: Runs during configuration
val version = file("version.txt").readText()

// GOOD: Defer to execution
val version = providers.fileContents(file("version.txt")).asText
```

### Recommended gradle.properties

```properties
# gradle.properties — full optimization set
org.gradle.configuration-cache=true
org.gradle.configuration-cache.problems=warn
org.gradle.caching=true
org.gradle.parallel=true
org.gradle.jvmargs=-Xmx4g -XX:+UseParallelGC
android.nonTransitiveRClass=true

# If still using kapt (prefer KSP)
kapt.incremental.apt=true
kapt.use.worker.api=true
```

---

## STEP 4: CI/CD Build Optimization

### Remote Build Cache

Share build outputs across CI runners and developer machines:

```kotlin
// settings.gradle.kts
buildCache {
    local { isEnabled = true }
    remote<HttpBuildCache> {
        url = uri("https://cache.example.com/")
        isPush = System.getenv("CI") == "true"
        credentials {
            username = System.getenv("CACHE_USER")
            password = System.getenv("CACHE_PASS")
        }
    }
}
```

### Gradle Build Scans (Develocity)

```kotlin
// settings.gradle.kts
plugins {
    id("com.gradle.develocity") version "3.17"
}

develocity {
    buildScan {
        termsOfUseUrl.set("https://gradle.com/help/legal-terms-of-use")
        termsOfUseAgree.set("yes")
        publishing.onlyIf { System.getenv("CI") != null }
    }
}
```

### Skip Unnecessary Tasks in CI

```bash
# Skip tests for UI-only changes
./gradlew assembleDebug -x test -x lint

# Only run affected module tests
./gradlew :feature:login:test

# Profile build locally
./gradlew assembleDebug --profile
# Report saved to build/reports/profile/
```

---

## Bottleneck Analysis

### Slow Configuration Phase

**Symptoms**: Build scan shows long "Configuring build" time.

| Cause | Fix |
|-------|-----|
| Eager task creation | Use `tasks.register()` instead of `tasks.create()` |
| buildSrc with many dependencies | Migrate to Convention Plugins with `includeBuild` |
| File I/O in build scripts | Use `providers.fileContents()` |
| Network calls in plugins | Cache results or use offline mode (`--offline`) |

### Slow Compilation

**Symptoms**: `:app:compileDebugKotlin` takes too long.

| Cause | Fix |
|-------|-----|
| Non-incremental changes | Avoid `build.gradle.kts` changes that invalidate cache |
| Large modules | Break into smaller feature modules |
| Excessive kapt usage | Migrate to KSP |
| Kotlin compiler memory | Increase `kotlin.daemon.jvmargs` |

### Cache Misses

**Symptoms**: Tasks always rerun despite no changes.

| Cause | Fix |
|-------|-----|
| Unstable task inputs | Use `@PathSensitive`, `@NormalizeLineEndings` |
| Absolute paths in outputs | Use relative paths |
| Missing `@CacheableTask` | Add annotation to custom tasks |
| Different JDK versions | Standardize JDK across environments |

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| Build fails after AGP update | Plugin API changes | Check AGP release notes; update convention plugin imports |
| `Could not resolve plugin` | Convention plugin not registered | Verify `gradlePlugin {}` block in `build-logic/convention/build.gradle.kts` |
| OOM during build | Insufficient JVM heap | Increase `-Xmx` in `gradle.properties`; check for memory leaks in custom tasks |
| Slow Gradle sync in IDE | Large dependency graph, many modules | Enable parallel sync; reduce `include()` count; use `--offline` for repeated syncs |
| Cache misses on CI | Environment differences | Standardize JDK, Gradle wrapper version, and OS across runners |
| `Configuration cache problems found` | Plugin incompatibility | Set `problems=warn` first; file issues with plugin maintainers |
| Version catalog not visible in build-logic | Missing catalog access | Add `versionCatalogs { create("libs") { from(files("../gradle/libs.versions.toml")) } }` to build-logic settings |

---

## CRITICAL RULES

### MUST DO

- Use convention plugins in `build-logic/` instead of duplicating config across modules
- Define all dependency versions in `libs.versions.toml` -- never hardcode versions in `build.gradle.kts`
- Enable Configuration Cache, Build Cache, and Parallel Execution in `gradle.properties`
- Use KSP instead of kapt for all annotation processors that support it
- Pin all dependency versions -- never use `+` or range notation
- Use `tasks.register()` for custom tasks -- never `tasks.create()`
- Measure before and after every optimization with `--scan` or `--profile`
- Put `google()` before `mavenCentral()` in repository declarations
- Use `providers.fileContents()` for file reads in build scripts
- Standardize JDK version across all developer machines and CI runners

### MUST NOT DO

- Copy-paste build configuration between module `build.gradle.kts` files -- use convention plugins instead
- Use `buildSrc/` for build logic -- use `build-logic/` composite build instead (faster, avoids full recompilation)
- Read files or make network calls during the configuration phase -- defer to execution with providers
- Use dynamic dependency versions (`+`, `latest.release`) -- pin exact versions in the version catalog
- Skip build scan analysis when investigating slow builds -- measure with `--scan` instead of guessing
- Add repositories at the module level when `repositoriesMode.set(FAIL_ON_PROJECT_REPOS)` is active
- Ignore Configuration Cache warnings -- treat them as migration tasks and fix incrementally
- Batch multiple optimization changes -- apply one at a time and measure each independently
