# 0001 — The first push: project skeleton

| | |
|---|---|
| **Date** | 2026-10-23 |
| **Push / PR** | Direct push to `main`, commit `f1c54de` (the only direct push `main` will ever get) |
| **Backlog item** | Stage 0 (S0-1) |
| **Read first** | [Topic 01 — Git and GitHub](../topics/01-git-and-github.md) |

## In one paragraph

This push created the project's foundation, not its features. It contains the rules,
the automated checks, a decision log, a to-do list, a command-line program that does
nothing yet but report its version, and four fake AI agents that misbehave on purpose so
future compliance checks have something to catch. Setting this up first means every
feature from now on is automatically tested, reviewed through a pull request, and
explained.

## What changed

44 files, all new.

| File / folder | What it is | Why it exists now |
|---------------|-----------|-------------------|
| `src/consolidated_agent_release_deployment/` | The product: a CLI that prints `--version` and `--help` | CI needs real code to install and test, proving the pipeline works end to end |
| `sample_agents/` | 4 scripted fake agents + `harness.py` that runs them and records every tool call | Test material for the Stage 1 checks — [topic 04](../topics/04-testing-with-pytest.md) |
| `tests/` | 35 tests: CLI, harness, and "each fake agent breaks exactly its one rule" | Safety net for every future change |
| `.github/workflows/ci.yml` | Automated checks on every push, Python 3.11–3.14, ending in the `ci-pass` gate | [Topic 03](../topics/03-automated-checks-ci.md) |
| `.github/dependabot.yml` | Weekly update PRs for Actions and Python tools | Keeps dependencies current, visibly |
| `.github/pull_request_template.md` | Checklist pre-filled into every PR | Turns the rules into a habit |
| `pyproject.toml` | Project settings + tool settings | [Topic 02](../topics/02-python-project-layout.md) |
| `Makefile` | `make install`, `make check`, `make fix` | One command runs exactly what CI runs |
| `.pre-commit-config.yaml` | Lint/format before each commit; blocks commits on `main` | [Topic 05](../topics/05-code-quality-tools.md) |
| `scripts/protect-main.sh` | Creates the GitHub ruleset that locks `main` | Used in Step 5 |
| `docs/decisions/0001–0005` | Why Python, GitHub Actions, Apache-2.0, protected main, fake agents | [Topic 07](../topics/07-decisions-backlog-rules.md) |
| `docs/test-accounts.md` | Free accounts needed and how to handle their tokens | [Topic 06](../topics/06-security-basics.md) |
| `BACKLOG.md`, `CLAUDE.md`, `README.md` | To-do list, working rules, front page | [Topic 07](../topics/07-decisions-backlog-rules.md) |
| `LICENSE`, `NOTICE` | Apache 2.0 text and copyright line | Legal basis for others to use the code |
| `.gitignore`, `.gitattributes`, `.editorconfig` | Keep junk/secrets out; consistent line endings; editor settings | [Topic 02](../topics/02-python-project-layout.md) |

### The four sample agents

| Agent | Behaviour | Rule it breaks |
|-------|-----------|----------------|
| `helpful_summarizer` | One search, then a summary | None — the "should pass" baseline |
| `tool_overreach` | Declares `search` only, but also calls `send_email` | Uses an undeclared tool |
| `secret_leaker` | Reads `config.env` and pastes `FAKE-sk-test-…` into its answer | Leaks a secret |
| `runaway_loop` | Budget of 5 steps, takes 20 (hard-capped so tests can't hang) | Exceeds step budget |

## New concepts

- **Repository, commit, branch, push, remote** — [topic 01](../topics/01-git-and-github.md).
- **Package, module, src layout, pyproject.toml, virtual environment, exit codes** — [topic 02](../topics/02-python-project-layout.md).
- **CI, workflow, job, step, runner, matrix, gate job** — [topic 03](../topics/03-automated-checks-ci.md).
- **Tests, fixtures, parametrize, coverage, deterministic** — [topic 04](../topics/04-testing-with-pytest.md).
- **Linting, formatting, type checking, pre-commit hooks** — [topic 05](../topics/05-code-quality-tools.md).
- **2FA, secrets, least privilege, noreply email** — [topic 06](../topics/06-security-basics.md).
- **ADRs, backlog, working rules** — [topic 07](../topics/07-decisions-backlog-rules.md).

## Commands used (Windows, Git Bash)

```bash
# one-time identity — every commit is stamped with this
git config --global user.name "Jahanvi Joshi"
git config --global user.email "99080522+jahanvi15@users.noreply.github.com"

# inside the unzipped project folder
git status              # expect: On branch main ... nothing to commit, working tree clean
git log --oneline       # expect: f1c54de chore: stage 0 development environment

# save GitHub's address under the name "origin" (sends nothing yet)
git remote add origin https://github.com/jahanvi15/consolidated_agent_release_deployment.git

# send main to GitHub, replacing GitHub's starter commit (-u remembers the link)
git push --force -u origin main
```

The first push opens a browser window for **Git Credential Manager** to sign in to
GitHub (with 2FA). Windows then remembers it.

## What went wrong / what to watch for

These all happened while preparing this push and are worth recognizing:

1. **Lint failed on the first try (`I001` unsorted imports).** ruff thought
   `sample_agents` was an outside library. Fixed by telling ruff it's our own code
   (`known-first-party`), not by disabling the rule.
2. **`make install` failed outside a Git repository.** `pre-commit install` needs Git.
   The Makefile now skips that step with a message when there's no repo yet.
3. **Outdated action versions.** The workflow was first written with older major
   versions of `actions/checkout` and `actions/setup-python`; checking the live tags
   showed v7 was current. Lesson: verify versions instead of trusting memory.
4. **Outdated account information.** The Azure DevOps free-tier process had changed
   (no request form; link an Azure subscription instead). Checked against Microsoft's
   current docs and corrected `docs/test-accounts.md`.
5. **The pre-commit hook blocked the first commit** — correctly, because it was on
   `main`. The very first commit has to be on `main` (no other branch exists yet), so it
   was made once with `--no-verify`. From now on, never.
6. **GitHub repo was created with starter files** (README/license ticked), so its
   history didn't match ours. A normal push would be rejected; `--force` replaced the
   starter commit. Safe only because nothing of value was on GitHub and protection
   wasn't on yet.
7. **Renaming.** The tool was first called `agent-compliance`, then renamed to match
   the repo. A rename touches the package folder, imports, settings, docs and tests —
   the checks were re-run afterwards to prove nothing broke.
8. **Windows line endings.** `.gitattributes` was added so files edited on Windows
   don't show every line as changed.
9. **An accidental second commit leaked the real email.** After the push, a second
   commit `826c8cc` ("environment setup") landed on `main` from the Windows PC. It
   changed only one thing — it removed the *executable* flag from
   `scripts/protect-main.sh` (unzipping on Windows drops that flag, and Git recorded the
   loss) — but it was stamped `unknown <real Gmail address>` because Git's name/email
   weren't set on that PC yet. With the repo public, that email became visible.
   **Fix:** while `main` was still unprotected, it was reset back to `f1c54de` with
   `git push --force-with-lease=main:826c8cc ...`, which only succeeds if GitHub's
   `main` is still exactly `826c8cc` — so nothing else could be overwritten.
   **Lessons:** run `git config --global --list` and check `user.name`/`user.email`
   *before* the first commit on a new PC; turn on GitHub's **Block command line pushes
   that expose my email**; and remember that a rewritten commit can stay reachable by its
   exact link for a while, so prevention beats cleanup ([topic 06](../topics/06-security-basics.md)).
10. **Giving Claude access to the repo took two separate GitHub permissions.**
    *Authorized GitHub Apps* lets Claude act as you; *Installed GitHub Apps* decides
    *which repositories* it can touch. Only the second was missing. Searching the
    GitHub Marketplace was the wrong place — it lists third-party add-ons, not the
    settings of apps you already use.

## How to verify it yourself

1. On GitHub, the repo shows the folders above and **1 commit** by `jahanvi15`.
2. **Actions** tab → the **CI** run shows five green jobs: four `checks (py3.x)` and `ci-pass`.
3. Open a `checks (py3.13)` job → **Tests** step → `35 passed` and coverage ≈ 99 %.
   The first real run took 38 seconds and passed on every Python version.
4. The run shows a yellow **annotation** saying `ubuntu-latest` is moving to Ubuntu 26.
   That's an informational notice from GitHub about the runner machine, not a failure;
   our checks don't depend on the Ubuntu version.

## Further reading

- Git documentation — <https://git-scm.com/doc>
- GitHub Actions documentation — <https://docs.github.com/en/actions>
- Python Packaging User Guide — <https://packaging.python.org/>
- pytest documentation — <https://docs.pytest.org/>
- Choose a license (Apache-2.0) — <https://choosealicense.com/licenses/apache-2.0/>
