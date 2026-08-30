---
name: android-create-navigation
description: Register a Navigation route in the Android family — route + args + deny-by-default guards on authenticated destinations.
user-invocable: false
tools: Read, Write, Glob, Grep
related_skills:
  - android-create-composable-screen
---

Register/add one **navigation route**. Create-only where the route is new (extend the existing graph otherwise).

## Inputs
`screen` · feature/package · route + arguments · auth requirement.

## Procedure
1. `section-query` `lib/android/reference/presentation-impl.md` → `## Navigation`.
2. Add the route + destination to the navigation graph; pass arguments as route params.
3. Any authenticated destination gets a **deny-by-default guard driven by auth state** ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §4); unauthenticated → redirect to sign-in. Back-stack/args behavior per the family reference.

## Output
`Glob` + `Grep` the route registered in the graph; confirm the auth guard exists where required.