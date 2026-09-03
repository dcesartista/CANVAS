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
`screen` · feature/package · its ViewModel · the nav route · **`archetype`** (one of the 13 in Palette ADR-0003) · **`shell`** (`page` | `overlay` | `focused`).

**`archetype` and `shell` are both required.** If the caller did not supply them, infer from the screen's purpose and **state the inference**; if genuinely ambiguous, STOP and ask. A screen with no declared archetype is what structural drift looks like at the start.

**Check buildability first.** `presentation-impl.md` → `## Screen archetypes` lists which archetypes ink-basic can build today. If yours cannot, **STOP and say so** — do not hand-roll it from raw M3. A hand-rolled screen is precisely the drift this layer exists to prevent, and it will be rebuilt when the archetype lands anyway.

## Procedure
1. `section-query` `reference/presentation-theory.md` → `## Screen` and `lib/android/reference/presentation-impl.md` → `## Screen`, `## Screen archetypes` **and** `## ink-basic self-check`.
1b. **Model the phases first.** The UI state exposes its loadable subject as `ScreenState<T>` (`Loading` · `Empty(reason)` · `Error(message)` · `Content(value)`), never parallel `loading: Boolean` / `error: String?` fields. Handle exactly the phases the archetype requires — Collection needs all four; Detail and Form have no `empty`.
1c. **Resolve slot coverage.** For each slot the archetype defines, decide whether the app can fill it. `required` and unfillable → STOP and ask. `recommended` and unfillable → proceed and report. `optional` → omit silently. State the decisions you made.
2. Write `ui/<feature>/<Screen>Screen.kt`:
   - `@Composable`; collects UI state **lifecycle-aware**; renders the state; forwards events to the ViewModel — no business logic in the composable.
   - split into a stateless content composable for previews/tests.
   - **build the structure from `com.canvas.ink.basic.layout`, not by hand**: the declared shell for the frame (never a raw `Scaffold`, never a hand-assembled `Column { CanvasTopBar(...); ... }`), `CanvasStateHost` for the phases (never a hand-rolled `when { loading -> … }`), and the archetype's body — `CanvasCollection` for Collection, `CanvasFormBody` for Form. Use the padding the shell hands you; do not invent page padding.
   - **supply slots as values, never widgets.** Build `CollectionItemSlots` from the domain object; do not choose `CanvasCard` versus `CanvasListItem` at the call site, and do not set the size or shape of media — pass the ink's `Modifier` straight through to your image loader. Choosing widgets here is what makes a second ink impossible.
   - **name the archetype in the content composable's KDoc**, e.g. `archetype: **list** (Palette ADR-0003)`. A reviewer must be able to see the declared structure without reading the body.
   - **build from the swappable UI library `ink-basic`** (the agnostic Palette contract realized in Compose) — use its components (`CanvasButton`, `CanvasCard`, `CanvasTextField`, `CanvasTopBar`, `CanvasBottomNav`, `CanvasTabRow`, `CanvasListItem`, `CanvasEmptyState`, `CanvasErrorState`, `CanvasSnackbar`, `CanvasProgress`) and never raw `MaterialTheme` primitives. See `lib/android/reference/presentation-impl.md` → `## ink-basic`. If a screen needs a compound that ink-basic lacks, compose it from existing components (T3 tokens) instead of hand-rolling M3 widgets.
   - accessibility: content descriptions / semantics; touch targets ≥48dp; correct focus order ([QUALITY-BAR](../../../../QUALITY-BAR.md) §5).
3. Performance: keys on lazy lists, stable models, no work on the main thread ([QUALITY-BAR](../../../../QUALITY-BAR.md) §5).
4. **Self-check the seam** — CANVAS enforces the ink-basic contract itself, invisibly to the user. `Grep` the written file for the violations in `presentation-impl.md` → `## ink-basic self-check`: raw M3 widgets (`Button(`, `OutlinedTextField(`, `Card(`, `TopAppBar(`, `NavigationBar(`, `TabRow(`, `Snackbar(`, `LinearProgressIndicator(`, `Divider(`, and the non-layout M3 set), raw hex `Color(0x...`, raw `dp` where a token exists, and bare `MaterialTheme.` usage. If any appear, **fix them** (use `Canvas*` components and `LocalSemanticTokens`) and re-run the self-check until clean.
4b. **Self-check the structure** — same file, same discipline, checks 5–9 of the self-check list. Reject and fix if any appear:
   - `Grep "\bScaffold\("` → must be one of the three shells. Use the word boundary: a bare `Scaffold(` pattern also matches the shell names and reports every conformant screen as a violation.
   - `Grep "state.loading|state.error != null|isLoading"` in the screen → phases belong in `CanvasStateHost`, not in a screen-level branch.
   - `Grep "LazyColumn(|LazyVerticalGrid("` in a Collection screen → must be `CanvasCollection`. A `LazyRow` inside an item (a feed rail) is fine.
   - A Collection screen whose state cannot express `Empty` → add it; empty is an outcome, not an oversight.
   - `Grep "\.size(|\.aspectRatio(|\.clip("` inside a slot lambda → the ink sizes media, not the screen.
   - Page-level `padding(t.space.` applied to the body root → use the scaffold's padding. Padding *inside* a card or row is not a violation; read the match, do not count it.
5. Register/confirm the route via `android-create-navigation`.

## Output
`Glob` + `Grep`; confirm lifecycle-aware collection + no logic in the composable + **seam self-check clean** (no raw M3 widgets, no raw hex/dp, no bare `MaterialTheme` outside ink-basic's component set) + **structure self-check clean** (declared archetype and shell, shell frame, `CanvasStateHost` phases, archetype body, all required phases handled, slots supplied as values).