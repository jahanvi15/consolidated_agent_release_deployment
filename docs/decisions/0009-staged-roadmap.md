# 0009. Follow the staged roadmap (features 1–13, Stages 0–7)

- **Status:** Accepted
- **Date:** 2026-10-24
- **Decider:** Jahanvi Joshi

## Context

The product plan defines 13 features in 7 stages, ordered by what each feature needs
(full table in `docs/project-context.md`). It left five choices open. Early backlog items
for "Stage 1" were written before the plan was in the repository and didn't follow it.

## Options considered (the plan's open choices)

1. Move 12 (dependency map) and/or 4 (quality test) into Stage 1 — larger first version.
2. Build 13 (fake business systems) alongside Stage 1 — more realistic testing, slower first version.
3. Start a basic audit record (part of 9) in Stage 1 — cheap now, hard to retrofit.
4. Move 10 (watching for outside changes) after Stage 7.

## Decision

- Order: **0 → 1, 2, 3 → 12, 4 → 13 → 5 → 8, 9 → 10 → 6, 7**; 11 grows throughout.
- **Stage 1 = features 1, 2, 3** (the one-month first version). 12 and 4 stay in Stage 2.
- **13 stays in Stage 3.** Until then, tests use the scripted sample agents and fake tools.
- **A basic audit record starts in Stage 1**; every feature appends to it.
- **10 stays in Stage 6.**
- Backlog items are re-aligned to these stages and tagged with feature numbers (`F1`, `F2`…).

## Consequences

- Everyone (people and Claude sessions) builds in the same order; `docs/project-context.md`
  is the shared reference and must be kept current.
- Rule checks (3) in Stage 1 work on version records and change summaries, not on running
  agents; running agents belongs to the quality test (4) in Stage 2.
- Several product questions are still open (first users, first platform, first business
  systems, rule scope, where versions are stored) — listed in the context doc; each will
  need its own ADR.
