---
name: android-create-dto
description: Create a Data Transfer Object in the Android family's data tier — only when the contract client does NOT already generate the payload type (contract-first guardrail).
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-mapper
---

Create one **DTO**. Create-only — if it exists, STOP.

## Inputs
`dto_name` · feature/package · payload shape + source.

## Procedure
1. `section-query` `reference/data-theory.md` → `## DTO` and `lib/android/reference/data-impl.md` → `## DTO`.
2. **Contract-first guardrail:** if the payload type is (or should be) generated from the contract, STOP — never hand-write DTOs for contract-covered payloads ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §3).
3. Write `data/<feature>/<X>Dto.kt`: a plain data holder mirroring the payload; validate where the source is untrusted; stays in the data tier.

## Output
`Glob` + `Grep` the DTO; confirm it lives in data and is consumed by mappers, never by domain.