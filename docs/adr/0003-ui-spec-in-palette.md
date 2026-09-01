# ADR-0003 — UI design contract lives in the sibling "Palette" project

> **Status:** Accepted
> **Date:** 2026-09-01
> **Context:** CANVAS needed a UI design contract to fix "structured but bad" UI. The token/component spec is **framework-agnostic** (the token tiers, completeness rule, replaceability, `on*` contrast contract, and component vocabulary apply to any UI framework). CANVAS is Android-native by design, and future systems (Flutter, React Native) will need the same spec. Keeping an agnostic spec inside an Android-only repo would misplace it.

## Decision

The framework-agnostic design-token & component spec lives in a **sibling project: `palette`** (`~/Documents/Learn/palette`). CANVAS **references** it; it does not vendor it.

- Palette = the neutral "what" (tokens + component contract).
- CANVAS = one platform implementation (Android/Compose) that reads Canvas's QUALITY-BAR for Android core-correctness and implements the palette contract in Compose.
- Future Flutter/RN systems will also implement against Palette.

## Consequence

- `docs/adr/0001-ui-token-contract.md` and `docs/adr/0002-component-inventory.md` (initially drafted in CANVAS) were **moved to `palette/docs/`**, retaining their ADR numbering within Palette.
- The Android-facing implementation decisions that remain CANVAS-specific (Compose components, the M3 bridge, where `ink-basic` installs) belong to CANVAS / the Android UI package and are tracked separately.
