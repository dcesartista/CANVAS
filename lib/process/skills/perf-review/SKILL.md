---
name: perf-review
description: Score the agentic run that just built something — spawns the perf-scorer to rate efficiency + quality dimensions and surface the highest-leverage system improvement (logged as an initiatives candidate). Improves the toolkit, not the app. Invoke e.g. `/perf-review` after a build.
user-invocable: true
allowed-tools: Agent, Bash, Read
---

Score the **run** (process efficiency + quality), not the app. Routes only — gathers inputs, spawns the `perf-scorer`, relays the scorecard, logs the top improvement candidate.

## Step 0 — Inputs
- the work built (path / diff) + its **audit score** — if no recent `/audit` exists, run it first (the perf-scorer needs it for D1).
- any session signals available (tokens, tool-call counts, rejected/duplicate calls, which skills/workers ran).

## Step 1 — Spawn the perf-scorer
> Score this run. Work: <path/diff>. Audit result: <score + must-fixes>. Classify the work nature, score D1–D6, and name the single highest-leverage system improvement.

## Step 2 — Report + log
Relay the `## Perf review:` scorecard. Append the **top improvement** to `docs/initiatives/` triage (recurrence noted). Per P1, do **not** edit the system on the fly — the human decides what graduates.

## Notes
- Encode-on-recurrence: a one-off is noted, not yet acted on; a pattern across runs graduates to a change.
- Pairs with `/audit` — that scores the artifact; this scores how it was produced.