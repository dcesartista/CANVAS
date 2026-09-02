# Android — concurrency impl (Coroutines & Flow)

> How coroutine-based concurrency Terms ([concurrency-theory.md](../../../reference/concurrency-theory.md)) are written in native Android with **kotlinx.coroutines + kotlinx.flow** (QUALITY-BAR §1, §3).
> **Rules (QUALITY-BAR §3):** every coroutine lives in a structured scope tied to a real lifetime (`viewModelScope`/`lifecycleScope`); `GlobalScope` forbidden; dispatch boundaries at data edges, never in domain; main thread never blocked; UI state is `StateFlow` + `collectAsStateWithLifecycle`, one-shot events are `SharedFlow`; dispatchers injected and swapped under `kotlinx-coroutines-test`.

## Structured Concurrency <!-- 14 -->
The rule that **every coroutine runs in a scope whose lifetime its work cannot outlive** (kotlinx.coroutines) is enforced by construction in Android: coroutines are launched only inside a platform-provided or explicitly owned scope, and the parent completes only when its children do. Cancellation and leak-freedom therefore stop being "be careful" and become structural — a ViewModel that finishes cancels its in-flight work automatically, and there is no orphaned background work left behind.
```kotlin
class SearchViewModel @Inject constructor(
  private val search: SearchProducts,
) : ViewModel() {
  // viewModelScope is cancelled automatically when the ViewModel is cleared
  fun onQueryChanged(q: String) = viewModelScope.launch {
    _results.update { search(q) } // children die with the screen's scope
  }
}
```
A coroutine is never launched "into the void"; if a scope has no one-word owner answer, the code is guessing at its own lifetime (QUALITY-BAR §3).

## CoroutineScope Ownership <!-- 14 -->
Every scope has **one clear owner whose lifetime it mirrors** (QUALITY-BAR §3): `viewModelScope` for ViewModels, `lifecycleScope` for composable/activity work, and explicit app-scoped `SupervisorJob` graphs for long-lived services. `GlobalScope` is a forbidden anti-pattern — orphaned work with no parent. Ownership is a decision made once, at the boundary, then every child inherits it.
```kotlin
class AppServices @Inject constructor(
  private val syncEngine: SyncEngine,
) {
  // owned by the app process; child jobs in an app-lifetime supervisor
  private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
  fun start() { scope.launch { syncEngine.run() } }
  fun stop()  { scope.cancel() } // explicit owner shuts the whole tree down
}
```
Feature-level scopes are explicit and injected; nothing creates a scope ad hoc inside a use case or domain object.

## Dispatchers <!-- 14 -->
The **executor policy** for a coroutine is injected at the edges, not hard-coded (QUALITY-BAR §3): `Dispatchers.IO` for network/disk in `data`, `Dispatchers.Default` for CPU in heavy compute, main for anything touching the UI. Dispatchers are constructor-injected so tests swap them for a test dispatcher with virtual time — a `Dispatchers.IO` hard-coded in a repository makes it impossible to test deterministically.
```kotlin
class DefaultProductRepository @Inject constructor(
  private val api: ProductsService,
  private val io: CoroutineDispatcher, // injected: Dispatchers.IO in prod, TestDispatcher in tests
) : ProductRepository {
  override suspend fun products(): List<Product> = withContext(io) {
    api.list(pageSize = 50).products.map { it.toDomain() }
  }
}
```
Dispatch switches happen at data boundaries, never scattered through use cases or leaking dispatchers into the pure domain.

## Cancellation <!-- 16 -->
**Work stops on command, cooperatively** (kotlinx.coroutines): when a scope is cancelled its children resume with `CancellationException` and unwind via `finally`. Cancellation must never be caught-and-swallowed — silencing it breaks the parent's tree; the pattern is "clean up on cancel, let it propagate otherwise." Timeouts are just cancellation (`withTimeout`).
```kotlin
viewModelScope.launch {
  try {
    val result = withTimeout(5_000) { slowNetworkCall() }
    _uiState.update { Ready(result) }
  } catch (e: CancellationException) {
    throw e                     // ALWAYS rethrow on cancel
  } finally {
    analytics.log("request_aborted") // cleanup runs, cancel propagates
  }
}
```
Code that catches `CancellationException` without rethrowing makes a cancelled scope re-enter cancelled parents — a silent lifecycle bug.

## Flow <!-- 15 -->
A **cold stream of values over time** (`Flow<T>`) is the reactive spine from data to presentation (kotlinx.flow, QUALITY-BAR §3). The domain exposes flows as plain return types; operators live at the data/UI edge, and `flowOn`/`stateIn` attach dispatchers and roots the cold stream into a hot, observable one. Flow replaces hand-rolled queues and callback forests for update streams and paging.
```kotlin
class ObserveCart @Inject constructor(
  private val repo: CartRepository,
  private val io: CoroutineDispatcher,
) : FlowUseCase<Unit, Cart> {
  override operator fun invoke(params: Unit): Flow<Cart> =
    repo.watchCart()          // cold source
      .flowOn(io)             // emits off main
      .map { it.toCart() }    // domain mapping stays pure
}
```
Cold means each collector gets its own fresh run; the domain exposes `Flow<T>` returns without threading any framework dispatcher through it.

## StateFlow vs SharedFlow <!-- 12 -->
Two hot flows chosen by **semantics: state vs events** (QUALITY-BAR §1). `StateFlow` caches **one value** and is distinct-until-changed — the right holder for UI state collected by one screen. `SharedFlow` broadcasts **ephemeral emissions** to N collectors — the one-shot event/lamp (snackbar, navigate). Picking by semantics prevents the two classic bugs: replaying an event on rotation and missing updates on a conflated state stream.
```kotlin
private val _state = MutableStateFlow(ProductsUiState.initial())
val state: StateFlow<ProductsUiState> = _state.asStateFlow()   // one value, distinct

// one-shot events — replay 0 so rotation does not re-fire a snackbar
private val _events = MutableSharedFlow<UiEvent>(extraBufferCapacity = 1)
val events: SharedFlow<UiEvent> = _events.asSharedFlow()
```
State is collected in Compose via `collectAsStateWithLifecycle`; events are collected in a `repeatOnLifecycle` block so emission and collection honor the lifecycle.

## Backpressure <!-- 15 -->
When a producer outruns a consumer the policy is **explicit** (kotlinx.flow buffering, QUALITY-BAR §5): `buffer()` queues, `conflate()` drops intermediates, `debounce()` shapes chatty input streams. In Compose-land the sane default is conflate-ish — latest state wins — because the user wants the newest frame, not an inventory of stale ones.
```kotlin
@Composable fun SearchField(state: SearchState, onQuery: (String) -> Unit) {
  var text by remember { mutableStateOf("") }
  LaunchedEffect(Unit) {
    snapshotFlow { text }                // every keystroke
      .debounce(300.milliseconds)        // wait until the user pauses typing
      .distinctUntilChanged()
      .collect { onQuery(it.trim()) }    // one query per pause, not per key
  }
}
```
`debounce`/`conflate`/`buffer` are chosen deliberately; an unexplicit stream that silently drops or queues is a latent jank or stale-UI bug.

## Testing Dispatchers <!-- 18 -->
Deterministic tests swap real dispatchers for **kotlinx-coroutines-test** `StandardTestDispatcher` with virtual time (QUALITY-BAR §6). Every class that dispatches takes its `CoroutineDispatcher` via injection so tests drive it forward manually with `advanceUntilIdle`/`runTest`, producing deterministic timing without sleeps or flakiness.
```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class SearchViewModelTest {
  private val testScheduler = TestCoroutineScheduler()
  private val io = StandardTestDispatcher(testScheduler)

  @Test
  fun `query maps to results`() = runTest(testScheduler) {
    val vm = SearchViewModel(fakeSearch, io)
    vm.onQueryChanged("shoes")
    advanceUntilIdle()           // drain virtual time; no real delay, no race
    assertEquals(2, vm.state.value.items.size)
  }
}
```
Rules: never `runBlocking` for logic under test, never `delay` in assertions; virtual time is what makes coroutine tests fast and repeatable.
