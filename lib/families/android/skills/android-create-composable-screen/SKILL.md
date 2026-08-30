---
name: android-create-composable-screen
description: Create a Compose Screen bound to a ViewModel in the Android family (dumb, lifecycle-aware, accessible).
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-viewmodel
  - android-create-navigation
---

Create one **Screen**. Create-only — if it exists, STOP.

## Inputs
`screen` · feature/package · its ViewModel · the nav route.

## Procedure
1. `section-query` `reference/presentation-theory.md` → `## Screen` and `lib/families/android/reference/presentation-impl.md` → `## Screen`.
2. Write `ui/<feature>/<Screen>Screen.kt`:
   - `@Composable`; collects UI state **lifecycle-aware**; renders the state; forwards events to the ViewModel — no business logic in the composable.
   - split into a stateless content composable for previews/tests.
   - accessibility: content descriptions / semantics; touch targets ≥48dp; correct focus order ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §5).
3. Performance: keys on lazy lists, stable models, no work on the main thread ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §5).
4. Register/confirm the route via `android-create-navigation`.

## Output
`Glob` + `Grep`; confirm lifecycle-aware collection + no logic in the composable.