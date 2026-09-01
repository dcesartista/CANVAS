# CANVAS

> An agentic Android coding system for building world-class, production-grade native Android apps (Kotlin · Jetpack Compose) rapidly, by leveraging AI against an authoritative quality bar.

CANVAS is where you paint production-grade Android apps. It lifts precise components (entities, use cases, repositories, ViewModels, Composables) and places them exactly where Clean Architecture says — anchored to a single authoritative quality bar, so a small team ships like a big one.

**Status: Phase 0 — anchor & scaffold.** The repo holds the anchor documents and the Android impl skeleton. Content is built from real friction in later phases (extract, don't predict).

## Install

CANVAS installs everywhere via **one curl command** — it fetches the corpus into a hidden cache (`~/.canvas`), renders into every supported host's project layout, and touches nothing global unless you opt in.

### Quick install — both hosts, project-local (default)

From your project's root (empty folder or existing repo):

```bash
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh
```

This writes into the **current folder** only — nothing global:

```
your-project/
├── .opencode/          opencode skills + agents
├── opencode.json       references.canvas (auto-fetch, no clone)
└── .claude/            claude-code skills + agents
```

### Global install — all projects (explicit opt-in)

```bash
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --global
```

Writes to `~/.config/opencode/` + `~/.claude/`. Not recommended for most setups.

### Install only one host

```bash
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --host opencode
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --host claude-code
```

### Override the CANVAS source

If you run a fork or private repo, point at your own git URL:

```bash
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh \
  | sh -s -- --url git@github.com:you/CANVAS-fork.git
```

### Update an existing install

Every successful install records its sources + scope in `~/.canvas/installed.json`. Replay the same command to refresh any recorded install that is behind its git commit (already-current installs are skipped):

```bash
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --update                 # this project
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --update --global     # global install
curl -fsSL https://raw.githubusercontent.com/dcesartista/CANVAS/main/scripts/install-canvas.sh | sh -s -- --update --project ../other
```

Identical-no-op: re-running right after an install reports "already up to date" and exits 0.

### The CLI (local checkout only)

If you already have the CANVAS repo cloned, run the CLI directly:

```bash
./scripts/canvas list                              # what CANVAS knows how to export
./scripts/canvas export --host opencode   --global --repo <CANVAS git URL>
./scripts/canvas export --host claude-code --global
./scripts/canvas update                            # same as the installer's --update
```

### After any install

**Restart the host tool** (skills aren't hot-reloaded), then run:

| Command | What it does |
| --- | --- |
| `/build-android-starter` | Scaffold a brand-new production-grade Android app |
| `/build-android-feature` | Add one bounded feature to an existing project |
| `/audit` | Score the current work against the Quality Bar (Gate 3) |
| `/perf-review` | Performance score the built work |

## How it works

CANVAS is written **once, host-neutral** and rendered to whichever agent host you use. The heavy knowledge lives in one place; each host gets thin routing files that point at it.

```
core/            the canonical, host-neutral WHAT — manifest (registry) + skills + agents
adapters/        the per-host HOW — render core/ into each host's on-disk format
lib/             the knowledge: android/, process/, cross-cutting/
scripts/canvas   the CLI that renders core/ + corpus into an adapter's format
scripts/install-canvas.sh  the curl | sh bootstrap (delegates to scripts/canvas)
~/.canvas/src/   cached git checkouts (never cloned into the consumer project)
~/.canvas/installed.json  recorded installs — what `--update` replays
```

### The tier model

```
process tier      lib/process/           universal — orchestration, gates, auditor, perf scorer
android           lib/android/           the HOW — native Android (strict Clean + Compose), done deeply
cross-cutting     lib/cross-cutting/     the shared "what": API contract, checklists
```

- **One target, done deeply.** CANVAS specializes in **native Android only** — the entire impl corpus, skills, and workers go deeper into one stack instead of staying shallow across many. There is no "families" tier because there is only one stack; `lib/android/` holds all the Android-specific "how".
- **Share the *what*** (domain models + API contract) — **specialize the *how*** (Compose UI + strict Clean Android).
- **Build the minimum, grow by recurrence** — heavier components are added only when real friction proves the need.
- **Every scaffold is production-grade by default** — auth, DI, architecture, testing, accessibility, and release readiness are included, never bolted on.

### The corpus & the reference seam

The impl corpus lives in `lib/android/reference/*-impl.md` (Clean architecture, DI, concurrency, security, performance, testing, release, …) alongside `lib/android/skills/` (low-level `android-create-*` procedures). The 4 workflow skills orchestrate; each host's adapter exposes this corpus to the agent — via a `references.canvas` git reference (opencode) or a reference-root preamble (claude-code).

### The process

Skills route intent to **workers** (subagents) that read the corpus and build; **gates** (build = Gate 1, tests = Gate 2) and the **auditor** (validation Gate 3, scoring against the Quality Bar) and the **perf scorer** verify the result before it's declared done.

## Sibling projects

CANVAS is Android-native but shares two **host-agnostic / swappable** sibling
repos (referenced, never vendored):

- **`palette`** — the framework-agnostic design-token & component contract (`docs/0001-ui-token-contract.md`, `docs/0002-component-inventory.md`).
- **`ink-basic`** — the Android/Compose implementation of that contract: the swappable default "look" (T3 tokens, `DefaultPalette`, `CanvasTheme`, and the component set). Screens are built from `ink-basic` components, never hand-rolled M3.

`ink-basic` can be deleted/replaced and another palette dropped in without
touching components — while the core-correctness floor (a11y, 48dp touch,
contrast) stays in CANVAS and is never themeable.

## Read first

- **[QUALITY-BAR.md](QUALITY-BAR.md)** — the highest rule. The cited, measurable definition of "production-grade Android." Everything is measured against it.
- **[CONVENTIONS.md](CONVENTIONS.md)** — how agents, skills, and reference docs are authored.
- **[golden-tasks/](golden-tasks/)** — the frozen regression yardstick.

## Governance

- **[docs/evaluation/](docs/evaluation/)** — append-only friction log (what happened, evidence-ranked).
- **[docs/initiatives/](docs/initiatives/)** — triaged candidates; promoted to action items only on real evidence.
- **[golden-tasks/](golden-tasks/)** — re-run after every system change to catch regressions.

Changes are batched, git-tagged per milestone, and re-validated against the golden tasks. The Quality Bar and conventions change deliberately, never silently.
