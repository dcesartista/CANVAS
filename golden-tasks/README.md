# Golden Tasks — the frozen regression yardstick

> The CANVAS analog of unit tests: frozen Android build tasks that any system change must not break. They are **the test suite for the toolkit itself** — "did CANVAS get better or worse?"
> Each task is scored **pass / partial / fail** per Quality-Bar item with file:line evidence; total score monitors the system over versions.

## How to run

1. Pick a task below (or all five) and run the corresponding workflow: `/build-android-starter` → a task, then `/build-android-feature` or scaffolded feature work, then `/audit`.
2. Score the result against the [Quality-Bar §1–§8](../QUALITY-BAR.md) items it touches.
3. Record scores + metrics (tokens/feature, one-shot rate, rework) in [docs/evaluation/](../docs/evaluation/) against the system version (VERSION + git tag).
4. A change that regresses golden-task score is **not** merged until fixed or deliberately accepted via the governance loop.

## The tasks

### GT-A1. Scaffold a runnable production scaffold
Run `/build-android-starter` with a chosen package + app name. **Exit criterion:** `./gradlew assembleDebug testDebugUnitTest ktlintCheck detekt lint jacocoCoverageVerification` all green; project launches on an emulator; **the launched app renders the palette, not Material baseline** (sample the page background — see `project-scaffold-impl.md` → `## Bring-up`); the project is a git repository with a first commit. Scored on: project structure §1, tooling/version catalog §7, auth baseline §4, DI §1, coverage floor §6, design-system seam §5, delivery §8.

> The 2026-09-02 run passed the build/test/lint half and still shipped stock Material, a forked design system, an unmeasured coverage floor and no repository — see [docs/evaluation/GT-A1-2026-09-02.md](../docs/evaluation/GT-A1-2026-09-02.md). The render, coverage and repository clauses above exist because of it.

### GT-A2. Build a bounded domain → data → presentation feature
Scaffold, then add a feature with a real entity (e.g. an `Item` with an `ItemId`), a repository (domain interface + Room/Retrofit impl + mapper), a use case, and a Compose screen wired to a ViewModel. **Exit criterion:** feature compiles, is unit-tested (≥75% new-code coverage), UI test renders it. Scored on: strict-Clean layer order §1, purity §1, UDF §1, testing §6, accessibility §5.

### GT-A3. Auth flow end-to-end
Scaffold with auth. **Exit criterion:** login/register/token-refresh (401 → `Authenticator`) / logout work against a live backend; token in secure storage; deny-by-default nav guard blocks authed screens when unauthenticated. Scored on: §4, §3 concurrency, §1 UDF.

### GT-A4. Offline-first + state survival
Feature with a local Room cache and remote datasource; kill/rotate during an in-flight load. **Exit criterion:** data survives process death (SSOT, `@Transaction`, migration path), UI restores state via `rememberSaveable`/SavedStateHandle, no crash, no jank. Scored on: §2 data, §1 state persistence, §5 performance/a11y.

### GT-A5. Release-readiness pass
A complete scaffold passes the full release audit. **Exit criterion:** `/audit` returns no `fail` on §7 (R8/AAB/baseline profile/version catalog/CI) — including a green CI run and an `assembleRelease` build with baseline profile + minification. Scored on: §7 release, §8 delivery.

## Scoring rubric

- **pass** — meets all cited Quality-Bar items for that task (evidence: file + line).
- **partial** — meets some; each miss must be a listed, concrete gap.
- **fail** — breaks a hard invariant (e.g. domain imports `android.*`, tests don't run, gate skipped).

A task is only **pass** when every gate (typecheck → tests → audit) cleared that task's path with no skips.
