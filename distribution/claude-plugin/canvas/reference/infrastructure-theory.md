# Infrastructure — theory

> What the infrastructure (cross-cutting) ring IS and why. The assembly + operation of the app.
> How, per stack: `../lib/android/reference/infrastructure-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §3, §4.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Infrastructure holds **everything cross-cutting that makes the app assembled, configured, observable, and reachable** (QUALITY-BAR §3, §4): DI wiring, config, logging, analytics, crash reporting, networking plumbing, and time. It is the outer ring in scaffold-theory terms — layers depend on these services through injected abstractions (QUALITY-BAR §1), so the domain never sees a logger, a crash SDK, or an HTTP client.

## Composition Root <!-- 3 -->
The **single place where the dependency graph is assembled** (QUALITY-BAR §1, §7): Hilt composes concrete adapters into repositories, repositories into use cases, use cases into ViewModels — and only here does the graph name both an interface and its implementation ([Hilt](https://developer.android.com/training/dependency-injection/hilt-android)). Everything else depends on interfaces; there are no scattered `new` calls and no runtime service-locator. A graph you cannot trace in one place is a graph you cannot reason about.

## Dependency Injection <!-- 3 -->
Providing dependencies **through the constructor/composition root, not lookups** (QUALITY-BAR §7): each class declares what it needs, and tests replace any of it with a fake. DI *is* the enforcement of the dependency rule — a class that constructs its own repository is a class that cannot be unit-tested (testing-theory). The discipline: interfaces at boundaries, scopes per lifetime (app/service/screen), no singletons pretending to be short-lived.

## Configuration <!-- 3 -->
Environment-varying settings are **typed, validated at boot, and injected** (QUALITY-BAR §4): endpoints, flags, and toggles arrive as typed config through the graph, with secrets injected from secure sources, never baked in (security-theory). The app fails fast at startup on missing or invalid config instead of crash-mid-session with a null. Config is the small surface where dev and prod genuinely differ — the seam that stops "works locally" from diverging into "breaks in CI".

## Logging <!-- 3 -->
Structured, leveled logs **across every layer through one injected interface** (QUALITY-BAR §4): behavior tracing with context (screen, operation, result), and strict hygiene that secrets and PII never reach the output (security-theory Logging Hygiene). Logs are the "what did the app actually do" record that crash reports and support tickets both live off. Unstructured `Log.d` scattered at random call sites is the same record nobody can filter.

## Analytics <!-- 3 -->
**Event telemetry with a maintained taxonomy** (QUALITY-BAR §4): named events and parameters, with definitions versioned in the repo and reviewed like a schema — not ad-hoc strings typed in fourteen places. Analytics is how the product learns which journeys work; it is also a privacy surface, so what is collected must match what is declared. Events flow through an abstraction; the SDK stays a swappable detail behind it.

## Crash Reporting <!-- 3 -->
Unhandled failures are **captured, grouped, and surfaced per release** (QUALITY-BAR §7 scope note): the crash SDK runs at app scope, taking stack plus context (version, device, session) without secrets. Crash monitoring turns "support says it broke" into "release 1.7.2 has a crash cluster in checkout". A crash reporter wired before release-readiness is what tells you whether the release theory actually held.

## Networking <!-- 3 -->
The transport stack is **one coherent client (Retrofit + OkHttp + kotlinx.serialization) assembled at infra** (QUALITY-BAR §3): timeouts, retries, interceptors, TLS/network-security, and auth attachment (security-theory) live in one configured layer — and every call crosses a **sealed-result** boundary (data-theory) into the app. Networking is infrastructure because *everything* talks through it; scattered ad-hoc HTTP is the anti-layer this prevents.

## Interceptors <!-- 3 -->
**Cross-cutting request/response hooks in one chain** (QUALITY-BAR §3, §4): auth headers, logging with redaction, retry-with-backoff, accept-headers. Interceptors keep concerns orthogonal — a timeout policy or a token is not something forty call sites each implement. Interceptor order is effectively the pipeline's contract; it is documented and tested (a MockWebServer-based interceptor test is among the first the scaffold writes).

## Time & Clock <!-- 3 -->
The app's notion of **now is a single injectable clock** (QUALITY-BAR §6): nothing calls wall-clock directly in logic that must be tested — expiry checks, TTLs, "last updated" stamping all read the injected `Clock`. Faking time is what makes coroutine and cache tests deterministic (testing-theory). Real time is a hidden, injectable seam, bought cheapest at the infrastructure ring.

## Feature Flags <!-- 3 -->
Capability gating is **a first-class config surface** (QUALITY-BAR §3): flags ride the injected configuration, default to production-safe, and roll out per audience (remote/local) without a release. Flags are also the incident-response tool — kill-switch a broken feature without shipping. The rule: a flag is declared, typed, and documented; a string-typed `"on"` flag written in code is debt, not a flag.

## App Bootstrap <!-- 3 -->
The app **boots in a fixed, dependency-safe order** (QUALITY-BAR §1): initialize the graph, validate config, start telemetry/crash, then enter the first screen — with anything slow deferred past first frame (performance-theory Cold Start). Bootstrap is where "it ran" is decided, so it is explicit and single-location: no feature initializes itself on import. Stray setup in a random class's `init` is how startup order becomes spaghetti.

## Cross-Cutting Boundaries <!-- 3 -->
Infrastructure may **touch every layer — but only through interfaces** (QUALITY-BAR §1): the domain declares what it needs (a clock, a session, a repository port), and infra supplies the implementations. The discipline that keeps infra from becoming a god-layer is the same dependency rule as the rest: infra knows everything; nothing outward knows infra's specifics — the forbidden-import lint exists precisely to keep a crash SDK or an OkHttp type out of the domain.

## Telemetry & Supportability <!-- 4 -->
Beyond crash: **observability of the running app** (QUALITY-BAR §7 scope note) — networking traces, cold-start metrics, frame stats, and the "what happened before this crash" breadcrumbs. Infrastructure wires the *sinks* so layers stay clean; a version-aware, session-aware telemetry trail is what makes a support ticket answerable and a QA report reproducible. It is release-phase reality, but the abstractions must exist from scaffold day one.

