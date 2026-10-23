# Contributing

Welcome! This guide takes a new contributor from nothing to their first merged pull
request, on **Windows**, working through **their own Claude**. No prior experience with
Git or Python tooling is assumed — every term is explained in
[`learning/glossary.md`](learning/glossary.md).

**Part A** is for the new contributor. **Part B** is for the maintainer (repo owner).
Allow about one hour for Part A.

---

## Part A — New contributor setup

### A1. GitHub account with two-factor authentication (10 min)

1. Sign up at **github.com** (free plan) or sign in. Your username is public; keep it professional.
2. **profile picture → Settings → Password and authentication → Enable two-factor
   authentication.** Choose an **authenticator app** (Google Authenticator, Microsoft
   Authenticator, 1Password) — safer than SMS.
3. **Download the recovery codes** and store them in a password manager. They're the only
   way back in if you lose your phone.

Why: whoever controls your account can change this project's code. See
[topic 06](learning/topics/06-security-basics.md).

### A2. Keep your email private (3 min)

Every commit records its author's email, publicly and forever, because this repository
is public.

1. **Settings → Emails.**
2. Tick **Keep my email addresses private.**
3. Tick **Block command line pushes that expose my email.**
4. Copy the address shown under "Keep my email addresses private". It looks like
   `12345678+yourname@users.noreply.github.com`. This is your **noreply email** — all your
   commits will use it. You'll give it to Claude in step A5.

(This project already had one real email leak, fixed by rewriting history — see
[journal 0001](learning/journal/0001-initial-scaffold.md), problem 9. Prevention is
much easier than cleanup.)

### A3. Accept the invitation (2 min)

The maintainer invites you as a **collaborator** (Part B1). You'll get an email from
GitHub, or open
<https://github.com/jahanvi15/consolidated_agent_release_deployment/invitations>.
Click **Accept invitation**. Invitations expire after 7 days — ask for a new one if needed.

As a collaborator you can push branches, open, review and merge pull requests. You
**cannot** push to `main` directly (the `protect-main` ruleset blocks everyone), change
settings, or invite people.

### A4. Connect your Claude to GitHub (5 min)

You need your own Claude account on a plan that includes **Claude Code** (Claude's
coding agent; it can run in the Claude app and on the web).

1. In Claude, start connecting GitHub (Claude prompts for this the first time you
   pick a repository). GitHub shows an **Authorize Claude** screen — approve it.
2. The **Claude GitHub app is already installed on this repository** by the
   maintainer. You don't install it yourself; authorizing is enough, and Claude can
   then reach this repo through your collaborator access.
3. Check: start a Claude Code session and select the repository
   `jahanvi15/consolidated_agent_release_deployment`. If it isn't listed, make sure you
   accepted the invitation (A3); if it still isn't, ask the maintainer to check
   Part B3.

Two permission screens exist on GitHub — **Settings → Applications → Authorized GitHub
Apps** (Claude may act as you) and **Installed GitHub Apps** (which repos an app may
touch). The GitHub **Marketplace** is something else entirely; don't install Claude-
named tools from it. Details: [topic 01](learning/topics/01-git-and-github.md#giving-an-app-like-claude-access-to-a-repository).

### A5. Your first Claude session (10 min)

Claude reads [`CLAUDE.md`](CLAUDE.md) automatically — those are the project rules. To
give it the rest of the context, start your first session with this message (fill in
the two blanks):

```text
I'm a new contributor to this repository. My name for commits is "<Your Name>"
and my GitHub noreply email is "<12345678+yourname@users.noreply.github.com>".
Set these as the git identity for every commit you make for me.

Before doing anything: read docs/project-context.md, docs/features.md, CLAUDE.md, CONTRIBUTING.md,
BACKLOG.md, docs/decisions/README.md and learning/README.md. Then summarize in plain
words: what we are building and why, the roadmap stages, where the project is now,
which open questions are still undecided, and which backlog items are free to pick up.
I'm a beginner: explain every technical step, and ask me with options whenever
there's a decision to make.
```

Everything decided so far lives in the repository, not in anyone's chat history:

| Where | What it tells you |
|-------|-------------------|
| `docs/project-context.md` | **Start here:** what we're building, the 13 features, the roadmap, status, open questions |
| `docs/features.md` | Each feature in detail: problem, behaviour, examples, first-version scope, open questions |
| `CLAUDE.md` | Rules for Claude and humans |
| `BACKLOG.md` | What's done, in progress (and by whom), and next |
| `docs/decisions/` | Every decision and why (ADRs) |
| `docs/agent-manifest.md` | The `agent.toml` format |
| `learning/` | Beginner explanations of everything, one journal entry per change |

### A6. Read the learning notes (30 min, once)

Follow the reading order in [`learning/README.md`](learning/README.md). At minimum:
topic 01 (Git and GitHub), topic 03 (the automated checks), topic 07 (decisions and
rules), and the journal entries.

### A7. Your first change

Ask Claude to pick a free backlog item (or try something small, like fixing a typo in
the learning notes). The workflow, which Claude follows from `CLAUDE.md`:

1. **Claim it** — the item moves to *In progress* in `BACKLOG.md` with your GitHub
   username, so two people never build the same thing.
2. **Branch** from the latest `main`: `<type>/<backlog-id>-<short-topic>`, e.g.
   `feat/s1-3-secret-check` ([ADR 0006](docs/decisions/0006-merge-commits-and-branch-per-feature.md)).
3. **Change, test, journal.** `make check` must pass; every change adds a learning
   journal entry (rule 7).
4. **Push and open a pull request.** The automated checks run; wait for **`ci-pass`** ✓.
5. **Ask the other person to look** (request them as reviewer on the PR). Not required
   by the rules ([ADR 0008](docs/decisions/0008-two-contributors-zero-required-approvals.md)),
   but a second pair of eyes is cheap.
6. **Merge your own PR** with **Create a merge commit**, then **Delete branch**. Never
   merge someone else's PR unless they asked you to.

### A8. Optional — the code on your own PC

Not needed when working through Claude. If you want to browse the code locally:

1. Install **Git for Windows** from git-scm.com. During setup choose: editor
   **Notepad** or **VS Code** (not Vim); initial branch name **Override → `main`**;
   keep **Git Credential Manager**.
2. In **Git Bash**:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "12345678+yourname@users.noreply.github.com"
   git config --global --list        # check both are right BEFORE any commit
   cd ~ && mkdir -p Projects && cd Projects
   git clone https://github.com/jahanvi15/consolidated_agent_release_deployment.git
   ```
3. Running the checks locally on Windows needs extra steps — the `Makefile` assumes Mac or
   Linux (backlog inbox item). Leave testing to Claude and CI for now.

---

## Part B — Maintainer checklist (repo owner)

### B1. Invite the collaborator

**Repo → Settings → Collaborators** (left sidebar, under *Access*) → **Add people** →
search their GitHub username → **Add … to this repository**. GitHub may ask for your
password or 2FA code.

Personal-account repositories have one collaborator level (read + write). Collaborators
can push branches and merge PRs, but not change settings, invite others, or bypass the
`protect-main` ruleset.

### B2. Code owners

`.github/CODEOWNERS` names who is automatically asked to review changes. It lists
`@jahanvi15` for everything. When the collaborator should be auto-requested for some
areas, add a line such as `/learning/ @their-username` (later lines win).

### B3. Claude app access

Nothing to do if **Settings → Applications → Installed GitHub Apps → Claude → Configure**
already includes this repository (it does). If the collaborator's Claude can't see the
repo after A3 and A4, check that screen first.

### B4. Removing access later

**Settings → Collaborators → Remove**. Their open pull requests stay; they can no longer
push.
