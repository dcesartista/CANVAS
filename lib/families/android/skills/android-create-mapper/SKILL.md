---
name: android-create-mapper
description: Create a Mapper (DTO/Room ↔ domain) in the Android family's data tier — pure, one direction each, no side effects.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-dto
  - android-create-domain-entity
---

Create one **Mapper** set. Create-only — if it exists, STOP.

## Inputs
source type + target type (`dto/room ↔ domain`) · feature/package.

## Procedure
1. `section-query` `reference/data-theory.md` → `## Mapper` and `lib/families/android/reference/data-impl.md` → `## Mapper`.
2. Write `data/<feature>/Mapper.kt`: pure functions, one direction each (source→target and target→source where needed), no side effects, no framework dependencies.
3. Mapping logic lives here — never in entities, DTOs, or repositories ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §2).

## Output
`Glob` + `Grep` the mapper functions; confirm pure + data-tier placement, domain types on the domain-facing side.