# Android — domain impl (pure Kotlin)

> How the shared domain Terms ([domain-theory.md](../../../reference/domain-theory.md)) are written in native Android.
> **Hard rule (QUALITY-BAR §1, §6):** `domain` is **pure Kotlin** — zero `android.*` imports, zero Retrofit/Room/Compose, zero Hilt. The compile-time guard is a detekt/lint `forbidden-import` rule on the `domain` source set (`android.net`, `android.content`, `android.os.*`). Lives in a `:domain` module (or `domain/` package) compiled by plain `kotlin` — never `kotlin-android` — and unit-tested on the JVM.

## Entity <!-- 19 -->
A `data class` holding a value-object identity plus state; behavior is methods that enforce invariants and return copies. Equality by id via the value type; never hold framework types (no `Context`, no `Date` — use `Instant`/`kotlin.time`).
```kotlin
data class Order(
  val id: OrderId,
  val status: OrderStatus,
  val lineItems: List<LineItem>,
  val placedAt: Instant,
) {
  fun markPaid(now: Instant): Order {
    check(status == OrderStatus.PENDING) { "Order $id is not payable" }
    check(now >= placedAt) { "Clock skew: paidAt before placedAt" }
    return copy(status = OrderStatus.PAID)
  }
  val total: Money get() = lineItems.fold(Money.ZERO, Money::plus)
}
```
Entities are `@Immutable`-eligible data classes: all `val`, no `var`, no mutable collections; use `List`, never `MutableList`. Status is an `enum class` (`OrderStatus { PENDING, PAID, SHIPPED }`) — only valid states exist, so the guard in `markPaid` is the single transition point.

## Value Object <!-- 17 -->
A `@JvmInline value class` (or, for multi-field values, a plain `data class`) whose companion factory enforces the invariant and throws a `DomainError`. Never let an invalid value through the constructor — make it `private` so the type is *unrepresentable* in an invalid state (fail-fast by construction, not by convention).
```kotlin
@JvmInline
value class Email private constructor(val value: String) {
  companion object {
    private val RE = Regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    fun of(raw: String): Email {
      val v = raw.trim().lowercase()
      if (!RE.matches(v)) throw InvalidEmail(raw)
      return Email(v)
    }
  }
}
```
`Money` is the canonical multi-field VO: `data class Money(val minorUnits: Long, val currency: Currency)` with `Money.ZERO`, `plus`, and `of(minorUnits, currency)` that rejects negative amounts; display formatting (locale, symbols) is presentation-only, never in the VO.

## Domain Error <!-- 13 -->
A `sealed class` extending `Exception` with a stable, wire-stable `code` string and structured fields. No HTTP status codes and no Android `IOException` cross the boundary — the data layer maps transport failures *into* these before the domain (or UI) sees them.
```kotlin
sealed class DomainError(open val code: String, message: String) : Exception(message) {
  class ProductNotFound(id: String) : DomainError("PRODUCT_NOT_FOUND", "no product $id")
  class OrderNotPayable(id: OrderId) : DomainError("ORDER_NOT_PAYABLE", "order $id")
  class Network(cause: Throwable) : DomainError("NETWORK", cause.message.orEmpty())
  class SessionExpired : DomainError("SESSION_EXPIRED", "credentials are no longer valid")
  class Unknown(cause: Throwable) : DomainError("UNKNOWN", cause.message.orEmpty())
}
```
`code` doubles as a stable idempotency/analytics key and a fallback for the UI to show a localized message without mapping exceptions in the presentation layer.

## Model <!-- 3 -->
Pure Kotlin composite aggregates or shaped read "projections" that span entities; still immutable and dependency-light. Use when a feature needs `ProductWithStock` rather than mutating a core entity — note this Term overlaps `Use Case`/`Entity`; prefer it only for true aggregates or projections.

## Repository Interface <!-- 12 -->
An `interface` expressed **only in domain types**: `suspend` for one-shot ops, `Flow` for observation (live SSOT streams). Never leak DTOs, Room rows, or impl-specific `Page` classes here; option/result types live in domain too.
```kotlin
interface ProductRepository {
  fun observe(id: ProductId): Flow<Product?>
  fun observePage(cursor: String? = null): Flow<Page<Product>>
  suspend fun refresh(id: ProductId): Result<Product>
  suspend fun search(query: String): Result<List<Product>>
}
```
Errors surface as the sealed `Result`/either pattern (QUALITY-BAR §2) or as the thrown `DomainError` the caller consumes — never bare platform exceptions leaking through the interface.

## Use Case <!-- 16 -->
A `class` with constructor-injected ports only — no global/ServiceLocator — exposing `suspend operator fun invoke(...)`. One user-facing intent per class (`ListProducts`, `AddToCart`). ViewModels call `invoke` inside `viewModelScope`; a use case **never owns a scope** and is therefore trivially testable with fakes.
```kotlin
class AddToCart(
  private val cart: CartRepository,
  private val catalog: ProductRepository,
) {
  suspend operator fun invoke(product: ProductId, qty: Int): Result<Cart> {
    if (qty <= 0) return Result.failure(DomainError.Unknown(IllegalArgumentException("qty")))
    val existing = cart.observe().first()
    return cart.setLine(existing.upsert(product, qty))
  }
}
```
Prefer `Result` for expected failures and `runCatching` at the boundary; keep the use case re-entrant and side-effect-free outside its ports.

## Domain Service <!-- 13 -->
Stateless domain logic spanning multiple entities/VOs that doesn't fit a single use case; pure Kotlin, constructor-injected ports, no Android. Used for cross-cutting business rules (tax computation, discount stacking) shared by several use cases.
```kotlin
class PriceBreaker {
  fun discounted(base: Money, coupon: Coupon?, qty: Int): Money {
    if (coupon == null) return base
    val floor = Money.of((qty.toLong() * base.minorUnits) * 90 / 100, base.currency)
    return if (coupon.percent > 0) base.minusPercent(coupon.percent, floor) else base
  }
}
```
Keep it **stateless**; any configuration is injected as a port or passed as a parameter — never read from `BuildConfig` or a global inside `domain`, which would break the pure-Kotlin JVM test story.

## Page <!-- 9 -->
The pagination cursor type used by repository interfaces, defined in domain. Uses an opaque `String?` cursor (AIP-158 style), not numeric page offsets, and never the raw network page/DTO.
```kotlin
data class Page<T>(val items: List<T>, val nextCursor: String?)
fun <T, R> Page<T>.map(f: (T) -> R) = Page(items.map(f), nextCursor)
val <T> Page<T>.hasMore get() = nextCursor != null
```
`Page` shapes collections at the data boundary; `Result` carries outcomes. Keep both in domain so use cases and ViewModels depend only on stable, tested types.

## Compatibility <!-- 8 -->
`minSdk 34+` (QUALITY-BAR §1) lets `domain` use `java.time.*`/`kotlin.time` and standard-library features without desugaring surprises; keep the module compiled with `jvmTarget 17` to match the app. Avoid `androidx.annotation.*` in favor of Kotlin-stdlib constraints so the layer stays framework-clean and runs on a plain JVM in `testDebugUnitTest`.
```kotlin
// :domain/build.gradle.kts — no android plugin, pure kotlin
plugins { kotlin("jvm") }
kotlin { jvmToolchain(17) }
```
The detekt `forbidden-import` rule (`android.*`) runs on this module's `main` source set so the purity invariant is mechanically enforced, per QUALITY-BAR §1.
