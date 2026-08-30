# Contract — the shared API "what"

> CANVAS builds **native Android** apps that talk to a backend over **REST + OpenAPI 3.1**. The contract is the shared *what*: one spec, generated client, no hand-written DTOs (QUALITY-BAR §3).

## Principles
- **Spec-first:** the OpenAPI 3.1 document is the source of truth for the wire API.
- **Generated client:** `openapi-generator` (kotlin/retrofit) generates the client into an `api/` package; a `gen:contract` Gradle task regenerates it. **Never hand-write DTOs.**
- **Contract repo:** the spec lives in its own versioned repository (or a versioned path) so the backend can bump it independently; the Android app pins a version.

## Tooling
- `openapi-generator-cli` (kotlin/retrofit2) + `kotlinx.serialization` conversion.
- `Spectral` for linting the spec, `oasdiff` for breaking-change checks, `Redocly` for docs.
- Consumer-driven contract tests (Pact) — the generated client is the consumer, the contract is the pact.

## Flow
```
backend spec (versioned) ──▶ openapi-generator ──▶ Android client (api/ pkg)
        ▲                                                 │
        └────────── contract tests (Pact) ◀───────────────┘
```

## Android specifics
- Client beans map to `data/dto/`; mappers (`dto → domain`) convert at the data boundary.
- Error responses deserialized per RFC 9457 `problem+json` into domain errors.
- Auth: generated client paired with the OkHttp **Bearer interceptor** + 401 `Authenticator` (QUALITY-BAR §4).
