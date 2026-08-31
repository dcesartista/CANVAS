# CANVAS

> An agentic Android coding system for building world-class, production-grade native Android apps (Kotlin · Jetpack Compose) rapidly, by leveraging AI against an authoritative quality bar.

CANVAS is where you paint production-grade Android apps. It lifts precise components (entities, use cases, repositories, ViewModels, Composables) and places them exactly where Clean Architecture says — anchored to a single authoritative quality bar, so a small team ships like a big one.

**Status: Phase 0 — anchor & scaffold.** The repo holds the anchor documents and the Android impl skeleton. Content is built from real friction in later phases (extract, don't predict).

## Install & use

CANVAS is distributed per host — **"share the what, specialize the how."** Pick your agent host and follow its install path. After any install, **restart the host tool** (skills aren't hot-reloaded), open a consumer project, then run the slash commands below.

| Command | What it does |
| --- | --- |
| `/build-android-starter` | Scaffold a brand-new production-grade Android app |
| `/build-android-feature` | Add one bounded feature to an existing project |
| `/audit` | Score the current work against the Quality Bar (validation Gate 3) |
| `/perf-review` | Performance score the built work |

### Claude Code — one-tap plugin (no repo cloning)

```bash
claude plugin marketplace add <CANVAS git repo>
claude plugin install canvas@canvas-marketplace
```

The full quality corpus is bundled into the plugin, so nothing else is needed. Rebuild the bundle after a CANVAS change with:

```bash
./scripts/canvas export --host claude-plugin     # rebuild distribution/claude-plugin
```

### opencode

opencode has no file marketplace (plugins are npm TS/JS modules, which **cannot carry Agent Skills** today), so install is:

```bash
# all projects + corpus auto-fetched from the CANVAS repo (nothing to clone)
./scripts/canvas export --host opencode --global --repo <CANVAS git URL>

# or a single project, referencing a local CANVAS checkout via path:
./scripts/canvas export --host opencode --target <project>
```

`--global --repo` drops the 4 skills into `~/.config/opencode/skills/` and adds a `references.canvas` entry using `repository:` so opencode auto-fetches the corpus.

### Any project, any host — the CLI

If you already have a CANVAS checkout, the CLI renders/installs to any host:

```bash
./scripts/canvas list                          # what CANVAS knows how to export
./scripts/canvas export --host opencode    --target <project>   # per-project
./scripts/canvas export --host opencode    --global --repo <url>
./scripts/canvas export --host claude-code --global             # ~/.claude/ (all projects)
./scripts/canvas export --host claude-plugin                    # rebuild the Claude plugin bundle
```

## How it works

CANVAS is written **once, host-neutral** and rendered to whichever agent host you use. The heavy knowledge lives in one place; each host gets thin routing files that point at it.

```
core/            the canonical, host-neutral WHAT — manifest (registry) + skills + agents
adapters/        the per-host HOW — render core/ into each host's on-disk format
distribution/    pre-built, committed bundles (e.g. the Claude plugin)
lib/             the knowledge: android/, process/, cross-cutting/
scripts/canvas   the CLI that renders core/ + corpus into an adapter's format
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

The impl corpus lives in `lib/android/reference/*-impl.md` (Clean architecture, DI, concurrency, security, performance, testing, release, …) alongside `lib/android/skills/` (low-level `android-create-*` procedures). The 4 workflow skills orchestrate; each host's adapter exposes this corpus to the agent — via a `references.canvas` git reference (opencode), a bundled plugin corpus (Claude plugin), or a reference-root preamble (claude-code).

### The process

Skills route intent to **workers** (subagents) that read the corpus and build; **gates** (build = Gate 1, tests = Gate 2) and the **auditor** (validation Gate 3, scoring against the Quality Bar) and the **perf scorer** verify the result before it's declared done.

## Read first

- **[QUALITY-BAR.md](QUALITY-BAR.md)** — the highest rule. The cited, measurable definition of "production-grade Android." Everything is measured against it.
- **[CONVENTIONS.md](CONVENTIONS.md)** — how agents, skills, and reference docs are authored.
- **[golden-tasks/](golden-tasks/)** — the frozen regression yardstick.

## Governance

- **[docs/evaluation/](docs/evaluation/)** — append-only friction log (what happened, evidence-ranked).
- **[docs/initiatives/](docs/initiatives/)** — triaged candidates; promoted to action items only on real evidence.
- **[golden-tasks/](golden-tasks/)** — re-run after every system change to catch regressions.

Changes are batched, git-tagged per milestone, and re-validated against the golden tasks. The Quality Bar and conventions change deliberately, never silently.
