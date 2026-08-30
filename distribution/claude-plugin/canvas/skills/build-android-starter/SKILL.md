---
name: build-android-starter
description: "Scaffold a new runnable native Android project, production-grade by default per the Quality Bar. Parses project name, target directory, and the backend/contract it consumes, then dispatches to the android-scaffold-worker to follow the Android scaffold reference, call the android-create-* procedures, write the project, and bring it up. Use when starting a brand-new Android app. Example: \"build a project named canvas-kit at ./canvas-kit consuming the contract at https://api.example.com/openapi.json\""
slash_command: /build-android-starter
usage: "<project-intent>"
---

<!-- canvas-reference-root --> Reference corpus bundled in this plugin: QUALITY-BAR.md at plugin root; impl docs under lib/android/reference/; component skills under lib/android/skills/; theory docs under reference/. Load the file you need before authoring.

The user entry point for a **new, named Android project**. Routes only — parses intent, dispatches to the worker, relays the report.

## Step 0 — Parse intent
- **project name** — explicit/quoted. **Required** — ask once if absent.
- **target directory** — default `./<project-name>`.
- **backend/contract** — the backend it consumes + its contract-spec location. **Required** (the client is derived from the contract).
If the request is not a new project → STOP and route to `/build-android-feature`.

## Step 1 — Dispatch the worker
Hand this intent to the `android-scaffold-worker` (a sub-agent), inlined:

> Scaffold a new project named **<name>** at **<target_dir>**, consuming **<backend/contract>**.
> Follow `lib/android/reference/project-scaffold-impl.md`, call the `android-create-*` procedures, write the project, then **Bring it up** (Gate 1 build; install + launch if a target is available; Gate 2 tests) and self-validate. Report status + any friction.

## Step 2 — Report
Relay the worker's `## Scaffold Complete` (build + run status, created paths), then:
> Add features with `/build-android-feature`; run `/audit` before declaring done.

## Notes
- One invocation = one new named project, **production-grade by default** (QUALITY-BAR).
- Runs Gates 1–2; Gate 3 (`/audit`) on request.
