# 0002 — Adding these learning notes (first pull request)

| | |
|---|---|
| **Date** | 2026-10-23 |
| **Push / PR** | Branch `docs/learning-notes` → pull request into `main` |
| **Backlog item** | S0-7 |
| **Read first** | [0001](0001-initial-scaffold.md), [topic 01 — the branch → PR workflow](../topics/01-git-and-github.md#the-workflow-this-project-uses) |

## In one paragraph

This change adds the `learning/` folder you're reading and makes it a project rule
that every future push adds a journal entry here. It is also the **first change to go
through the proper workflow**: made on a separate branch, proposed as a pull request,
checked by CI, then merged. It doubles as the test that `main`'s protection works.

## What changed

| File / folder | Change | Why |
|---------------|--------|-----|
| `learning/README.md` | added | Index, reading order and the folder's rules |
| `learning/glossary.md` | added | A–Z of every technical term so far |
| `learning/topics/01`–`07` | added | Guides: Git, project layout, CI, testing, code quality, security, decisions |
| `learning/journal/_template.md` | added | The shape every entry follows |
| `learning/journal/0001`, `0002` | added | Entries for the first push and this one |
| `CLAUDE.md` | changed | New hard rule: every push adds a journal entry |
| `.github/pull_request_template.md` | changed | Checklist box for the journal entry |
| `README.md` | changed | `learning/` added to the repository map |
| `BACKLOG.md` | changed | S0-7 for this work; inbox item for Windows-friendly dev commands |

No code changed, so the tests are unaffected — but CI still runs, because protection
requires `ci-pass` on every PR.

## New concepts

**Documentation as part of "done".** Making the journal a rule in `CLAUDE.md` and a
checkbox in the PR template means it can't quietly be skipped. Rules that live next to
the work get followed; rules in someone's memory don't.

**Your first pull request.** Unlike push 0001, this change reaches `main` only through
a PR:

```bash
git switch -c docs/learning-notes          # create the branch and move onto it
# ...make the changes...
git add -A
git commit -m "docs: add beginner learning notes and journal rule"
git push -u origin docs/learning-notes     # push the BRANCH, not main
```

GitHub then shows a yellow banner **"docs/learning-notes had recent pushes — Compare &
pull request"**. Click it, check the description, and click **Create pull request**.
Once `ci-pass` is green, click **Merge pull request**, then **Delete branch**.

Locally, catch up afterwards:

```bash
git switch main
git pull                                   # brings the merged change into your main
git branch -d docs/learning-notes          # delete the local branch; -d refuses if unmerged
```

**Markdown.** Every `.md` file here is **Markdown**: plain text where `#` makes a
heading, `**bold**` makes bold, `|` builds tables and backticks mark `code`. GitHub
renders it nicely, so read these files on GitHub rather than in Notepad.

## What went wrong / what to watch for

- **CI's formatter checked the Markdown files too.** The first `make check` failed with
  `3 files would be reformatted` — all three were learning notes. Newer versions of
  ruff also format **Python code blocks inside Markdown** (the parts between
  ` ```python ` fences). Fixed by running `ruff format .`, which tidied the examples.
  Two lessons: (1) "documentation" can still fail code checks, so run `make check` even
  for docs-only changes; (2) our `pyproject.toml` says `ruff>=0.6`, so whoever installs
  later gets a newer ruff with new behaviour. Pinning tool versions exactly would make
  that predictable — a trade-off worth an ADR later.

- **The Makefile doesn't work on Windows as-is**: it uses `make` (not installed on
  Windows) and Mac/Linux paths (`.venv/bin/`; Windows uses `.venv\Scripts\`). Not a
  problem while Claude and CI run the checks, but noted in the backlog and in
  [topic 02](../topics/02-python-project-layout.md#windows-note).
- If a push of the branch is rejected with **GH013 "Repository rule violations"**, you
  pushed to `main` instead of the branch. Check `git branch` — the `*` must be on
  `docs/learning-notes`.

## How to verify it yourself

1. The PR's **Checks** section shows `ci-pass` ✓ before the Merge button turns green.
2. After merging, `learning/README.md` on GitHub shows the index with entries 0001 and 0002.
3. (After Step 5) Try `git push origin main` with a local change — GitHub should refuse.

## Further reading

- About pull requests — <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests>
- Basic Markdown syntax — <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax>
