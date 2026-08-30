---
name: build-android-feature
description: Build a feature into an existing project, in the family's prescribed artifact order (Phase 1 → Phase 2 → Phase 3 → wiring), consuming the backend contract. Spawns the android-feature-worker.
user-invocable: true
allowed-tools: Agent, AskUserQuestion, Bash, Read
---

The user entry point for building a **feature** into an existing project. Routes only — gathers intent and spawns the worker.

## Step 0 — Gather intent
If not supplied, ask (one batched `AskUserQuestion`):
- **feature / module** name
- the **backend endpoints** it uses (resource + operations, from the contract)
- the **screens** + interactions

## Step 1 — Spawn the worker
Spawn `android-feature-worker` with the intent inlined:

> Build a feature. **feature:** <name> · **endpoints:** <resource + operations> · **screens:** <specifies>.
> Follow the family's artifact order (Phase 1 → Phase 2 → Phase 3 → wiring) via the family `android-create-*` skills, **contract-first** (never hand-author what the contract generates). Validate (Gate 1 + Gate 2) before reporting, then surface `/audit` (Gate 3).

## Step 2 — Report
Relay the worker's `## Android Feature Complete`. Then:
> Run `/audit` before declaring done.

## Notes
- Contract-first — never hand-author what the contract generates ([QUALITY-BAR](../../../../QUALITY-BAR.md) §1, §3).