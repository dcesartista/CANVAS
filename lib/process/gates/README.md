# Validation gates

> The checks a built slice must pass before it's considered done. Run by the worker after building, and in CI on every PR.
> Universal (process tier) — the protocol is the same everywhere; the exact *commands* are per-stack, supplied by the family.

Run in order; each must pass before the next matters. **No gate may be skipped.**

## Gate 1 — Type-check / build
The type system is the first, cheapest correctness gate.
- Run the family-supplied typecheck/build command — must be **clean**.
- On error: read the actual definition (`Grep`+`Read`) and fix — **never by guessing**. Fix all, re-run once. If still failing, surface the exact output.

## Gate 2 — Tests
Per the test pyramid ([QUALITY-BAR](../../../QUALITY-BAR.md) §6).
- Run the family-supplied test command — must be **green**; coverage ≥75% on new code (a floor, not a goal).
- Domain + use cases tested with **fakes**; implementations tested against real local storage/network.

## Gate 3 — Audit against the Quality Bar
Conformance to [QUALITY-BAR](../../../QUALITY-BAR.md) for the work done — run `/audit` (or spawn the **`auditor`** agent directly).
- The auditor loads QUALITY-BAR + the family reference, verifies each *applicable* § against the code with file:line evidence, and emits **pass/partial/fail** per § + an overall score + a must-fix list.
- **Gate passes** when no § on Architecture / API + concurrency / Security is a **fail**.
- Pairs with `/perf-review`, which scores the *run* (efficiency) and reuses this audit score as its architecture dimension.

## On failure
A gate failure blocks "done". Fix at the source (read the real definition), re-run, and only proceed when green. **Never `--no-verify`, never skip a gate to claim completion** — both are canary violations for `/perf-review`.