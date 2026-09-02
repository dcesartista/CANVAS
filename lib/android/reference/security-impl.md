# Android — security impl (OWASP ASVS L2)

> How the security Terms ([security-theory.md](../../../reference/security-theory.md)) are implemented in native Android against **OWASP ASVS 5.0 Level 2** (QUALITY-BAR §4, §7).
> **Provenance:** the `Secure Token Storage`, `Bearer Interceptor` and `Single-Flight Refresh` samples are **extracted from a build that compiles and runs**, not composed here. Their predecessors were written ahead of use and did not compile: `MasterKey` came from the deprecated `androidx.security.crypto`, `Request.Builder` has no `retryTag`, and `authenticate` was declared `suspend` when OkHttp's `Authenticator` is a blocking interface. Verified 2026-09-02 against `canvas-commerce` (`docs/evaluation/GT-A1-2026-09-02.md`).
> **Rules (QUALITY-BAR §4):** tokens in Keystore-backed secure storage; short-lived rotating tokens; Bearer attached once via interceptor; 401 → single-flight refresh with `Mutex`; deny-by-default navigation; TLS everywhere with cleartext blocked; typed layer validation; secrets never in `BuildConfig`/VCS; logging redacts credentials.

## Secure Token Storage <!-- 39 -->
Tokens live in **Keystore-backed encrypted storage**, never plain `SharedPreferences`, never an unencrypted file, never readable by another app (QUALITY-BAR §4). The deprecated `security-crypto`/`EncryptedSharedPreferences` path is **not used**; the modern control is a **Google Tink AEAD** encryption scheme whose key stays inside the Android **Keystore** scoped to this app, so a device with physical access cannot read the token from storage. Access via a typed `TokenStore` so the rest of the app never touches ciphertext directly.
`MasterKey` belongs to the deprecated `androidx.security.crypto` library — do **not** reach for it here. Tink's own `AndroidKeysetManager` owns the keyset and names the Keystore key by URI:
```kotlin
class TinkTokenStore(context: Context) : TokenStore {
  private val appContext = context.applicationContext
  private val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

  private val aead: Aead by lazy {                 // keyset is Keystore-wrapped
    AndroidKeysetManager.Builder()
      .withSharedPref(appContext, PREFS, KEYSET_NAME)
      .withMasterKeyUri("android-keystore://canvas_master_key")
      .withKeyTemplate(AeadKeyTemplates.AES256_GCM)
      .build()
      .keysetHandle
      .getPrimitive(Aead::class.java)
  }

  override fun accessToken(): String? = read(KEY_ACCESS)

  override fun saveTokens(accessToken: String, refreshToken: String?) = prefs.edit {
    putString(KEY_ACCESS, encrypt(accessToken))     // only ciphertext is persisted
    putString(KEY_REFRESH, refreshToken?.let(::encrypt))
  }

  override fun clear() = prefs.edit { clear() }

  private fun encrypt(plain: String): String =
    Base64.encodeToString(aead.encrypt(plain.toByteArray(UTF_8), null), Base64.NO_WRAP)

  private fun decrypt(cipher: String): String? = runCatching {
    String(aead.decrypt(Base64.decode(cipher, Base64.NO_WRAP), null), UTF_8)
  }.getOrNull()                                    // corrupt/rotated key => null, never a crash

  private companion object { init { AeadConfig.register() } }  // once per process
}
```
`SharedPreferences` is acceptable *here* only because it stores ciphertext; the plaintext never leaves this class. Decryption returns `null` rather than throwing, so a rotated or corrupt keyset logs the user out instead of crashing the app. Storage is assumed readable by an attacker with the device in hand; Keystore-backed Tink encryption at rest is the control.

## Token Lifecycle <!-- 20 -->
Tokens are **short-lived and rotating** (QUALITY-BAR §4, NIST): the access token lives minutes, the refresh token persists and rotates on every use. A stolen access token is a minutes-long window, and a rotating refresh token invalidates its predecessor, making a stolen one a one-time asset. Logout **revokes server-side and clears all stored credentials** — local deletion alone leaves a ghost account.
```kotlin
class DefaultAuthRepository @Inject constructor(
  private val tokens: TokenStore,
  private val api: AuthService,
) : AuthRepository {
  override suspend fun refresh(): String {
    val new = api.refresh(tokens.refreshToken())
    tokens.save(new.access, new.refresh)   // refresh rotates; old one is dead
    return new.access
  }
  override suspend fun logout() {
    runCatching { api.revoke(tokens.refreshToken()) } // revoke server-side
    tokens.clear()                                    // then clear local
  }
}
```
`clear()` on every logout is an explicit security action, not an afterthought.

## Bearer Interceptor <!-- 16 -->
Authenticated requests attach the token **mechanically through one OkHttp interceptor** at the transport edge (QUALITY-BAR §4), so no caller can forget or hand-roll auth and no token is copied around the app. The interceptor **only attaches** — it never inspects the response code. 401 handling belongs to the `Authenticator` (next Term), which OkHttp invokes for exactly that purpose; splitting the concern across both is how retry loops get built by accident.
```kotlin
class AuthInterceptor(private val tokenStore: TokenStore) : Interceptor {
  override fun intercept(chain: Interceptor.Chain): Response {
    val request = chain.request()
    val token = tokenStore.accessToken()
    val authenticated =
      if (token.isNullOrBlank()) request
      else request.newBuilder().header("Authorization", "Bearer $token").build()
    return chain.proceed(authenticated)
  }
}
```
Use `header(...)`, not `addHeader(...)` — the former replaces, the latter appends a second `Authorization` header on a retried request. One attachment point = one thing to audit; token presence is the interceptor's job, never the caller's.

## Single-Flight Refresh <!-- 30 -->
The **thundering-herd control** (QUALITY-BAR §4): when several in-flight requests hit 401 at once, exactly **one** refresh starts and the rest await its result. An OkHttp `Authenticator` fronts this with a `Mutex` so concurrent renewals serialize into a single call; refresh failure revokes the session and never spins in a retry loop that rate-limits the app into lockout.
OkHttp's `Authenticator` is a **blocking Java interface** — `authenticate` cannot be `suspend`, so a coroutine `Mutex` has to be entered through `runBlocking`. The critical section is tiny (one refresh call), which is what makes that acceptable here:
```kotlin
class TokenAuthenticator(
  private val tokenStore: TokenStore,
  private val auth: AuthRepository,
) : Authenticator {
  private val mutex = Mutex()                       // single-flight guard

  override fun authenticate(route: Route?, response: Response): Request? =
    runBlocking {                                   // NOT suspend: OkHttp calls this blocking
      mutex.withLock {
        // Already sent with a token and still 401 => the session is beyond repair.
        if (response.request.header("Authorization") != null) {
          tokenStore.clear()
          return@withLock null                      // null => OkHttp stops retrying
        }
        val token = runCatching { auth.refresh() }.getOrNull()
          ?: run { tokenStore.clear(); return@withLock null }
        response.request.newBuilder()
          .header("Authorization", "Bearer $token").build()
      }
    }
}
```
Two things make this terminate. The `Authorization`-already-present check means a request is retried **at most once** — without it, a persistently invalid token loops until the server rate-limits the app into lockout. And a failed refresh clears the session and returns `null` rather than retrying. `Mutex` guarantees one refresh; the rest await it and re-read the now-valid token.

> **When the contract has no refresh endpoint** (many public APIs), keep the same shape: a 401 clears the session and returns `null`, the nav guard sees unauthenticated state and routes to login. Do not silently swallow the 401.

## Deny-By-Default <!-- 31 -->
**Start closed, open narrowly** (QUALITY-BAR §4): nothing is reachable, exported, or authorized unless an explicit gate lets it be. Every protected destination sits behind a navigation guard driven by **auth state**, not "known to be behind a logged-in screen." Components default to `android:exported=false`, files are private, and shared data is explicit — a default-open surface is a finding.
```kotlin
@Serializable data object LoginRoute
@Serializable data object HomeRoute
@Serializable data object AccountRoute
@Serializable data object AuthedGraph

@Composable fun AppNav(authState: StateFlow<AuthState>) {
  val state by authState.collectAsStateWithLifecycle()
  // The guard is the START DESTINATION, not a post-composition effect: an
  // unauthenticated session can never compose a protected screen, not even once.
  NavHost(
    navController,
    startDestination = if (state.isAuthenticated) AuthedGraph else LoginRoute,
  ) {
    composable<LoginRoute> { LoginScreen() }
    navigation<AuthedGraph>(startDestination = HomeRoute) {   // deny-by-default group
      composable<HomeRoute> { HomeScreen() }
      composable<AccountRoute> { AccountScreen() }
    }
  }
  LaunchedEffect(state.isAuthenticated) {        // react to sign-out mid-session
    if (!state.isAuthenticated) {
      navController.navigate(LoginRoute) { popUpTo(0) { inclusive = true } }
    }
  }
}
```
Authorized destinations live in a guarded group reached only when auth state already permits it. Deciding in `startDestination` rather than a `LaunchedEffect` after the `NavHost` is the difference between a screen that is unreachable and one that renders for a frame before redirecting — the latter has already leaked.

## Network Security <!-- 24 -->
**Transport is TLS everywhere and cleartext is blocked** (QUALITY-BAR §4): the default network-security config forbids cleartext, so an `http://` URL in production is an immediate failure. Private endpoints additionally pin or restrict trust via the network-security config. Certificates are validated by default (hostname + chain); debug-only endpoints are strictly separated from production.
```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
  <base-config cleartextTrafficPermitted="false">
    <trust-anchors>
      <certificates src="system"/>
    </trust-anchors>
  </base-config>
  <domain-config cleartextTrafficPermitted="false">
    <domain includeSubdomains="true">api.canvas.example</domain>
    <pin-set expiration="2027-01-01">
      <pin digest="SHA-256">BASE64_SPKI_PIN</pin>
    </pin-set>
  </domain-config>
</network-security-config>
```
```xml
<!-- AndroidManifest.xml -->
<application android:networkSecurityConfig="@xml/network_security_config" ... />
```
Cleartext is blocked app-wide by default; pins are added only for private endpoints the app fully controls.

## Input Validation <!-- 13 -->
Every external input is **validated before use at the type system** (QUALITY-BAR §4): typed contract-layer DTOs deserialize once, then domain value objects enforce edge rules — parameterized queries, escaped dynamic content, bounded ranges. Never interpolate untrusted strings into SQL, URLs, or markup; validation happens at the boundary so downstream use cases assume well-formed input.
```kotlin
@Serializable data class CreateOrderDto(val qty: Int, val note: String?) {
  init {
    require(qty in 1..999) { "qty out of range" }
    require(note.isNullOrBlank() || note.length <= 500) { "note too long" }
  }
}
// domain never trusts the wire; it trusts this validated boundary type
```
Validation in the type is fail-fast at the edge — the injection family is closed by construction, not by code review.

## Logging Hygiene <!-- 16 -->
**Secrets and personal data never reach logs** (QUALITY-BAR §4, ASVS): no tokens, passwords, or PII in crash reports, logcat, or analytics. Sensitive events (auth success/failure, refresh, logout) are logged *without credentials*; structured redaction is applied at the single logging indirection so a stray `Log.d("token", ...)` cannot leak.
```kotlin
object SafeLog {
  fun d(tag: String, message: String) = Log.d(tag, redact(message))

  private val SENSITIVE = listOf(
    Regex("(?i)Bearer\\s+[A-Za-z0-9._~+/-]+=*"),   // access token
    Regex("\"password\"\\s*:\\s*\"[^\"]+\""),       // credential field
    Regex("\\b[\\p{L}\\d._%+-]+@[\\p{L}\\d.-]+\\b"), // email/PII
  )
  private fun redact(text: String): String =
    SENSITIVE.fold(text) { acc, r -> r.replace(acc, "<redacted>") }
}
```
Every `log` call in the app routes through `SafeLog`; an accidental credential in a hot path becomes a redacted placeholder, not an account-takeover ticket.
