---
id: build-android-feature
kind: workflow
user_invocable: true
description: Build a bounded feature in an existing Android project, in strict Clean layer order (domain -> data -> presentation) and contract-first. Parses the feature name + target project, then dispatches to the android-feature-worker, which follows the impl references, calls the android-create-* procedures per layer, and self-validates. Use when adding a feature to an existing scaffold. Example: "build the feature 'cart' in my-app"
---

The user entry point for **adding a bounded feature** to an existing scaffold. Routes only — parses intent, dispatches to the worker, relays the report.

## Step 0 — Parse intent
- **feature name** — explicit/quoted. **Required** — ask once if absent.
- **target project** — default current repo. **Required**: must already be a CANVAS scaffold (have `domain/`, `data/`, `presentation/`).
If the target is not an existing scaffold → STOP and route to `/build-android-starter`.

## Step 1 — Dispatch the worker
Hand this intent to the `android-feature-worker` (a sub-agent), inlined:

> Build feature **<name>** in **<project>**:
> 1. **domain** — entity/value-object(s) + repository interface + use case(s).
> 2. **data** — DTO(s) + mapper(s) + datasource(s) (network/Room) + repository impl.
> 3. **presentation** — ViewModel + navigation route + Composable screen(s).
> 4. **wiring + tests + contract** — DI bindings, routes, unit/UI tests, generated client refresh.
> Follow `lib/android/reference/{domain,data,presentation}-impl.md`; call the matching `android-create-*` procedures; self-validate each layer before the next. Report status + any friction.

## Step 2 — Report
Relay the worker's `## Feature Complete` (paths + gate statuses), then:
> Run `/audit` before declaring done.

## Notes
- Strict layer order is a Quality-Bar hard rule — never skip back-to-front.
- Runs Gates 1–2 per layer; Gate 3 (`/audit`) on request.
