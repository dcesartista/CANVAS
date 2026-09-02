# Android — project scaffold impl (full spec)

> The exhaustive, authoritative spec of the CANVAS **native Android** scaffold — the "bring-up" blueprint. Same `##` Terms as [project-scaffold-theory.md](../../../reference/project-scaffold-theory.md), but expressed in real Kotlin/Compose/Gradle.
> Stack (QUALITY-BAR): Kotlin · Jetpack Compose (Material 3) · Hilt · Coroutines/Flow · Retrofit + kotlinx.serialization · Room · Navigation Compose 2.x (type-safe) · Keystore+Tink token storage · JUnit5/Turbine/MockWebServer. Single-activity, strict Clean.

## Module Layout <!-- 13 -->
Start **single-module** (`:app`), packaged by layer (Google: don't over-modularize a small app); split into `:app`/`:core:domain`/`:core:data` only when builds or layering enforcement warrant it. The layer split keeps `domain` compiling as pure Kotlin (no `kotlin-android`), which enforces QUALITY-BAR §1 at the compiler.
```
app/src/main/java/com/example/canvas/
  domain/        entity · valueobject · domainerror · repository · usecase    (pure Kotlin)
  data/          dto · mapper · datasource(remote/local) · repositoryimpl · network · auth
  ui/            <feature>/ (viewmodel + screens) · navigation · theme · components
  di/            Hilt modules
  App.kt (@HiltAndroidApp) · MainActivity.kt (single-activity) · CanvasTheme
app/src/main/res/     values/ (themes, strings, colors) · xml/ (network_security_config)
```
`domain` has **zero** `android.*` imports (detekt `forbidden-import`, see domain-impl); `data` may import android only for Room/Context-backed stores; `ui` depends on both.

## Package Layout <!-- 9 -->
Feature-first at `ui/<feature>/`: one folder per screen flow, containing its `*ViewModel` and its `*Screen`/`*Content` composables plus the feature-specific `UiState`/`UiEvent`. Shared cross-cutting (navigation, guards) live at `ui/navigation`. The **theme and the component set are NOT vendored per-project** — they come from the swappable `ink-basic` library (see `## Theme & Design Tokens` below).
```
ui/home/       HomeViewModel.kt · HomeScreen.kt · HomeUiState.kt
ui/cart/       CartViewModel.kt · CartScreen.kt
ui/navigation/ AppNavHost.kt · Routes.kt · AuthGuard.kt
```
All classes are `internal` by default within a package unless exported across packages; keep feature packages decoupled from each other (they talk only via domain use cases, not via other features' ViewModels).

## BuildConfig & Secrets <!-- 11 -->
`BuildConfig` carries **non-secret** build metadata (`BACKEND_URL`, `IS_DEBUG`, `APPLICATION_ID`); secrets (API keys, client secrets, keystore passwords) never belong in `BuildConfig`/VCS — they come from env/CI or a secure backend (QUALITY-BAR §4). Values are injected at build time.
```kotlin
defaultConfig {
  buildConfigField("String", "BACKEND_URL",
    "\"${providers.gradleProperty("BACKEND_URL").getOrElse("https://api.example.com")}\"")
  buildConfigField("boolean", "LOGGING", providers.gradleProperty("ENABLE_OKHTTP_LOG").getOrElse("false"))
}
```
`BACKEND_URL` is read from `local.properties`/env so each developer/CI points at its own backend; the field is absent from release where the real endpoint is a secret-provided value.

## Manifest & Security Config <!-- 19 -->
Single `MainActivity` (`android:exported="true"` with the launcher intent); `usesCleartextTraffic` is **blocked by default** (QUALITY-BAR §4) and any local `http://` dev endpoint is scoped to debug via a `network_security_config.xml`, never globally.
```xml
<application android:name=".App" android:networkSecurityConfig="@xml/network_security_config"
  android:theme="@style/Theme.Canvas" android:usesCleartextTraffic="false">
  <activity android:name=".MainActivity" android:exported="true">
    <intent-filter><action android:name="android.intent.action.MAIN"/>
      <category android:name="android.intent.category.LAUNCHER"/></intent-filter>
  </activity>
</application>
```
```xml
<network-security-config>
  <base-config cleartextTrafficPermitted="false"/>
  <domain-config cleartextTrafficPermitted="true"><domain>10.0.2.2</domain></domain-config>
</network-security-config>
```
`10.0.2.2` is the emulator host loopback; real private endpoints add `<trust-anchors>`/pin rules per endpoint instead.

## DI Setup <!-- 13 -->
Root `App.kt` is `@HiltAndroidApp`; Hilt modules in `di/` wire network, db, repository bindings, and the secure token store. Screens get ViewModels via `hiltViewModel()`; repository interfaces bind to impls via `@Binds` (see di-impl).
```kotlin
@Module @InstallIn(SingletonComponent::class)
object NetworkModule {
  @Provides @Singleton fun provideJson(): Json = Json { ignoreUnknownKeys = true }
  @Provides @Singleton fun provideOkHttpClient(interceptor: AuthInterceptor): OkHttpClient =
    OkHttpClient.Builder().addInterceptor(interceptor).build()
  @Provides @Singleton fun provideRetrofit(okHttp: OkHttpClient, json: Json): Retrofit = ...
}
```
Dependencies flow: `ui -> usecases(domain) -> repositories(domain iface) <- data impls <- datasources <- retrofit/room`. No screen constructs its own repo — it is always injected.

## Network Baseline <!-- 18 -->
Retrofit + OkHttp + kotlinx.serialization, base from `BuildConfig.BACKEND_URL`; **Bearer interceptor** attaches the access token, `Authenticator` refreshes on 401 (single-flight), errors map to domain `Result`/`DomainError` (QUALITY-BAR §2, §4). For contract-first projects the Retrofit service is the **generated client**.
```kotlin
interface ProductApi {
  @GET("v1/products") suspend fun list(@Query("cursor") cursor: String?): ProductListDto
}
```
```kotlin
class AuthInterceptor @Inject constructor(private val store: TokenStore) : Interceptor {
  override fun intercept(chain: Interceptor.Chain): Response {
    val r = chain.request().newBuilder()
      .apply { store.accessToken()?.let { header("Authorization", "Bearer $it") } }.build()
    return chain.proceed(r)
  }
}
```
`TokenStore` reads/writes **encrypted storage under the Android Keystore via Tink** (not deprecated `EncryptedSharedPreferences`) — never plain prefs for the access/refresh pair (QUALITY-BAR §4).

## Database Baseline <!-- 13 -->
Room with one `@Database` exposing DAOs; schema exported to `schemas/` for migration tests; forward-only `@Migration`s; `@Transaction` for multi-row writes. Entities/DAOs live in `data`; domain never sees them.
```kotlin
@Database(entities = [ProductEntity::class, CategoryEntity::class], version = 2, exportSchema = true)
abstract class AppDatabase : RoomDatabase() {
  abstract fun productDao(): ProductDao
  abstract fun categoryDao(): CategoryDao
  companion object { fun create(context: Context) = Room.databaseBuilder(
      context, AppDatabase::class.java, "canvas.db").addMigrations(MIGRATION_1_2).build() }
}
```
`exportSchema = true` + `room.schemaLocation` writes versioned JSON committed to VCS; combine with the migration test technique (testing-impl) to guard every schema bump.

## Auth Baseline <!-- 13 -->
Included by default (omit on `no-auth`): Compose login/register screens + ViewModels call the backend's `/v1/auth/*` endpoints via the generated client; tokens stored in `TokenStore`; deny-by-default `AuthGuard` on authed destinations (QUALITY-BAR §4). Logout revokes + clears tokens.
```kotlin
class LoginViewModel @Inject constructor(private val login: Login) : ViewModel() {
  fun submit(email: Email, pw: Secret) = viewModelScope.launch {
    _ui.update { it.copy(loading = true) }
    login(email, pw).onSuccess { user -> _ui.value = LoginUiState(loggedIn = true, user = user) }
      .onFailure { e -> _ui.update { it.copy(loading = false, error = e.message) } }
  }
}
```
The nav guard reads `AuthViewModel.uiState` and routes to `LoginRoute` when unauthenticated; a 401 mid-session triggers the `Authenticator` refresh then redirect to re-login if the refresh fails.

## Contract Setup <!-- 15 -->
Generate the **Kotlin client** (`openapi-generator` kotlin/retrofit) from the backend OpenAPI 3.1 spec into an `api/`/`generated/` package via a `gen:contract` Gradle task (QUALITY-BAR §3). **No hand-written DTOs**; the client is regenerated when the contract changes.
```kotlin
tasks.register<JavaExec>("genContract") {
  setClasspath(configurations["openapi"])
  mainClass.set("org.openapitools.codegen.OpenAPIGenerator")
  args(listOf("generate", "-i", "$rootDir/spec/openapi.yaml", "-g", "kotlin",
    "--library", "retrofit2", "-p", "useCoroutines=true",
    "-o", layout.buildDirectory.dir("generated/openapi").get().asFile.toString()))
}
```
Regeneration is base64-stable/no-op when the contract is unchanged; commit the generated sources so CI doesn't rebuild against a moving spec.

**Self-check the contract seam.** GT-A1 shipped 4 hand-written DTO files and no generator task, against §3's "no hand-written DTOs" — the discipline was dropped without anything noticing. After scaffolding, `grep` for `@Serializable data class .*Dto` outside the generated output directory. Every hit must be either generated, or justified in writing as a payload the contract genuinely does not describe. If the backend publishes no OpenAPI document, say so explicitly and record it as a deviation — do not silently hand-author the client and leave `## Contract Setup` looking satisfied.

## Theme & Design Tokens <!-- 21 -->
Compose UI consumes the **swappable `ink-basic` library** (the Android realization of the agnostic Palette contract) rather than hand-writing a theme. `CanvasTheme` from `com.canvas.ink.basic.palette` provides light/dark/highContrast palettes mapped to an M3 scheme + typography from T3 semantic tokens; components read tokens via `LocalSemanticTokens`. No raw `px`/hex/Dp in components (QUALITY-BAR §5); **no per-project `ui/theme/` color/type files** — the theme IS ink-basic.

**Wiring (required, not optional).** Resolve ink-basic from Maven Central (some apps pre-release may need `mavenLocal()` first — use Central when the version is live):
```kotlin
// app/build.gradle.kts
dependencies {
    implementation("com.cesartista.canvas:ink-basic:0.1.0")
}
```
Do **not** vendored-copy ink-basic into the project, add it as a module, or hand-roll a theme (`ui/theme/Color.kt`/`Type.kt`/`Theme.kt`). If the coordinate cannot be resolved, that is a hard blocker to report — not a license to hand-write Material3 (see `ink-basic/CONSUMING.md` `## Option B` local fallback for the offline `mavenLocal()` path).

**Use `CanvasTheme` at the root** (from `com.canvas.ink.basic.palette`), and `Canvas*` components everywhere; the app must not reference stock M3 widgets (`MaterialTheme`, `Button(`, `Card(`, etc.) anywhere it should use ink-basic:
```kotlin
import com.canvas.ink.basic.palette.CanvasTheme
@Composable fun DefaultTokens() = CanvasTheme { content() }
```
**Self-check the seam:** after scaffolding, `glob`-verify there is **no** hand-written `app/src/main/.../ui/theme/` and `grep` the source for raw M3 leaf components (`Button(`, `OutlinedTextField(`, `Card(`, `TopAppBar(`, `NavigationBar(`, `TabRow(`, `Snackbar(`, `LinearProgressIndicator(`) and bare `MaterialTheme.` — fix any to `Canvas*` + `LocalSemanticTokens` until clean. The build must resolve `com.cesartista.canvas:ink-basic` and compile.

To rebrand, pass a different `Palette` (e.g. `CanvasTheme(palette = myPalette)`); components are not re-themed in place. Type/size/color tokens live in ink-basic's T3 `token/` layer (see `ink-basic/CONSUMING.md`).

## Bring-up <!-- 26 -->
A "running instance" = a **debug APK installed on an emulator/device**, or a green build when no device is available. Concrete steps the worker takes from a clean checkout:
```bash
# 1. Point at a backend (local.properties or env)
echo "BACKEND_URL=http://10.0.2.2:8080" >> local.properties   # emulator -> host loopback
echo "org.gradle.jvmargs=-Xmx4g" >> local.properties
# 2. Full quality gate must pass
./gradlew ktlintCheck detekt lint testDebugUnitTest assembleDebug
# 3. Install + launch on an attached device/emulator
./gradlew :app:installDebug
adb shell am start -n com.example.canvas/.MainActivity
```
If no device is attached, report the successful `assembleDebug` + exact run instructions and note the Android SDK/JDK prerequisites (JDK 17, SDK at `ANDROID_HOME`). Never claim a running app without either an installed launch or a verified green build.

**Render check (required when a device is attached).** A green build proves the app compiles, not that it looks like the palette. GT-A1 shipped stock Material lavender past every textual gate. After launch, capture the screen and sample the page background:
```bash
adb exec-out screencap -p > /tmp/render.png
python3 - <<'EOF'
from PIL import Image                      # pip install pillow, or sample with any tool
im = Image.open("/tmp/render.png").convert("RGB")
w, h = im.size
print("background: #%02X%02X%02X" % im.getpixel((int(w*0.06), h//2)))
EOF
```
**Reject the build** if that pixel is an M3 baseline sentinel — `#FEF7FF` (light) or `#141218` (dark) — instead of the palette's `bgSurface`. A baseline value means the theme is not reaching the widget tree: usually an incomplete T2 bridge, occasionally a missing `CanvasTheme` root. Report the sampled value against the expected one; never report "launched successfully" on the strength of the process being alive.

## Repository Init <!-- 9 -->
A scaffold is not delivered until it is **under version control** (QUALITY-BAR §8). GT-A1 produced a complete app with no `.git`, which makes trunk-based development, Conventional Commits and CI gates unreachable by construction — §8 cannot be scored at all.
```bash
git init -b main
# .gitignore must exclude: build/, .gradle/, local.properties, *.keystore, .idea/, .kotlin/
git add -A && git commit -m "feat(scaffold): initial production-grade Android scaffold"
```
`local.properties` and any keystore are **never** committed (QUALITY-BAR §4); ship `local.properties.example` instead. Write the CI workflow in the same commit so the gate exists from the first push rather than being retrofitted.

## Quality Gates & CI <!-- 26 -->
Same gate for local and CI (QUALITY-BAR §7, §8): `ktlintCheck detekt lint testDebugUnitTest assembleDebug` on push; Compose UI + Robolectric/Room integration tests on a separate instrumented job; all red gates block merge; trunk-based + Conventional Commits.
```bash
./gradlew ktlintCheck detekt lint testDebugUnitTest assembleDebug # the universal gate
```
Release builds additionally run `bundleRelease` and regenerate the baseline profile.

**Coverage must be wired, not asserted.** GT-A1 passed 26/26 unit tests with no coverage tooling at all, so §6's ≥75% floor was unmeasurable — a floor nobody measures is not a floor. JaCoCo is part of the scaffold, and the verification task runs in the same gate:
```kotlin
// app/build.gradle.kts
plugins { jacoco }

tasks.register<JacocoCoverageVerification>("jacocoCoverageVerification") {
    dependsOn("testDebugUnitTest")
    violationRules {
        rule {                                   // QUALITY-BAR §6 — a floor, not a goal
            limit { minimum = "0.75".toBigDecimal() }
        }
    }
}
```
```bash
./gradlew ktlintCheck detekt lint testDebugUnitTest jacocoCoverageVerification assembleDebug
```
A below-floor merge fails loudly rather than shipping silently.

