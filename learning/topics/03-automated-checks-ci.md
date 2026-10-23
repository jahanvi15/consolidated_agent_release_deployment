# 03 — Automated checks (CI) with GitHub Actions

**You'll learn:** what CI is, how to read our workflow file line by line, what a
matrix and a gate job are, and how to read results on GitHub.

## Why CI

People forget to run tests. CI (Continuous Integration) removes the choice: every push
is checked automatically on a clean machine, and the result is shown on GitHub. With
branch protection, nothing reaches `main` unless the checks pass.

A clean machine also catches "works on my computer" problems — anything relying on a
file or setting that only exists on one person's PC fails in CI.

## Vocabulary

- **Workflow** — a YAML file in `.github/workflows/`. Ours: `ci.yml`.
- **Event / trigger** — what starts it (`push`, `pull_request`, manual button).
- **Job** — a group of steps that runs on one machine. Jobs run in parallel unless one
  `needs` another.
- **Step** — one command, or one reusable **action** (`uses: actions/checkout@v7`).
- **Runner** — the temporary cloud machine (`ubuntu-latest`). It's deleted afterwards.

## Our workflow, explained

```yaml
name: CI                         # name shown in the Actions tab

on:                              # TRIGGERS
  push:
    branches: ["**"]             # any push to any branch
  pull_request:                  # any pull request
  workflow_dispatch:             # adds a "Run workflow" button for manual runs

permissions:
  contents: read                 # the workflow may only READ the repo — least privilege

concurrency:
  group: ci-${{ github.ref }}    # one run per branch…
  cancel-in-progress: true       # …and a new push cancels the outdated run (saves time)
```

```yaml
jobs:
  checks:
    name: checks (py${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 10          # kill it if something hangs
    strategy:
      fail-fast: false           # if 3.11 fails, still finish 3.12–3.14 so we see everything
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]   # run this job 4 times
    steps:
      - uses: actions/checkout@v7          # download the repo onto the runner
        with:
          persist-credentials: false       # don't leave a GitHub token lying on the disk
      - uses: actions/setup-python@v7      # install the requested Python version
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip                       # reuse downloaded packages between runs → faster
      - name: Install
        run: python -m pip install -e ".[dev]"
      - name: Lint
        run: ruff check --output-format=github .   # problems appear as notes on the PR's lines
      - name: Format
        run: ruff format --check .                 # --check = report only, don't change files
      - name: Type check
        run: mypy
      - name: Tests
        run: pytest
```

`${{ ... }}` is an **expression**: GitHub fills in a value at run time, e.g. the current
matrix Python version or the branch name.

`@v7` pins the **major version** of an action. Dependabot opens a PR when a new major
version comes out, so we upgrade deliberately rather than by surprise.

## The gate job: `ci-pass`

```yaml
  ci-pass:
    if: always()                 # run even if 'checks' failed, so it can report failure
    needs: [checks]              # wait for every matrix copy of 'checks'
    steps:
      - run: # fail unless every needed job's result is "success"
```

Branch protection must name the exact checks required. Requiring four
`checks (py3.x)` names would mean editing protection every time the matrix changes.
Instead, protection requires only `ci-pass`, and `ci-pass` requires everything else.
To add a new job later, add it to `needs:` — protection stays untouched.

Why `if: always()`? Without it, if `checks` fails, `ci-pass` is *skipped*, and GitHub
treats a skipped required check as… passing. `always()` makes it run and fail properly.

## Reading results on GitHub

1. **Actions** tab → list of runs, newest first. Green ✓, red ✗, yellow ● (running).
2. Click a run → see each job. Click a job → each step expands to its full log.
3. On a **pull request**, results appear at the bottom as checks; red ones have a
   **Details** link straight to the failing log.
4. Lint problems also appear as annotations on the changed lines under **Files changed**.

**Reading a failure:** open the red step, scroll to the bottom; the real error is
usually in the last 20 lines. For pytest, look for `FAILED tests/...` and the `assert`
line above it.

## Cost

Public repositories get GitHub-hosted Actions minutes free. Private repos on the free
plan have a monthly minute allowance. Our full run takes a few minutes.

## Try it yourself

1. Open the **Actions** tab and click the first CI run. How many jobs ran? Why that number?
2. Open a `checks (py3.13)` job and expand the **Tests** step. Find the coverage total.
3. On the run page, find the **Re-run jobs** button. When would that be useful?
