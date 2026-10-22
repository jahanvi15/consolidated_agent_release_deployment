# Rules for Claude in this repository

These rules apply to every Claude session (Claude Code, the Claude app, or any agent) that
changes this repository. A human contributor should follow them too.

## What this project is

`consolidated-agent-release-deployment` checks AI agents for compliance problems *before* they are deployed
through a CI/CD pipeline. First pipeline platform: **GitHub Actions**. Language: **Python 3.11+**.
License: **Apache-2.0**. See `docs/decisions/` for why.

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

## How to work

- **Read first:** `BACKLOG.md` (what's next), `docs/decisions/` (what's settled).
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
  `agent.toml` manifest and an `agent.py`. Each one exists to exercise a specific check;
  say which in its manifest `purpose`.

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
