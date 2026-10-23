# 0005 — Writing down what we're building (project context and roadmap)

| | |
|---|---|
| **Date** | 2026-10-24 |
| **Push / PR** | Added to PR #3 (branch `docs/s0-8-contributor-onboarding`) |
| **Backlog item** | S0-8 |
| **Read first** | [`docs/project-context.md`](../../docs/project-context.md) |

## In one paragraph

Until now, the full product plan — 13 features across 7 stages — existed only in the
owner's earlier conversations. A new contributor's Claude, starting with an empty memory,
would have seen only Stage 0 and a backlog that (it turned out) didn't follow the plan.
This change writes the plan into `docs/project-context.md`: what we're building, the
features and their order, decisions on the plan's open choices, current status, how the
existing code fits, open questions, team and history. `CLAUDE.md` now tells every Claude to
read it first and keep it current, and the backlog was rebuilt around the roadmap.

## What changed

| File | Change | Why |
|------|--------|-----|
| `docs/project-context.md` | added | The shared "read this first" document |
| `docs/decisions/0009-staged-roadmap.md` | added | Records the roadmap and the four open choices decided today |
| `BACKLOG.md` | rewritten | Items grouped by stage, with feature-based IDs (`F1-3`); old S1-2…S1-6 kept under *Superseded* |
| `CLAUDE.md` | changed | New project description; "read project-context first"; build in roadmap order; keep the doc current |
| `CONTRIBUTING.md` | changed | First-session prompt and "where things live" table point to the context doc |
| `README.md`, `pyproject.toml` | changed | Describe the real product: release management for AI agents |
| `sample_agents/*/agent.toml` | changed | Descriptions point to the new backlog IDs |
| learning: template, topic 07, glossary | changed | New ID scheme and roadmap vocabulary |

## New concepts

**A shared source of truth.** Chats are private and forgotten; the repository is shared
and permanent. Anything two people (or two Claudes) must agree on belongs in a file in the
repo, reviewed through a PR like code.

**Roadmap ordered by dependencies.** Features are ordered by what they *need*: the
"what changed" summary compares two version records, so version records come first;
gradual release needs environment moves; undo needs gradual release. Building out of order
means building on nothing.

**Catching drift early.** The first backlog was written from only part of the plan and
quietly diverged from it (it planned "agent behaviour checks" as Stage 1, while the plan's
Stage 1 is version record → what changed → rule checks). Comparing the backlog against the
real plan caught it before any code was built on the wrong idea. The old items weren't
deleted — they moved to a *Superseded* section that says where each one went, so history
stays traceable.

**Open questions are written down, not guessed.** Who the first users are, which agent
platform and business systems come first, which compliance rules matter, and where
version records are stored are still undecided. The context doc lists them so no one —
and no Claude — fills the gap with an assumption. Backlog items marked **Decide** must be
answered by the owner (with an ADR) before building.

**Mermaid diagrams.** The roadmap picture in the context doc is written as text in a
` ```mermaid ` block; GitHub draws it as a diagram. Diagrams-as-text can be reviewed and
changed in PRs like code.

## Commands used

```bash
git switch docs/s0-8-contributor-onboarding
# ...write files...
make check
git add -A
git commit -m "docs: project context and staged roadmap for every contributor"
git push        # updates PR #3 automatically
```

Pushing more commits to a branch that already has an open PR **adds them to that PR** —
no new PR needed. CI runs again on the new commits.

## What went wrong / what to watch for

- **The backlog didn't match the plan** (see "Catching drift early"). Lesson: when work
  is planned in one place (a chat) and tracked in another (the repo), copy the plan into
  the repo first.
- **Feature numbers aren't in build order** (12 comes before 4; 13 before 5). They're the
  plan's original numbers, kept so references stay stable. Use the *stage* to know when,
  the *number* to know which.

## How to verify it yourself

1. Open `docs/project-context.md` on GitHub — the roadmap diagram renders as boxes and arrows.
2. Check that section 4's decision table matches what you chose.
3. Read section 8 (open questions). Answering them is the next real decision work —
   F1-2 (what a version contains, where it's stored) blocks Stage 1.

## Further reading

- GitHub: Creating diagrams (Mermaid) — <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams>
