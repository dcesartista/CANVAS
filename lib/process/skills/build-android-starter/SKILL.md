---
name: build-android-starter
description: Scaffold a NEW runnable project on demand, production-grade by default per the Quality Bar — parses project name, target directory, and the backend/contract it consumes, then spawns the android-scaffold-worker, which follows the family scaffold reference, calls the family android-create-* skills, writes the project, and Brings it up. Invoke e.g. `/build-android-starter create a project named "canvas-kit" at ./canvas-kit consuming the contract at https://api.example.com/openapi.json`.
user-invocable: true
allowed-tools: Agent, AskUserQuestion, Bash, Read
---

The user entry point for a **new, named project**. Routes only — parses intent, spawns the worker, relays the report.

## Step 0 — Parse intent
- **project name** — explicit/quoted. **Required** — ask once if absent.
- **target directory** — default `./<project-name>`.
- **backend/contract** — the backend it consumes + its contract-spec location. **Required** (the client is derived from the contract).
If the request is not a new project → STOP and route to `/build-android-feature`.

## Step 1 — Spawn the worker
Spawn `android-scaffold-worker` with the intent inlined:

> Scaffold a new project named **<name>** at **<target_dir>**, consuming **<backend/contract>**.
> Follow `lib/families/android/reference/project-scaffold-impl.md`, call the family `android-create-*` skills, write the project, then **Bring it up** (Gate 1 build; install + launch if a target is available; Gate 2 tests) and self-validate with Glob+Grep. Report status + any friction.

## Step 2 — Report
Relay the worker's `## Scaffold Complete` (build + run status, created paths), then:
> Add features with `/build-android-feature`; run `/audit` before declaring done.

## Notes
- One invocation = one new named project, **production-grade by default** ([QUALITY-BAR](../../../../QUALITY-BAR.md)).
- Runs Gates 1–2; Gate 3 (`/audit`) on request.