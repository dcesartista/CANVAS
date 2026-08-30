# Android — accessibility impl (Compose semantics & TalkBack)

> How accessibility Terms ([accessibility-theory.md](../../accessibility-theory.md)) are written in native Compose, per WCAG 2.2 AA and QUALITY-BAR §5.
> **Rule:** every interactive element exposes a semantic description/role; focus order is correct; touch targets ≥ 48dp; contrast ≥ 4.5:1 in Material 3 (AA). Compose builds an accessibility tree from the semantics layer automatically — you augment, not reimplement.

## Semantics <!-- 8 -->
Compose creates a `SemanticsNode` tree from composables; TalkBack reads it. Add `Modifier.semantics { }` to convey meaning beyond the default — merge descendants, set `contentDescription`, `role`, `stateDescription`, `selected`, and `disabled`. For lists define a stable custom semantics read via `SemanticsPropertyKey`.
```kotlin
Image(painter, contentDescription = "Shopping cart icon", modifier = Modifier.size(24.dp))
IconButton(onClick, modifier = Modifier.semantics { contentDescription = "Favorite" }) { Icon(...) }
```
A decorative icon with no meaning should get `contentDescription = null` (decorative) — not an empty string, which TalkBack reads aloud. Use `mergeDescendants()` for compound controls where a single announcement is clearer than per-child.

## Content Description <!-- 8 -->
`contentDescription` should describe the *purpose/action*, not the raw text of the icon: "Back" not an arrow glyph; "Add to cart" not "cart-plus". For `Text`+`Icon` combos, prefer a `role` + state (`Checked`/`Unchecked`) and let the label speak.
```kotlin
Icon(painter = Icons.Filled.AddShoppingCart, contentDescription = "Add to cart")
Button(onClick, modifier = Modifier.semantics { role = Role.Button }) { Text("Checkout") }
```
Validate with a TalkBack pass over each screen; a good content description announces *what it is* and *what it does*, in a natural sentence.

## Focus Order <!-- 14 -->
Logical tab/focus order should match visual reading order. Compose infers order from layout position; use `Modifier.focusOrder` / explicit `focusProperties` and `FocusRequester`/`FocusTarget` to fix deviations, and `onFocusChanged` for announcements. Avoid trapping focus.
```kotlin
@Composable fun Form() {
  val firstName = FocusRequester()
  Column {
    OutlinedTextField(..., Modifier.focusRequester(firstName).onFocusChanged { ... })
    // Reverse-order focus on screen open:
    LaunchedEffect(Unit) { firstName.requestFocus() }
  }
}
```
For TalkBack, order follows the semantics/accessibility traversal set by placement; grouping with `mergeDescendants` also collapses siblings into one accessible parent to reduce tab-stop noise.

## Touch Targets <!-- 11 -->
Every interactive element must have at least a **48×48 dp** touch target (WCAG 2.5.5 / Material guidance). Apply `minimumInteractiveComponentSize()` or explicit `size(48.dp)` padding so the hit area meets the floor even when the glyph is smaller.
```kotlin
IconButton(onClick, modifier = Modifier.size(48.dp)) { Icon(..., Modifier.size(24.dp)) }
ListRow(Modifier
  .minimumInteractiveComponentSize()
  .clickable(onClick = { ... })
  .padding(horizontal = 16.dp, vertical = 12.dp))
```
Small icons/links still pass when the *combined* touch area (icon + padding) reaches 48dp; never shrink below for critical actions.

## Contrast <!-- 8 -->
Material 3 color tokens must meet **4.5:1** (AA) for text and 3:1 for large/UI components. Prefer theme tokens over raw hex so dark mode inherits; when a custom color is used, verify with a contrast checker rather than trusting the palette.
```kotlin
Text("Total \$12.00", style = MaterialTheme.typography.titleMedium,
  color = MaterialTheme.colorScheme.onSurface)     // theme already contrasty
```
Elements like `onErrorContainer`/`onTertiary` are darker variants for text; use `surfaceVariant` for backgrounds. Automated contrast lint (Accessibility Scanner) plus thematic `ColorScheme` tokens keeps AA without hand-tuning every screen.

## TalkBack & Testing <!-- 8 -->
Validate with TalkBack and automated `SemanticsMatcher`s in Compose UI tests instead of `onNodeWithText`. Compose test assertions double as accessibility checks because they query the semantics tree — good descriptions = testable UI.
```kotlin
composeRule.onNodeWithContentDescription("Add to cart").assertExists()
composeRule.onNode(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Button)).assertIsDisplayed()
```
Run an Accessibility Scanner pass in CI; compose failures on missing descriptions surface regressions before release, tying §5 to the acceptance gate.
