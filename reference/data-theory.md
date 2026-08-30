# Data — theory

> What the data layer IS and why. Family-agnostic — the single source of truth.
> How, per stack: `reference/families/android/data-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §1, §2.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

The data layer is an **outer ring**: it implements the ports the domain owns (QUALITY-BAR §1) and is the only place that knows a transport or persistence technology. It depends on the domain; the domain never depends on it. Every Retrofit call, every Room query, every mapper lives here — translated at the boundary back into plain domain objects and domain-typed errors ([Google data layer](https://developer.android.com/topic/architecture/data-layer)).

## DTO <!-- 3 -->
A **plain data structure crossing a boundary** — a JSON payload, a Room row — mirroring an *external* schema with **no behavior and no invariants**. DTOs exist so the shape some outside system dictates never contaminates the domain; a Mapper translates them inward. They are deliberately dumb: serialization libraries construct and destroy them freely, which is exactly why they must not travel into the domain.

## Mapper <!-- 3 -->
A **pure, explicit translator** between DTOs/rows and domain entities/value objects (and back). It is the seam isolating the domain from external schemas: an API can add a field, a database can rename a column, and only the mapper changes. Mapping is **total** — every field accounted for — and lives entirely in this layer. Watch for N+1 and mapping-in-the-wrong-layer; both are symptoms of a leaky boundary.

## Data Source <!-- 3 -->
The **lowest data-layer unit**: it talks to **exactly one** external system (a network API, a local database, a cache) and returns or consumes DTOs. It holds **no business logic** and knows nothing of other sources. Splitting per source keeps each swappable and testable in isolation and lets a repository compose several without any of them knowing the rest exists.

## Remote Data Source <!-- 3 -->
The **network source**: issues HTTP calls against the API contract (QUALITY-BAR §3) and maps wire shapes to DTOs. It owns transport mechanics — timeouts, retries, cancellation, auth-attachment — but never business decisions. Its errors surface as technical signals (timeout, 503, parse failure) so the layers above decide policy; this source merely reports what the network did.

## Local Data Source <!-- 3 -->
The **on-device persistence source** (Room, DataStore): structured data and cache, owned by this source. It is the offline story and the fast-read story; schema versioning, transactions, and queries are its concerns — the *decision* of what to cache is the repository's. Room entities are DTOs here and must never appear in domain code ([Room](https://developer.android.com/training/data-storage/room)).

## Repository Implementation <!-- 3 -->
The **concrete implementation of a domain Repository Interface**: it composes data sources + mappers to fulfil the port in domain terms, resolves cache-vs-network conflict, and is the only place that "knows" how data is persisted. The domain calls the interface; the composition root injects this implementation. As Google notes, repositories converge the app's reads and writes into one owner ([data layer](https://developer.android.com/topic/architecture/data-layer)).

## Sealed Result <!-- 3 -->
The **typed return the domain sees**: a sealed type carrying either the domain value or a domain-typed failure (QUALITY-BAR §2) — never bare exceptions as control flow. Every technical failure from a source (network, disk, parse) is *translated* here into this shape before crossing outward-in. It makes each caller handle every case exhaustively; the compiler enforces what the happy path forgot.

## Offline-First <!-- 3 -->
**The app works with no network** — reads resolve from the local source, writes are queued and synchronized when connectivity returns. It is a product decision with architectural teeth ([offline-first](https://developer.android.com/topic/architecture/data-layer)): the local source is a *source of truth*, not an afterthought cache. Distinguish the always-writable synchronous path from the background-sync path; both route through the repository.

## Cache Strategy <!-- 3 -->
**Which data is cached, for how long, and who refreshes it** — TTL-based, freshness-token, or write-through, chosen per aggregate. Cache is a policy, so it lives in the repository (or a dedicated cache facade), never scattered across screens. The rule: never serve stale-unbounded data silently — surface "offline snapshot" as state the UI can show rather than pretending it is current.

## Single Source of Truth <!-- 3 -->
**One authoritative owner per piece of state** (QUALITY-BAR §1): the local database for persisted domain data, the server for account truth, the UI layer for render state. Every other layer observes or requests that owner rather than keeping its own copy. Where sources disagree (cache says X, server says Y), the SSOT wins and the loser is reconciled or cleared — never silently shown as truth.

## Migration <!-- 3 -->
**Schema evolution done forward-only and without data loss** (QUALITY-BAR §2): versioned migrations (`Migration` objects / `AutoMigration`) ship in release order, the schema export is version-controlled and exercised in tests. Destructive changes are explicit and reviewed. A data layer without a migration story is a data layer that blocks every future release.

## Unit of Work <!-- 4 -->
A **transaction boundary**: several source operations run **atomically** (all-or-nothing) through an interface the data layer implements (QUALITY-BAR §2). Use cases express "write the aggregate and its sync-queue entry together" *without importing the transport/database type*. This prevents the partial writes that corrupt the SSOT — the classic case is a write plus its outbox event failing together versus apart.

