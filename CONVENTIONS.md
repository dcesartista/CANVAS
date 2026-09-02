# Conventions — how CANVAS is authored

> Rules for writing agents, skills, and reference docs in this repo.
> The goal: a system whose pieces an LLM agent can read cheaply, apply consistently, and that humans can audit.

These conventions are themselves subject to the governance loop (`docs/initiatives/`) — but they start from the [Quality Bar](QUALITY-BAR.md).

---

## 1. The three tiers (hard invariant)

```
process tier      lib/process/           universal — orchestration, gates, auditor, perf scorer
android           lib/android/           the HOW — native Android (strict Clean + Compose), done deeply
cross-cutting     lib/cross-cutting/     the shared "what": API contract, checklists
```

**Invariant:** the **process tier may contain ZERO layer-decomposition or framework-idiom knowledge** — ever. Layer models, stacks, and Compose/Kotlin syntax live only in `lib/android/`. If you find yourself writing Compose/Kotlin/Gradle/Hilt idioms in a process-tier file, stop — that belongs in the Android tier.

**Single-target model:** CANVAS specializes in **native Android only**. There is no "families" tier because there is only one stack; `lib/android/` holds all the Android-specific "how". This is what lets CANVAS go *deeper* than a multi-family system: the whole impl corpus, skill set, and worker library are dedicated to one stack's best practices.

## 2. Stack options (within the one Android target)

- The one target is **native Android**: **Kotlin · Jetpack Compose · Hilt · strict Clean**, exactly as profiled in the impl reference docs.
- Variants (e.g. modularization choices, feature scenarios) are **decisions the worker makes per-project** against the reference — never a second divergent archetype at the top tier.
- Rules in `lib/android/` **cite the [Quality Bar](QUALITY-BAR.md)** — they never weaken or redefine it. They are *how* to meet the universal bar in this stack.

## 3. Reference docs

The single source of architectural knowledge, read on demand — never embedded in agents.

**Theory / impl split**
- `reference/*-theory.md` — *what / why*, stack-agnostic, cites Quality-Bar authorities. Single source of truth.
- `lib/android/reference/*-impl.md` — *how*, in the Android stack/syntax. This is where CANVAS goes deep.

**Grep-addressable headings (the read contract)**
- Every `##` heading is a **Term** — the canonical name for one concept. One concept = one heading. No synonyms at `##` level (platform dialect goes in the body).
- Each `##` heading carries a line count: `## Term <!-- N -->` where `N` = lines from this heading up to (not including) the next `##` heading — or to end of file for the final heading. Agents extract `N` as the `limit` in `Read(file, offset=heading_line, limit=N)` to read exactly one section. A missing, non-integer, or drifted `<!-- N -->` is a violation: an `N` smaller than the real section silently truncates it, and the agent never learns it read a partial rule.
- **Enforced, not trusted:** `scripts/selfcheck.py` verifies every count, every `## Term` cross-reference, every relative link, and that no read-only agent renders with a mutating tool. `--fix` rewrites drifted counts. It runs in CI on every PR; recompute counts after editing any reference doc.
- **`section-query` pattern:** `Grep "^## <Term>"` → `Read(offset, limit=N)`. Never read a whole reference file unless style-matching a new one.

## 4. Component model (build the minimum; grow by recurrence)

| Component | Location | Role | Must contain |
|---|---|---|---|
| **Workflow skill** | `core/skills/` (host-neutral source; rendered per host) | User entry point — routes, loads context, spawns | single user-facing task; owns the workflow |
| **Worker** | `core/agents/` (host-neutral source; rendered per host) | Reads plan → calls procedure skills → writes code → self-validates | `## Input`, `## Scope`, `## Search Protocol`, `## Output` (Glob+Grep verified) |
| **Procedure skill** | `lib/android/skills/` | Thin, **create-only** "hands" for one artifact type | one task, references reference docs, no branching |
| **Reference doc** | `reference/` + `lib/android/reference/` | Theory + deep Android impl (§3) | grep-addressable `## Term <!-- N -->` headings |
| **Planner** *(add when features span ≥3 layers)* | `lib/android/planners/` | Explores one layer read-only, reports findings + impact | read-only tools only |
| **Orchestrator** *(add with planners)* | `core/agents/` | Brain-only — returns decision blocks, spawns nothing, writes only plan artifacts | structured `Decision:` blocks |
| **Auditor** *(Phase 3)* | `core/agents/` | Scores output against the Quality Bar | per-§ pass/partial/fail |
| **Perf scorer** *(Phase 3)* | `core/agents/` | Scores session efficiency/quality across versions | metrics |

> Day-1 minimum = workflow skill + worker + procedure skills + reference. Orchestrator/planners are deferred until cross-layer planning pain is felt.

## 5. Authoring rules

- **Agents are the brain (lean):** decision logic only — *what to do, when, what to check on failure*. No step-by-step procedures (those go in skills). No embedded reference content (Grep it).
- **Skills are the hands (thin):** one task, create-only, no branching — the agent decides *which* skill to call.
- **Grep-first:** before any `Read`, ask "do I need the whole file or one section/symbol?" Default to `Grep` → targeted `Read(offset, limit)`.
- **Pass paths, not contents** between components where possible; verify outputs exist (`Glob` + `Grep`) before reporting them.
- **Cite, don't restate:** a rule that's a universal truth → reference/Quality-Bar; a rule that's "do this in this workflow" → the agent body.

## 6. Naming

- Reference: `<topic>-theory.md` (root), `<topic>-impl.md` (in `lib/android/reference/`).
- Skills (procedure): `<layer>-create-<artifact>` (create-only).
- Agents: `<role>` or `<persona>-<domain>-<role>` — suffixes `-worker`, `-planner`, `-orchestrator`.
- Terms (reference `##` headings): canonical, identical across the corpus.

## 7. Versioning & governance

- CANVAS is git-tagged per milestone (cheap rollback).
- Changes flow through the governance loop: friction logged in `docs/evaluation/` → candidates in `docs/initiatives/` → promoted on real evidence → batched → tagged → golden tasks re-run.
- The [Quality Bar](QUALITY-BAR.md) and these conventions are authoritative; they change deliberately, never silently.
