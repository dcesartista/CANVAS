# Android — testing impl (JUnit5 + Turbine + MockWebServer + Compose)

> How the testing Terms ([testing-theory.md](../../testing-theory.md)) are written in native Android, per the Google [test pyramid](https://developer.android.com/training/testing/fundamentals) (~70/20/10) and QUALITY-BAR §6.
> **Rules:** fakes > mocks; ≥75% coverage on new code (JaCoCo); unit tests on the JVM, integration on Robolectric/in-memory Room, UI with Compose semantics. Google test sizes (`Small`/`Medium`/`Large`) drive placement.

## Unit Test <!-- 14 -->
JVM-only tests for `domain` (pure Kotlin) and `presentation` (ViewModel w/ fakes). Run on the JVM with `runTest` (kotlinx-coroutines-test) and **Turbine** to assert `StateFlow`/`Flow` emissions. No emulator, no instrumented DI.
```kotlin
class CartViewModelTest {
  private val repo = FakeCartRepository()
  private val vm = CartViewModel(repo)
  @Test fun `adding same product increments quantity`() = runTest {
    vm.onAdd(ProductId("p1"))
    vm.uiState.test { withTimeout(1_000) { assertEquals(1, awaitItem().items.single().qty) } }
  }
}
```
Use `StandardTestDispatcher` via `runTest`; inject a `MainDispatcherRule` for dispatchers; never test real network/DB, assert against fakes and pure domain invariants.

## Test Double <!-- 11 -->
Hand-written fakes implementing domain interfaces, reused across unit tests — not a mock framework. One mutable, in-memory implementation per interface lives in `testFixtures` or `test/` and is swapped via Hilt `@TestInstallIn` (see di-impl).
```kotlin
class FakeProductRepository(private val backing: MutableMap<ProductId, Product> = mutableMapOf()) : ProductRepository {
  override fun observe(id: ProductId) = flowOf(backing[id])
  override suspend fun refresh(id: ProductId): Result<Product> =
    backing[id]?.let { Result.success(it) } ?: Result.failure(DomainError.ProductNotFound(id.value))
}
```
Fakes keep tests independent of framework internals and make failure injection trivial (throw from a fake to exercise an error path).

## ViewModel Test <!-- 19 -->
ViewModels are tested on the JVM with a Main dispatcher and fakes; assert state transitions and one-shot events. Provide a `MainDispatcherRule` that swaps `Dispatchers.Main` for `runTest`'s scheduler so `viewModelScope` jobs advance deterministically.
```kotlin
class MainDispatcherRule(val dispatcher: TestDispatcher = UnconfinedTestDispatcher()) :
  TestWatcher() {
  override fun starting(d: Description) { Dispatchers.setMain(dispatcher) }
  override fun finished(d: Description) { Dispatchers.resetMain() }
}
class ProductListViewModelTest {
  @get:Rule val main = MainDispatcherRule()
  @Test fun `emits error when repo fails`() = runTest {
    val vm = ProductListViewModel(FailingRepo())
    vm.onRefresh()
    assertTrue(vm.uiState.value.error != null)
  }
}
```
Turbine's `.test {}` consumes the flow; combined with `UnconfinedTestDispatcher` events are emitted synchronously for `awaitItem()`.

## Repository Test <!-- 15 -->
**Integration** for the data layer: in-memory Room + **MockWebServer** (or the generated client against a local stub server) to verify SQL, mappers, and network handling without a device. Assert DTO→domain mapping and offline-first behavior.
```kotlin
@RunWith(AndroidJUnit4::class) class ProductRepoTest {
  private lateinit var db: AppDatabase
  @Before fun setup() { db = Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).build() }
  @Test fun `observe falls back to cached row offline`() = runTest {
    val repo = DefaultProductRepository(FailingRemote(), Dao(db.productDao()))
    dao.upsertAll(listOf(entity("p1")))
    assertEquals("p1", repo.observe(ProductId("p1")).first()?.id?.value)
  }
}
```
`inMemoryDatabaseBuilder` gives an isolated schema; add all real migrations so the test exercises the actual schema evolution.

## Compose UI Test <!-- 11 -->
Compose UI tests via `createAndroidComposeRule<MainActivity>()` (Hilt-enabled) or `createComposeRule()` for a standalone screen. Assert with **semantics** (contentDescription, roles) not fragile `onNodeWithText`; `performClick`, `onNodeWithContentDescription`.
```kotlin
@get:Rule val composeRule = createAndroidComposeRule<MainActivity>()
@Test fun `renders product then opens detail`() {
  composeRule.onNodeWithContentDescription("product p1").assertIsDisplayed().performClick()
  composeRule.onNodeWithText("Detail").assertIsDisplayed()
}
```
Accessibility semantics double as the test selector (QUALITY-BAR §5, §8): every interactive node exposes a stable description/role so tests and TalkBack agree. Add `testTagsAsResourceId()` and prefer `Modifier.testTag` for list items.

## Room Migration Test <!-- 14 -->
Verify each forward migration against the exported schema JSON (`room.schemaLocation`) using `MigrationTestHelper`; run on the instrumented/`@Config(sdk=[])` Robolectric or device. This catches schema drift before release.
```kotlin
@RunWith(AndroidJUnit4::class) class MigrationTest {
  @get:Rule val helper = MigrationTestHelper(InstrumentationRegistry.getInstrumentation(),
    AppDatabase::class.java, emptyList(), true)
  @Test fun `migrates 1 to 2`() {
    val db = helper.createDatabase(TEST_DB, 1).apply { execSQL("INSERT INTO products...") }
    helper.runMigrationsAndValidate(TEST_DB, 2, true, MIGRATION_1_2)
  }
}
```
Commit the generated `schemas/` directory; `runMigrationsAndValidate` asserts the post-migration schema matches the target version's exported schema exactly.

## Coverage <!-- 11 -->
JaCoCo reports unit + instrumented coverage; enforce **≥75% on new code** (QUALITY-BAR §6) via a Gradle `jacocoTestReport` + `ratchet` gate in CI, failing the build below the floor.
```kotlin
jacoco { toolVersion = "0.8.12" }
tasks.withType<JacocoReport>().configureEach {
  classDirectories.setFrom(fileTree(layout.buildDirectory.dir("tmp/kotlin-classes/debug")) { exclude("**/*Dto*") })
  reports { xml.required.set(true); html.required.set(true) }
}
```
Coverage floors apply to domain+data logic (pure Kotlin, cheap to cover) and to new branches — exclude generated client/DTO code and Compose UI from the floor.
