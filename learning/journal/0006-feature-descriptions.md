# 0006 — Describing every feature in detail

| | |
|---|---|
| **Date** | 2026-10-24 |
| **Push / PR** | Added to PR #3 (branch `docs/s0-8-contributor-onboarding`) |
| **Backlog item** | S0-8 |
| **Read first** | [`docs/features.md`](../../docs/features.md) |

## In one paragraph

The roadmap named the 13 features in a line each. That's enough to order the work, not to
build it. `docs/features.md` now describes each feature — the problem it solves, what it
does, an example, what it needs and what uses it, what to build first, and what is still
undecided — so anyone (or any Claude) picking up a feature starts from the same
understanding.

## What changed

| File | Change |
|------|--------|
| `docs/features.md` | added — all 13 features plus the basic audit record, in build order |
| `docs/project-context.md` | links to it; "platform" marked ambiguous; history row |
| `CLAUDE.md`, `CONTRIBUTING.md` | tell every session to read a feature's section before working on it |
| `BACKLOG.md` | F11-1 now asks what "platform" means first |

## New concepts

**Decided vs proposed.** The plan fixed each feature's name, purpose, stage and
dependencies. The details in `features.md` (examples, contents of a version record, sample
rules) are *proposed scope*: a sensible starting interpretation, clearly labelled, which
the owner confirms or changes. Writing "proposed" next to an assumption is what stops it
from silently becoming a decision nobody actually made.

**Spotting ambiguous words.** "One view across all platforms" could mean pipeline
platforms (GitHub Actions, Azure DevOps) or agent platforms (where agents are built). Both
readings are plausible, and they lead to very different work — so it's written down as an
open question instead of being guessed. Look for words like this whenever you read a plan.

**Immutable, append-only records.** Version records and the audit log are never edited
— a change creates a *new* entry. That's what makes them trustworthy as evidence.

**Fingerprint (hash).** A short ID computed from content: identical content always gives
the same ID, and any change gives a different one. Git's commit IDs work the same way.

## Commands used

Same branch as journal 0005; `git push` adds the commit to PR #3.

## What went wrong / what to watch for

- The context doc had defined "platform" as "where agents are built or run" — itself a
  guess. Corrected to say the meaning is open.

## How to verify it yourself

Read the section for feature 1 in `docs/features.md` and its *Open questions*. Those are
the decisions needed before Stage 1 can really start (backlog F1-2).
