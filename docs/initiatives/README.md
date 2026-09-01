# Initiatives — triaged candidates

> Candidate improvements to CANVAS, triaged by evidence. Nothing here is *done* until it's proven by recurrence and promoted; nothing is accepted on speculation.
> Lifecycle: **candidate → (recurrence) → promoted → action item → (batch + tag) → done.**

## Candidates

| # | Candidate | Why (evidence / motivation) | Status | Trigger to promote |
|---|---|---|---|---|
| I-1 | Orchestrator + planners | Cross-layer planning pain across GT-A2/A4 | open | a feature span ≥3 layers repeatedly |
| I-2 | Contract CI gate | OpenAPI drift between backend & generated client | open | a contract mismatch bites a golden task |
| I-3 | Multi-AI (claude/gpt) support | Stability across model providers | open | a second model produces a pass |
| I-4 | Modularization guidance | `:domain`/`:data`/`:app` split beyond single-module | open | a scaffold outgrows a single module |
| I-5 | Baseline-profile CI regen | Profile drift after deps bump | open | release task shows stale baseline |
| I-6 | A visual/render gate | GT-A1: the app shipped stock M3 lavender (`#FEF7FF`) past build+lint+ktlint+detekt. Every CANVAS gate is textual; the defect was visual | **promoted** | proven by GT-A1 |
| I-7 | `git init` + first commit in the scaffold | GT-A1: `canvas-commerce` has no repository, so §8 (trunk, Conventional Commits, CI) is unreachable by construction | **promoted** | proven by GT-A1 |
| I-8 | Wire JaCoCo in the scaffold | GT-A1: §6's ≥75% floor is unmeasurable — 26 tests pass, coverage unknown | **promoted** | proven by GT-A1 |
| I-9 | Resolve the Navigation 3 vs Nav Compose 2.x contradiction | GT-A1: QUALITY-BAR §1 mandates Nav 3; `navigation-impl.md` claims Nav 3 in prose but shows 2.x in every sample; the build followed the samples | **promoted** | proven by GT-A1 |
| I-10 | Enforce contract-first generation | GT-A1: 4 hand-written DTO files, no generator task, against §3's "no hand-written DTOs" | **promoted** | proven by GT-A1 |

## Done

| # | Change | Evidence |
|---|---|---|
| — | `scripts/selfcheck.py` + CI | Corpus contracts were unenforced; 31 counts, 32 links, 5 Terms had drifted. Caught a regression on its first live encounter (45ade97 grew a section without updating its count). |
| — | Per-agent tool grants | The read-only auditor and perf-scorer were rendered with Write/Edit by both adapters. |
