---
name: perf-review
description: "Score the agentic run that just built something (efficiency + quality dimensions), then surface the single highest-leverage system improvement as an initiatives candidate. Dispatches to the perf-scorer. Improves CANVAS, not the app. Invoke after a build, e.g. \"/perf-review\" after /build-android-feature."
slash_command: /perf-review
usage: "<project-intent>"
---

<!-- canvas-reference-root --> Reference corpus bundled in this plugin: QUALITY-BAR.md at plugin root; impl docs under lib/android/reference/; component skills under lib/android/skills/; theory docs under reference/. Load the file you need before authoring.

Score the run that just occurred. Routes only — determines the subject, dispatches to the `perf-scorer`, relays the report. Read-only; improves CANVAS, not the produced app.

## Step 0 — Scope
- **Default:** the most recent build session (last scaffold/feature).
- Or a specific session the user names.

## Step 1 — Dispatch the perf-scorer
Hand the run to the `perf-scorer` (read-only sub-agent):

> Score the recent <scope> run on efficiency + quality dimensions (skill usage, token efficiency, routing, gate compliance, one-shot rate).
> Emit per-dimension scores + the single highest-leverage system improvement; append it to `docs/initiatives/` triage with recurrence noted. Do NOT edit the system on the fly.

## Step 2 — Report
Relay the `## Perf review:` scorecard + the top improvement. Flag it in `docs/initiatives/`.

## Notes
- Per governance, do **not** edit CANVAS during the run — the human decides what graduates.
- Pairs with `/audit` (its quality reading is reused as one dimension).
