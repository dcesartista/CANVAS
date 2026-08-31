# ADR-0001 — AI-friendly tokenized UI component contract

> **Status:** Accepted
> **Date:** 2026-08-31
> **Context:** CANVAS produces structurally correct but visually bland UI ("structured, but bad"). Root cause: the spec is correctness-complete and aesthetics-empty. We address this with a tokenized, replaceable UI component system — a "look" is a complete palette; components are immutable tokens consumers.

## Decision

Establish a **four-tier token system** with a strict layering rule, custom semantic names, a hand-crafted default palette, and strict palette completeness.

### The tiers

| Tier | Name | Role | Themed by user? |
|---|---|---|---|
| T1 | Primitives | Raw values (spacing base, radius steps, durations, color spectrum) | No (shared default) |
| T2 | Alias / bridge | Internal mapping of semantic names → M3 role primitives under the hood | No (internal) |
| **T3** | **Semantic (THE contract)** | What components read; a complete theme = a complete T3 set | **Yes — this is the contract** |
| T4 | Component (sugar) | Optional shorthand resolving to T3; never invents values | No (derived) |

**Layering rule:** components consume *only* T3 semantic tokens. They never compute, derive, or read T1/T4 directly. T4 is convenience that must resolve to T3; a new theme only ever overrides T3 and T4 recomputes automatically.

### Custom semantic names
CANVAS defines its own semantic token names (see below), bridged to Material 3 primitives internally via T2. Users never see M3 concept-leak; this enables a differentiated, hand-crafted default look rather than stock-Material blandness.

### Hand-crafted default
The free default palette is **hand-crafted** as a coherent designed look — not an M3 auto-pick. It is simultaneously the quality floor and the first sellable-looking product.

### Strict completeness
- A **valid theme = a complete T3 set.** No partial themes accepted.
- A palette is actually **three complete sets** — `light`, `dark`, `highContrast` — because a "look" must hold in every mode. A theme is not valid until all three resolve.
- T1/T2/T4 are shared defaults, not user-themed.

### The seam / replacement model
A "look" (free default, future paid theme, or a user's system) is **just a complete T3 palette** against the same component contract. Components are immutable; users swap palettes, never components. The design-direction mode is a *later, deliberate* extension against this same seam — deferred, not designed now.

## Canonical token vocabulary (T3)

### Color

| Token | Purpose |
|---|---|
| `color.bg.surface` | Base screen surface |
| `color.bg.surfaceAlt` | Slightly distinct surface (sidebar, groupings) |
| `color.bg.surfaceRaised` | Raised surface (cards, sheets) — tonal delta coordinated with elevation |
| `color.text.primary` | Primary body text |
| `color.text.secondary` | Secondary / supporting text |
| `color.text.tertiary` | Muted / placeholder |
| `color.text.disabled` | Disabled text |
| `color.text.inverse` | Text on inverse/high-contrast surfaces |
| `color.accent.primary` | Primary brand accent |
| `color.accent.onPrimary` | Contrast pair for `accent.primary` |
| `color.accent.secondary` | Secondary accent |
| `color.accent.onSecondary` | Contrast pair for `accent.secondary` |
| `color.state.error` | Error color |
| `color.state.onError` | Contrast pair for error |
| `color.state.warning` | Warning color |
| `color.state.onWarning` | Contrast pair for warning |
| `color.state.success` | Success color |
| `color.state.onSuccess` | Contrast pair for success |
| `color.state.info` | Info color |
| `color.state.onInfo` | Contrast pair for info |
| `color.outline` | Outlines / stroke |
| `color.divider` | Dividers |
| `color.overlay` | Scrim / selection overlay |

### Type
Each type token = `{ size, weight, lineHeight, letterSpacing }` (fontFamily is themeable so paid skins can swap it):

| Token |
|---|
| `type.display` |
| `type.h1` … `type.h4` |
| `type.body` |
| `type.bodySmall` |
| `type.label` |
| `type.labelSmall` |
| `type.caption` |

### Spacing

| Token |
|---|
| `space.xxs` `space.xs` `space.sm` `space.md` `space.lg` `space.xl` `space.xxl` |
| `space.layout.page` `space.layout.section` `space.layout.item` |

Base = 4dp scale: `0/4/8/12/16/24/32/48/64`.

### Radius

| Token |
|---|
| `radius.none` `.sm` `.md` `.lg` `.pill` |

Steps `0/2/4/8/12/16/999`.

### Elevation

| Token |
|---|
| `elevation.flat` `.sm` `.md` `.lg` |

Each = shadow + tonal surface delta (a raised surface shifts tone consistently).

### Motion

| Token |
|---|
| `motion.duration.fast` `.normal` `.slow` |
| `motion.easing.standard` `.decelerate` `.accelerate` |

Durations `100/200/300/500ms`.

### Sizing / density

| Token |
|---|
| `density.compact` `.comfortable` |
| `size.touchTarget` — **pinned by core to ≥48dp, not themeable** |

## Explicitly deferred (fill in later)

- **Breakpoints / responsive tokens** — app scaffold is phone-first; add when tablet/landscape arrives.
- **Icon system** (`icon.family`, `icon.size.*`) — defer until a second skin actually needs to swap icon sets.

## Core correctness (always-on, not themeable)
Accessibility and correctness UI rules remain in the core Quality Bar (§5) and are never a "look" decision: touch targets ≥48dp, `contentDescription`, tokens-not-pixels, dark-mode, WCAG contrast. A theme can change *looks*; it cannot change *quality*.

## Consequences
- **Positive:** replaceable looks, no accidental component breakage (contract immutable), no partial-theme inconsistency (strict completeness), clean future commercialization (paid skins = more T3 palettes).
- **Cost:** hand-crafting a genuinely good default + three-mode palette is real design work; strict completeness requires tooling to validate a palette resolves every T3 token in all three modes.
