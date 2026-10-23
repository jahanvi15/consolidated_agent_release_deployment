# 0006. Merge pull requests with merge commits; create one branch per feature as work starts

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

All changes reach `main` through pull requests (ADR 0004). Two follow-up choices:
how a PR's commits land on `main`, and when feature branches are created. Stage 1
features depend on each other (S1-1 → S1-2/3/4 → S1-5 → S1-6).

## Options considered

**Merge style** (GitHub offers three):

1. **Create a merge commit** — keeps every branch commit unchanged and adds one
   "Merge pull request #N" commit. Complete history; shows exactly when each feature
   landed. Noisier log.
2. **Squash and merge** — the whole branch becomes one new commit. Tidy log, but the
   branch's individual commits are lost and branches built on top of it must be rebased.
3. **Rebase and merge** — replays each commit onto `main` with new IDs. Linear, but also
   breaks branches built on top.

**Branch timing:**

1. **One branch per feature, created when work starts**, from the latest `main`.
2. All branches up front — they go stale and need rebasing as dependencies land.

## Decision

- Merge style: **Create a merge commit**.
- Branches: **one per backlog item, created when work starts**, named
  `<type>/<backlog-id>-<short-topic>`, e.g. `feat/s1-1-manifest-schema`.
- When a feature depends on an open, unmerged PR, its branch may start from that PR's
  branch. Because merge commits keep commit IDs unchanged, no rebase is needed once
  the earlier PR merges.

## Consequences

- `git log --oneline --first-parent main` shows one line per merged PR — the tidy view.
  Plain `git log` shows every commit.
- Work-in-progress commit messages stay in history forever, so write them properly.
- To enforce this, untick **Allow squash merging** and **Allow rebase merging** in
  Settings → General → Pull Requests (optional; not done yet).
