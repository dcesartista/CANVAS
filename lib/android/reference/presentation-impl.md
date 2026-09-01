# Android — presentation impl (Compose + StateFlow + Hilt)

> How the presentation Terms ([presentation-theory.md](../../presentation-theory.md)) are written in native Android, per Google's [App Architecture Guide](https://developer.android.com/topic/architecture) and [UDF](https://developer.android.com/topic/architecture/ui-layer#udf).
> **Rules (QUALITY-BAR §1, §5):** `presentation` depends on `domain` only; no ViewModel knows `Activity`/`Context`; state flows **down** via `StateFlow`, events flow **up** via VM functions. All Compose code lives here.

## ViewModel <!-- 25 -->
`@HiltViewModel` with `@Inject constructor`; exposes a single `StateFlow<UiState>` and semantically-named event functions. `MutableStateFlow` is private internal; use `viewModelScope.launch` for side effects; **no `Context`, no `Application`, no `Activity`** — anything the UI needs is injected as a domain port.
```kotlin
@HiltViewModel
class ProductListViewModel @Inject constructor(
  private val listProducts: ListProducts,
  private val savedState: SavedStateHandle,
) : ViewModel() {
  private val _ui = MutableStateFlow(ProductListUiState())
  val uiState: StateFlow<ProductListUiState> = _ui.asStateFlow()

  init { loadFromArgs(savedState.get<String>("categoryId")) }

  private fun loadFromArgs(categoryId: String?) = onLoadMore()

  fun onRefresh() = viewModelScope.launch {
    _ui.update { it.copy(loading = true, error = null) }
    listProducts(limit = 20)
      .onSuccess { p -> _ui.update { it.copy(loading = false, items = p.items, hasMore = p.hasMore) } }
      .onFailure { e -> _ui.update { it.copy(loading = false, error = e.message) } }
  }
}
```
Every `fun` maps to a UI intent; run `runCatching`/`Result` inside the scope and reduce into `_ui` — never expose the mutable flow.

## UI State <!-- 12 -->
An immutable `data class` (single loading/error/content shape) or a `sealed interface` when states are mutually exclusive. All fields `val`; use `.copy()` for updates; view-model state is screen-scoped and hoisted only for what the screen needs to render.
```kotlin
data class ProductListUiState(
  val loading: Boolean = false,
  val items: List<Product> = emptyList(),
  val hasMore: Boolean = false,
  val error: String? = null,
) : @Immutable UiState
```
Annotate `@Immutable` (Compose) so recomposition skips stable fields. For distinct screens prefer a `sealed interface` (e.g. `Loading`/`Content`/`Error`) and `when` in the screen.

## One-shot Event <!-- 13 -->
Transient occurrences (toasts, navigate after login, snackbars) that must **not** survive rotation are delivered once via a `Channel`/`SharedFlow` and replayed with `replay=0`. They are separate from `uiState` (state is for rendering; events are for one-time side effects).
```kotlin
private val _events = Channel<UiEvent>(Channel.BUFFERED)
val events = _events.receiveAsFlow()
fun onAddToCart(p: ProductId) = viewModelScope.launch {
  val ok = addToCart(p, 1).isSuccess
  if (ok) _events.send(UiEvent.ShowSnackbar("added"))
}
sealed interface UiEvent { data class ShowSnackbar(val msg: String) : UiEvent }
```
Old "event as state + consume" is discouraged; `Channel` gives `trySend`/`receiveAsFlow` semantics with `shareIn` if multiple collectors are needed.

## Unidirectional Data Flow <!-- 10 -->
State travels **down** via the single `StateFlow` and is collected lifecycle-aware; events travel **up** through VM functions — never the reverse, and no `var` state at the top of a composable. This makes the screen a pure function of state (`ProductListScreen(state, onRefresh)`).
```kotlin
@Composable fun ProductListScreen(
  state: ProductListUiState,
  onRefresh: () -> Unit, onItemClick: (ProductId) -> Unit,
) { when { state.loading -> CanvasProgress()
        state.items.isEmpty() -> CanvasEmptyState("No products", action = {...})
        else -> LazyColumn { items(state.items, key = { it.id }) { ... } } } }
```
Logic that isn't presentation (pagination math, discount) stays in `domain`; the composable only maps state → UI and callbacks → events.

## Screen <!-- 15 -->
`@Composable` functions collect state with `collectAsStateWithLifecycle()` (never bare `collectAsState`) and render dumb content. Separate a smart `*Screen` (owns the VM/collection) from dumb `*Content` composables (pure params) so they're testable without Hilt.
```kotlin
@Composable
fun ProductListRoute(
  vm: ProductListViewModel = hiltViewModel(),
) {
  val state by vm.uiState.collectAsStateWithLifecycle()
  LaunchedEffect(Unit) { vm.events.collect { e -> when (e) {
    is UiEvent.ShowSnackbar -> snackbarHostState.showSnackbar(e.msg) } } }
  ProductListScreen(state, onRefresh = vm::onRefresh, onItemClick = vm::onSelected)
}
```
`collectAsStateWithLifecycle` (from `androidx.lifecycle:lifecycle-runtime-compose`) stops collecting when the composable leaves the idle/started window, saving CPU on backgrounded screens.

## Material 3 Theme <!-- 11 -->
Theming is a Compose `@Composable` wrapper over `MaterialTheme`. CANVAS apps do **not** hand-write a theme — they consume the swappable UI library **`ui-default`** (the Android realization of the agnostic Palette contract). `CanvasTheme` from `com.canvas.ui.default.palette` supplies a complete light/dark/highContrast palette and the M3 bridge (color scheme + typography) mapped from T3 semantic tokens:
```kotlin
import com.canvas.ui.default.palette.CanvasTheme
import com.canvas.ui.default.palette.DefaultPalette
import com.canvas.ui.default.palette.LocalSemanticTokens

@Composable
fun AppRoot() {
    CanvasTheme {            // CanvasTheme(palette = ..., darkTheme = ..., highContrast = ...)
        AppNavHost()
    }
}
```
Wrap `MainActivity.setContent { CanvasTheme { AppNavHost() } }`. To rebrand, pass a different `Palette` (swappable) — components are **not** re-themed in place. All colors/sizes reach components as T3 semantic tokens via `LocalSemanticTokens`; never raw hex/Dp in components ([QUALITY-BAR](../../../QUALITY-BAR.md) §5).

## ui-default <!-- 9 -->
`ui-default` is a separate Android library (`com.canvas.ui.default`) holding the swappable default "look": the token layer (T3 semantics), `DefaultPalette` for each mode, `CanvasTheme`, and the component set. Screens **build only from these components** — never raw `MaterialTheme`/M3 widgets or hand-rolled theme:
- Containers: `CanvasCard`, `CanvasTopBar` (64dp), `CanvasBottomNav`(+`NavDest`), `CanvasTabRow`, `CanvasListItem`
- Inputs/actions: `CanvasButton`, `CanvasButtonSecondary`, `CanvasTextField`
- Feedback/states: `CanvasEmptyState`, `CanvasErrorState`, `CanvasSnackbar`, `CanvasProgress`
- Type bridge: `TextFromType` → `TextStyle` from `TypeStyle` tokens (use instead of raw `TextStyle(...)`)

Pull it in as a dependency (composite build / submodule or published Maven — see `ui-default/CONSUMING.md`). The contract these realize lives in the agnostic sibling **Palette** repo (`docs/0001-ui-token-contract.md`, `docs/0002-component-inventory.md`); CANVAS owns the non-themeable core-correctness floor only.

## State Hoisting <!-- 8 -->
Request state (and any state with lifecycle needs) is hoisted to the ViewModel and passed down; local, ephemeral UI state (text field draft, expansion toggles) stays in the composable via `rememberSaveable`. Hoist the *minimum*: lift state only until it's needed by siblings or for persistence.
```kotlin
var query by rememberSaveable { mutableStateOf("") }       // ephemeral, survives config
val visibleItems by remember(state.items) { derivedStateOf { state.items.filter { it.matches(query) } } }
```
`rememberSaveable` survives configuration changes via the saved-state registry; `remember` does not — choose per data lifetime.

## Lifecycle & Collection <!-- 7 -->
Collect flows only within `LaunchedEffect`/`collectAsStateWithLifecycle` in the composition. Avoid collecting in `init` for long-lived events; stop at the right lifecycle boundary so we don't process work while paused/destroyed. `viewModelScope` auto-cancels on clear; `lifecycleScope` ties to the UI lifecycle.
```kotlin
LaunchedEffect(Unit) { uiState.collect { /* one-time joins, analytics */ } }
```
Rules: no `GlobalScope` (QUALITY-BAR §3); everything structured; any `Dispatchers.IO`/`Default` call stays at the `data` boundary, not in the VM.
