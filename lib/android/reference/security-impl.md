# Android — security impl (OWASP ASVS L2)

> How the security Terms ([security-theory.md](../../../reference/security-theory.md)) are implemented in native Android against **OWASP ASVS 5.0 Level 2** (QUALITY-BAR §4, §7).
> **Rules (QUALITY-BAR §4):** tokens in Keystore-backed secure storage; short-lived rotating tokens; Bearer attached once via interceptor; 401 → single-flight refresh with `Mutex`; deny-by-default navigation; TLS everywhere with cleartext blocked; typed layer validation; secrets never in `BuildConfig`/VCS; logging redacts credentials.

## Secure Token Storage <!-- 15 -->
Tokens live in **Keystore-backed encrypted storage**, never plain `SharedPreferences`, never an unencrypted file, never readable by another app (QUALITY-BAR §4). The deprecated `security-crypto`/`EncryptedSharedPreferences` path is **not used**; the modern control is a **Google Tink AEAD** encryption scheme whose key stays inside the Android **Keystore** scoped to this app, so a device with physical access cannot read the token from storage. Access via a typed `TokenStore` so the rest of the app never touches ciphertext directly.
```kotlin
@Provides @Singleton fun provideTokenStore(context: Context): TokenStore {
  // key lives in the Android Keystore, never extractable by other apps
  val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
  // Tink AEAD encrypts from the Keystore-backed key; byte[] is the ciphertext
  val aead = AeadFactory.getPrimitive(masterKey)
  return TinkEncryptedTokenStore(aead)        // get/set access + refresh, never plain
}
// with a Proto DataStore: datastore <-> Tink AEAD gives typed at-rest encryption
```
Storage is assumed readable by an attacker with the device in hand; Keystore-backed Tink encryption at rest is the control.

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

## Bearer Interceptor <!-- 20 -->
Authenticated requests attach the token **mechanically through one OkHttp interceptor** at the transport edge (QUALITY-BAR §4), so no caller can forget or hand-roll auth and no token is copied around the app. It reads the current token from the `TokenStore` in a single place and is also the single point that turns a 401 into a refresh round-trip.
```kotlin
class AuthInterceptor @Inject constructor(
  private val tokens: TokenStore,
) : Interceptor {
  override fun intercept(chain: Interceptor.Chain): Response {
    val req = chain.request().newBuilder()
    tokens.accessToken()?.let { req.addHeader("Authorization", "Bearer $it") }
    val resp = chain.proceed(req.build())
    if (resp.code == 401 && !"retry".equals(req.retryTag, true)) {
      // let the Authenticator coordinate refresh; failed auth never hides here
      return chain.proceed(req.header("Authorization")?.let { req } ?: req)
    }
    return resp
  }
}
```
One attachment point = one thing to audit; token presence is the interceptor's job, never the caller's.

## Single-Flight Refresh <!-- 20 -->
The **thundering-herd control** (QUALITY-BAR §4): when several in-flight requests hit 401 at once, exactly **one** refresh starts and the rest await its result. An OkHttp `Authenticator` fronts this with a `Mutex` so concurrent renewals serialize into a single call; refresh failure revokes the session and never spins in a retry loop that rate-limits the app into lockout.
```kotlin
class TokenAuthenticator @Inject constructor(
  private val auth: AuthRepository,
) : Authenticator {
  private val mutex = Mutex()                       // single-flight guard

  override suspend fun authenticate(route: Route?, response: Response): Request? {
    val token = mutex.withLock {
      // only the first caller refreshes; the rest re-read the now-valid token
      try { auth.refresh() } catch (e: Exception) { return null } // fail => trigger logout
    }
    return response.request.newBuilder()
      .addHeader("Authorization", "Bearer $token").build()
  }
}
```
`Mutex` guarantees one refresh; a failed refresh returns `null` (signal to log out), never a loop of retries.

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
