---
name: android-create-viewmodel
description: Create a screen ViewModel + its UI State in the Android stack (single observable state, UDF, no platform context).
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-usecase
  - android-create-composable-screen
---

Create one **ViewModel** (+ its UI State). Create-only — if it exists, STOP.

## Inputs
`screen` · feature/package · the use case(s) it calls · the screen's states + events.

## Procedure
1. `section-query` `reference/presentation-theory.md` → `## ViewModel` / `## UI State` and `lib/android/reference/presentation-impl.md` → the same Terms.
2. Write `ui/<feature>/<Screen>ViewModel.kt` + `<Screen>UiState.kt`:
   - `@HiltViewModel`, constructor-injected use cases; **single observable state** exposed (internal mutable + `copy()` updates — UDF, [QUALITY-BAR](../../../../QUALITY-BAR.md) §1).
   - events as functions (`onX`); one-shot events per `lib/android/reference/presentation-impl.md` → `## One-Shot Event`.
   - immutable UI state type: a `data class` whose **loadable subject is a `ScreenState<T>`** (`Loading` · `Empty(reason)` · `Error(message)` · `Content(value)`), never parallel `loading: Boolean` / `error: String?` fields. Data shown *alongside* the subject stays a plain field — one phase per loadable subject.
   - **map outcomes to phases here, not in the screen.** An empty result is `Empty`, not `Content(emptyList())`; give it a `reason` when the copy should differ (filtered vs unfiltered, signed-out vs genuinely empty).
3. **No platform context** in the ViewModel; screen-scoped.

## Output
`Glob` + `Grep`; confirm observable state exposure + no platform-context reference + **the UI state carries `ScreenState`, not parallel `loading`/`error` fields**.