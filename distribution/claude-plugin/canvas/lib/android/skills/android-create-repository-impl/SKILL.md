---
name: android-create-repository-impl
description: Create a Repository Implementation of a domain port in the Android family's data tier — composes datasources + mappers, offline-first, returns domain types via Flow.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-repository-interface
  - android-create-datasource
  - android-create-mapper
---

Create one **Repository Implementation** (composing its datasources + mappers). Create-only — if it exists, STOP.

## Inputs
`aggregate` · feature/package · the domain `Repository Interface` it implements · remote + local sources.

## Procedure
1. `section-query` `reference/data-theory.md` → `## Repository Implementation` and `lib/android/reference/data-impl.md` → `## Repository Implementation`.
2. `Grep`+`Read` the domain interface signatures before writing — never assume.
3. Write `data/<feature>/<X>RepositoryImpl.kt` `implements` the domain interface: composes datasources via mappers, **offline-first**, surfaces failures without leaking data-tier types; exposes `Flow` of domain types.

## Output
`Glob` + `Grep`; confirm it `implements` the domain interface and returns domain types (no DTO/Room leak, signatures match the port).