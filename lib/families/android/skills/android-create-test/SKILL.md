---
name: android-create-test
description: Create unit + UI tests for an artifact in the Android family — fakes over mocks, ≥75% coverage on new code, semantics-based UI assertions.
user-invocable: false
tools: Read, Write, Glob, Grep, Bash
related_skills:
  - android-create-usecase
  - android-create-repository-impl
  - android-create-viewmodel
  - android-create-composable-screen
---

Create **tests** for one artifact (unit + UI where applicable). Create-only — if they exist, STOP.

## Inputs
artifact (entity / use case / repository / view-model / screen) · feature/package · the cases.

## Procedure
1. `section-query` `lib/families/android/reference/testing-impl.md` → `## Unit Test` / `## UI Test` (+ [QUALITY-BAR](../../../../../QUALITY-BAR.md) §6).
2. **Unit:** JUnit + coroutines-test (dispatcher control) + Turbine for flows; **fakes** over mocks for domain/data.
3. **Integration:** in-memory datastore for queries; real local/network boundaries (not mocks).
4. **UI:** framework UI-test API with **semantics-based assertions**; a few full-flow tests.
5. ≥75% coverage on new code (a floor, not a goal).

## Output
`Glob` + `Grep` the test classes + assertions; run **Gate 2** — must be green.