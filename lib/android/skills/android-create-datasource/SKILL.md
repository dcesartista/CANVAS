---
name: android-create-datasource
description: Create a Data Source (remote or local boundary) in the Android family's data tier — suspend/Flow, explicit dispatcher boundary, no blocking.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-repository-impl
---

Create one **Data Source** (remote or local boundary). Create-only — if it exists, STOP.

## Inputs
`name` · feature/package · boundary type (remote/local) · the data-tier types it handles.

## Procedure
1. `section-query` `reference/data-theory.md` → `## Data Source` and `lib/android/reference/data-impl.md` → `## Data Source`.
2. Write `data/<feature>/<X>DataSource.kt`: exposes `suspend`/`Flow` operations over its transport (remote via the generated/contract client; local via `android-create-datastore`). Coroutines/Flow only; explicit dispatcher at the boundary; never blocks ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §3).
3. Data-tier types stay here; never leak outward.

## Output
`Glob` + `Grep` the data source (interface + impl); confirm no domain-facing leak.