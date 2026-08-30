---
id: audit
kind: workflow
user_invocable: true
description: Score built Android work against the Quality Bar, per matching section, with file:line evidence. Dispatches to the read-only auditor and relays the scored report (pass/partial/fail per section + overall score + must-fix list). This is validation Gate 3. Use before declaring build work done, e.g. "/audit" (current diff) or "/audit the feature at ui/detail in my-app".
---

Score built work against the [Quality Bar](../../QUALITY-BAR.md). Routes only — determines scope, dispatches to the `auditor`, relays the report. Read-only; suggests fixes, applies none.

## Step 0 — Scope
- **Default:** the current git diff — uncommitted + vs `main` (`git diff --name-only` + `git diff --name-only main...HEAD`).
- Or a path / feature / module / scaffold the user named.

## Step 1 — Dispatch the auditor
Hand the scoped work to the `auditor` (read-only sub-agent):

> Audit <scope> for work matching <optional §>.
> Load QUALITY-BAR + the Android impl references, verify each applicable § against the code with file:line evidence, emit pass/partial/fail per § + overall score + must-fix list.

## Step 2 — Report
Relay the auditor's scorecard verbatim. Highlight any *fail* on §1 Architecture, §3 API/concurrency, §4 Security — those are release blockers.

## Notes
- Auditor is read-only — it never edits.
- Must-fix item count + score should be logged to `docs/evaluation/`.
