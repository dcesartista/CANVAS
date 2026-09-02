# Android — infrastructure impl (composition root)

> How the cross-cutting infrastructure Terms ([infrastructure-theory.md](../../../reference/infrastructure-theory.md)) are assembled in native Android, with **Hilt** as the composition root (QUALITY-BAR §1, §3, §4, §7).
> **Rules (QUALITY-BAR §7):** the dependency graph is built in one place (`CanvasApp` + Hilt modules); config is typed and validated at boot; logging/analytics flow through injected abstractions; the network stack is one configured client; the app boots in a fixed, dependency-safe order.

## Composition Root <!-- 14 -->
The **single place where the dependency graph is assembled** (QUALITY-BAR §1, §7). `@HiltAndroidApp` on `CanvasApp` generates the root `SingletonComponent`; Hilt modules bind interfaces to their concrete adapters. Only here does the graph name *both* an interface and its implementation — everything downstream depends on abstractions, and there are no scattered `new` calls or a runtime service-locator.
```kotlin
@HiltAndroidApp
class CanvasApp : Application() {
  @Inject lateinit var bootstrapper: AppBootstrapper
  override fun onCreate() {
    super.onCreate()
    bootstrapper.bootstrap() // graph is alive only after Hilt has composed it
  }
}
```
A graph you cannot trace in one place is a graph you cannot reason about; Hilt keeps that trace in the generated component and module declarations.

## DI Wiring <!-- 21 -->
Dependencies are provided **through the constructor/root, not lookups** (QUALITY-BAR §7): each class declares its needs as `@Inject constructor(...)` params, and Hilt satisfies them from the component. `@Binds` wires an abstraction to its impl; `@Provides` builds framework integrations (Retrofit, OkHttp, Room, `Json`). This *is* the enforcement of the dependency rule — a class that constructs its own repository cannot be unit-tested.
```kotlin
@Module @InstallIn(SingletonComponent::class)
abstract class WiringModule {
  @Binds abstract fun bindProductRepo(i: DefaultProductRepository): ProductRepository
  @Binds abstract fun bindAuthRepo(i: DefaultAuthRepository): AuthRepository
}

@Module @InstallIn(SingletonComponent::class)
object NetworkingModule {
  @Provides @Singleton fun provideJson(): Json =
    Json { ignoreUnknownKeys = true; explicitNulls = false }
  @Provides @Singleton fun provideRetrofit(ok: OkHttpClient, json: Json): Retrofit =
    Retrofit.Builder().baseUrl(BuildConfig.BACKEND_URL)
      .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
      .client(ok).build()
}
```
Interfaces at boundaries, scopes per lifetime, no singletons pretending to be short-lived.

## Configuration <!-- 20 -->
Environment-varying settings are **typed, validated at boot, and injected** (QUALITY-BAR §4). `Config` is loaded once from `BuildConfig` (non-secret) plus `local.properties`/CI for secrets, validated eagerly so the app fails fast at startup instead of crash-mid-session with a null. Dev and prod differ only at this typed seam.
```kotlin
// local.properties (not committed; .example placeholder in repo)
# BACKEND_URL=https://api.canvas.example
// build.gradle.kts — read into BuildConfig for non-secret config
val backendUrl = providers.gradleProperty("BACKEND_URL").orElse("https://api.staging.canvas")
buildConfigField("String", "BACKEND_URL", "\"$backendUrl\"")
```
```kotlin
data class Config(val backendUrl: String, val enableCrashReporting: Boolean) {
  init {
    require(backendUrl.startsWith("https://")) { "insecure URL refused: $backendUrl" }
  }
}
@Provides @Singleton fun provideConfig(): Config =
  Config(BuildConfig.BACKEND_URL, BuildConfig.DEBUG.not())
```
Secrets never come from `BuildConfig`; they are injected from secure sources (env/CI secrets) per security-theory.

## Logging <!-- 19 -->
Structured, leveled logs flow **through one injected indirection**, not scattered `Log.d` calls (QUALITY-BAR §4): Timber wraps `LogcatTree` in debug and a no-op/redacting tree in release, and a `SafeLog` front adds redaction (security-impl Logging Hygiene) so secrets and PII never reach the output. Every tag and operation-name is consistent, making the record filterable.
```kotlin
@Provides @Singleton fun provideLogger(
  @IsDebug isDebug: Boolean,
): Logger {
  if (isDebug) Timber.plant(Timber.DebugTree())
  Timber.plant(SafeLog.Tree())       // release: structured + redacted
  return { tag, message -> Timber.tag(tag).d(message) }
}

class DefaultOrderRepository @Inject constructor(private val log: Logger) {
  suspend fun checkout() {
    log("order.checkout", "started")   // context + operation, no payload
  }
}
```
Logs are the "what did the app actually do" record; an injected `Logger` keeps crash reports and support tickets talking the same language.

## Analytics <!-- 20 -->
**Event telemetry with a maintained taxonomy** (QUALITY-BAR §4): named events and parameters are typed constants reviewed like a schema, not ad-hoc strings typed in fourteen places. Events flow through an injected abstraction so the SDK stays a swappable detail — and the app only reports the parameters it declared, keeping collection aligned with privacy.
```kotlin
sealed interface AnalyticsEvent {
  data class ScreenViewed(val screen: String) : AnalyticsEvent
  data class ProductPurchased(val id: String, val priceCents: Long) : AnalyticsEvent
  data object CheckoutFailed : AnalyticsEvent
}

class Analytics @Inject constructor(private val sdk: AnalyticsSdk) {
  fun log(event: AnalyticsEvent) = when (event) {
    is AnalyticsEvent.ScreenViewed -> sdk.track("screen_viewed", mapOf("screen" to event.screen))
    is AnalyticsEvent.ProductPurchased -> sdk.track(
      "product_purchased", mapOf("product_id" to event.id, "value_cents" to event.priceCents))
    AnalyticsEvent.CheckoutFailed -> sdk.track("checkout_failed", emptyMap())
  }
}
```
Typed events mean no misspelled strings and no drift between code and the analytics schema.

## Crash Reporting <!-- 18 -->
Unhandled failures are **captured, grouped, and surfaced per release** (QUALITY-BAR §7 scope note): the crash SDK (e.g. Crashlytics) is initialized at app scope, taking stack plus context (version, device, session) — never secrets. A `Thread.UncaughtExceptionHandler` seam hoists the raw crash into a logged, reported path so "support says it broke" becomes "release 1.7.2 has a crash cluster in checkout."
```kotlin
object CrashReporter {
  fun setup(context: Context, config: Config) {
    if (!config.enableCrashReporting) return      // not wired in debug/dev
    FirebaseCrashlytics.getInstance().apply {
      setCustomKey("environment", if (config.enableCrashReporting) "prod" else "dev")
      recordException(Throwable("boot"))          // smoke: SDK is talking
    }
    Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
      CrashReporter.log(throwable, thread.name)   // structured, no credentials
    }
  }
}
```
Crash monitoring wired before release-readiness is what tells you whether the release actually held.

## Networking Baseline <!-- 18 -->
The transport stack is **one coherent client assembled at infra** (QUALITY-BAR §3): Retrofit + OkHttp + kotlinx.serialization with timeouts, retries, interceptors, TLS/network-security, and auth attachment all configured in one layer, and every call crosses a sealed-result boundary into the app. Nothing below/around it reaches the network ad hoc.
```kotlin
@Provides @Singleton fun provideOkHttp(
  @AuthOkHttp tokenAuthenticator: Authenticator,
  authInterceptor: AuthInterceptor,
): OkHttpClient =
  OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)
    .readTimeout(30, TimeUnit.SECONDS)
    .retryOnConnectionFailure(true)
    .authenticator(tokenAuthenticator)            // 401 single-flight refresh
    .addInterceptor(authInterceptor)              // Bearer attachment
    .addInterceptor(SafeLog.HttpLogging)          // redacted wire logging
    .build()
```
Scattered ad-hoc HTTP is the anti-layer this single configured client prevents.

## App Bootstrap <!-- 19 -->
The app **boots in a fixed, dependency-safe order** (QUALITY-BAR §1): initialize the graph, validate config, start telemetry/crash, then enter the first screen — with anything slow deferred past first frame (performance-theory Cold Start). Bootstrap is explicit and single-location; no feature initializes itself on import.
```kotlin
class AppBootstrapper @Inject constructor(
  private val config: Config,
  private val crashReporter: CrashReporterController,
  private val analytics: Analytics,
  private val tokenStore: TokenStore,
) {
  fun bootstrap() {
    crashReporter.setup()        // 1. crash first — capture boot failures
    require(config.isValid())    // 2. fail fast on bad config
    analytics.log(ScreenViewed("bootstrap"))
    if (tokenStore.accessToken() != null) analytics.log(ScreenViewed("authed.boot"))
    // 3. heavy init deferred past first frame via WorkManager / lazy singletons
  }
}
```
Stray setup in a random class's `init` is how startup order becomes spaghetti; bootstrap is the one place it is decided.
