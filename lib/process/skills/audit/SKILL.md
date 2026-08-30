---
name: audit
description: Audit built work against the Quality Bar per § — spawns the read-only auditor and relays the scored report. This is validation Gate 3. Invoke e.g. `/audit` (current diff) or `/audit the feature at ui/detail in my-app`.
user-invocable: true
allowed-tools: Agent, Bash, Read
---

Score built work against the [Quality Bar](../../../../QUALITY-BAR.md). Routes only — determines scope, spawns the `auditor`, relays the report. Read-only; suggests fixes, applies none.

## Step 0 — Scope
- **Default:** the current git diff — uncommitted + vs `main` (`git diff --name-only` + `git diff --name-only main...HEAD`).
- Or a path / feature / module / scaffold the user named.

## Step 1 — Spawn the auditor
Spawn `auditor` with the scope inlined:

> Audit <scope>. `section-query` QUALITY-BAR per § + the family reference; verify each *applicable* § against the code with file:line evidence; score and list must-fixes.

## Step 2 — Report
Relay the auditor's `## Audit:` block verbatim (score · findings · must-fix · N/A). If any **must-fix**, state that Gate 3 is **not passed** until they're resolved.

## Notes
- Fulfills **validation Gate 3** (`lib/process/gates`) — run it after a feature/scaffold build, before declaring done.
- Pairs with `/perf-review`, which scores the *run* (efficiency) using this audit's score as its architecture dimension.