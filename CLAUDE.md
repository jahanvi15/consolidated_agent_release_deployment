# Rules for Claude in this repository

These rules apply to every Claude session (Claude Code, the Claude app, or any agent) that
changes this repository. A human contributor should follow them too.

## What this project is

`consolidated-agent-release-deployment` is **release management for AI agents**, run inside CI/CD
pipelines: a record of every agent version, a "what changed" summary, automatic rule checks,
and later dependency maps, quality tests, environment moves, sign-off, audit evidence,
change watching, gradual release and undo. First pipeline platform: **GitHub Actions**.
Language: **Python 3.11+**. License: **Apache-2.0**.

**Read [`docs/project-context.md`](docs/project-context.md) before starting any work.** It has
the 13 features, the 7-stage roadmap (ADR 0009), current status and open questions.

## Hard rules (never break these)

1. **Never commit or push to `main`.** Work on a branch named `<type>/<short-topic>`
   (`feat/`, `fix/`, `chore/`, `docs/`, `test/`) and open a pull request.
2. **Run `make check` before saying a change is done.** It runs exactly what CI runs.
   If it fails, the change is not done. Never weaken a check (lower coverage, add a
   blanket `# type: ignore`, `# noqa`, or `pytest.skip`) to make it pass. If a narrow
   ignore is truly needed, give the reason on the same line.
3. **No real secrets, tokens, or personal data anywhere** in code, tests, fixtures,
   commit messages, or logs. Fake secrets in tests must use the `FAKE-` prefix
   (e.g. `FAKE-sk-0000`) so scanners and humans can tell them apart.
4. **Tests never touch the network or a real LLM.** Sample agents are deterministic
   Python. Anything that talks to GitHub, Azure DevOps or a model provider is mocked
   in unit tests; live integration tests live under `tests/integration/` and are
   opt-in (marker `integration`, added when the first one exists).
5. **No new runtime dependency without an ADR.** `dependencies` in `pyproject.toml`
   is empty on purpose. Dev-only tools may be added to `[project.optional-dependencies].dev`
   with a one-line reason in the PR.
6. **Don't change these files without the human asking:** `LICENSE`, `NOTICE`,
   `.github/workflows/*`, `scripts/protect-main.sh`, existing accepted ADRs.
7. **Every push or pull request adds a learning journal entry.** The project owner is
   learning as the project grows, so each change must explain itself for a beginner:
   - Add `learning/journal/NNNN-short-title.md` (next number), following
     `learning/journal/_template.md`: what changed and why, new concepts, exact commands
     (with Windows Git Bash notes where they differ), what went wrong, how to verify.
   - Add a row to the journal index in `learning/README.md`.
   - Add every new technical term to `learning/glossary.md`.
   - If the change teaches something new about a subject, update or add a guide in
     `learning/topics/`.
   - Assume no prior knowledge. Never include real secrets, even as examples.

## How to work

- **Read first:** `docs/project-context.md` (what and why), `BACKLOG.md` (what's next),
  `docs/decisions/` (what's settled).
- **Build in roadmap order.** Pick items from the current stage in `BACKLOG.md`; don't
  start later-stage features early. Items marked **Decide** need the owner's answer
  first — ask with options, then record an ADR.
- **Keep `docs/project-context.md` current.** Update it in the same PR when a stage's
  status changes, an open question is answered, or a feature's scope changes.
- **Pick work from `BACKLOG.md`.** Move the item to *In progress* when you start and to
  *Done* (with the PR link) when merged. New ideas go to *Inbox*, not straight into code.
- **Decisions:** if you make a choice someone could reasonably disagree with
  (library, data format, public API shape, security trade-off), write an ADR in
  `docs/decisions/` using `0000-template.md`, numbered next in sequence, status
  `Proposed`. The human changes it to `Accepted`.
- **Keep PRs small:** one backlog item per PR; aim for under ~400 changed lines.
- **Tests come with the change.** New behavior needs a test that fails without it.
  Coverage floor is 90 % (enforced).
- **Code style:** type hints on everything (mypy strict), ruff for lint and format,
  standard library first, small pure functions, no global state, no `print` in library
  code (CLI only).
- **Sample agents** (`sample_agents/`) are test fixtures, not product code. Each has an
  `agent.toml` manifest (format: `docs/agent-manifest.md`), an `agent.py`, and an
  `expected.toml` with the verdict the checks should reach. Each one exists to exercise a
  specific check; say which in its manifest `description`.

## Working with more than one person

Two people (the owner `@jahanvi15` and a collaborator) work here, each through their own
Claude. Setup for newcomers: `CONTRIBUTING.md`.

- **Commit as the human you work for.** Set `git config user.name` and `user.email` to
  their name and GitHub **noreply** email (`<id>+<username>@users.noreply.github.com`)
  before the first commit. If you don't know it, ask — never use a real personal email.
- **Claim before you start.** Put the backlog item under *In progress* with the person's
  GitHub username (`[F1-3] ... — @username, branch feat/f1-3-...`). Don't start an item
  someone else has claimed.
- **Start from the latest `main`:** `git fetch origin && git switch -c <branch> origin/main`
  (or from an unmerged PR branch you depend on, per ADR 0006).
- **Keep your branch current** by merging, not rebasing: `git fetch origin && git merge
  origin/main` (or the PR's **Update branch** button). Resolve conflicts, then re-run
  `make check`.
- **Journal numbers can collide** when two PRs are open. Whoever merges second renumbers
  their entry to the next free number and fixes its row in `learning/README.md`.
- **Request the other person as reviewer** on every PR. Approvals aren't required
  (ADR 0008), but never merge someone else's PR unless they ask.

## Commands

```bash
make install   # create .venv and install dev tools
make check     # lint + format check + type check + tests (same as CI)
make fix       # auto-fix lint and formatting
```

## When unsure

Stop and ask the human rather than guessing on anything that is hard to undo:
deleting files, rewriting history, changing CI or branch protection, or adding a
dependency.
