# Android — navigation impl (Navigation 3, type-safe)

> How navigation Terms ([navigation-theory.md](../../navigation-theory.md)) are written in native Android with **Navigation 3** (`androidx.navigation3`, state-driven, single-activity). Routes are **type-safe** (Kotlin serialization-based `@Serializable` routes, replacing string routes and `composable("path/{id}")`). Navigation Compose 2.x is only a fallback for a deep legacy graph; new graphs are Navigation 3.
> **Rules (QUALITY-BAR §1, §4):** single `MainActivity` + one `NavHost`; navigation driven by UI state/events, never from inside content composables; auth destinations are deny-by-default behind a nav guard.

## Nav Graph <!-- 18 -->
One `NavHost` per screen region, composed from `@Serializable` route objects. Type-safe routes carry strongly-typed arguments (no bundle string keys); create the graph with `composable<T> { }` and navigate with `navController.navigate(T(...))`.
```kotlin
@Serializable data object HomeRoute
@Serializable data class ProductDetailRoute(val productId: String)

@Composable fun RootNavHost(navController: NavHostController = rememberNavController()) {
  NavHost(navController, startDestination = HomeRoute) {
    composable<HomeRoute> { HomeScreen(onOpen = { id -> navController.navigate(ProductDetailRoute(id)) }) }
    composable<ProductDetailRoute> { entry ->
      val route = entry.toRoute<ProductDetailRoute>()
      ProductDetailRoute(route.productId, onBack = { navController.popBackStack() })
    }
  }
}
```
Type-safe routes end the string-matching/`getArgument` fragility: arguments are compile-checked and deserialized with the same kotlinx.serialization used in `data`.

## Screen Router <!-- 12 -->
A top-level branch that maps UI state/events to destinations. Screens never hold the `NavController` for arbitrary navigation; they emit an event and the router/`NavHost` reacts. This keeps navigation testable and decoupled from content.
```kotlin
@Composable fun AppRoot() {
  val navController = rememberNavController()
  val authVm: AuthViewModel = hiltViewModel()
  val authState by authVm.uiState.collectAsStateWithLifecycle()
  RootNavHost(navController, startDestination = if (authState.isLoggedIn) HomeRoute else LoginRoute)
}
```
Start destination is chosen from auth state (see Nav Guard); subsequent auth-driven redirects are emitted as events collected in the router.

## Nav Arguments <!-- 8 -->
Forward declared on the `@Serializable` route class; Navigation 3 encodes them into the route. Use immutable `val`s (no defaults for required args) and pass them via `toRoute<T>()` in the destination.
```kotlin
@Serializable data class SearchRoute(val query: String = "", val cursor: String? = null)
composable<SearchRoute> { entry -> SearchScreen(entry.toRoute<SearchRoute>()) }
```
Optional args get defaults; nullable types encode as absent query params. Never pass objects/`Parcelable` in routes — navigate by id and let the screen observe its own data from the repository.

## Nav Guard <!-- 10 -->
**Deny-by-default** (QUALITY-BAR §4): any authed destination re-checks auth state before it is shown, using a composition-local guard or a `NavHost` start-destination decision. Unguarded routes render `RedirectToLogin` when unauthenticated; navigation is a function of `uiState`, not permissions logic in content.
```kotlin
@Composable fun AuthGuard(destination: @Composable AnimatedContentScope.() -> Unit) {
  val auth by authViewModel().uiState.collectAsStateWithLifecycle()
  if (auth.isLoggedIn) destination() else RedirectToLogin()
}
```
Combine with a `Authenticator` refresh (data layer) so a stale token triggers refresh → relogin, and revoke/clear on logout. Guard is applied at the router level, never inside a single screen's branch.

## Deep Links <!-- 11 -->
App links (`https://host/path`) attached to `@Serializable` routes via `deepLinks = [navDeepLink<Route>("https://host/products/{productId}")]` inside the `composable<T>` builder. Verified domains in asset links open the app directly to that destination.
```kotlin
@Serializable data class DeepProductRoute(val productId: String)
composable<DeepProductRoute>(
  deepLinks = listOf(navDeepLink<DeepProductRoute>
    ("https://example.com/products/{productId}")),
) { entry -> ProductDetailScreen(entry.toRoute<DeepProductRoute>().productId) }
```
Enable via the `<intent-filter>` in `AndroidManifest.xml` plus `assetlinks.json` for the domain; Navigation 3 handles the `PendingIntent`/`Intent` automatically and pops the back stack to the deep target in place.

## Bottom Navigation <!-- 21 -->
Material 3 `NavigationBar` with `NavigationBarItem`s drives a **nested graph** (one top-level route, child screens beneath it). Current destination tracked via `currentBackStackEntryAsState()` to highlight the active tab.
```kotlin
@Composable fun MainScaffold(nav: NavController) {
  val back by nav.currentBackStackEntryAsState()
  val dest = back?.destination
  NavigationBar {
    items.forEach { item ->
      NavigationBarItem(
        selected = dest?.hierarchy?.any { it.hasRoute(item.route::class) } == true,
        onClick = { nav.navigate(item.route) { popUpTo(nav.graph.findStartDestination().id) { saveState = true }
          launchSingleTop = true; restoreState = true } },
        icon = { Icon(item.icon, contentDescription = item.label) },
        label = { Text(item.label) },
      )
    }
  }
}
```
`saveState`/`restoreState` + `launchSingleTop` preserve tab state across switches; `popUpTo(startDestination)` prevents unbounded back-stack growth.

## Nested Graphs <!-- 13 -->
Group related destinations (`Home` → list → detail) into a nested `NavGraph` so back behavior, deep links, and bottom-nav scoping are consistent; a top-level tab IS a nested graph.
```kotlin
NavHost(...) {
  navigation<HomeTab>(startDestination = HomeRoute) {      // nested graph
    composable<HomeRoute> { ... }
    composable<ProductDetailRoute> { ... }
  }
  composable<SettingsRoute> { ... }
}
```
`startDestination` resolves within the nested scope; navigate within a tab, and `popUpTo`/`launchSingleTop` operate on that tab's stack — the pattern behind clean bottom-nav.

## Transitions & Arguments <!-- 10 -->
Wire animations with `enterTransition`/`exitTransition` on `composable<T>` (or a shared `NavHost` default) and read route args before scoping. Keep transitions subtle (`fadeIn`/`slideInHorizontally`) for 60fps; avoid heavy transforms on large lists.
```kotlin
composable<HomeRoute>(
  enterTransition = { fadeIn(animationSpec = tween(220)) },
  exitTransition = { fadeOut(animationSpec = tween(150)) },
) { HomeRoute() }
```
Complex per-screen shared-element transitions stay out of scope here — prefer predictable fade/slide defaults unless a feature explicitly needs them.
