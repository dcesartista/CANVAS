# Android — data impl (Retrofit + Room + kotlinx.serialization)

> How the data Terms ([data-theory.md](../../../reference/data-theory.md)) are written in native Android.
> **Rules (QUALITY-BAR §1, §2):** Retrofit/Room types live **only** here; `domain` imports none of them. Frontend maps DTOs ⇄ domain via mappers in `data`. Frontend persists locally with Room and talks to the backend with the **generated client** from the OpenAPI contract (nos hand-written DTOs) — though hand-written examples below show the mapping shape.

## DTO <!-- 13 -->
Network models serialized with **kotlinx.serialization** (`@Serializable`) and Room rows as `@Entity` classes. DTOs are plain: no behavior, no domain logic, and never type `android.*`; `data` classes with `@SerialName` for snake_case contract fields.
```kotlin
@Serializable
data class ProductDto(
  @SerialName("id") val id: String,
  @SerialName("price_minor") val priceMinor: Long,
  @SerialName("currency") val currency: String,
  @SerialName("title") val title: String,
)
```
With the generated client the DTOs arrive ready-made; with hand-written sources keep field names exact and `ignoreUnknownKeys = true` in the JSON builder for forward compatibility.

## Room Entity <!-- 23 -->
A `@Entity` row for offline persistence. Add `@PrimaryKey`, indices, and `@ForeignKey` where integrity matters (QUALITY-BAR §2) and `autoGenerate` only for real surrogate keys.
```kotlin
@Entity(
  tableName = "products",
  indices = [Index(value = ["categoryId"])],
  foreignKeys = [ForeignKey(
    entity = CategoryEntity::class,
    parentColumns = ["id"], childColumns = ["categoryId"],
    onDelete = ForeignKey.CASCADE,
  )],
)
data class ProductEntity(
  @PrimaryKey val id: String,
  val title: String,
  val priceMinor: Long,
  val currency: String,
  @ColumnInfo(name = "category_id") val categoryId: String?,
  val updatedAt: Long,
)
```
Room supports `@Embedded` and `data class` relations via `@Relation` for joined read models; every schema change requires a forward-only `Migration` and an exported schema JSON for testing (§ Migration).

## DAO <!-- 15 -->
A `@Dao` interface of suspend / `Flow` queries. Observation returns `Flow` (SSOT streaming); writes are `suspend`. Multi-statement writes go inside `@Transaction` so a partial failure rolls back.
```kotlin
@Dao
interface ProductDao {
  @Query("SELECT * FROM products WHERE id = :id") fun observe(id: String): Flow<ProductEntity?>
  @Query("SELECT * FROM products ORDER BY updatedAt DESC") fun observeAll(): Flow<List<ProductEntity>>
  @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun upsertAll(rows: List<ProductEntity>)
  @Delete suspend fun delete(e: ProductEntity)
  @Transaction @Query("SELECT * FROM categories WHERE id = :id")
  fun observeWithProducts(id: String): Flow<CategoryWithProducts?>
}
```
Never call DAO from the main thread implicitly — Room offloads suspend/`Flow` to its own executor; guard heavy joins with indexes.

## Mapper <!-- 19 -->
Pure functions converting DTO/Room row → domain and back. Both directions are needed (network→domain when reading, domain→id/entity when writing). Keep them as top-level functions or extension functions in `data`; no Android imports.
```kotlin
fun ProductDto.toDomain() = Product(
  id = ProductId(id),
  title = title,
  price = Money.of(priceMinor, Currency.getInstance(currency)),
)
fun ProductEntity.toDomain() = Product(
  id = ProductId(id), title = title,
  price = Money.of(priceMinor, Currency.getInstance(currency)),
)
fun Product.toEntity() = ProductEntity(
  id = id.value, title = title, priceMinor = price.minorUnits,
  currency = price.currency.currencyCode, updatedAt = System.currentTimeMillis(),
)
```
Mapping is the only place DTO/entity fields become domain values; `Currency.getInstance`/VOs validate here so domain never sees invalid input.

## Data Source <!-- 14 -->
One per origin: a **Remote** source (Retrofit API / generated client) and a **Local** one (Room DAO). Sources return DTOs/rows and hold no business logic; they model the byte/row boundary only.
```kotlin
interface ProductRemote {           // wrap the generated client
  suspend fun list(cursor: String?): ProductListDto
  suspend fun get(id: String): ProductDto
}
class ProductRemoteImpl(private val api: GeneratedProductsApi) : ProductRemote {
  override suspend fun list(cursor: String?) = api.listProducts(cursor)   // generated
  override suspend fun get(id: String) = api.getProduct(id)
}
```
The **Local** source is usually the DAO directly; wrap it when you want cache timestamps or write-through policy at the source level rather than the repo.

## DataStore <!-- 18 -->
**Proto DataStore** is the store for preferences and small typed app state (QUALITY-BAR §2) — never `SharedPreferences`, which has no transactional guarantee, no typing, and a blocking read on the main thread. A schema-backed store gives a typed object, an atomic `updateData`, and a `Flow` the repository layer can expose like any other source.
```kotlin
val Context.settingsStore: DataStore<Settings> by dataStore(
  fileName = "settings.pb",
  serializer = SettingsSerializer,          // generated from settings.proto
)

class SettingsLocal @Inject constructor(private val store: DataStore<Settings>) {
  val settings: Flow<Settings> = store.data                       // observable, typed
  suspend fun setTheme(mode: ThemeMode) =
    store.updateData { it.toBuilder().setTheme(mode).build() }     // atomic read-modify-write
}
```
Reads are a `Flow`, so a preference change propagates like any other data change — no manual listener, no stale copy held in a ViewModel.

**Secrets never go here in plaintext.** Access/refresh tokens are encrypted at rest with a Keystore-backed key (see `## Network & Auth` and `security-impl.md` → `## Secure Token Storage`); `security-crypto`/`EncryptedSharedPreferences` is deprecated and must not be introduced. DataStore holds preferences; the token store holds credentials, and the two are not the same file.

## Repository Implementation <!-- 22 -->
`@Inject constructor` class that implements the domain interface, composing remote + local + mappers into an **offline-first SSOT**: always emit from Room immediately, then refresh from the network and write through. Errors map to domain `Result`/`DomainError`.
```kotlin
class DefaultProductRepository @Inject constructor(
  private val remote: ProductRemote,
  private val dao: ProductDao,
  private val connectivity: ConnectivityChecker,
) : ProductRepository {
  override fun observe(id: ProductId) = dao.observe(id.value).map { it?.toDomain() }

  override suspend fun refresh(id: ProductId): Result<Product> =
    runCatching { remote.get(id.value).toDomain() }
      .onSuccess { dao.upsertAll(listOf(it.toEntity())) }            // write-through
      .fold(onSuccess = { Result.success(it) },
            onFailure = { Result.failure(DomainError.Network(it)) })

  override fun observePage(cursor: String?) =
    dao.observeAll().map { Page(it.map(ProductEntity::toDomain), cursor) }
}
```
When the network is unreachable the Room `Flow` still serves the last-known-good data — that is the offline-first contract. Never catch and swallow; surface `DomainError`s only.

## Unit of Work <!-- 16 -->
For a multi-row write with an all-or-nothing contract use a Room `@Dao` method marked `@Transaction` (or a `@Transaction` `suspend` body). This guarantees atomicity across the statements in the method.
```kotlin
@Dao
interface CartDao {
  @Transaction
  suspend fun replaceCart(userId: String, items: List<CartItemEntity>) {
    clearUser(userId)
    items.forEach { insert(it) }
  }
  @Query("DELETE FROM cart_items WHERE userId = :userId") suspend fun clearUser(userId: String)
  @Insert suspend fun insert(item: CartItemEntity)
}
```
Room semantics: delete-then-insert inside `@Transaction` keeps a partially-failed "replace" from leaving a corrupt cart. Gaps allowed: keep `update`/`production.upgrade` minimal.

## Network & Auth <!-- 12 -->
OkHttp client with a **Bearer interceptor** attaching the access token and an `Authenticator` that refreshes on **401** (single-flight) then retries; tokens live in a **Keystore-backed Tink store** (not deprecated `EncryptedSharedPreferences`), never plain prefs (QUALITY-BAR §4, security-impl).
```kotlin
class AuthInterceptor(private val store: TokenStore) : Interceptor {
  override fun intercept(chain: Interceptor.Chain) = chain.proceed(
    chain.request().newBuilder()
      .apply { store.accessToken()?.let { header("Authorization", "Bearer $it") } }
      .build())
}
```
Map transport failures (`SocketTimeoutException`, `HttpException`) to `DomainError.Network`/`SessionExpired` in the remote source so no HTTP type reaches the domain.

## Migration <!-- 14 -->
Forward-only `Migration` objects bump `version`; never `.fallbackToDestructiveMigration()` in production. Export schema JSON (`room.schemaLocation`) into `schemas/` and commit it for Room migration tests.
```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {
  override fun migrate(db: SupportSQLiteDatabase) {
    db.execSQL("ALTER TABLE products ADD COLUMN category_id TEXT")
    db.execSQL("CREATE INDEX idx_products_category ON products(category_id)")
  }
}
Room.databaseBuilder(ctx, AppDatabase::class.java, "app.db")
  .addMigrations(MIGRATION_1_2).build()
```
`AutoMigration` (with `@AutoMigration(from=1,to=2)` + specs) covers simple additive changes; keep explicit migrations for anything non-trivial and test each one against the exported schema.

## Result Wrapper <!-- 14 -->
The data layer normalizes every boundary outcome into a `Result`/sealed either type so the domain never sees bare exceptions as control flow (QUALITY-BAR §2). One-shot network calls return `Result<T>`; streams emit domain values directly with failures represented as state, not thrown.
```kotlin
sealed interface ApiOutcome<out T> {
  data class Ok<T>(val data: T) : ApiOutcome<T>
  data class Err(val error: DomainError) : ApiOutcome<Nothing>
}
suspend inline fun <T> safeCall(block: () -> T): ApiOutcome<T> =
  try { ApiOutcome.Ok(block()) }
  catch (e: HttpException) { ApiOutcome.Err(DomainError.Network(e)) }
  catch (e: CancellationException) { throw e }   // never swallow cancellation
  catch (e: Exception) { ApiOutcome.Err(DomainError.Unknown(e)) }
```
Re-throwing `CancellationException` is critical — swallowing it breaks structured concurrency and cancels the parent scope silently.
