---
name: android-create-baseline-profile
description: Create/wire the baseline profile in the Android family — startup + hot paths, regenerated per release, shipped in the release build.
user-invocable: false
tools: Read, Write, Glob, Grep
---

Create the **baseline profile** for the app module. Create-only where it doesn't exist.

## Inputs
app module · featured entry points + hot paths.

## Procedure
1. `section-query` `lib/families/android/reference/project-scaffold-impl.md` → `## Baseline Profile` (+ [QUALITY-BAR](../../../../../QUALITY-BAR.md) §5, §7).
2. Guard the startup + hot paths, generate the profile on a reference device, commit + wire shipping builds, so the release build ships it ([QUALITY-BAR](../../../../../QUALITY-BAR.md) §7).
3. Regenerate per release — never ship a stale profile.

## Output
`Glob` + `Grep` the profile artifact + wiring; confirm it's part of the release build.