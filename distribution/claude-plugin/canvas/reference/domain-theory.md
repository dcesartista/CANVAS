# Domain — theory

> What the domain layer IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/domain-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §1.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

The domain is the **pure inner core** of strict Clean (QUALITY-BAR §1): nothing but business meaning — entities, value objects, repository interfaces, use cases — in **pure Kotlin**, with zero `android.*` imports and zero framework types. Everything outward depends on it; it depends on nothing. This is exactly the split [Google App Architecture](https://developer.android.com/topic/architecture) recommends, so the app's meaning can be reasoned about — and tested — without a device.

## Pure Kotlin Core <!-- 3 -->
The charge: every file here imports nothing from `android.*`, Compose, Retrofit, Room, Hilt, or any platform SDK. Coroutines are allowed (Kotlin, not Android); platform types (`String!`) are resolved or forbidden. If an import can't be purged, the concept it serves belongs outward — and the compiler (detekt forbidden-import) enforces this mechanically, per QUALITY-BAR §1.

## Dependency Rule <!-- 3 -->
Dependencies point **inward only**: UI/data layers depend on domain abstractions, never the reverse (QUALITY-BAR §1). The domain never knows who implements its ports. This single direction is what keeps the core stable when UI or storage technology churns; [Google App Architecture](https://developer.android.com/topic/architecture#recommended-app-arch) defines its layers by exactly this arrow.

## Entity <!-- 3 -->
A business object with a **distinct identity** that persists through time and change (an `Order`, a `Profile`). Equality is identity, not attributes. An entity **owns its invariants** — it exposes behavior that keeps it valid rather than raw mutation — and carries no persistence or framework concern. It is the most stable, most-tested object in the system.

## Identity <!-- 3 -->
**Why an object is "the same"** across updates — a stable ID (UUID/surrogate) distinct from mutable attributes. Entities keep identity constant while properties change; two instances with the same identity are the same thing. Identity is a domain decision, not a database one — don't let a Room `@PrimaryKey` or a server row ID dictate it.

## Value Object <!-- 3 -->
An **immutable** object defined wholly by its attributes, with **no identity** (`Money`, `EmailAddress`, `AppointmentTime`). Equality is by value; it **validates on construction** so illegal states are unrepresentable. Prefer value objects over primitives — pushing correctness into types eliminates a whole bug class (a [Kotlin idiom](https://kotlinlang.org/docs/idioms.html)).

## Aggregate <!-- 3 -->
A **cluster of domain objects** treated as one unit for change (an `Order` plus its `LineItem`s), exposed through one aggregate root that enforces cross-object invariants. The aggregate is the unit of persistence and consistency, so it also bounds transaction scope on the way out — over-broad aggregates are a top cause of data contention ([DDD reference](https://martinfowler.com/bliki/DDD_Aggregate.html)).

## Domain Error <!-- 3 -->
A **typed, named failure** for a violated invariant or precondition (`InsufficientStock`, `SessionExpired`) — never a bare `Exception`, never exceptions as control flow. It carries a **stable machine code** callers branch on and **knows nothing of HTTP**; translation into RFC 9457 `problem+json` is a data-layer adapter concern (QUALITY-BAR §3).

## Repository Interface <!-- 3 -->
A **port the domain owns**: it declares how aggregates are retrieved and persisted in domain terms only — no rows, no DTOs, no cache flags. The data layer *implements* it (dependency inversion). Define one even for a single source: it is the seam that makes the core testable with a fake and the storage swappable ([data layer](https://developer.android.com/topic/architecture/data-layer)).

## Use Case <!-- 3 -->
**One application operation = one user intent** (`PlaceOrder`, `ListInvoices`): it coordinates entities, value objects, and repository ports to fulfil that intent. Input and output are plain data (command in, result out); business *rules* live in entities/value objects — the use case orchestrates them. In Android this maps to the use-case layer Google places between data and UI ([app architecture](https://developer.android.com/topic/architecture)).

## Domain Service <!-- 3 -->
**Stateless domain logic that fits no single entity** because it spans several (a pricing rule across cart + promotions). It stays pure and is the exception, not the default — if the logic belongs to an entity, put it there. A canonical Android example: a session/authorization service deriving roles and permissions from entities for the deny-by-default checks (QUALITY-BAR §4).

## Invariant <!-- 3 -->
A **business rule the domain enforces, always** — either by value objects that make bad states unconstructible or by entities that guard their mutations. Invariants never rely on the UI ("the button is disabled") or the server ("it validates on save"); the domain is the last line that cannot be skipped. Enforcing them here is what prevents corruption at the source.

## Nullability <!-- 3 -->
Kotlin's **null-safety is part of the core's contract** (QUALITY-BAR §1): return types say `Result<T>` or `T`, never nullable "maybe it was missing" — absence is an explicit concept (a `NotFound` error or an empty collection). Platform types (`!`) and `!!` are banned here; the compiler is the first check the domain ships to production with.

## Testability <!-- 4 -->
The payoff: a domain that imports nothing runs in **plain JVM unit tests at millisecond speed** — the ~70% base of the pyramid (QUALITY-BAR §6) — with fakes standing in for every port, no instrumentation, no Robolectric, no device. If a domain test needs a device or a database, the boundary was drawn wrong.

