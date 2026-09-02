# API — theory

> What a well-formed REST API IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/api-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §3.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

The API is the **wire contract the mobile app lives by** (QUALITY-BAR §3): REST over HTTP, specified **first** in OpenAPI 3.1, with the client generated from that spec so there are no hand-written DTOs to drift. Every rule below exists to keep that contract correct, stable, and evolvable — because a shipping app cannot renegotiate the wire shape overnight. [Google AIP](https://google.aip.dev/) is the style authority; RFC 9457 and IETF drafts set the message formats.

## Contract-First <!-- 3 -->
The **spec is written before the code** (QUALITY-BAR §3): the OpenAPI document is the source of truth that the server implements and the client is generated from, both sides bound to the same file. It is versioned and reviewed like code, and changes through review — not via an engineer quietly editing a retrofitted endpoint. Spec drift is the failure contract-first exists to prevent.

## OpenAPI Contract <!-- 3 -->
A **single, machine-readable description of the interface** — paths, operations, request/response schemas, error shapes — in OpenAPI 3.1 (QUALITY-BAR §3). It is the negotiating surface for clients and servers. Every endpoint, every field, every error code is documented **in the spec**, so the spec and the behavior cannot disagree. The app's whole knowledge of "what the server looks like" is this one file.

## Generated Client <!-- 3 -->
The Android client is **produced from the contract** (`openapi-generator` kotlin/retrofit), never handwritten (QUALITY-BAR §3). Generation guarantees the client matches the spec literally — when the spec evolves, regeneration diffs the change into code review. Hand-written DTOs are forbidden because they reintroduce exactly the drift that contract-first removes.

## Resource & Naming <!-- 3 -->
APIs expose **resources** (nouns) as collections (`/products`, `/orders/{id}/items`) — Google AIP-122 — with operations as HTTP verbs, never RPC action names in the path (`/getProduct` is rejected). Naming is stable and version-independent. Predictable nouns + consistent verbs give the generated client a clean, discoverable surface and make general client logic (auth, paging, errors) reusable.

## Versioning <!-- 3 -->
**The major version lives in the path** (`/v1`) — Google AIP-185. Additive, backward-compatible changes ship in place; breaking changes move to a new major (`/v2`), with the old version kept alive for installed clients (QUALITY-BAR §3). Mobile makes this non-optional: you cannot force-upgrade devices. A second layer is the contract package's own SemVer — path version and package version are *both* managed.

## Pagination <!-- 3 -->
List endpoints paginate **from day one** — adding it later is breaking — per Google AIP-158: request `page_size` (the server caps it) plus an **opaque** `next_page_token`; an empty token signals the end. Tokens are opaque and non-parseable so the server can change its cursor strategy beneath them. Mobile lists are infinite-scroll by nature; the API must serve that from the start.

## Idempotency <!-- 3 -->
Unsafe writes (POST/PATCH) accept an **`Idempotency-Key`** header (IETF draft): the server stores the key with the first response and **replays that stored result on retry**, so a client that retries after a timeout never double-creates (QUALITY-BAR §3). Keys are unique per logical operation and never reused across payloads. Mobile networks drop requests; this is what makes "retry" safe.

## Error Response <!-- 3 -->
All failures share **RFC 9457 `application/problem+json`** (`type, status, title, detail, instance`) plus a stable **machine code** — QUALITY-BAR §3. One consistent envelope for 400s, 4xx, and 5xx means the client's error path is one parser, one reader, one UI. The `type` URI documents the problem; `detail` is human-readable, never parsed by code.

## Machine Code <!-- 3 -->
The **stable, client-branchable identifier** of a problem (`SESSION_EXPIRED`) inside the error envelope — the app's commlink. It is versioned and documented in the spec. UI and state holders branch on the machine code, *never* on the HTTP status or `detail` prose; a status like 401 is transport context. This is what lets the mobile client map errors to typed domain outcomes.

## Request Validation <!-- 3 -->
**Validation happens at the edge against the contract**, before a use case runs: malformed requests get a 400 + `problem+json`, never a 500 (QUALITY-BAR §3). The use case can then assume well-formed input and enforce deeper *business* invariants. The client ideally validates too — but the server remains the authority, because clients drift, lie, and get bypassed.

## Retry & Backoff <!-- 3 -->
Transient failures (timeouts, 429, 5xx) are **retried with bounded backoff**, honoring `Retry-After` when present (QUALITY-BAR §3). Idempotency keys make retries safe; backoff makes them polite. The client distinguishes *retryable* (network, 429/503 — retry with backoff) from *definitive* (4xx — surface, never retry blindly); retrying a 400 is how clients wedge themselves.

## Evolvability <!-- 3 -->
A contract is **built to change additively**: new fields are optional, new endpoints are additive, fields are removed only in a new major (QUALITY-BAR §3). Clients ignore unknown fields (never crash on them), which is exactly why generated DTOs are deserialized permissively. Combined with path versioning, this keeps old clients safe and new features deployable without coordinated release.

