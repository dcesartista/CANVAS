# Screen recipes

> Domain screens as **compositions**, never as components. A screen named for a business noun
> — `product-list`, `checkout` — is a recipe: an archetype (Palette ADR-0003) with its slots
> filled by domain content. Recipes live here in prose. They never ship in ink-basic, because
> a design system whose units are business nouns is coupled to one product's domain and stops
> being swappable.

Read with `lib/android/reference/presentation-impl.md` → `## Screen archetypes`.

## How to read a recipe <!-- 9 -->

Each recipe names its **archetype**, its **shell**, and how its **slots** are filled. It does
not describe layout — that is the ink's, and two inks will render the same recipe very
differently. The recipes below are drawn from two unrelated commercial kits, and where they
disagree that disagreement is recorded rather than resolved: it is evidence about what varies.

---

## `product-list` <!-- 17 -->

| | |
|---|---|
| Archetype | Collection · Page shell |
| `item.title` | product name |
| `item.supporting` | brand *(editorial)* or description *(marketplace)* |
| `item.price` | formatted by the app; the ink never does currency maths |
| `item.priceCompare` · `discountLabel` | marketplace only |
| `item.rating` | marketplace only |
| `empty` | distinguish **filtered** from **unfiltered**: `Empty("Nothing in $category")` vs `Empty()` |
| `error` | always retryable |

**Observed divergence:** the editorial kit ships title + price and nothing else; the
marketplace kit fills every optional slot. Same recipe. If your app has no rating data, the
slot is simply absent — that is not a defect.

## `product-detail` <!-- 11 -->

| | |
|---|---|
| Archetype | Detail · Page shell |
| Bands | `media → identity → options → commit → support → related` |
| `commit` | one action *(editorial: add to basket)* or two co-equal *(marketplace: cart + buy now)* |
| `empty` | not applicable — a product that does not exist is `Error("Product not found")` |

**Not yet buildable.** Needs media carousel, swatch picker and disclosure.

## `cart` <!-- 7 -->

| | |
|---|---|
| Archetype | Review · Overlay shell |
| `empty` | first-class, and **actionable**: the pinned region persists and its action changes from "buy now" to "continue shopping". Use `emptyAction` |

## `checkout` <!-- 11 -->

| | |
|---|---|
| Archetype | Review · Page shell |
| Flow | single review *(editorial)* or a multi-step **flow** *(marketplace: review → payment → order → confirm)* |
| submission failure | banner inside `content`, never the `error` phase — that would discard the address just typed |

**Flow is a wrapper, not an archetype.** It supplies step position and back/next; each step is
an ordinary Review, Form or Picker.

## `search` <!-- 11 -->

| | |
|---|---|
| Archetype | Search entry *(Overlay)* → results are a **Collection** |
| `empty` | carries two meanings — pre-search idle and no-matches. Both are `Empty(reason)` |

**Observed divergence worth knowing:** one kit has a dedicated search overlay; the other has no
search screen at all, only a persistent header field feeding the Collection. Whether search is
a screen may itself be an ink-level decision.

## `home` (feed) <!-- 9 -->

| | |
|---|---|
| Archetype | Feed · Page shell |
| `sections[]` | editorial: hero, new-arrivals grid, brand strip, collections, video, social. marketplace: promo carousel, deal-of-day, product rails, sponsored |

**Not yet buildable.** Needs hero, rails and promo bands.

## `settings` <!-- 7 -->

| | |
|---|---|
| Archetype | Form · Page shell |
| phases | content-only in practice — nothing loads, nothing submits. Do **not** add a phase host that can only ever render one phase |

## `auth` <!-- 12 -->

| | |
|---|---|
| Archetype | Auth · **Focused** shell |
| navigation | on success, navigate from a `LaunchedEffect` — **never from composition**, which re-fires on every recomposition |
| submit | disables while busy; never replaced by a spinner, which removes it from the accessibility tree mid-interaction |

**Not yet buildable.** Needs secure field and social-auth row.

---

## Adding a recipe <!-- 6 -->

Write it here first. A recipe becomes an **archetype** only when two independent external
references share its structure — not when two screens in one app happen to. Deriving
archetypes from screens the system itself generated is circular and was the mistake that
required ADR-0003 to be rewritten.
