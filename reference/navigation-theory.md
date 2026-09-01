# Navigation — theory

> What navigation IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/navigation-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §1, §4.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Navigation is **state, not action**. Where the user is amounts to a value the app owns and can render, save, restore, and test; moving between screens is an event that produces a new value. Treating navigation as a sequence of imperative jumps issued from inside content is what makes back behavior unpredictable, deep links special-cased, and authorization checks skippable — the failure QUALITY-BAR §1 and §4 exist to prevent.

## Destination <!-- 3 -->
**One addressable place in the app.** A destination is identified by a typed value carrying exactly the arguments it needs, so an unreachable or under-specified screen is a compile-time error rather than a blank render. Untyped string addresses defer that failure to runtime and lose every argument guarantee.

## Back Stack <!-- 3 -->
**The ordered history of destinations** — the app's memory of how the user arrived. It is owned state: inspectable, serializable, restorable across process death. Back is not "undo the last call"; it is popping a structure the app can reason about, which is why history that lives only in framework internals cannot be tested or restored.

## Navigation Event <!-- 3 -->
**An intent to move, emitted upward** — never a navigation call made inside content. A screen says "the user chose this item"; something above decides what that means. This keeps screens reusable in any position, testable without a navigator, and prevents the same transition being reimplemented differently at three call sites.

## Route Argument <!-- 3 -->
**Typed data a destination requires to render.** Arguments are part of the destination's identity, passed as values rather than fetched from shared mutable state. Required arguments carry no defaults — a default on a required argument converts a missing-data bug into a screen that renders something wrong.

## Nav Guard <!-- 3 -->
**Deny-by-default gating driven by state** (QUALITY-BAR §4). A protected destination is unreachable unless an explicit condition permits it; it is never "safe" merely because the only link to it sits behind a login screen. The guard is evaluated as part of resolving the destination, not after the screen has begun rendering — a protected screen that draws once before redirecting has already leaked.

## Single Source of Truth <!-- 3 -->
**One authority for current location.** Nested graphs, tab state, and dialogs all resolve from the same structure; a second parallel notion of "where we are" guarantees divergence. When location is single-sourced, restoring state is replaying one value.

## Nested Graph <!-- 3 -->
**A group of destinations sharing an entry point, lifetime, or guard.** Grouping makes a shared condition expressible once for the whole region rather than repeated per destination, and gives the group a lifetime — state scoped to a flow is discarded when the flow is left, not carried into unrelated screens.

## Deep Link <!-- 3 -->
**An external address resolving to a destination with its arguments.** A deep link must produce the same state as navigating there in-app, including a sensible back stack, and it is untrusted input: arguments are validated and guards apply exactly as they would internally. A deep link that bypasses a guard is an authorization bypass, not a navigation bug.

## Transition <!-- 3 -->
**The visual change between destinations** — presentation only, carrying no logic and gating nothing. A transition never decides whether navigation is permitted, and it stays cheap enough not to drop frames (QUALITY-BAR §5). Logic that lives in an animation is logic that disappears when the animation is disabled.

## State Restoration <!-- 3 -->
**Location and per-destination state survive process death.** The back stack and each destination's saved state are restorable, so returning to a killed app resumes where the user was. Durable truth still lives in the data layer; navigation restores position and transient input, not domain data.

## Result Passing <!-- 3 -->
**A destination returns a value to whoever launched it** through an explicit typed channel, consumed once. Communicating a result via shared mutable state couples two screens invisibly and re-delivers the value on every restoration — the one-shot-versus-state confusion, in navigation form.

## Testability <!-- 2 -->
**Navigation is verifiable without a UI.** Because location is state and moves are events, a test can assert that an event produces the expected destination, that a guard blocks an unauthenticated one, and that restoring a serialized stack yields the same place. Navigation reachable only by driving real screens is navigation that will not be tested.
