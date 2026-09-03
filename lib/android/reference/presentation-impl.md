# Android — presentation impl (Compose + StateFlow + Hilt)

> How the presentation Terms ([presentation-theory.md](../../../reference/presentation-theory.md)) are written in native Android, per Google's [App Architecture Guide](https://developer.android.com/topic/architecture) and [UDF](https://developer.android.com/topic/architecture/ui-layer#udf).
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

## UI State <!-- 26 -->
An immutable `data class` whose **loadable subject is a `ScreenState<T>`**, not a set of parallel flags. All fields `val`; use `.copy()` for updates; state is screen-scoped and holds only what the screen renders.
```kotlin
data class ProductListUiState(
  val products: ScreenState<List<Product>> = ScreenState.Loading,   // the phase
  val categories: List<String> = emptyList(),                       // ambient, not a phase
  val selectedCategory: String? = null,
) : @Immutable UiState
```
`ScreenState` (ink-basic `layout` package) is `Loading` · `Empty(reason)` · `Error(message)` · `Content(value)`. The ViewModel maps outcomes onto it; the screen renders it via `CanvasStateHost` and never decides a phase itself.

**Never do this:**
```kotlin
// ❌ parallel fields — permits "loading and error at once", and every screen then
//    invents its own precedence rule. Empty becomes invisible: `items.isEmpty()` is
//    indistinguishable from "not loaded yet".
data class ProductListUiState(
  val loading: Boolean = false,
  val items: List<Product> = emptyList(),
  val error: String? = null,
)
```
Not every field is a phase — data the screen shows *alongside* the subject (filter chips, the signed-in user) stays a plain field. One phase per loadable subject.

Annotate `@Immutable` (Compose) so recomposition skips stable fields.

## One-Shot Event <!-- 13 -->
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

## Unidirectional Data Flow <!-- 12 -->
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

## Material 3 Theme <!-- 16 -->
Theming is a Compose `@Composable` wrapper over `MaterialTheme`. CANVAS apps do **not** hand-write a theme — they consume the swappable UI library **`ink-basic`** (the Android realization of the agnostic Palette contract). `CanvasTheme` from `com.canvas.ink.basic.palette` supplies a complete light/dark/highContrast palette and the M3 bridge (color scheme + typography) mapped from T3 semantic tokens:
```kotlin
import com.canvas.ink.basic.palette.CanvasTheme
import com.canvas.ink.basic.palette.DefaultPalette
import com.canvas.ink.basic.palette.LocalSemanticTokens

@Composable
fun AppRoot() {
    CanvasTheme {            // CanvasTheme(palette = ..., darkTheme = ..., highContrast = ...)
        AppNavHost()
    }
}
```
Wrap `MainActivity.setContent { CanvasTheme { AppNavHost() } }`. To rebrand, pass a different `Palette` (swappable) — components are **not** re-themed in place. All colors/sizes reach components as T3 semantic tokens via `LocalSemanticTokens`; never raw hex/Dp in components ([QUALITY-BAR](../../../QUALITY-BAR.md) §5).

## ink-basic <!-- 9 -->
`ink-basic` is a separate Android library (`com.canvas.ink.basic`) holding the swappable default "look": the token layer (T3 semantics), `DefaultPalette` for each mode, `CanvasTheme`, and the component set. Screens **build only from these components** — never raw `MaterialTheme`/M3 widgets or hand-rolled theme:
- Containers: `CanvasCard`, `CanvasTopBar` (64dp), `CanvasBottomNav`(+`NavDest`), `CanvasTabRow`, `CanvasListItem`
- Inputs/actions: `CanvasButton`, `CanvasButtonSecondary`, `CanvasTextField`
- Feedback/states: `CanvasEmptyState`, `CanvasErrorState`, `CanvasSnackbar`, `CanvasProgress`
- Type bridge: `TextFromType` → `TextStyle` from `TypeStyle` tokens (use instead of raw `TextStyle(...)`)

Pull it in as a dependency (composite build / submodule or published Maven — see `ink-basic/CONSUMING.md`). The contract these realize lives in the agnostic sibling **Palette** repo (`docs/0001-ui-token-contract.md`, `docs/0002-component-inventory.md`); CANVAS owns the non-themeable core-correctness floor only.

## ink-basic self-check <!-- 26 -->
CANVAS is the tool that *builds* the UI, so it enforces the seam itself — no separate linter needed. After writing a screen, **`Grep` the generated file and reject it** if any violation below appears; fix and re-verify before reporting done (mirrors the build/test gates). These are the only valid escape hatches and must not be used lightly:
1. **Raw M3 widget instead of a `Canvas*` component** — a call to `Button(`, `OutlinedButton(`, `OutlinedTextField(`, `Card(`, `TextField(`, `TopAppBar(`, `NavigationBar(`, `TabRow(`, `Snackbar(`, `LinearProgressIndicator(` / `CircularProgressIndicator(`, `Divider(`/`HorizontalDivider(`. Use the ink-basic names instead (`CanvasButton`, `CanvasTextField`, `CanvasCard`, `CanvasTopBar`, `CanvasBottomNav`, `CanvasTabRow`, `CanvasSnackbar`, `CanvasProgress`). Only the **layout** primitives (`Column`, `Row`, `LazyColumn`, `Box`, `Spacer`, `Surface`) may remain raw — **`Scaffold` no longer may**; use `CanvasScreenScaffold` (see `## Screen archetypes`).
2. **Raw primitive color/hex in a component** — a literal `Color(0x...` or `Color.Red`/`Color.White` used as fill/text/border/bg. Use a T3 semantic color via `LocalSemanticTokens` (e.g. `t.color.textPrimary`, `t.color.bgSurface`, `t.color.error`), never a hex literal.
3. **Raw `dp` where a token exists** — `padding(16.dp)`, `height(64.dp)`, `size(48.dp)` etc. for spacing/elevation/radius/sizing. Use `t.space.*`, `t.radius.*`, `t.elevation.*`, `t.sizing.*`. (Hairline strokes `1.dp` borders/dividers and `0.dp` gaps are accepted.)
4. **Bare `MaterialTheme.typography.*` / `MaterialTheme.colorScheme.*`** — UI must come from ink-basic tokens (`TextFromType` or the component's own text). This also catches a missing `CanvasTheme` root (which is what populates `LocalSemanticTokens`).
5. **Raw `Scaffold(`** — the page frame is `CanvasScreenScaffold`, which owns the regions and resolves page inset to `space.layout.page`.
6. **Hand-rolled phase branching** — a `when {` or `if/else` in a screen that switches on `state.loading` / `state.error != null` / `isEmpty()`. Phases are `ScreenState` and are rendered by `CanvasStateHost`. This is the highest-value check: it is what produced nine screens with four different loading treatments, four error treatments, and three that rendered nothing when empty.
7. **A missing empty phase** — a `list`-archetype screen whose state cannot express empty. Empty is an outcome, not an oversight.
8. **An unkeyed lazy list** — `LazyColumn` written directly instead of `CanvasListBody`, whose `key` parameter is mandatory.
9. **Page padding invented locally** — a screen applying its own `padding(t.space.md)` at page level instead of using the padding `CanvasScreenScaffold` hands it.

Anti-pattern example the self-check must reject:
```kotlin
// ❌ REJECT — raw M3 + hardcoded hex + raw dp
Button({ onClick() }) { Text("Go", style = MaterialTheme.typography.titleMedium) }
Box(Modifier.padding(16.dp).background(Color(0xFF4F46E5))) { ... }
```
```kotlin
// ✅ PASS — ink-basic, token-sourced
CanvasButton("Go", onClick = {})
val t = LocalSemanticTokens.current
Box(Modifier.padding(t.space.md).background(t.color.accentPrimary)) { ... }
```
If the screen legitimately needs behavior ink-basic lacks, **compose it from existing `Canvas*` components** rather than dropping to raw M3. Only a genuinely new compound should be added to ink-basic (and then to the Palette inventory), never hand-rolled in the screen.

## Screen archetypes <!-- 39 -->
Structure is a contract, not a per-screen decision (Palette **ADR-0003**). Every screen **declares an archetype** and is built from the `com.canvas.ink.basic.layout` package rather than assembling regions by hand.

| Archetype | Frame | Body | Phases required |
|---|---|---|---|
| `list` | `CanvasScreenScaffold` | `CanvasListBody` (mandatory `key`) | loading · empty · error · content |
| `detail` | `CanvasScreenScaffold` | `verticalScroll` column, or `CanvasSection`s | loading · error · content (no empty) |
| `form` | `CanvasScreenScaffold` | `CanvasFormBody` (applies the keyboard inset) | loading · error · content (no empty) |

`feed` and `wizard-step` are **recipes**, not archetypes — compose them from the above (see `screen-recipes.md`). A screen named for a business noun is always a recipe.

**The phase type.** UI state models phases as `ScreenState<T>` — `Loading` · `Empty(reason)` · `Error(message)` · `Content(value)` — never parallel `loading: Boolean` / `error: String?` fields, which permit "loading and error at once". Map to it in the ViewModel; the screen never decides a phase.

**Form caveat.** For a `form`, the `error` phase means the form could not be *prepared*. A failed **submission** renders as a `CanvasBanner` inside the content — never as the error phase, because that replaces the body and discards what the user typed. A busy submit control **disables**; it is never swapped for a progress indicator, which would remove it from the accessibility tree mid-interaction.

```kotlin
// ✅ list archetype — frame, phases and item identity are all structural
CanvasScreenScaffold(
    topBar = { CanvasTopBar(title = "Products") },
) { padding ->
    CanvasStateHost(state = state.products, onRetry = onRefresh) { products ->
        CanvasListBody(items = products, key = { it.id.value }, contentPadding = padding) {
            ProductRow(it)
        }
    }
}
```
```kotlin
// ❌ REJECT — hand-rolled frame and phases; no empty branch at all
Column(Modifier.fillMaxSize()) {
    CanvasTopBar(title = "Products")
    when {
        state.loading -> Box(Modifier.fillMaxSize()) { CanvasProgress() }
        state.error != null -> Box(Modifier.fillMaxSize()) { Text(state.error) }
        else -> LazyColumn { items(state.products) { ProductRow(it) } }
    }
}
```

## State Hoisting <!-- 8 -->
Request state (and any state with lifecycle needs) is hoisted to the ViewModel and passed down; local, ephemeral UI state (text field draft, expansion toggles) stays in the composable via `rememberSaveable`. Hoist the *minimum*: lift state only until it's needed by siblings or for persistence.
```kotlin
var query by rememberSaveable { mutableStateOf("") }       // ephemeral, survives config
val visibleItems by remember(state.items) { derivedStateOf { state.items.filter { it.matches(query) } } }
```
`rememberSaveable` survives configuration changes via the saved-state registry; `remember` does not — choose per data lifetime.

## Lifecycle & Collection <!-- 6 -->
Collect flows only within `LaunchedEffect`/`collectAsStateWithLifecycle` in the composition. Avoid collecting in `init` for long-lived events; stop at the right lifecycle boundary so we don't process work while paused/destroyed. `viewModelScope` auto-cancels on clear; `lifecycleScope` ties to the UI lifecycle.
```kotlin
LaunchedEffect(Unit) { uiState.collect { /* one-time joins, analytics */ } }
```
Rules: no `GlobalScope` (QUALITY-BAR §3); everything structured; any `Dispatchers.IO`/`Default` call stays at the `data` boundary, not in the VM.
