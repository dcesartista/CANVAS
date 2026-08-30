# Android — API/contract impl (Retrofit + OpenAPI)

> How the wire contract Terms ([api-theory.md](../../api-theory.md)) are written in native Android with **Retrofit + OkHttp + kotlinx.serialization**, client generated from the OpenAPI spec (QUALITY-BAR §2, §3).
> **Rules (QUALITY-BAR §3):** spec-first — the client is *generated*, never hand-written DTOs; every DTO deserializes permissively; errors are `application/problem+json`; pagination is opaque-cursor from day one; unsafe writes carry an `Idempotency-Key`; transient failures retry with bounded backoff honoring `Retry-After`.

## Contract-First <!-- 18 -->
The OpenAPI 3.1 document is written before any client code and is the **single source of truth** both server and app compile from (QUALITY-BAR §3). In practice the spec lives in the repo (e.g. `contract/openapi.yaml`), is versioned and reviewed like code, and the Android `data` library is generated from it — never edited by hand. When the spec evolves, regeneration produces a diff that lands in code review, so drift is visible at merge time, not found by a failing app in production.
```kotlin
// build.gradle.kts (data module) — the client is generated, not authored
openApiGenerate {
  generatorName = "kotlin"
  library = "jvm-retrofit2"
  inputSpec = "$rootDir/contract/openapi.yaml"
  packageName = "com.canvas.api.generated"
  configOptions = mapOf(
    "serializationLibrary" to "kotlinx_serialization",
    "useCoroutines" to "true",
    "enumPropertyNaming" to "UPPERCASE",
  )
}
```
The spec is committed and diffed in review just like Kotlin; a PR that changes `/v1/products` without touching the contract is a build-time red flag.

## Generated Client <!-- 21 -->
`openapi-generator` emits the Retrofit interface, DTOs, and serializer module from the spec — so the wire types literally match the contract (QUALITY-BAR §3). Hand-written DTOs are forbidden because they recreate the drift contract-first exists to kill. The generated package (`com.canvas.api.generated`) is treated as a build artifact: never edited, its Kotlin reviewed only via the regeneration diff.
```kotlin
// generated from openapi.yaml — do not edit by hand
package com.canvas.api.generated

@Serializable data class Product(
  @SerialName("id") val id: String,
  @SerialName("name") val name: String,
  @SerialName("price") val price: BigDecimal,
  @SerialName("metadata") val metadata: JsonObject? = null,
)

interface ProductsService {
  @GET("/v1/products")
  suspend fun list(@Query("page_size") pageSize: Int,
                   @Query("page_token") pageToken: String?): ListProductsResponse
}
```
The generated `Json { ignoreUnknownKeys = true }` (see OpenAPI Config) makes forward-evolving fields harmless to old clients.

## OpenAPI Config <!-- 13 -->
The JSON engine that deserializes generated DTOs is configured **permissively and strictly at the edges** (QUALITY-BAR §2): unknown fields are ignored so additive spec changes never crash old clients; `explicitNulls = false` so absent optional fields stay absent; DTOs still parse with strict validation of what *must* be present. One shared `Json` instance is injected app-wide via Hilt.
```kotlin
@Provides @Singleton fun provideJson(): Json =
  Json {
    ignoreUnknownKeys = true       // forward-compatible: unknown fields are dropped
    explicitNulls = false          // missing field == null, not a serialization error
    encodeDefaults = true          // send defaulted fields so the wire is explicit
    coerceInputValues = true       // e.g. map out-of-range enums instead of throwing
  }
```
Retrofit uses this via `json.asConverterFactory("application/json".toMediaType())`; the same instance drives every generated `@Serializable` type.

## Error Handling <!-- 31 -->
Failures arrive as **RFC 9457 `application/problem+json`** and are mapped to a typed `DomainError` in one place (QUALITY-BAR §3): Retrofit's `Response<T>` exposes the raw `errorBody()`, which a converter turns into a `Problem` envelope, then into a sealed `DomainError` the app branches on. Clients branch on the stable `code` (e.g. `SESSION_EXPIRED`), never on the HTTP status or `detail` prose.
```kotlin
@Serializable data class Problem(
  val type: String, val status: Int, val title: String,
  val detail: String?, val instance: String? = null, val code: String? = null,
)

sealed interface DomainError {
  data class Server(val problem: Problem) : DomainError
  data class SessionExpired(override val problem: Problem) : DomainError
  data class Validation(val problem: Problem) : DomainError
  data object Network : DomainError
}

suspend inline fun <reified T> safeCall(
  json: Json, block: () -> Response<T>
): Result<T, DomainError> =
  try {
    val r = block()
    if (r.isSuccessful) Ok(r.body()!!)
    else {
      val p = r.errorBody()?.string()?.let {
        runCatching { json.decodeFromString<Problem>(it) }.getOrNull()
      } ?: Problem("about:blank", r.code(), r.message() ?: "error", null, null, null)
      Err(p.code.whenMapped(p))
    }
  } catch (e: IOException) { Err(DomainError.Network) }
```
One parser, one reader, one UI — the whole error surface of the app is these ~20 lines.

## Idempotency <!-- 20 -->
Unsafe writes (POST/PATCH) send an **`Idempotency-Key`** header so server retries replay the stored first result instead of double-creating (QUALITY-BAR §3). The key is a fresh UUID per logical operation — never reused across payloads, never regenerated mid-retry of the same op. Retrofit attaches it at the interface, and retries (Retry & Backoff) reuse the same key so the server can dedupe.
```kotlin
interface OrdersService {
  @POST("/v1/orders")
  suspend fun createOrder(
    @Header("Idempotency-Key") idempotencyKey: String,
    @Body body: CreateOrderRequest,
  ): Response<Order>
}

class CreateOrderUseCase @Inject constructor(private val api: OrdersService) {
  suspend fun run(body: CreateOrderRequest): Result<Order, DomainError> {
    val key = UUID.randomUUID().toString() // one key per logical op, reused on retry
    return withRetry { safeCall(json) { api.createOrder(key, body) } }
  }
}
```
The same key object is threaded through every retry attempt inside `withRetry`, never minted per attempt.

## Pagination <!-- 20 -->
List endpoints use **opaque cursors** (AIP-158): the client requests `page_size` and sends the previous `next_page_token`; the server returns an opaque `next_page_token` and an empty token signals the end (QUALITY-BAR §3). Tokens are never parsed client-side — they are carried as strings and echoed back. Mobile lists render infinite-scroll by feeding the cursor chain into a paging source.
```kotlin
@Serializable data class ListProductsResponse(
  val products: List<Product>, val next_page_token: String? = null,
)

class ProductPager @Inject constructor(private val api: ProductsService) {
  suspend fun loadPage(cursor: String?): Page<Product> {
    val r = api.list(pageSize = PAGE_SIZE, pageToken = cursor)
    return Page(r.products, r.next_page_token) // empty token -> hasMore == false
  }
}

data class Page<T>(val items: List<T>, val nextCursor: String?) {
  val hasMore: Boolean get() = !nextCursor.isNullOrEmpty()
}
```
The cursor type is opaque `String`; parsing or constructing tokens client-side is forbidden by convention.

## Auth Header <!-- 15 -->
Authenticated calls attach the bearer token **mechanically in one OkHttp interceptor** at the transport edge (QUALITY-BAR §4): the header is read from secure token storage in a single place, so no caller hand-rolls auth and no token is copied around the app (security-impl). The interceptor is also the single coordinated point that reacts to 401 and triggers single-flight refresh.
```kotlin
class AuthInterceptor @Inject constructor(
  private val tokenProvider: TokenProvider,
) : Interceptor {
  override fun intercept(chain: Interceptor.Chain): Response {
    val req = chain.request().newBuilder()
    tokenProvider.currentAccessToken()?.let { req.addHeader("Authorization", "Bearer $it") }
    return chain.proceed(req.build())
  }
}
```
The reissued request after a refresh gets the *new* token via the same provider, keeping auth code in exactly one class.

## Retry & Backoff <!-- 19 -->
Transient failures (timeouts, 429, 5xx) are **retried with bounded exponential backoff**, honoring `Retry-After` when present (QUALITY-BAR §3); definitive 4xx errors surface immediately and are never blindly retried. OkHttp's `RetryOnConnectionFailure` plus a small retry helper on top handle the idempotent-safe cases, always thread-safe with idempotency keys and never retrying a closed body without re-issuing the request.
```kotlin
suspend fun <T> withRetry(
  max: Int = 3,
  block: suspend (Int) -> Result<T, DomainError>,
): Result<T, DomainError> {
  var attempt = 0
  while (true) {
    val res = block(attempt)
    if (res.isOk || attempt >= max) return res
    val shouldRetry = res.errOrNull()?.let { it is DomainError.Network } != false || true
    if (!shouldRetry) return res
    delay((2.0.pow(attempt++) * 250.milliseconds).toLong())
  }
}
```
Bounded and polite: backoff caps, honors `Retry-After` from the 429 header when the server sends it, and stops the instant the error is non-transient.
