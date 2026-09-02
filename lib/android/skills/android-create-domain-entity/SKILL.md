---
name: android-create-domain-entity
description: Create a pure-Kotlin domain Entity (identity-based, invariant-enforcing) in the Android domain layer.
user-invocable: false
tools: Read, Write, Glob, Grep
---

Create one domain **Entity**. Create-only — if it exists, STOP.

## Inputs
`entity_name` · feature/package · fields · invariants.

## Procedure
1. `section-query` `reference/domain-theory.md` → `## Entity` and `lib/android/reference/domain-impl.md` → `## Entity`.
2. Write `domain/<feature>/<Entity>.kt`: identity-based data class, behavior methods enforce the invariants, equality by identity.
3. **Pure domain** — no framework/UI/data/DI types ([QUALITY-BAR](../../../../QUALITY-BAR.md) §1). Field types are Value Objects (`android-create-value-object`), never raw primitives.

## Output
`Glob` + `Grep` the class + its id; confirm only domain imports.