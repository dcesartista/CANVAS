# Audit checklist — the Quality Bar as checkable items

> A checklist form of [QUALITY-BAR](../../../QUALITY-BAR.md) for the **auditor** to verify mechanically. One item per rule; fill pass/partial/fail + file:line evidence.
> This lives in cross-cutting because the checklist itself is universal; the concrete syntax/commands are per-stack (family).

## 1. Architecture
- [ ] Strict Clean: `domain` pure Kotlin — zero `android.*` imports (forbidden-import rule on).  (§1)
- [ ] Dependency rule: UI/data → domain abstractions only.  (§1)
- [ ] UDF: state flows one way; ViewModel reduces; `collectAsStateWithLifecycle` renders.  (§1)
- [ ] `minSdk 34+`, `targetSdk` latest, single-activity + Navigation 3.  (§1)

## 2. Data & persistence
- [ ] Room entities ↔ DTOs mapped in `data`; no leak into `domain`.  (§2)
- [ ] Forward-only migrations; schema versioned/exported.  (§2)
- [ ] Retrofit + OkHttp + kotlinx.serialization; sealed results across boundaries.  (§2)
- [ ] Secrets in Keystore-backed Tink storage (Proto DataStore), never plain SharedPreferences / deprecated EncryptedSharedPreferences.  (§2)

## 3. API, contract & concurrency
- [ ] Spec-first OpenAPI 3.1; client generated — no hand-written DTOs.  (§3)
- [ ] Errors as RFC 7807/9457 problem+json; idempotency on writes; cursor pagination.  (§3)
- [ ] Coroutines/Flow with structured concurrency; `viewModelScope`/`lifecycleScope`; no `GlobalScope`.  (§3)
- [ ] No main-thread blocking.  (§3)

## 4. Security & auth
- [ ] OWASP ASVS L2; zero Top-10:2025.  (§4)
- [ ] Tokens in Keystore-backed secure storage; Bearer interceptor; single-flight 401 refresh; logout clears.  (§4)
- [ ] Deny-by-default authz; secrets not in VCS / BuildConfig.  (§4)
- [ ] TLS; no cleartext.  (§4)

## 5. UI & accessibility
- [ ] Material 3 theme, light+dark, dynamic color.  (§5)
- [ ] TalkBack semantics/content descriptions on interactive elements; touch targets ≥48dp.  (§5)
- [ ] 60fps; no jank; stable models; LazyColumn keys.  (§5)
- [ ] Baseline profile regenerated per release.  (§5)

## 6. Testing
- [ ] Pyramid ~70/20/10; ≥75% coverage floor on new code.  (§6)
- [ ] Unit: JUnit + Turbine + MockWebServer + coroutines-test; fakes > mocks.  (§6)
- [ ] Robolectric where framework logic; Room in-memory tests.  (§6)
- [ ] Compose UI tests (semantics-based).  (§6)

## 7. Tooling, build & release
- [ ] Gradle KTS + version catalog; AGP/KSP latest; Compose BOM.  (§7)
- [ ] ktlint + detekt blocking; CI green.  (§7)
- [ ] Release: baseline profile, AAB, R8 rules verified, signing outside VCS.  (§7)

## 8. Delivery & code quality
- [ ] Trunk-based; Conventional Commits; CI gates: lint → ktlint/detekt → tests → build → UI tests.  (§8)
- [ ] ADRs for architecture decisions.  (§8)
