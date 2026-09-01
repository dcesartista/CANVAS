# Dependency injection — theory

> What dependency injection IS and why. Family-agnostic — the single source of truth.
> How, per stack: `../lib/android/reference/di-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §1.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Dependency injection is how the dependency rule of QUALITY-BAR §1 is *enforced at construction time* rather than hoped for. A component declares what it needs and receives it; it never reaches out to find or build it. That single inversion is what makes the outer→inner dependency direction mechanical, lets any collaborator be replaced by a test double, and keeps object lifetimes explicit instead of accidental.

## Inversion of Control <!-- 3 -->
**A component states its needs; something else satisfies them.** The class under construction does not choose, build, or locate its collaborators — it accepts them. This is what turns the dependency rule into a compile-time property: a domain type that only ever accepts domain abstractions physically cannot acquire a data-layer one. Control living inside the class is the defect DI exists to remove.

## Constructor Injection <!-- 3 -->
**Dependencies arrive through the constructor** — the default, and the only form that makes a half-built object unrepresentable. Every collaborator is visible in one signature, so the type's real coupling is readable at a glance and the compiler rejects an instance missing one. Field or setter injection defers the failure to runtime and hides the true dependency count; use it only where a framework constructs the object for you.

## Explicit Dependencies <!-- 3 -->
**A type's dependencies are all visible in its signature**, none acquired covertly. A class that reaches for a global, a singleton accessor, or a service locator lies about what it needs, and the lie surfaces as an untestable unit. A long constructor is not a DI problem — it is the design telling you the type does too much, and the honest signal is worth keeping.

## Abstraction Boundary <!-- 3 -->
**Inner layers own the interface; outer layers supply the implementation.** The domain declares the port it needs; the data layer binds a concrete adapter to it. Bindings are the only place both sides are named together, which is what keeps every other file ignorant of the implementation and free to be re-pointed without edit.

## Module <!-- 3 -->
**A declaration of how abstractions are satisfied** — the wiring, gathered in one auditable place and separated from the logic it wires. Modules are grouped by concern (network, storage, repository bindings) so a reader can find the one binding that matters. Wiring scattered across call sites is the state DI is meant to end.

## Provider <!-- 3 -->
**A recipe for constructing something the container cannot build itself** — a third-party type, a type needing configuration, or one assembled from several inputs. A provider is construction only: it holds no business rule and makes no decision, because logic hidden in wiring is logic no test will reach.

## Binding <!-- 3 -->
**A statement that one abstraction is served by one implementation.** This is the substitution seam: swapping the bound type re-points every consumer at once, with no consumer edited. It is also the audit point — the complete list of bindings is the complete list of what the app actually runs.

## Qualifier <!-- 3 -->
**A distinguishing tag when one type has several meaningful instances** — two base URLs, two dispatchers, an authenticated and an anonymous client. Without qualifiers such cases collapse into an ambiguity resolved by accident. With them the choice is named at the injection site, so reading the parameter tells you which instance arrives.

## Scope <!-- 3 -->
**The declared lifetime of an instance** — per-application, per-screen, per-request. Scope is a correctness property, not an optimization: an over-scoped object leaks state between users or screens, and an under-scoped one silently duplicates a resource meant to be shared. Every scope is a deliberate decision, never a default that went unexamined.

## Object Graph <!-- 3 -->
**The whole set of types and their satisfied dependencies**, resolved as one connected structure. Because it is resolved as a whole, a missing or circular binding is a build-time failure rather than a crash on the screen that needed it. A cycle in the graph is a design error surfacing early, which is exactly where you want it.

## Test Substitution <!-- 3 -->
**Any dependency can be replaced without touching the code under test.** This is the payoff for everything above: the unit sees an abstraction, so a test supplies a fake and drives real behavior with no network, clock, or database. A type that cannot have a collaborator substituted is not badly tested — it is badly injected.

## Composition Root <!-- 2 -->
**One place where the graph is assembled**, at the outermost edge of the application. Only that edge knows every concrete type; everything inside knows abstractions. Construction leaking inward means some inner type has taken on an outer responsibility, and the dependency rule has already been broken.
