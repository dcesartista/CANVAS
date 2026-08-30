# Android — DI impl (Hilt)

> How dependency injection Terms ([di-theory.md](../../di-theory.md)) are written in native Android with **Hilt** (compile-time DI over Dagger).
> **Rules (QUALITY-BAR §1, §7):** constructor injection everywhere (`@Inject constructor`); modules wire interfaces → impls via `@Binds`; scoping is deliberate; tests override at the `@Singleton` component (`@TestInstallIn`) or per-test via the generated Hilt test component. No ServiceLocator/globals for app objects.

## Hilt Application <!-- 17 -->
The `Application` is annotated `@HiltAndroidApp` and `MainActivity`/components use `@AndroidEntryPoint`. This generates the root `SingletonComponent` and lets Hilt inject Android framework types into tests and screens.
```kotlin
@HiltAndroidApp
class CanvasApp : Application()
```
```kotlin
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContent { CanvasTheme { AppRoot() } }
  }
}
```
Only one `@HiltAndroidApp` per app; any `@Composable` receiving `hiltViewModel()` needs an `@AndroidEntryPoint` host context.

## Constructor Injection <!-- 10 -->
The default and preferred mechanism (QUALITY-BAR): `class X @Inject constructor(a: A, b: B) : IX`. Hilt satisfies the parameters by resolving them from the component; interfaces need a `@Binds` binding or `@Provides`; concrete unimplemented classes need no module at all.
```kotlin
class DefaultProductRepository @Inject constructor(
  private val remote: ProductRemote,
  private val dao: ProductDao,
) : ProductRepository
```
Prefer it for use cases, repos, ViewModels. Only `@Provides` when a class is an interface, an Android integration point (Retrofit/Room), or needs custom construction — never as the default.

## Modules <!-- 11 -->
Annotated `@Module` with `@InstallIn` limiting it to a component scope. `@Binds` wires an abstraction to an impl; `@Provides` builds framework integrations (OkHttp, Retrofit, Room, kotlinx.serialization `Json`). Everything that needs the same singleton instance is scoped `@Singleton`.
```kotlin
@Module @InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
  @Binds abstract fun bindProductRepo(i: DefaultProductRepository): ProductRepository
  @Binds abstract fun bindCartRepo(i: DefaultCartRepository): CartRepository
}
```
`@InstallIn` scopes matter (QUALITY-BAR §7): `ActivityRetainedComponent` per-activity-retained instances, `ViewModelComponent` per-ViewModel. Keep bindings thin; do construction in `@Provides` only for non-injectable types.

## Provides <!-- 13 -->
For third-party or Android-framework types (Retrofit, OkHttp, Room, `Json`) use `@Provides` returning the interface and scope it `@Singleton` so there is exactly one client/DB/JSON builder per app.
```kotlin
@Provides @Singleton fun provideJson(): Json =
  Json { ignoreUnknownKeys = true; explicitNulls = false; encodeDefaults = true }

@Provides @Singleton fun provideRetrofit(okHttp: OkHttpClient, json: Json): Retrofit =
  Retrofit.Builder().baseUrl(BuildConfig.BACKEND_URL)
    .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
    .client(okHttp).build()
```
`@Provides` funs are named for what they provide (`provide*`) and take their dependencies as params (Hilt provides those). Never `new` objects inside a `@Provides` that Hilt could inject.

## Qualifiers <!-- 13 -->
Distinguish multiple bindings of the same type with `@Qualifier` annotations (`@Named` or a custom qualifier) — e.g. two `OkHttpClient`s (one authed, one plain) or two `Dispatcher`s.
```kotlin
@Qualifier annotation class AuthOkHttp
@Qualifier annotation class PlainOkHttp

@Provides @Singleton @AuthOkHttp fun provideAuthOkHttp(tokenStore: TokenStore): OkHttpClient { ... }
@Provides @Singleton @PlainOkHttp fun providePlainOkHttp(): OkHttpClient { ... }
# injection
class SyncWorker @Inject constructor(@AuthOkHttp private val ok: OkHttpClient) { ... }
```
Define a custom named qualifier rather than scattering string `@Named("x")`; it is type-safe and grep-able. Qualifiers pair with `@Provides`/`@Binds` on the same type.

## Scoping <!-- 9 -->
Match instance lifetime to component lifetime: `@Singleton` (app), Activity-scoped (`@ActivityScoped`), ViewModel-scoped, or unscoped (default — new instance per injection). Test doubles can be unscoped safely.
```kotlin
@Singleton class AppScopeThing @Inject constructor()            // one per app process
@ActivityScoped class Session @Inject constructor()            // one per activity lifecycle
class Unscoped @Inject constructor()                            // new per injection site
```
Wrong scoping is a subtle memory-leak source: never `@Singleton`-scope something that holds an `Activity`/`Context` beyond app scope, and keep `@Inject constructor` classes with no scoping annotation by default.

## Testing Overrides <!-- 11 -->
Tests replace bindings at the root `SingletonComponent` with a fake install, or use Hilt's `@TestInstallIn` for a fake module; per-test overrides bind a fake where the real impl is required.
```kotlin
@TestInstallIn(components = [SingletonComponent::class], replaces = RepositoryModule::class)
@Module abstract class FakeRepositoryModule {
  @Binds abstract fun fakeProductRepo(i: FakeProductRepository): ProductRepository
  @Binds abstract fun fakeAuthRepo(i: FakeAuthRepository): AuthRepository
}
```
`@TestInstallIn(replaces=...)` swaps the module for the whole test class; Robolectric/Hilt test rules (`createAndroidComposeRule`, `HiltAndroidRule`) inject the fakes. Prefer fakes over mocks (QUALITY-BAR §6) and override only the seam under test.
