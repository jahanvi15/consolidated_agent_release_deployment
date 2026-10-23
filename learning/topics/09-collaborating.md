# 09 — Working with other people on one repository

**You'll learn:** how GitHub grants access, how two people avoid stepping on each other,
what reviews and code owners are, and how to handle the merge conflicts that eventually
happen.

## Ways to give someone access

| Model | How | Fits |
|-------|-----|------|
| **Collaborator** | Owner invites them (Settings → Collaborators). They push branches to *this* repo. | A small, trusted team — **what we use** |
| **Fork** | They copy the repo to their own account, work there, and send PRs back. No access needed. | Open-source projects accepting changes from strangers |
| **Organization with teams** | Repo belongs to an organization; teams get roles (Read, Triage, Write, Maintain, Admin). | Companies, larger groups |

On a repository owned by a **personal account** (like ours), there's only one collaborator
level: read + write. Collaborators can push branches and merge PRs; only the owner can
change settings, invite people, or delete the repo. And the `protect-main` ruleset applies
to everyone, so a collaborator can't push to `main` either.

## Avoiding duplicate or clashing work

1. **Claim** an item: add your username to it under *In progress* in `BACKLOG.md`.
2. **One branch per item**, started from the latest `main`.
3. **Small PRs, merged quickly.** The longer a branch lives, the more `main` moves under it.

## Code review

A **review** is someone reading a PR's changes and leaving comments, then choosing
**Comment**, **Approve**, or **Request changes** (PR → **Files changed** → **Review changes**).

Our rule (ADR 0008): approval isn't *required*, but always *ask* the other person
(**Reviewers** ⚙ on the PR page), and never merge someone else's PR without being asked.

What to look for as a reviewer, even as a beginner:
- Does the PR description say what and why? Is there a journal entry that makes sense to you?
- Are there tests for the new behaviour?
- Anything that looks like a password, token or real email? (Stop and say so.)
- Anything you don't understand — ask. A question is a useful review comment.

## Code owners

`.github/CODEOWNERS` maps file patterns to people:

```text
*            @jahanvi15        # everything
/learning/   @someone-else     # later lines win for matching paths
```

GitHub then **automatically requests** those people as reviewers on PRs touching those
files. With 0 required approvals, it's a notification, not a blocker.

## Keeping a branch up to date

While your PR is open, someone else's PR may merge into `main`. Bring those changes into
your branch:

- On GitHub: the PR shows **This branch is out-of-date with the base branch** →
  click **Update branch** (choose the merge option).
- In Git: `git fetch origin` then `git merge origin/main`, then push.

We **merge**, not rebase (ADR 0006), so commit IDs never change under anyone's feet.

## Merge conflicts

A **conflict** happens when both branches changed the *same lines* of a file. Git can't
guess which version is right, so it stops and marks the file:

```text
<<<<<<< HEAD
| 0004 | ... my journal entry ...
=======
| 0004 | ... their journal entry ...
>>>>>>> origin/main
```

To resolve: edit the file into the correct final version (here: keep both rows, renumber
yours to 0005), delete the `<<<<<<<`, `=======`, `>>>>>>>` marker lines, then
`git add <file>` and `git commit`. Run `make check` again before pushing. Claude can do
this for you — ask it to explain what each side contained before it chooses.

In this project the likeliest conflict spots are the shared lists: `BACKLOG.md`, the
journal index in `learning/README.md`, `learning/glossary.md`, and `docs/decisions/README.md`.
Rule: **whoever merges second renumbers** their journal entry or ADR.

## Each person's own identity

Every commit must carry its real author — your name and **your** noreply email — so the
history shows who did what. Claude sets this per session from what you tell it; check
`git log --format='%an <%ae>'` if in doubt.

## Try it yourself

1. Open a PR, click **Files changed**, and leave a comment on one line.
2. Find **Reviewers** on a PR page. Who does CODEOWNERS request automatically?
3. Read the "Working with more than one person" section of `CLAUDE.md`.
