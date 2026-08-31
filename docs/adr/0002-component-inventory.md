# Component inventory — the tokenized UI component system (draft v1)

> Companion to **ADR-0001**. Defines the concrete components the tokenized system must provide, and which T3 semantic tokens each consumes. **Components are immutable; only palettes (complete T3 sets) are swappable.** Components read T3 tokens only — never T1/T4 directly, never compute values.
> This is the **contract inventory** (what a full system must ship). Default/commercial palettes map onto it later.

## Principles
- Every component consumes **only** T3 semantic tokens.
- A component must not hardcode raw values (no `16.dp` literals, no `Color(0xFF…)`) — it reads `space.md`, `color.bg.surface`, etc.
- Every interactive component:
  - touch target ≥ `size.touchTarget` (core-pinned, 48dp min)
  - has `contentDescription` / semantics (QUALITY-BAR §5)
  - renders all states (enabled/disabled/loading/error/pressed) from the same token system
- Components with text guarantee contrast via their `on*` token pairs.
- Dark/highContrast use the same components; only T3 palette differs (ADR-0001).

## The inventory

### 1. Display & text
| Component | Consumes |
|---|---|
| `CanvasText` (style) | `type.*` + `color.text.*` |
| `CanvasHeadline` / `CanvasBody` / `CanvasLabel` / `CanvasCaption` | `type.display/h1..h4/body/label/caption`, `color.text.primary/secondary/tertiary/disabled` |

### 2. Buttons & actions
| Component | Consumes |
|---|---|
| `CanvasButton` (primary) | `color.accent.primary`, `color.accent.onPrimary`, `space.md/lg`, `radius.md` |
| `CanvasButtonSecondary` | `color.bg.surface`, `color.outline`, `color.text.primary` |
| `CanvasButtonGhost / TextButton` | `color.text.primary`, `color.accent.primary` |
| `CanvasButtonIcon` | `size.touchTarget`, `color.text.secondary` |
| `CanvasFab` | `color.accent.primary`, `color.accent.onPrimary`, `elevation.md/lg`, `radius.pill` |
| `CanvasSegmentedControl` | `color.bg.surfaceAlt`, `color.accent.onPrimary`, `radius.sm/md` |

### 3. Inputs
| Component | Consumes |
|---|---|
| `CanvasTextField` | `color.bg.surface`, `color.outline`, `color.text.primary`, `color.state.error`, `radius.sm/md` |
| `CanvasTextFieldFilled` | `color.bg.surfaceAlt`, `color.text.primary` |
| `CanvasSearchBar` | `color.bg.surfaceAlt`, `radius.pill`, `color.text.secondary` |
| `CanvasToggle` / `CanvasSwitch` / `CanvasCheckbox` | `color.accent.primary`, `color.bg.surface`, `color.state.*` |
| `CanvasSlider` | `color.accent.primary`, `color.bg.surfaceAlt` |
| `CanvasChip` (filter/choice) | `color.bg.surfaceAlt`, `color.outline`, `color.text.*`, `radius.pill` |

### 4. Layout & surfaces
| Component | Consumes |
|---|---|
| `CanvasCard` | `color.bg.surfaceRaised`, `elevation.sm/md`, `radius.lg`, `space.layout.item` |
| `CanvasCardElevated` | `elevation.lg`, `color.bg.surfaceRaised` |
| `CanvasSurface` / `CanvasSurfaceAlt` | `color.bg.surface/surfaceAlt` |
| `CanvasDivider` | `color.divider` |
| `CanvasSkeleton` | `color.bg.surfaceAlt` (loading placeholder) |
| `CanvasEmptyState` | `space.layout.*`, `color.text.secondary`, `type.body` + icon |
| `CanvasErrorState` | `color.state.error`, `color.state.onError`, `type.body` |

### 5. Navigation
| Component | Consumes |
|---|---|
| `CanvasTopBar` | `color.bg.surface`, `color.text.primary`, `space.layout.page`, `elevation.flat/sm` |
| `CanvasAppBarLarge` | `type.h1/h2`, `color.bg.surface` |
| `CanvasBottomNav` | `color.bg.surface`, `color.accent.primary` (selected), `color.text.secondary` (unselected) |
| `CanvasTabRow` | `color.accent.primary` (active), `color.text.secondary` (inactive), `color.divider` |
| `CanvasDrawer` | `color.bg.surface`, `color.text.primary/secondary` |

### 6. Lists & feedback
| Component | Consumes |
|---|---|
| `CanvasListItem` | `color.bg.surface`, `color.text.primary/secondary`, `space.layout.item`, `space.md/lg` |
| `CanvasListSectionHeader` | `type.label`, `color.text.secondary` |
| `CanvasBadge` | `color.accent.primary`/`color.state.*`, `color.accent.on*`, `radius.pill` |
| `CanvasSnackbar` | `color.text.inverse`, `color.bg.surfaceRaised`, `motion.duration.normal` |
| `CanvasDialog` / `CanvasAlertDialog` | `color.bg.surfaceRaised`, `color.state.error`, `color.accent.primary`, `elevation.lg`, `radius.lg` |
| `CanvasProgress` (linear/circular) | `color.accent.primary`, `color.bg.surfaceAlt` |
| `CanvasTooltip` | `color.text.inverse`, `color.bg.surfaceRaised` |

### 7. Data display
| Component | Consumes |
|---|---|
| `CanvasAvatar` | `color.accent.primary`, `color.accent.onPrimary` |
| `CanvasImagePlaceholder` | `color.bg.surfaceAlt` |

## The shared `on*` contract
Every accent/state color ships with its contrast pair (`color.accent.onPrimary`, `color.state.onError`, …). A component that fills a surface with an accent **must** pair its text/border with the matching `on*` token — guaranteeing contrast in every theme by construction, never by runtime luck.

## Completeness requirement
A full component system ships **all** of the above. A *theme* (palette) need only supply the T3 tokens they consume — it need not define components, because components are invariant. This is what makes paid skins and user palettes simple: they only ever produce T3 values.

## Open items (for the build step)
- **Which components does the *default* ship first?** Recommend the core set (~12): button, secondary-button, text-field, card, list-item, top-bar, bottom-nav, tab-row, empty-state, error-state, snackbar, progress — enough to compose most screens without reaching for stock Material.
- **Icon tokens** deferred (ADR-0001) until a second skin needs to swap icon sets.
- **Responsive/breakpoint tokens** deferred (ADR-0001) — phone-first.
