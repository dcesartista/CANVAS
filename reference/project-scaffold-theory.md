# Project Scaffold — theory

> What a production-grade Android scaffold IS and why. The skeleton that ships standards before features.
> How, per stack: `reference/families/android/project-scaffold-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md).
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

A scaffold is the **quick-start**: a runnable, empty-but-correct Android project that already embodies the Quality Bar ([Android project setup](https://developer.android.com/studio/projects)), so the first feature lands into a production-shaped home instead of a blank folder. Everything below is wiring and conventions — no business logic — and the success criterion is: clone, bring up, and build features against real standards in minutes.

## Production-Grade Skeleton <!-- 3 -->
The scaffold is **release-ready from day one**, not "hello world with tabs" (QUALITY-BAR §7): DI, auth, tests, lint, signing, minification, accessibility, and observability plumbing are present and wired — never bolted on later. Retrofitting standards onto a working app is the expensive path; embodying them in the skeleton makes every feature inherit them for free.

## Layered Structure <!-- 3 -->
The dependency-rule directories exist **before the first feature** (QUALITY-BAR §1): pure domain, data (sources + mappers + repository impls), and presentation, plus a shared kernel. Adding a feature means adding into a pre-existing layer slot, never restructuring. The folder tree *encodes* the architecture so it can't silently drift into fat Activities and god classes.

## Module Layout <!-- 3 -->
Packaging is **modular where the boundaries earn it** (QUALITY-BAR §7): the app shell plus separable feature modules, with domain kept dependency-free so it can be lifted or shared ([modules](https://developer.android.com/studio/projects#module-types)). Monolithic-from-the-start is simpler and often right; the skeleton keeps the seams *possible* — thin interfaces between layers — so modularization later is a rename, not a rewrite.

## Tooling Baseline <!-- 3 -->
Language + **strict typing + linter + static-analysis + test runner**, all configured and runnable via documented commands (QUALITY-BAR §7). Strictness is on from the start because it is painful to retrofit (detekt-as-warning doesn't count). One command each for `build`, `lint`, `static analysis`, `unit test` — the gates every later stage builds on.

## Version Catalog <!-- 3 -->
Every dependency and plugin version is declared **once**, in a Gradle version catalog (QUALITY-BAR §7), and referenced everywhere else. Bumps become a single-line, reviewable change (Dependabot/Renovate) instead of scattered `build.gradle` edits. The catalog kills accidental version drift: two modules can no longer silently disagree about kotlinx-serialization.

## Static Analysis <!-- 3 -->
**Compile-time and static gates** run before tests (QUALITY-BAR §7): a formatter, a lint engine, and a rule set that catches anti-patterns *as writes* — including the forbidden-import rules keeping `android.*` out of domain. These gates are blocking in CI, not advisory. Cheap to run and surgical in what they catch, they turn structural standards from "reviewer memory" into compiler checks.

## Test Baseline <!-- 3 -->
The three tiers are scaffolded empty-but-real (QUALITY-BAR §6): a unit-test module wired to JUnit5 + MockWebServer, integration tests with in-memory Room + Robolectric, and Compose UI-test setup with semantics-based tooling. A tiny exemplar test per tier proves the plumbing works end to end. "Tests exist" means "a test of each tier passes in CI", not "there's a test source set".

## DI Wiring <!-- 3 -->
**Dependency injection is assembled in the skeleton** (QUALITY-BAR §7): the composition root (Hilt) provides the app's graph, repositories, and ViewModels, and every new component declares its dependencies rather than constructing them ([Hilt](https://developer.android.com/training/dependency-injection/hilt-android)). Injection from day one is what keeps layer boundaries honest — a class that can't be injected with a fake can't be tested.

## Configuration Baseline <!-- 3 -->
Environment-varying config (endpoints, feature flags) is **typed and injectable, not scattered constants** — and **no secrets live in `BuildConfig` or VCS** (QUALITY-BAR §4): keys come from secure injection (env/CI secrets or a secure backend) through the graph. `local.properties`/env drive local dev; the scaffold ships `.example` files documenting every key. A build with hardcoded credentials is unshippable by definition.

## Auth Baseline <!-- 3 -->
A **correct identity skeleton** per QUALITY-BAR §4 is wired before features: tokens in Keystore-backed secure storage, a Bearer interceptor, single-flight refresh on 401, logout that revokes and clears. Most apps need auth; scaffolding a correct baseline prevents every project reinventing — and getting wrong — its most security-sensitive code, and makes everything after it correctly exercised.

## Security Baseline <!-- 3 -->
Minimum security hygiene is in the skeleton (QUALITY-BAR §4): cleartext blocked, TLS enforced, R8 rules present and verified, export/safety lint rules, and the deny-by-default nav guard. These are **defaults, not options** — a scaffold that ships with `usesCleartextTraffic=true` or `exported=true` components has already taught the team bad defaults.

## Release Baseline <!-- 3 -->
The release path is **present and green before the first feature** (QUALITY-BAR §7): AAB packaging, R8 minification with verified rules, versioned reproducible builds, a baseline profile regenerated per release, and a keystore loaded from CI secrets — never VCS. Deciding versioning and signing once, at scaffold time, is what makes a real release a non-event later.

## Bring-Up <!-- 3 -->
The scaffold documents **how to run everything**: one local-machine path (`./gradlew` + local emulator) and one scripted path, from `start` (dependencies) to an installed running app (QUALITY-BAR §7). "Bring it up" is a fixed sequence in the README, verified by a fresh-clone test. Unwritten bring-up is the #1 cause of "works on my machine" onboarding — for new joiners and for agents alike.

## CI Gates <!-- 4 -->
A CI pipeline runs the gates on **every PR from day one** (QUALITY-BAR §8): lint → static analysis → unit tests → build, with an instrumented/Compose job on an emulator. Trunk-based + Conventional Commits enforced mechanically. The pipeline is cheap to add at scaffold time and expensive to retrofit — so it ships in the skeleton and is never invented later.

