# Quality Bar — the highest rule

> The cited, measurable definition of **"production-grade native Android."** Every agent, skill, and scaffold in CANVAS is measured against this. No option may weaken it.
> Authorities are external and authoritative (Google, OWASP, Kotlin, JetBrains) — never invented. Each § cites its source.

---

## 1. Architecture — strict Clean + Android (Google)
- **Strict Clean Architecture:** `domain` (pure Kotlin, zero Android imports — no `android.*`), `data` (datasources, mappers, repository impls), `presentation/ui` (Compose + ViewModel). Dependency rule: **outer → inner only**; UI/data depend on domain abstractions, never the reverse. [Google App Architecture](https://developer.android.com/topic/architecture) · [Android Developers — layers](https://developer.android.com/topic/architecture#recommended-app-arch).
- **Single source of truth (SSOT)** + **Unidirectional Data Flow (UDF):** state flows one way — UI emits events → ViewModel reduces → StateFlow/`collectAsStateWithLifecycle` renders. No view-model holding UI state, no logic in composables beyond presentation. [UDF](https://developer.android.com/topic/architecture/ui-layer#udf).
- **ViewModels survive config changes**; state hoisted to `StateFlow`; one-shot events via `Channel`/`SharedFlow` sink. [Save UI state](https://developer.android.com/develop/ui/compose/state).
- `minSdk` 34+ (the post-Android-14 API surface, no legacy workarounds — do not ship lower for new apps). Verify current reach against the [distribution dashboard](https://developer.android.com/about/dashboards) before committing a floor; no share figure is asserted here, because it moves, `compileSdk`/`targetSdk` = latest stable (AGP 9 / Compose 1.12+ require `compileSdk 37`); **single-activity** + **Navigation Compose 2.x, type-safe** — `@Serializable` route types with `composable<T>` / `toRoute<T>()`, never string routes or `composable("path/{id}")`. Navigation is state-driven: destinations are a function of UI state, and content composables never navigate directly. [Type-safe navigation](https://developer.android.com/guide/navigation/design/type-safety).
- Mechanical enforcement preferred: **lint rules / detekt** that block domain-layer Android imports (e.g. `forbidden-import` / custom check).

## 2. Data & persistence (Google / SQLite)
- **Room** for structured on-device data: entities ↔ DTOs mapped in `data` (never leak into `domain`), `@Transaction` for multi-row writes, indices + foreign keys where integrity matters. [Room](https://developer.android.com/training/data-storage/room).
- **Forward-only migrations** (`Migration` objects / `AutoMigration`); never destructive without explicit review; schema versioned + exported for testing.
- Network via **Retrofit + OkHttp + kotlinx.serialization**; every DTO validated; `sealed` result types (`Result`/either) across boundaries — no bare exceptions as control flow.
- **Proto DataStore** for preferences; secrets/tokens in **Android Keystore-backed encryption via Google Tink (AEAD/StreamingAEAD)** — `androidx.datastore:datastore-tink` or equivalent (`security-crypto`/`EncryptedSharedPreferences` is **deprecated** — do not introduce it) — never plain `SharedPreferences` for secrets. [DataStore](https://developer.android.com/topic/libraries/architecture/datastore) · [EncryptedSharedPreferences deprecated](https://developer.android.com/jetpack/androidx/releases/security).

## 3. API, contract & concurrency (IETF / Google)
- **REST + OpenAPI 3.1, spec-first**: client **generated** from the contract (`openapi-generator` kotlin/retrofit) — **no hand-written DTOs**.
- Errors as structured problems (RFC 7807/9457 `problem+json`); `Idempotency-Key` on writes; opaque-cursor pagination from day one (AIP-158).
- **Coroutines + Flow everywhere.** Structured concurrency: scoped to `viewModelScope`/`lifecycleScope`; `Dispatchers.Default/IO` boundaries explicit in `data`; no `GlobalScope`. **Never block the main thread.** [Kotlin coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html).

## 4. Security & auth (OWASP / NIST)
- **OWASP ASVS 5.0 Level 2**, zero Top-10:2025 findings.
- **Token handling:** access token in **Keystore-backed secure storage** (Tink/Keystore, not deprecated `EncryptedSharedPreferences`); Bearer interceptor attaches it; **401 → `Authenticator` refresh (rotating)**, single-flight refresh to avoid thundering herd; logout revokes + clears. [Keystore](https://developer.android.com/privacy-and-security/keystore) · [Tink](https://developer.android.com/topic/security/data).
- **Deny-by-default** authorization on every authed destination (nav guard driven by auth state); no secret in `BuildConfig`/VCS — secrets via `local.properties`/env or secure backend.
- **TLS everywhere**; network security config pins/ACL where sockets touch private endpoints; no cleartext traffic (blocked by default on modern Android).

## 5. UI & accessibility (Material / W3C)
- **Jetpack Compose Material 3**: dynamic color + themes (light/dark), `@Composable` theming tokens, no raw pixel magic (use `dp`/`sp` + system density). **Coil 3** for image loading; **Paging 3** for on-device list paging (`collectAsLazyPagingItems`) — opaque-cursor pagination is the *wire/API* concern (AIP-158), this is the UI-layer pagination engine.
- **Accessibility (WCAG 2.2 AA / TalkBack):** every interactive element has a content description / semantics; focus order correct; touch targets ≥ 48dp; `contentDescription` on icons; **60fps** — no jank, no work on main thread, keys on lazy lists (`key=`), stable (`@Immutable`/`@Stable`) models to avoid recomposition storms.
- Compose **performance checklist**: `remember`/`rememberSaveable`, `derivedStateOf`, `LazyColumn` keys, `strongSkipping`/stability, no lambda allocations in hot paths beyond need, `baselineProfile` regenerated per release. [Compose performance](https://developer.android.com/jetpack/compose/performance).

## 6. Testing (Google testing pyramid)
- **Pyramid ~70/20/10**: 70% unit (domain+data with fakes), 20% integration (Room/network), 10% UI (Compose).
- Google **test sizes**; fakes > mocks; **≥75% coverage floor on new code** (JaCoCo).
- **Unit:** JUnit5 + Turbine (Flow) + MockWebServer (Retrofit) + kotlinx-coroutines-test for dispatchers.
- **Integration:** Robolectric for Android-framework-dependent logic; Room in-memory tests.
- **UI:** `androidx.compose.ui.test` — `createComposeRule`/`createAndroidComposeRule`, semantics-based assertions (not `onNodeWithText` hacks); a few full-flow tests.
- **Contract:** Pact / consumer-driven tests against the generated client.

## 7. Tooling, build & release readiness (Gradle / Google)
- **Gradle Kotlin DSL + version catalog** (`libs.versions.toml`) + **convention plugins** (`build-logic`/included build) for multi-module; AGP latest stable; **KSP** for Hilt/Room; Compose BOM (Material3) + **Compose compiler stability config** (`compose-compiler` metrics / `@Immutable`/`@Stable`). [Version catalog](https://developer.android.com/build/migrate-to-catalogs).
- **ktlint + detekt** (blocking); `assembleDebug`, `testDebugUnitTest`, `lint`, `ktlintCheck` all green in CI.
- **16 KB page size** support (AGP 9 / compileSdk 36+ handles it automatically; explicit NDK check only if any native libs).
- **Release:** reproducible/versioned build; **baseline profile** shipped + verified via **Jetpack Macrobenchmark**; **App Bundle (AAB)**; proper **minification (R8)**: crash-free ProGuard/R8 rules verified; **signing** kept out of VCS (keystore from env/CI secrets); version catalog bumps via Dependabot/Renovate; target **Play deadlines** (target API 36 + mandatory developer-identity verification) satisfied before submission.

## 8. Delivery & code quality (Git / Google)
- Trunk-based; **Conventional Commits**; Google code-review standard; short PRs.
- **CI quality gates:** lint → ktlint/detekt → unit tests → build → (separate job) instrumented/Compose UI tests on an emulator.
- ADRs for architecture decisions.

---

> **Scope note (±):** engineering + CI quality gates are *universally enforced*; Play Store submission, live SLOs/monitoring (Crashlytics/Play Vitals) are explicit release-phase items — aspirational until an app reaches real distribution, but the code must be *ready* for them.
