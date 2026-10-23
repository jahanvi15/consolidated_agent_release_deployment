# 01 — Git and GitHub

**You'll learn:** what Git and GitHub are, how history is stored, the everyday commands,
and the branch → pull request → merge workflow this project uses.

## Git vs GitHub

- **Git** is a program on your computer. It records every change to a folder as a
  series of snapshots (**commits**) and can send them elsewhere.
- **GitHub** is a website that stores a copy of that history online and adds
  teamwork features: pull requests, automated checks (Actions), security scanning.

You can use Git without GitHub, but not GitHub without Git.

## Where the history lives

Inside the project folder is a hidden folder called `.git`. That *is* the repository:
every commit ever made. The visible files around it are the **working tree** — the
current version you're editing. Never edit or delete anything inside `.git` by hand.

On Windows, show hidden folders with File Explorer → **View → Show → Hidden items**.

## The three places a change passes through

```
 working tree  --git add-->  staging area  --git commit-->  local history  --git push-->  GitHub
 (your edits)               (what goes in                  (.git folder)               (origin)
                             the next commit)
```

The staging area exists so you can choose which edits go into a commit. You can edit
five files but commit only two of them.

## Everyday commands

Run these in **Git Bash** (Windows) or Terminal (Mac/Linux), inside the project folder.

| Command | What it does |
|---------|--------------|
| `git status` | Shows the current branch and which files are changed, staged, or new. Run it constantly; it's harmless. |
| `git log --oneline` | Lists commits, newest first, one per line: `f1c54de chore: stage 0 ...` |
| `git diff` | Shows exactly which lines changed and aren't staged yet. |
| `git add <file>` / `git add -A` | Stages one file / all changes. |
| `git commit -m "message"` | Saves staged changes as a commit with that message. |
| `git push` | Sends your commits to GitHub. |
| `git pull` | Downloads new commits from GitHub and merges them into your branch. |
| `git switch <branch>` | Moves to another branch. |
| `git switch -c <new-branch>` | Creates a new branch and moves to it. |
| `git branch` | Lists local branches; `*` marks the current one. |

**Quitting the log viewer:** if `git log` fills the screen and shows `:` at the bottom,
press `q`.

## One-time setup (done in journal 0001)

```bash
git config --global user.name "Jahanvi Joshi"
git config --global user.email "99080522+jahanvi15@users.noreply.github.com"
```

`--global` applies to every repository on this computer. The email is GitHub's
private **noreply** address, so the real email never appears in public history
(see [topic 06](06-security-basics.md)).

Check what's set: `git config --global --list`. **Do this on every new computer before
the first commit.** If the name/email are missing, Git may fall back to something like
`unknown <your-real-email>` — which is exactly how a real email leaked in journal 0001.

## Giving an app (like Claude) access to a repository

GitHub separates two permissions, both under **Settings → Applications**:

- **Authorized GitHub Apps** — you allowed the app to sign in and act *as you*.
- **Installed GitHub Apps** — *which repositories* the app may touch
  (**Configure → Repository access**). Prefer **Only select repositories**.

An app needs both. The **Marketplace** is a different thing: a catalogue of third-party
tools to install, not the settings of apps you already use.

## Commit messages

We use the **Conventional Commits** style: `<type>: <what changed>`.

| Type | Use for |
|------|---------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | Maintenance: setup, tooling, dependencies |

Good: `feat: check that agents only use declared tools`.
Bad: `stuff`, `fixed it`, `update`. A message should let someone understand the change
a year later without opening it.

## The workflow this project uses

`main` must always work, so nobody (not even Claude) changes it directly.

1. **Branch:** `git switch -c feat/manifest-schema` — names follow `<type>/<short-topic>`.
2. **Change and commit** on that branch, as many commits as needed.
3. **Push the branch:** `git push -u origin feat/manifest-schema`
   (`-u` remembers the link, so later just `git push`).
4. **Open a pull request** on GitHub. It shows the changes and runs CI automatically.
5. **Wait for `ci-pass` to go green.** If red, fix on the same branch and push again —
   the PR updates itself.
6. **Merge** on GitHub, then delete the branch (GitHub offers a button).
7. **Update your copy:** `git switch main` then `git pull`.

## Remotes

A **remote** is a saved address of another copy of the repository. `origin` is the
conventional name for the GitHub copy.

```bash
git remote -v      # list remotes and their addresses
git remote add origin https://github.com/jahanvi15/consolidated_agent_release_deployment.git
```

## Dangerous commands — understand before using

| Command | Why it's dangerous |
|---------|--------------------|
| `git push --force` | Overwrites GitHub's history with yours, deleting commits that exist only there. Blocked on `main` once protection is on. If you must force-push, prefer `git push --force-with-lease`, which refuses if GitHub has commits you haven't seen. |
| `git reset --hard` | Throws away all uncommitted changes in your folder. No undo. |
| `git clean -fd` | Deletes every untracked file. No undo. |
| `git commit --amend` | Rewrites the last commit. Fine before pushing; causes trouble after. |

If something goes wrong, stop and ask before trying fixes — most Git mistakes are
recoverable if you don't pile more commands on top.

## Common errors

| Message | Meaning and fix |
|---------|-----------------|
| `fatal: not a git repository` | You're in the wrong folder. `cd` into the project folder. |
| `! [rejected] main -> main (fetch first)` | GitHub has commits you don't. Run `git pull`, then push again. |
| `GH007: Your push would publish a private email address` | Your commit uses your real email while GitHub's email privacy is on. Set the noreply email (above) and re-commit. |
| `remote: error: GH013: Repository rule violations` | You tried to push straight to protected `main`. Push a branch and open a PR instead. |

## Try it yourself

1. In the project folder run `git log --oneline` and `git status`. Explain each line of output.
2. Run `git show --stat f1c54de` to see which files the first commit added.
3. On GitHub, click the commit count above the file list and open the first commit.
