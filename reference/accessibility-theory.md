# Accessibility — theory

> What accessible Android UI IS and why. WCAG 2.2 AA mapped to the platform — QUALITY-BAR §5.
> How, per stack: `../lib/android/reference/accessibility-impl.md`. Anchored to [QUALITY-BAR](../QUALITY-BAR.md) §5.
> Read one Term via `section-query`: Grep `^## <Term>` → Read(offset, limit=N).

Accessibility makes the app **usable by everyone, including TalkBack and other assistive technology** (QUALITY-BAR §5). It is not a bonus for the few: it is WCAG 2.2 AA applied to a native screen, tested like a feature. The platform's semantics tree is the exact hook W3C's criteria expect — [Google accessibility](https://developer.android.com/guide/topics/ui/accessibility) docs and the [WCAG 2.2 quickref](https://www.w3.org/WAI/WCAG22/quickref/) are the authorities.

## Inclusive Product <!-- 3 -->
Accessibility is a **product requirement with measurable criteria**, scored per screen like performance (QUALITY-BAR §5): every screen passes color contrast, every control has a spoken name, every flow is fully operable by a screen reader, and text scales without breaking layout. A screen that only works under perfect vision, hearing, and dexterity is incomplete by definition — the goal is the set of users who can complete it.

## Semantics Tree <!-- 3 -->
Compose exposes UI to assistive tech through the **semantics tree — the accessibility API's view of the screen**, a parallel tree of nodes with roles, names, state, and actions ([semantics in Compose](https://developer.android.com/jetpack/compose/semantics)). Screen readers announce and operate this tree, not pixels. A screen with no semantics is literally invisible to TalkBack; building the tree as part of layout — not after — is the discipline.

## Content Description <!-- 3 -->
Every element conveys its **name and role** (QUALITY-BAR §5): icons get content descriptions / semantics labels ("Add to cart", not "plus icon"), and decorative elements opt *out* so the reader stays on meaning. Text-bearing elements usually read fine as-is; the failures live with icons, image buttons, charts, and grouped controls. Descriptions summarize *what it does*, never read raw IDs aloud.

## Grouping & Hierarchy <!-- 3 -->
Related elements are **grouped so the reader gets structure, not a flat dump** (WCAG 1.3.1): a card's title, body, and button read as one unit; screen sections are announced; semantically decorative children that would fragment a sentence are merged (an icon glued to its label, the tokens inside a price). Grouping is the difference between "reads like a page" and "reads like a linear transcript of pixels".

## Touch Targets <!-- 3 -->
Interactive elements are **at least 48dp × 48dp with no dead zones** (QUALITY-BAR §5, [Material guidance](https://m3.material.io/foundations/accessible-design/overview)): below that, a motor-limited finger misses and hits something adjacent. Small targets are not comfort — WCAG 2.2's target-size criterion grades them. Where space forbids, enlarge the invisible tappable area, keeping visual and hit area aligned.

## Focus Order <!-- 3 -->
**Keyboard/D-pad focus moves in reading order — logical, visible, and complete** (WCAG 2.2 focus order): every interactive element is reachable, the order flows naturally (top-down/reading direction, never the renderer's whim), and the focused element is clearly indicated. A focus that jumps, skips, or lands invisibly fails the same criterion a tab-order mis-sort fails on a desktop site. Focus follows order + semantics, not pixel layout.

## State Announcement <!-- 3 -->
Changes that matter are **announced, not just drawn** (WCAG 4.1.3 status): "Item added to cart", "Sync complete", an inline error — live-region semantics announce them without stealing focus. A spinner that spins but never says "loading… done" is a silent success and a silent failure. The UI's one-shot events (presentation-theory) are exactly the moment to announce, tied to the state that produced them.

## Text Scaling <!-- 3 -->
The UI **lays out correctly at large font scales** (QUALITY-BAR §5, WCAG 1.4.4): `sp`-based text, `dp`-based containers, flow/wrap instead of clipping, no fixed-line truncation of essential content. Users range up to 200% and beyond; "text overflows and the button slides off-screen" fails at the first scale check. Every screen is visually verified at the largest common scale — automatically, in the checks.

## Contrast & Color <!-- 3 -->
Text and meaningful UI meet **WCAG AA contrast (4.5:1 text, 3:1 large/non-text)** and **never rely on color alone** (QUALITY-BAR §5, WCAG 1.4.1/1.4.3): an error state is color *plus* text/icon, a legend is pattern *plus* label. Contrast is grid-checkable and auto-reported (accessibility lint does this). "It's red, so obviously it failed" is exactly the sentence that fails a color-blind user.

## TalkBack Flow <!-- 3 -->
The screen is **fully operable by TalkBack end to end** (QUALITY-BAR §5): a narrated pass over each primary journey, every action reachable by swipe-gesture traversal, no element unreachable, no noisy component a user must swipe past with nothing to do. This is the closest thing to a true WCAG walk on the platform — automated checks catch contrast and sizes; the manual TalkBack pass catches *flow*. Both are in the bar.

## Custom Actions & Gestures <!-- 3 -->
Custom gestures **ship with accessible alternatives** (WCAG 2.2): swipe-to-dismiss gains an action or button, drag-and-drop has an accessible option or narration, custom range inputs announce value changes. Interactive elements expose their *actions* semantically so TalkBack users can activate what gesture users swipe ([Material motion](https://m3.material.io/)). An interaction not expressible in semantics is one assistive-tech users simply cannot do.

## Automated + Manual <!-- 3 -->
Accessibility is verified by **both an automated gate and a manual pass** (QUALITY-BAR §5): lint/checks (touch targets, missing descriptions, contrast probes) run in CI and fail the build; narrated passes (TalkBack + large scale) are scheduled like QA because only a human ear hears an announcement that reads in the wrong order. Automated catches regressions; manual catches "perfect metrics, unusable flow".

## Representational Care <!-- 3 -->
Media and language are handled **beyond test coverage** (WCAG 1.2/1.4.5/3.1): video carries subtitles, images carry meaning not decoration, and text is locale-correct — RTL, locale-sensitive digits and plurals (a raw `"$count items"` concatenation breaks half the world, not just screen readers). This is where accessibility, i18n, and quality genuinely meet: an app is accessible in the language it is shown in, not the one it was written in.

