---
name: android-create-usecase
description: Create a domain Use Case (one user intent) in the Android family — constructor-injected ports, suspend operator invoke.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-repository-interface
---

Create one **Use Case**. Create-only — if it exists, STOP.

## Inputs
`name` (a user intent) · feature/package · input/output · the ports it needs.

## Procedure
1. `section-query` `reference/domain-theory.md` → `## Use Case` and `lib/android/reference/domain-impl.md` → `## Use Case`.
2. Write `domain/<feature>/<Name>.kt`: a `class` with **constructor-injected** repository interfaces + `suspend operator fun invoke(...)`; returns domain types; depends only on domain ports.
3. Verify port signatures (`Grep`+`Read`) before calling — never assume.

## Output
`Glob` + `Grep` the class + `invoke`; confirm pure domain (domain imports only).