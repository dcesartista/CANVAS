---
name: android-create-datastore
description: Create a Room datastore (entity + DAO) in the Android family's data tier — structured, relational, forward-only migrations.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-mapper
  - android-create-repository-impl
---

Create one **Room datastore** (entity + DAO). Create-only — if it exists, STOP.

## Inputs
entity name · feature/package · fields + relations · integrity rules.

## Procedure
1. `section-query` `lib/families/android/reference/data-impl.md` → `## Datastore` (+ [QUALITY-BAR](../../../../../QUALITY-BAR.md) §2).
2. Write the Room entity + DAO in `data/<feature>`: DAO as `suspend` queries + `Flow` for observation; `@Transaction` for multi-row writes; indices + foreign keys where integrity matters.
3. Migrations are **forward-only** (Migration objects / auto-migration, schema versioned + exported); never destructive without explicit review.
4. Data-tier only — exposed to domain via `android-create-mapper` + `android-create-repository-impl`.

## Output
`Glob` + `Grep` the entity, DAO, and migration; confirm data-tier placement, no domain leakage.