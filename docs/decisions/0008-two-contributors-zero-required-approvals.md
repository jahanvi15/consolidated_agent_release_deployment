# 0008. Keep 0 required approvals with two contributors

- **Status:** Accepted
- **Date:** 2026-10-24
- **Decider:** Jahanvi Joshi
- **Amends:** 0004 (which planned to raise approvals to 1 "when a second reviewer exists")

## Context

A second contributor joins as a collaborator with write access, working through their
own Claude on Windows. ADR 0004 anticipated requiring one approval at this point.

## Options considered

1. **Require 1 approval** — every PR waits for the other person. Catches mistakes and
   spreads knowledge; slows both people down, and PRs block whenever one is away.
2. **Keep 0** — each person merges their own PR once `ci-pass` is green. Fast; relies on
   automated checks and voluntary review.

## Decision

Keep **0 required approvals**. Reviews are encouraged, not enforced:

- Request the other person as reviewer on every PR (CODEOWNERS does this for the owner).
- Never merge someone else's PR unless they ask.
- Claim backlog items with your username before starting, so work never overlaps.

## Consequences

- No one is blocked waiting; automated checks remain the hard gate.
- A careless change can reach `main` without a human second look. Revisit — raise to 1
  in the `protect-main` ruleset — when the product is used by others, or after any
  incident a review would have caught.
