---
name: android-create-hilt-module
description: Create/extend a Hilt DI module in the Android family — interface→impl bindings with explicit scope; no manual construction in production code.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-repository-impl
  - android-create-viewmodel
---

Create a **DI module** (or extend the existing one). Create-only where the module is new.

## Inputs
feature/package · the bindings needed (interface→impl, dependencies, scope).

## Procedure
1. `section-query` `lib/families/android/reference/project-scaffold-impl.md` → `## Hilt Module` ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §1).
2. Add the bindings: interface → implementation with explicit scope (singleton/feature-scoped); network/db/factory bindings where the scaffold prescribes.
3. Bindings satisfy every consumption site; no manual construction in production code.

## Output
`Glob` + `Grep` each binding present; confirm consumption sites build (Gate 1).