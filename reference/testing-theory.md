# Testing — theory

> What good tests ARE and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/testing-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §6, §7.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Tests exist to **let you change code with confidence** (QUALITY-BAR §6). We test *behavior*, not lines — coverage is a floor, not a goal. Push tests **down** the pyramid: many fast, isolated unit tests; fewer integration tests; a handful of UI flows. Categories follow [Google's testing foundation](https://developer.android.com/training/testing/foundations) and the split is ~70/20/10 (QUALITY-BAR §6).

## Test Pyramid <!-- 3 -->
The healthy shape: **~70% unit / 20% integration / 10% UI** (QUALITY-BAR §6). Many cheap, fast, deterministic tests at the base; few slow, flaky ones at the top. The **ice-cream cone** is the disease — UI/E2E-heavy suites are slow and brittle and end up disabled. When in doubt about where a test goes, prefer the layer that costs a millisecond and never needs a device.

## Test Size <!-- 3 -->
Google classifies tests **by runtime/resources, not layer** ([test sizes](https://developer.android.com/topic/libraries/testing-support-library/index.html)): **small** = pure logic, no I/O; **medium** = localhost services (a database, MockWebServer); **large** = real device/infra, sparse. Size governs what a test may use — a small test never boots an emulator or touches a network. Tag every test with its size so CI can split and time-box them.

## Unit Test <!-- 3 -->
Tests **one class in isolation with no I/O** (small). The prime targets: domain value objects, entities, and use cases — pure logic driven through **fakes** of their ports. These run in milliseconds, never flake, and carry most of the coverage. If a unit test needs a database or a device, the boundary is wrong — the dependency should sit behind an interface you can fake.

## Integration Test <!-- 3 -->
Tests an **adapter against the real external system it wraps** (medium): a repository implementation against a real Room database, a generated client against MockWebServer (QUALITY-BAR §6). It proves what unit tests deliberately fake: SQL, mapping, transactions, wire conformance. Fewer than unit tests and slower — but a faked repository proves your logic, never your persistence.

## UI Test <!-- 3 -->
Runs the **real composables on a device/emulator** and asserts via semantics — the accessibility tree, not coordinates or text probes (QUALITY-BAR §6). Keep to a **few full-flow journeys**; this is the slowest, most brittle tier, so each test should cover a real user path, not trivia. If a UI test only checks that one component renders, it is a rendering unit test that climbed the pyramid to the wrong height.

## Fake vs Mock <!-- 3 -->
**Prefer fakes over mocks** (QUALITY-BAR §6): a *fake* is a working lightweight implementation of a port (an in-memory repository with the same behavior contract), so tests assert on real behavior and survive refactors. A *mock* asserts on specific calls and arguments, coupling tests to implementation detail. Use interfaces + injection so any dependency is fakes-able; reserve mocks for behavior a fake cannot implement.

## Coverage Floor <!-- 3 -->
**≥75% line coverage on new code** is a floor, never a target (JaCoCo, QUALITY-BAR §6) — the goal is behavioral coverage of the risky paths. Coverage degradation on a PR fails the gate: the fraction is a tripwire for untested code, most costly in domain and data where bugs bite hardest. Measuring is cheap; gaming it (asserting nothing) is why behavior rules sit above the number.

## Behavior Naming <!-- 3 -->
Test names read as **behavior, not implementation**: `pricing: applies volume discount over threshold`, not `pricingViewModelTest_01` or `getList_returnsNotNull`. Each test asserts one observable outcome with an arrange-act-assert (given-when-then) shape. A suite whose failures read as sentences tells you what broke; one whose failures read as identifiers forces you to debug the test to find out.

## Determinism <!-- 3 -->
A test run is **reproducible or it is worthless** ([testing fundamentals](https://developer.android.com/training/testing/fundamentals)): no wall-clock sleeps, no flaky ordering, no dependence on leftover state. Time is injected (a `Clock`), randomness is seeded, and "sleeping N ms" is replaced with idling resources or virtual time. Teams that tolerate flakes end with a suite they stop trusting — and stop running.

## Coroutine Testing <!-- 3 -->
Code that suspends is tested with a **virtual-time dispatcher** that gives deterministic control (`kotlinx-coroutines-test`, QUALITY-BAR §6): advancement is explicit, assertions observe settled state, and "wait 500 ms then check" is permanently banned. The dispatcher, like the clock, is injected, never hard-coded. This is the difference between a suite that passes every run and one that passes "usually".

## Contract Test <!-- 3 -->
Consumer-driven verification across the API boundary (Pact, QUALITY-BAR §6): the app expresses what it needs; the server verifies it in CI. It catches breaking changes between app and API **without** a live environment and locks only the behavior the app actually uses — complementing the OpenAPI spec: the spec defines the shape; the contract test verifies runtime conformance.

## Fast Feedback <!-- 3 -->
The suite's job is **feedback velocity**: a change surfaces its breakage in minutes on a laptop, not hours in a pipeline ([local testing](https://developer.android.com/training/testing/local-tests)). That is what the pyramid is for — the base answers "did my edit break anything?" in milliseconds on every save. When a suite gets slow it stops being run on save, and its power silently decays.

