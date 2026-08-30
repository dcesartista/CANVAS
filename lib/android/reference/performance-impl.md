# Android — performance impl (Compose stability & jank)

> How performance Terms ([performance-theory.md](../../performance-theory.md)) are written in native Android Compose, per Google's [Compose performance guide](https://developer.android.com/jetpack/compose/performance) and QUALITY-BAR §5 (60fps, no work on main, stable models, baseline profiles).
> **Rule:** measure first (layout inspector / `@Preview` + baseline), optimize hot paths, regenerate the baseline profile each release. Stability is the #1 lever.

## Stability <!-- 11 -->
Compose skips recomposition of a composable only if all its parameters are **stable**. Mark immutable models `@Immutable` (or keep them `val`-only `data` classes, which are stable by convention) and state holders `@Stable`. Avoid unstable types (e.g. `ArrayList`, `LocalDate` wrapped in `MutableState`) in hot signatures.
```kotlin
@Immutable
data class Product(@Immutable ...)   // all val, no mutable collections

@Stable
class TimerState { var elapsed by mutableLongStateOf(0) }   // stable property read
```
If a screen recomposes on every frame it is usually an unstable parameter (a fresh lambda or a mutable container). Compose now emits compile-time + runtime stability logs (`-P compilerMetricsDirectory`) to find unstable parameters without guessing.

## Recomposition Scope <!-- 9 -->
Subdivide composables so state changes recompose only the smallest scope. Hoist mutable state above its read sites; use `derivedStateOf` to convert frequent scalar changes into rarely-changing derived values and isolate unstable reads in a sub-composable.
```kotlin
val progress by viewModel.progress.collectAsStateWithLifecycle()
val showSpinner by remember { derivedStateOf { progress > 0f } }   // bool, cheap
Subcontent(showSpinner)   // only this reads/proxies showSpinner
```
The goal is that a slider drag or list scroll recomposes a few small nodes, not the whole screen — every unnecessary recomposition is main-thread CPU taken from the 60fps budget.

## LazyColumn Keys <!-- 11 -->
`LazyColumn`/`LazyRow` needs stable, unique `key`s per item so Compose preserves item state (scroll, input) and reuses nodes across updates. Key by a stable domain id, never by index.
```kotlin
LazyColumn(contentPadding = ...) {
  items(items = products, key = { it.id.value }) { product ->
    ProductRow(product, onOpen = onOpen)
  }
}
```
Without keys an insert at the head re-lays-out and re-creates every later item. For list-heavy screens use keys plus `@Immutable` rows and `contentType` to split heterogenous item layouts.

## remember & rememberSaveable <!-- 9 -->
`remember` caches an expression across recompositions (keyed by inputs); `rememberSaveable` additionally survives config change/process death via the saveable registry. Use `remember` for objects derived from stable inputs; use `rememberSaveable` for user-facing ephemeral state (text, selection) so rotation doesn't reset it.
```kotlin
val snackbar = remember { SnackbarHostState() }          // recreated on process death — fine
var query by rememberSaveable { mutableStateOf("") }      // survives rotation
val items by remember(products) { derivedStateOf { filter(products, query) } }
```
Don't over-cache: `remember` keyed wrongly (e.g. on mutable state it doesn't read) defeats state; cost a recompute is cheaper than a stale cache.

## Strong Skipping / Runtime Opt <!-- 10 -->
Newer Compose enables **strong skipping** (`composeOptions.strongSkippingMode`; on by default in recent BOMs), which skips recomposition for composables whose parameters are equal (`equals`) rather than only stable — making a wider class of parameters effectively stable. Keep models with stable `equals` (data classes) so this applies.
```kotlin
composeOptions {
  strongSkippingMode = true
  runtimeComposeNumericInstability = ...
}
```
Enabling strong skipping reduces the "unstable param" burden, but doesn't remove the need for correct keys, small scopes, and not allocating lambdas inside `items`. Verify with baseline/layout inspector rather than assuming.

## Baseline Profiles <!-- 13 -->
A pre-compiled set of startup-critical classes/methods shipped in the AAB (`com.android.tools.build:gradle` baseline-profile plugin emits `baseline-prof.txt` from an `androidx.baselineprofile` run). Installation pre-AOT's these paths, cutting cold-start time measurably.
```kotlin
// :app/build.gradle.kts
plugins { id("androidx.baselineprofile") }
baselineProfile {
  automaticGenerationDuringApplicationMerge.set(false)
  managedDevices { "pixel2api35" ... }
}
dependencies { baselineProfile(project(":baselineprofile")) }
```
Generate with the `generateBaselineProfile` task per release (QUALITY-BAR §7) and commit the resulting `src/main/baseline-prof.txt`; regenerate whenever the navigation/startup path changes.

## Jank Avoidance <!-- 10 -->
Avoid work on the main thread: no I/O, DB, reflection, or allocation in composition/layout; defer with `Dispatchers.IO`/`Default` at the data boundary (QUALITY-BAR §3) and let `collectAsStateWithLifecycle` resume on the UI dispatcher. Skip heavy lambdas in `items`/`content` blocks.
```kotlin
val deferred by remember(products) { derivedStateOf { heavyButIdempotent(products) } }  // cheap
items(products, key = { it.id }) { p ->
  Row(Modifier.clickable { onOpen(p.id) }) { ... }   // lambda allocation here is fine once
}
```
Profile with `ProfileInstaller` + Layout Inspector and the frame-timeline in [Android Studio profiling] to find the true hot path; never guess. Watch for `Unnecessary recomposition` warnings as the automated signal.
