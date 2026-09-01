# Android — release impl (Gradle Kotlin DSL + R8 + AAB + CI)

> How release/build Terms ([release-theory.md](../../../reference/release-theory.md)) are written in native Android: Gradle Kotlin DSL + version catalog, AGP/KSP/Compose BOM, R8 minification, AAB, baseline profile, signing from env, and GitHub Actions CI. Per QUALITY-BAR §7.
> **Rule:** the build must be reproducible and versioned; secrets (keystore, signing) never in VCS; every release ships a fresh baseline profile + AAB and passes `lint`, `ktlint`, `detekt`, and tests.

## Gradle Kotlin DSL <!-- 11 -->
All `build.gradle.kts` use the Kotlin DSL with a **version catalog** (`gradle/libs.versions.toml`) — no hard-coded versions in modules, so bumps are centralized and Dependabot/Renovate can target `libs.versions.toml`.
```kotlin
// settings.gradle.kts
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS) }
rootProject.name = "canvas"
include(":app", ":domain", ":data")
```
Kotlin DSL gives type-safe `tasks`, `android {}`, and `namespace`; `FAIL_ON_PROJECT_REPOS` forces versions through the catalog.

## Version Catalog <!-- 14 -->
`gradle/libs.versions.toml` centralizes versions, plugins, and libraries in one table. Reference as `libs.<group>.<name>` in build files; bump a single line to update every consumer.
```toml
[versions]
agp = "8.7.3"; kotlin = "2.1.0"; composeBom = "2025.06.01"
room = "2.7.1"; hilt = "2.52"; ksp = "2.1.0-1.0.29"
[libraries]
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
[plugins]
agp = { id = "com.android.application", version.ref = "agp" }
```
Add `baselineprofile-gradle-plugin`, `kotlin-android`, `kotlin-kapt-compat`/`ksp` as plugins; pin everything so builds are reproducible.

## App Build Script <!-- 22 -->
The `:app/build.gradle.kts` wires application config, Compose BOM, KSP for Room/Hilt, and R8. `namespace`, `minSdk 34`, `compileSdk`/`targetSdk` latest stable (37 for AGP 9/Compose 1.12); `buildConfig` fields come from env (never secrets in source).
```kotlin
plugins { alias(libs.plugins.agp); alias(libs.plugins.kotlin.android); alias(libs.plugins.ksp) }
android {
  namespace = "com.example.canvas"; compileSdk = 37
  defaultConfig { applicationId = "com.example.canvas"; minSdk = 34; targetSdk = 36
    versionCode = 42; versionName = "1.4.2" }
  buildFeatures { compose = true; buildConfig = true }
  buildTypes {
    release { isMinifyEnabled = true; isShrinkResources = true
      proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro") }
  }
}
dependencies {
  implementation(platform(libs.androidx.compose.bom))
  implementation(libs.androidx.ui); implementation(libs.androidx.material3)
  ksp(libs.androidx.room.compiler); ksp(libs.hilt.compiler)
}
```
`buildConfigField("String","BACKEND_URL","\"${providers.gradleProperty("BACKEND_URL")...}\"")` injects the endpoint from `local.properties`/env only.

## R8 & ProGuard <!-- 13 -->
R8 aggressively shrinks/obfuscates; keep what reflection/`kotlinx.serialization`/network/Compose need. Ship a minimal, correct `proguard-rules.pro` — over-keeping bloats the AAB, under-keeping crashes on release. Test the release build's R8 rules with `testDebugUnitTest` run against the minified variant when feasible.
```properties
# kotlinx.serialization needs to keep generated serializer classes
-keepattributes *Annotation*, InnerClasses, EnclosingMethod
-keepclassmembers class * { @kotlinx.serialization.Serializable *; }
-keepclasseswithmembers class * { @retrofit2.http.* <methods>; }
# Retrofit
-keepattributes Signature, Exceptions
-dontwarn okhttp3.**, okio.**
```
Never `-keep` the whole app (defeats R8); keep only framework-touching classes. Verify with a `assembleRelease` + crash-free smoke test on a real device path.

## App Bundle & Profile <!-- 10 -->
Release artifacts are **App Bundles (AAB)** for Play and APKs for internal side-loading; the **baseline profile** ships in the AAB to pre-AOT the startup path (see performance-impl). Wire tasks so `bundleRelease` produces the final artifact.
```kotlin
androidComponents { onVariants { v ->
  v.artifacts.use(v.artifacts.getBuiltArtifactsLoader()) { ... }   // optional custom bind
} }
tasks.register("ship") { dependsOn("bundleRelease", "assembleDebug") }
```
Shipping the baseline profile requires the `androidx.baselineprofile` plugin and a `:baselineprofile` module; run `generateBaselineProfile` on a managed emulator and commit the profile (QUALITY-BAR §7).

## Signing <!-- 17 -->
Keystore + passwords come from **environment/CI secrets**, never VCS. Configure signing conditionally from `local.properties`/env so `debug` builds work without secrets and release reads keystore path/alias/password from injected env.
```kotlin
val ksPath = providers.environmentVariable("KEYSTORE_PATH").orNull
signingConfigs {
  create("release") {
    if (ksPath != null) {
      storeFile = file(ksPath)
      storePassword = providers.environmentVariable("KEYSTORE_PASSWORD").get()
      keyAlias = providers.environmentVariable("KEY_ALIAS").get()
      keyPassword = providers.environmentVariable("KEY_PASSWORD").get()
    }
  }
}
```
If unset, `assembleRelease` fails clearly rather than signing with a placeholder; the CI job injects these from its secret store.

## Quality Gates (CI) <!-- 10 -->
GitHub Actions: on push/PR, run the full gate — `ktlintCheck detekt lint testDebugUnitTest assembleDebug` — with UI/Compose tests on an emulator job (QUALITY-BAR §8). Fail on first red gate; cache Gradle to keep it fast.
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-java@v4; with: { distribution: temurin, java-version: '17' }
  - uses: gradle/actions/setup-gradle@v4; with: { cache-read-only: true }
  - run: ./gradlew ktlintCheck detekt lint testDebugUnitTest assembleDebug
```
Add a separate job `instrumented` for `connectedDebugAndroidTest`/`generateBaselineProfile` on an emulator via `reactivecircus/android-emulator-runner`, gating only on the fast job + a smoke UI test to avoid flaky blocking.
