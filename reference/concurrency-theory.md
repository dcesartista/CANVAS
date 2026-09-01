# Concurrency — theory

> What coroutine-based concurrency IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/concurrency-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §3.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Android concurrency is **coroutines + Flow** (QUALITY-BAR §3): lightweight suspending work managed by structured concurrency — every coroutine lives in a scope, every scope has a lifetime, and cancellation travels top-down. This is the model [the Kotlin coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html) describes: the app must never outlive its scopes and must never block the main thread.

## Structured Concurrency <!-- 3 -->
The rule that **every coroutine runs in a scope whose lifetime its work cannot outlive** ([structured concurrency](https://kotlinlang.org/docs/coroutines-basics.html#structured-concurrency)): launch a child only inside a parent, and the parent completes when its children do. No orphaned goroutines, no fire-and-forget fibers. This turns cancellation and leak-freedom from "be careful" into a language-enforced guarantee — the foundation of the whole layer.

## Coroutine <!-- 3 -->
A **suspendable unit of work** — the language's answer to a thread that frees its carrier thread whenever it suspends. Thousands can coexist on one thread; a suspension point resumes work on whatever dispatcher the context says. Coroutines make concurrency cheap enough to use *per unit of work* (per download, per query) rather than hand-pooling "background threads".

## CoroutineScope <!-- 3 -->
A **defined lifetime + context in which coroutines are launched** — the unit of "when should these tasks end". Scopes tie to real lifetime boundaries (a screen, a feature) and create children within a job. Launching into an unstructured scope, or creating one with no clear owner, is what leaks work past its screen. The [official guide](https://kotlinlang.org/docs/coroutines-basics.html) treats scope construction as a deliberate act.

## Child Jobs & Hierarchy <!-- 3 -->
A scope's children form a **tree (parent → child)** and termination is structural: **cancelling any node cancels its subtree; failing a child fails the subtree** (kotlinx.coroutines semantics). This hierarchy is how "cancel the page load" cascades down to the image fetches underneath. Launch-and-ignore children, then hoping they die, breaks the tree's guarantees.

## Cancellation <!-- 3 -->
**Work stops on command, cooperatively**: when a scope/job is cancelled, its children's coroutines resume with `CancellationException` and unwind via `finally` ([cancellation guide](https://kotlinlang.org/docs/cancellation-and-timeouts.html)). Cancellation is not an error to catch-and-swallow; silencing it breaks the parent's tree. "Clean up on cancel, let it propagate otherwise" is the whole discipline; timeouts are just cancellation (`withTimeout`).

## Cooperative Cancellation <!-- 3 -->
A coroutine **responds to cancellation only at suspension points**: CPU-bound loops that never suspend must cooperate — check `isActive`/`ensureActive()` ([cancellation and timeouts](https://kotlinlang.org/docs/cancellation-and-timeouts.html)). Work that ignores cancellation gets nothing; it finishes late, holding a cancelled scope's place. Blocking a thread inside a coroutine (a `Thread.sleep`, a blocking call) is doubly bad: it blocks *and* disables cooperation.

## Dispatcher <!-- 3 -->
The **executor policy for a coroutine**: which thread(s) carry which work — the main/UI thread for render-touching, the IO pool for network/disk, `Default` for CPU (QUALITY-BAR §3). Dispatchers are **injected and swapped in tests** (virtual time); a hard-coded dispatcher deep in a class makes it untestable. Context switches belong at the edges (in data), not scattered through use cases ([dispatchers](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html)).

## Context <!-- 3 -->
The **bundled carrier of coroutine settings** (dispatcher, job, name, elements) that travels the suspension tree. `withContext(Dispatchers.IO)` *switches* the dispatcher for a block — the idiom for "this suspend fun talks to disk" without perverting the caller's context. Freely re-declaring context is how off-main leaks into the domain; keep the domain context-agnostic and put dispatch at data boundaries.

## Flow <!-- 3 -->
A **cold stream of values over time** (`Flow<T>`) — the reactive spine for the data → presentation path and any repeated work (update streams, paging, event sequences) ([Flow guide](https://kotlinlang.org/docs/flow.html)). Cold means each collector gets its own fresh run; operators stay at the data/presentation edge, and the domain exposes flows as plain return types without threading the framework. Flow replaces hand-rolled queues and callback forests.

## StateFlow vs SharedFlow <!-- 3 -->
Two hot flows chosen by **semantics: state vs events** (QUALITY-BAR §1): `StateFlow` caches **one value**, is distinct-until-changed, and is ideal for UI state collected by one screen at a time. `SharedFlow` broadcasts **ephemeral emissions** to N collectors — the one-shot/event signal (presentation-theory). Picking by semantics prevents the two classic bugs: replaying an event on rotation and missing updates on a non-conflated state stream.

## Backpressure & Conflation <!-- 3 -->
When a producer outruns a consumer, the policy is **explicit** ([flow buffering](https://kotlinlang.org/docs/flow.html#buffering)): `buffer()` queues, `conflate()` drops intermediates (perfect for UI state — rendering every stale frame is worse than rendering the newest), `debounce()`/`sample()` shape chatty streams. In Compose-land the sane default is conflate-ish: latest state wins, because the user wants newest, not inventory.

## Supervision <!-- 3 -->
A **child-failure boundary that does NOT kill the parent** (`supervisorScope`/`SupervisorJob`): one slow sibling may fail while its scope lives on — the right shape for independent loaders on one screen ([exception handling](https://kotlinlang.org/docs/exception-handling.html)). Default `Job` semantics (any child failure cancels the tree) are correct for dependent work; supervision is for independent fan-out. Use flow's `catch`/`onEach` near the consumer so errors become state, not crashes.

## Scope Ownership <!-- 3 -->
Every scope has **one clear owner whose lifetime it mirrors** (QUALITY-BAR §3): the platform provides `viewModelScope`/`lifecycleScope` for screens; feature-level scopes are explicit and owned. `GlobalScope` is forbidden — it is the anti-pattern of orphaned work. "Which scope does this run in?" must always have a one-word answer; if it doesn't, the code is guessing at its own lifetime.

