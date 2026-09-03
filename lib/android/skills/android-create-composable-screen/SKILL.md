---
name: android-create-composable-screen
description: Create a Compose Screen bound to a ViewModel in the Android stack (dumb, lifecycle-aware, accessible).
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-viewmodel
  - android-create-navigation
---

Create one **Screen**. Create-only — if it exists, STOP.

## Inputs
`screen` · feature/package · its ViewModel · the nav route · **`archetype`** (`list` | `detail` | `form`).

**`archetype` is required.** If the caller did not supply one, infer it from the screen's purpose and **state the inference**; if it is genuinely ambiguous, STOP and ask. A screen with no declared archetype is what structural drift looks like at the start.

## Procedure
1. `section-query` `reference/presentation-theory.md` → `## Screen` and `lib/android/reference/presentation-impl.md` → `## Screen`, `## Screen archetypes` **and** `## ink-basic self-check`.
1b. **Model the phases first.** The UI state exposes its loadable subject as `ScreenState<T>` (`Loading` · `Empty(reason)` · `Error(message)` · `Content(value)`), never parallel `loading: Boolean` / `error: String?` fields. Handle exactly the phases the archetype requires — `list` needs all four; `detail` and `form` have no `empty`.
2. Write `ui/<feature>/<Screen>Screen.kt`:
   - `@Composable`; collects UI state **lifecycle-aware**; renders the state; forwards events to the ViewModel — no business logic in the composable.
   - split into a stateless content composable for previews/tests.
   - **build the structure from `com.canvas.ink.basic.layout`, not by hand**: `CanvasScreenScaffold` for the frame (never a raw `Scaffold`, never a hand-assembled `Column { CanvasTopBar(...); ... }`), `CanvasStateHost` for the phases (never a hand-rolled `when { loading -> … }`), and the archetype's body — `CanvasListBody` for `list` (its `key` is mandatory), `CanvasFormBody` for `form`. Use the padding the scaffold hands you; do not invent page padding.
   - **name the archetype in the content composable's KDoc**, e.g. `archetype: **list** (Palette ADR-0003)`. A reviewer must be able to see the declared structure without reading the body.
   - **build from the swappable UI library `ink-basic`** (the agnostic Palette contract realized in Compose) — use its components (`CanvasButton`, `CanvasCard`, `CanvasTextField`, `CanvasTopBar`, `CanvasBottomNav`, `CanvasTabRow`, `CanvasListItem`, `CanvasEmptyState`, `CanvasErrorState`, `CanvasSnackbar`, `CanvasProgress`) and never raw `MaterialTheme` primitives. See `lib/android/reference/presentation-impl.md` → `## ink-basic`. If a screen needs a compound that ink-basic lacks, compose it from existing components (T3 tokens) instead of hand-rolling M3 widgets.
   - accessibility: content descriptions / semantics; touch targets ≥48dp; correct focus order ([QUALITY-BAR](../../../../QUALITY-BAR.md) §5).
3. Performance: keys on lazy lists, stable models, no work on the main thread ([QUALITY-BAR](../../../../QUALITY-BAR.md) §5).
4. **Self-check the seam** — CANVAS enforces the ink-basic contract itself, invisibly to the user. `Grep` the written file for the violations in `presentation-impl.md` → `## ink-basic self-check`: raw M3 widgets (`Button(`, `OutlinedTextField(`, `Card(`, `TopAppBar(`, `NavigationBar(`, `TabRow(`, `Snackbar(`, `LinearProgressIndicator(`, `Divider(`, and the non-layout M3 set), raw hex `Color(0x...`, raw `dp` where a token exists, and bare `MaterialTheme.` usage. If any appear, **fix them** (use `Canvas*` components and `LocalSemanticTokens`) and re-run the self-check until clean.
4b. **Self-check the structure** — same file, same discipline, checks 5–9 of the self-check list. Reject and fix if any appear:
   - `Grep "Scaffold("` → must be `CanvasScreenScaffold`.
   - `Grep "state.loading|state.error != null|isLoading"` in the screen → phases belong in `CanvasStateHost`, not in a screen-level branch.
   - `Grep "LazyColumn("` → must be `CanvasListBody` (mandatory `key`).
   - A `list` screen whose state cannot express `Empty` → add it; empty is an outcome, not an oversight.
   - Page-level `padding(t.space.` outside the scaffold → use the scaffold's padding.
5. Register/confirm the route via `android-create-navigation`.

## Output
`Glob` + `Grep`; confirm lifecycle-aware collection + no logic in the composable + **seam self-check clean** (no raw M3 widgets, no raw hex/dp, no bare `MaterialTheme` outside ink-basic's component set) + **structure self-check clean** (declared archetype, `CanvasScreenScaffold` frame, `CanvasStateHost` phases, archetype body, all required phases handled).