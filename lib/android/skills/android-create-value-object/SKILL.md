---
name: android-create-value-object
description: Create a domain Value Object (immutable, equality by value, invalid state unrepresentable) in the Android family's domain tier.
user-invocable: false
tools: Read, Write, Glob, Grep
---

Create one domain **Value Object**. Create-only — if it exists, STOP.

## Inputs
`name` · feature/package · value fields · constraints.

## Procedure
1. `section-query` `reference/domain-theory.md` → `## Value Object` and `lib/android/reference/domain-impl.md` → `## Value Object`.
2. Write `domain/<feature>/<Name>.kt`: immutable, equality by value, validated construction — invalid states unrepresentable; no identity, no mutable state.
3. **Pure domain**, no framework/data/DI types ([QUALITY-BAR](../../../../QUALITY-BAR.md) §1). Used as entity/use-case field types (`android-create-domain-entity`).

## Output
`Glob` + `Grep` the value class + validation; confirm only domain imports.