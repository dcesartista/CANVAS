# Presentation — theory

> What the presentation/UI layer IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/presentation-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §1, §5.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

The presentation layer renders domain/use-case output and captures user intent — nothing else. It is a **pure function of state**: given the same state object, it draws the same screen. All logic lives in state holders (ViewModels) that reduce user events into new state; the UI contains no business decision and no domain-model mutation ([Google UI layer](https://developer.android.com/topic/architecture/ui-layer)).

## Unidirectional Data Flow <!-- 3 -->
**State flows down, events flow up** (QUALITY-BAR §1): the UI is `render(state)`, and user actions are events the ViewModel reduces into *new* state. There is no two-way binding, no screen editing data directly, no state held in the composable tree. UDF is what makes state reproducible, testable, and safe across configuration changes — the mandated wiring of QUALITY-BAR §1 ([UDF](https://developer.android.com/topic/architecture/ui-layer#udf)).

## UI State <!-- 3 -->
A **single immutable object describing everything the screen renders** — loading · data · content · error — exposed as one observable property. It is updated by producing a new instance, never mutated in place (QUALITY-BAR §1). Model mutually-exclusive phases as a sealed type so the compiler rules out "loading and error at once"; parallel fields are a bug waiting to happen.

## Screen <!-- 3 -->
The **declarative UI surface**: it observes the ViewModel's state, renders it, and emits user events to the ViewModel. It is **dumb** — no business logic, no domain types beyond what state already carries, no navigation decisions beyond what an event triggers. A screen is exactly `render(state)`; anything else living in it is a smell, not a feature.

## ViewModel <!-- 3 -->
A **screen-scoped state holder** that owns UI state, reduces user events, and calls use cases — holding **no view/framework references** and surviving configuration changes (QUALITY-BAR §1). It never pushes one-off results "up" (see One-Shot Event). Reusable sub-pieces use plain state holders, not ViewModels: one ViewModel per destination/feature, not per widget ([ViewModel](https://developer.android.com/topic/architecture/ui-layer#viewmodels)).

## State Hoisting <!-- 3 -->
**Lifting state to the nearest common ancestor** that needs to read or write it ([Compose state](https://developer.android.com/develop/ui/compose/state)): stateless composables receive value + callbacks, stateful ones own them. Stateless composables are reusable and testable; hoisting to the ViewModel gives config-change survival. A composable that implicitly "knows" data it never received is heavily coupled and unfixable at the call site.

## State Collection <!-- 3 -->
The screen **collects the ViewModel's state stream lifecycle-aware** — active only while on-screen, restarted on re-entrance. Collection is distinct-until-changed (avoid redundant renders), on the right dispatcher (never the main-thread observer doing off-main work), and never free-standing where a built-in scope exists. Wrong lifecycle collection is the classic cause of both wasted renders and missed updates.

## One-Shot Event <!-- 3 -->
An **ephemeral signal the UI consumes once** — a snackbar message, a "navigate to checkout" — that must not reappear on rotation (QUALITY-BAR §1). State is for *what is now true*; events are for *what happened once*. They travel through a single-use channel that is drained exactly once, fired by the state holder at the boundary. Confusing the two is the top presentation bug.

## Immutability <!-- 3 -->
UI state is **fully immutable**: constructing new instances on change gives the renderer cheap, correct diffing and makes state safe to share across threads (QUALITY-BAR §5). Mutable state smuggled into a data class (`var`, mutable collections) breaks recomposition skipping and produces stale screens. If a field "must" mutate in place, the design is wrong — rebuild it.

## State Persistence <!-- 3 -->
State survives **configuration changes and process death** (QUALITY-BAR §1). Config-change survival is the ViewModel's own job; process-death survival needs a saveable mechanism (`rememberSaveable`-equivalent / saved-state holder). Saved state is for transient UI positions and small inputs; durable truth lives in the data layer. A structure saved with no restore strategy is not persistence.

## User Event <!-- 3 -->
**Intention carried up**: a click, a scroll, a text change — modeled as named events the UI emits, not direct calls into domain/data (QUALITY-BAR §1). An event is a *what*, not a *how*: "submitForm", never "callRepository().save()". This indirection lets the state holder control access, validation, and feedback, and lets tests drive the UI with real user-shaped events.

## Lifecycle Awareness <!-- 3 -->
**Work follows the screen's lifecycle** (QUALITY-BAR §1): collection stops when the UI leaves, and active work is scoped so a backgrounded screen doesn't burn battery or network. The platform provides the scopes (`viewModelScope`/`lifecycleScope`); the rule is to let them own the coroutines and never leak a scope upward. UI that "keeps running" after leaving the screen is a battery-and-memory defect.

## Validation Location <!-- 4 -->
**User input is validated after the event, in the state holder** — not in a separate mutable layer the screen juggles. The result (valid · invalid-reason) becomes **state**, so the screen renders it and accessibility announces it. Instant per-field feedback and async server validation coexist here; the UI never decides "this is invalid" on its own.

