# Performance — theory

> What performant Compose UI IS and why. 60fps with responsive cold start — the QUALITY-BAR §5 contract.
> How, per stack: `reference/families/android/performance-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §5, §7.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Performance is a **user-experience contract, not a benchmark**: frames land within 16.6ms, scrolling stays at 60fps, cold start reaches content fast, and memory stays flat across long sessions. The official [Compose performance](https://developer.android.com/jetpack/compose/performance) guidance is the authority; the rules below make jank structurally hard and make performance *measurable* per release (QUALITY-BAR §5, §7).

## Frame Budget <!-- 3 -->
Every frame has **16.6ms at 60fps** to compose, lay out, draw, and resolve — a frame that misses is jank, and repeated misses read as "laggy" ([rendering](https://developer.android.com/topic/performance/rendering)). The discipline: small stable work per frame, nothing expensive on the UI thread, nothing in composition that belongs off-thread. When a frame is busy, hunt the boundary — main-thread work that should be suspended or precomputed.

## Jank <!-- 3 -->
The visible symptom: a **scroll that hiccups, a screen that pauses, a click that lags**. Its causes are mostly structural, not random: main-thread I/O, allocation storms in fast paths, unstable state triggering full-screen recomposition, missing list keys ([frame stats](https://developer.android.com/topic/performance/understanding-performance#frame-stats)). A profile showing nothing hot on a janky frame means the jank is elsewhere — usually over-broad recomposition.

## Recomposition <!-- 3 -->
When state changes, Compose **re-runs only the composables whose inputs changed** and skips the rest ([mental model](https://developer.android.com/jetpack/compose/mental-model)). The performance question is *scope*: does a click on one row recompose the whole list? Recomposing too much shows up as "it works but animations run at 30fps". Minimizing recomposition scope is the single highest-leverage Compose optimization; the levers are stability and state-read placement.

## Stability & Skipping <!-- 3 -->
Compose can **skip a composable whose inputs are stable-and-unchanged**, based on each parameter's *stability* (QUALITY-BAR §5): immutable/sealed/`@Immutable` types are skippable; un-declared-stable inputs (`var`, `MutableState`, framework types) may not be ([stability](https://developer.android.com/jetpack/compose/performance#stability)). Making hoisted state data `@Immutable`/`@Stable` is the difference between "every change redraws the list" and "only the changed row redraws".

## Immutable State <!-- 3 -->
UI-state data classes are **`val`-only, with immutable collections** (QUALITY-BAR §5): a mutable `List` held in a "state" class defeats stability and makes every change look like a brand-new object. Construct whole new instances on change instead (presentation-theory). Immutability here *is* a performance fix, not just correctness — the diff-er cannot outsmart a type that lies about being constant.

## Late State Reads <!-- 3 -->
**Read state where it's needed, not where it's available** ([state reads](https://developer.android.com/jetpack/compose/performance#state-reads)): reading a hoisted state at the top recomposes the whole subtree; reading it in the few leaf composables that display it shrinks recomposition to those leaves. Pass *values* down, keep *state* up — the same hoisting discipline as presentation-theory, paying twice: architecture and frames.

## Lazy List Discipline <!-- 3 -->
Long lists use lazy composition with **stable per-item `key`s** and lean item content (QUALITY-BAR §5): keys preserve scroll position and item state across reorder/refresh, and per-item composables are minimal. A list without keys reorders incorrectly *and* recomposes explosively — missing keys are simultaneously a correctness bug and a performance bug.

## Allocation Discipline <!-- 3 -->
**Hot-path allocation is bounded** (QUALITY-BAR §5): lambdas recreated per recomposition, per-frame collections, string concatenation in item composables. Prefer `remember`/`rememberUpdatedState`/`rememberSaveable` for objects that persist, `derivedStateOf` for values computed from state, and hoisted stateless composables for stable slots. Profile first — allocation is not wrong until it shows up as frame time.

## Main-Thread Discipline <!-- 3 -->
**Nothing expensive on the main thread, ever** (QUALITY-BAR §3, §5): no I/O, no parsing, no database, no heavy computation in composition — those suspend in data (concurrency-theory) or are precomputed. A 30ms block on the main thread is exactly two dropped frames. The profiler's main-thread trace is the indictment; every red zone is a violation of this rule, not a minor one.

## Cold Start <!-- 3 -->
**Time-to-first-meaningful-content from launch** (QUALITY-BAR §5, §7): startup is the moment users judge, so anything non-essential is deferred past first frame and the first screen is cheap. Heavy initialization (database, network pools, large serialization) is lazily scheduled and first-frame work is trimmed to the necessary minimum. The OS treats startup as a budget ([launch time](https://developer.android.com/topic/performance/launch-time)); so should you.

## derivedStateOf <!-- 3 -->
**Deriving state computes when inputs change, not on every recomposition** ([derived state](https://developer.android.com/jetpack/compose/state#derived-state-of)): a `derivedStateOf` over a filtered or summed list does that work once per input change, not once per recomposition. It also kills redundant recomposition when the derived value is actually unchanged. The failure mode to avoid: recomputing the same expensive derivation frame after frame.

## Baseline Profile <!-- 3 -->
A **shipped, per-release performance artifact** telling the runtime which code to AOT-compile at install — profile-guided optimization that fixes both cold start and first-run jank (QUALITY-BAR §5, §7). It is regenerated and verified per release, never written once: apps move; profiles rot with them ([baseline profiles](https://developer.android.com/topic/performance/baselineprofiles)). This is the difference between "fast for testers who repeated a screen 50 times" and "fast for a new install".

## Memory & Leaks <!-- 3 -->
**Flat, predictable memory across the session** (QUALITY-BAR §5): no activity/context/ViewModel leaks, no unbounded caches, no retained coroutines (concurrency-theory Scope Ownership exists because of this). Measurement is in the pipeline from day one (QUALITY-BAR §7), because "it felt OK in my tester session" is exactly how leaks ship. A forever-growing heap is a performance bug with a delayed fuse.

## Measure First <!-- 4 -->
Performance work begins at **measurement**: profile before and after, never "optimize by feel" (QUALITY-BAR §5). The pipeline produces per-release regressions (frame times, cold start, profile coverage), and work intends something measurable — "≤1 recomposition per row while scrolling", "cold start under X". Optimizing blind is the only way to ship a net-worse app while believing it got faster.

