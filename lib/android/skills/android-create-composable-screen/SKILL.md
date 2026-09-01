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
1. `section-query` `reference/presentation-theory.md` → `## Screen` and `lib/android/reference/presentation-impl.md` → `## Screen` **and** `## ui-default self-check`.
2. Write `ui/<feature>/<Screen>Screen.kt`:
   - `@Composable`; collects UI state **lifecycle-aware**; renders the state; forwards events to the ViewModel — no business logic in the composable.
   - split into a stateless content composable for previews/tests.
   - **build from the swappable UI library `ui-default`** (the agnostic Palette contract realized in Compose) — use its components (`CanvasButton`, `CanvasCard`, `CanvasTextField`, `CanvasTopBar`, `CanvasBottomNav`, `CanvasTabRow`, `CanvasListItem`, `CanvasEmptyState`, `CanvasErrorState`, `CanvasSnackbar`, `CanvasProgress`) and never raw `MaterialTheme` primitives. See `lib/android/reference/presentation-impl.md` → `## ui-default`. If a screen needs a compound that ui-default lacks, compose it from existing components (T3 tokens) instead of hand-rolling M3 widgets.
   - accessibility: content descriptions / semantics; touch targets ≥48dp; correct focus order ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §5).
3. Performance: keys on lazy lists, stable models, no work on the main thread ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §5).
4. **Self-check the seam** — CANVAS enforces the ui-default contract itself, invisibly to the user. `Grep` the written file for the violations in `presentation-impl.md` → `## ui-default self-check`: raw M3 widgets (`Button(`, `OutlinedTextField(`, `Card(`, `TopAppBar(`, `NavigationBar(`, `TabRow(`, `Snackbar(`, `LinearProgressIndicator(`, `Divider(`, and the non-layout M3 set), raw hex `Color(0x...`, raw `dp` where a token exists, and bare `MaterialTheme.` usage. If any appear, **fix them** (use `Canvas*` components and `LocalSemanticTokens`) and re-run the self-check until clean.
5. Register/confirm the route via `android-create-navigation`.

## Output
`Glob` + `Grep`; confirm lifecycle-aware collection + no logic in the composable + **self-check clean** (no raw M3 widgets, no raw hex/dp, no bare `MaterialTheme` outside ui-default's component set).