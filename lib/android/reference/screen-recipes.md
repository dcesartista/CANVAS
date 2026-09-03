# Screen recipes

> Domain screens as **compositions**, never as components. A screen named for a business noun
> — `product-list`, `checkout`, `settings` — is a recipe: an archetype (Palette ADR-0003) plus
> domain content. Recipes live here, in prose. They are never added to ink-basic, because a
> design system whose units are business nouns is coupled to one product's domain and stops
> being swappable.

Read with `lib/android/reference/presentation-impl.md` → `## Screen archetypes`.

## How to read a recipe <!-- 7 -->

Each recipe names its **archetype**, what goes in each **region**, what the **phases** mean
for this screen, and anything non-obvious. Everything else follows from the archetype.

---

## `product-list` <!-- 12 -->

| | |
|---|---|
| Archetype | `list` |
| top | `CanvasTopBar` with the catalogue name |
| body | `CanvasListBody`, item = `CanvasCard` with thumbnail · title · category · price |
| header | optional `LazyRow` of `CanvasChip` category filters |
| bottom | none |
| `empty` | distinguish **filtered** from **unfiltered**: `Empty("Nothing in $category")` vs `Empty()`. Same layout, different copy — this is what `reason` is for |
| `error` | always offer retry; a catalogue that failed to load is always retryable |

## `product-detail` <!-- 10 -->

| | |
|---|---|
| Archetype | `detail` |
| top | `CanvasTopBar` + back `CanvasIconButton` |
| body | full-bleed media header, then title · price · rating · description in `CanvasSection`s |
| bottom | **pinned** "Add to cart" — a long description must not push the primary action off-screen |
| `empty` | not applicable. A product that does not exist is `Error("Product not found")` |

## `search` <!-- 9 -->

| | |
|---|---|
| Archetype | `list` |
| top | `CanvasTopBar` + `CanvasSearchBar` — **in the top region**, so it stays put while results scroll |
| body | `CanvasListBody` of result cards |
| `empty` | carries **two** meanings: pre-search idle (`Empty("Type to search")`) and no matches (`Empty("No results for \"$q\"")`). Both are `empty` with a reason — do not invent an `Idle` phase for this |

## `checkout` <!-- 12 -->

| | |
|---|---|
| Archetype | `form`, as a **wizard-step** recipe |
| top | `CanvasTopBar` + `CanvasStepper` showing position |
| body | `CanvasFormBody`; one step's fields at a time |
| bottom | **pinned** Back / Continue. This recipe is why the `bottom` region is in the contract |
| `error` | the **cart** failed to load — checkout cannot start |
| submission failure | `CanvasBanner` inside the body. Never the `error` phase: replacing the body would discard the address the user just typed |
| `empty` | an empty or signed-out cart is `Empty(reason)`, with the reason carrying the fix |

## `ecommerce-home` (feed) <!-- 9 -->

| | |
|---|---|
| Archetype | `list`, as a **feed** recipe |
| top | `CanvasTopBar` |
| body | `CanvasListBody` whose item is a `CanvasSection` wrapping a `LazyRow` rail |
| note | the outer list is lazy and keyed by rail; each rail is keyed by product. Nesting a `LazyRow` inside a `CanvasListBody` item is fine — nesting a *vertical* scroller inside one is not |

## `settings` <!-- 10 -->

| | |
|---|---|
| Archetype | `form` |
| top | `CanvasTopBar` |
| body | `CanvasFormBody` with `fieldSpacing = space.layout.section`, grouped into `CanvasSection`s |
| bottom | none — preferences apply on change |
| phases | in practice content-only: there is nothing to load and nothing to submit. Do not add a phase host that can only ever render one phase |

## `auth` / `login` <!-- 12 -->

| | |
|---|---|
| Archetype | `form` |
| top | `CanvasTopBar` |
| body | `CanvasFormBody`; submit control **disables** while busy, never swapped for a spinner |
| submission failure | `CanvasBanner` at the top of the body |
| navigation | on success, navigate from a `LaunchedEffect` — **never from composition**. Calling a navigation callback in the composable body re-fires on every recomposition |

---

## Adding a recipe <!-- 5 -->

Write it here first. A recipe **graduates to an archetype** only when a second, independent
screen shares its structure (ADR-0003 admission rule) — at which point it moves into ADR-0003
and the layout layer, not before. `feed` and `wizard-step` are both sitting at one instance.
