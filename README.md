# CANVAS

> An agentic Android coding system — **Cesartista Android Native Verified App System** — for building world-class, production-grade native Android apps (Kotlin · Jetpack Compose) rapidly, by leveraging AI against an authoritative quality bar.

CANVAS is where you paint production-grade Android apps. It lifts precise components (entities, use cases, repositories, ViewModels, Composables) and places them exactly where Clean Architecture says — anchored to a single authoritative quality bar, so a small team ships like a big one.

**Status: Phase 0 — anchor & scaffold.** The repo holds the anchor documents and the Android impl skeleton. Content is built from real friction in later phases (extract, don't predict).

## Read first

- **[QUALITY-BAR.md](QUALITY-BAR.md)** — the highest rule. The cited, measurable definition of "production-grade Android." Everything is measured against it.
- **[CONVENTIONS.md](CONVENTIONS.md)** — how agents, skills, and reference docs are authored.
- **[golden-tasks/](golden-tasks/)** — the frozen regression yardstick.

## The model

```
process tier      lib/process/           universal — orchestration, gates, auditor, perf scorer
android           lib/android/           the HOW — native Android (strict Clean + Compose), done deeply
cross-cutting     lib/cross-cutting/     the shared "what": API contract, checklists
```

- **One target, done deeply.** Unlike full-stack CRUISE, CANVAS specializes in **native Android only** — the entire impl corpus, skills, and workers go deeper into one stack instead of staying shallow across many. There is no "families" tier because there is only one stack; the `lib/android/` tier holds all the Android-specific "how".
- **Share the *what*** (domain models + API contract) — **specialize the *how*** (Compose UI + strict Clean Android).
- **Build the minimum, grow by recurrence** — heavier components are added only when real friction proves the need.
- **Every scaffold is production-grade by default** — auth, DI, architecture, testing, accessibility, and release readiness are included, never bolted on.

## Host-agnostic distribution

CANVAS is written **once, host-neutral** and rendered to whichever agent host you use.

- **[core/](core/)** — the canonical, host-neutral source: `manifest.json` (the registry) + `skills/` (workflow entry points) + `agents/` (subagents/workers).
- **[adapters/](adapters/)** — per-host renderers that map `core/` onto each host's on-disk format. Ships: `opencode/`, `claude-code/`. Planned: `cursor/`, `copilot/`, `codex/`.
- **[scripts/canvas](scripts/canvas)** — the CLI that renders and installs.

```bash
./scripts/canvas list                          # what CANVAS knows how to export
./scripts/canvas export --host opencode    --target <project>   # per-project
./scripts/canvas export --host claude-code --target <project>   # per-project
./scripts/canvas export --host claude-code --global             # ~/.claude/ (all projects)
```

**opencode** — per-project install writes `<project>/.opencode/skills/*/SKILL.md`,
`<project>/.opencode/agent/*.md`, and merges `references.canvas` into
`<project>/opencode.json` pointing at this repo — so `lib/android/reference/`
and `lib/android/skills/` are reachable from any consumer project and update
with a single `git pull` of CANVAS.

**claude-code** — installs skills → `.claude/skills/` and subagents →
`.claude/agents/`. `--global` installs into `~/.claude/` for all projects.
Each exported file carries a one-line "reference root" preamble pointing the
model at the CANVAS corpus (no config merge needed — Claude Code has no
`references` key, so the corpus is addressed by the CANVAS repo path).

Restart the host tool after installing, open a consumer project, then e.g.
`/build-android-starter`, `/build-android-feature`, `/audit`, `/perf-review`.

## Governance

- **[docs/evaluation/](docs/evaluation/)** — append-only friction log (what happened, evidence-ranked).
- **[docs/initiatives/](docs/initiatives/)** — triaged candidates; promoted to action items only on real evidence.
- **[golden-tasks/](golden-tasks/)** — re-run after every system change to catch regressions.

Changes are batched, git-tagged per milestone, and re-validated against the golden tasks. The Quality Bar and conventions change deliberately, never silently.
