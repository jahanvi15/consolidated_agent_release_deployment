# 0004 — Preparing the repository for a second contributor

| | |
|---|---|
| **Date** | 2026-10-24 |
| **Push / PR** | Branch `docs/s0-8-contributor-onboarding` → pull request into `main` |
| **Backlog item** | S0-8 (also completes S0-5, CODEOWNERS) |
| **Read first** | [Topic 09 — Working with other people](../topics/09-collaborating.md) |

## In one paragraph

A second person is joining, working on Windows through their own Claude. Everything that
was set up in the owner's chat — accounts, email privacy, GitHub access, Claude access,
the branch-and-PR workflow — is now written down in `CONTRIBUTING.md`, so a newcomer can
follow it alone. `CLAUDE.md` gained team rules (claim work, commit under your own name,
merge-not-rebase, journal renumbering), so *every* Claude session follows them, not just
the owner's. Reviews stay optional: ADR 0008 keeps 0 required approvals.

## What changed

| File | Change | Why |
|------|--------|-----|
| `CONTRIBUTING.md` | added | Part A: newcomer setup (A1–A8); Part B: maintainer checklist |
| `.github/CODEOWNERS` | added | Auto-requests `@jahanvi15` as reviewer on every PR (S0-5) |
| `CLAUDE.md` | changed | New section "Working with more than one person"; sample-agent rule updated for S1-1 |
| `docs/decisions/0008-...` | added | Keep 0 required approvals; reviews encouraged, not enforced |
| `README.md` | changed | Points newcomers to `CONTRIBUTING.md` |
| `BACKLOG.md` | changed | S0-8 in progress; usernames on claimed items; S0-5, S0-7 done |
| `learning/topics/09-collaborating.md` | added | Access models, reviews, code owners, conflicts |

## New concepts

**Collaborator** — someone the owner invites with write access to a repo. On personal-
account repos there is just one level (no "read-only" or "maintain" choice); roles exist
only for organizations. A collaborator still can't bypass the `protect-main` ruleset.

**Why the guide lives in the repo, not in a chat** — this chat is visible only to its
owner. The new person's Claude starts with no memory of it. Anything both need — rules,
decisions, status, how-tos — must be in files both can read: `CLAUDE.md` (Claude reads it
automatically), `BACKLOG.md`, `docs/decisions/`, `learning/`, `CONTRIBUTING.md`.

**Authorizing vs installing a GitHub App** — the owner *installed* the Claude app on this
repo (which repos it may touch). The newcomer only *authorizes* it for their own account
(it may act as them). Together, their Claude can reach this repo through their
collaborator access.

**CODEOWNERS** — a file mapping paths to reviewers who are requested automatically.

**Amending a decision without editing it** — ADR 0004 said "raise approvals to 1 when a
second reviewer exists". That moment came, and the choice was different. Accepted ADRs
aren't edited; ADR 0008 records the new choice and says it *amends* 0004.

**Branching on an unmerged PR (again)** — this branch starts from
`feat/s1-1-manifest-schema` (PR #2), because both change the journal index and backlog;
starting on top of #2 avoids a merge conflict between them. Merge #2 first.

## Commands used

```bash
git fetch origin
git switch feat/s1-1-manifest-schema && git pull --ff-only
git switch -c docs/s0-8-contributor-onboarding
# ...write files...
make check
git add -A
git commit -m "docs: onboarding guide for a second contributor (S0-8)"
git push -u origin docs/s0-8-contributor-onboarding
```

## What went wrong / what to watch for

- **An accepted ADR was edited by mistake** (a note on 0004's status line), then
  reverted: `CLAUDE.md` rule 6 says accepted ADRs aren't changed. The index and ADR 0008
  carry the link instead.
- **A stale rule in `CLAUDE.md`** still told Claude sample agents use a `purpose` field,
  which S1-1 renamed to `description`. Rules files go stale like code — review them when
  a feature changes what they describe.
- **"Unpushed commits" warning** (between journals 0003 and 0004): Claude's working copy
  had been cloned to follow only `main`, so it didn't know `feat/s1-1-manifest-schema`
  already existed on GitHub. Nothing was lost; the copy was set to track all branches
  (`git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`).

## How to verify it yourself

1. Read `CONTRIBUTING.md` on GitHub as if you were new. Is any step unclear? Comment on the PR.
2. After merging, open any new PR: `jahanvi15` is requested as reviewer automatically.
3. Do Part B1 (invite) and send the newcomer the link to `CONTRIBUTING.md`.

## Further reading

- Inviting collaborators to a personal repository — <https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository>
- About code owners — <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners>
- Resolving a merge conflict on GitHub — <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-on-github>
