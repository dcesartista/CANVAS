---
name: android-create-repository-interface
description: Create a domain Repository Interface (port) in the Android family — domain types only, suspend + Flow.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-repository-impl
---

Create one **Repository Interface** (port). Create-only — if it exists, STOP.

## Inputs
`aggregate` · feature/package · the operations the domain needs.

## Procedure
1. `section-query` `reference/domain-theory.md` → `## Repository Interface` and `lib/android/reference/domain-impl.md` → `## Repository Interface`.
2. Write `domain/<feature>/<Aggregate>Repository.kt`: an `interface` in **domain types only** — `suspend` operations + `Flow` for observation. **No DTO/Room/network types** in any signature ([QUALITY-BAR](../../../../QUALITY-BAR.md) §1).
3. The implementation is created separately (`android-create-repository-impl`).

## Output
`Glob` + `Grep` the interface; confirm no data-layer imports.