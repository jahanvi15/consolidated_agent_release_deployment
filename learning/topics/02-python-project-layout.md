# 02 — How a Python project is laid out

**You'll learn:** what every folder and file in this repository is for, what
`pyproject.toml` does, virtual environments, and how the command-line tool is wired up.

## The map

```
consolidated_agent_release_deployment/      ← repository root
├── src/
│   └── consolidated_agent_release_deployment/   ← the product (a Python "package")
│       ├── __init__.py      marks the folder as a package; holds __version__
│       ├── cli.py           the command-line program
│       └── py.typed         empty marker: "this package has type hints"
├── sample_agents/           fake agents used only for testing
├── tests/                   automated tests
├── docs/decisions/          decision records (ADRs)
├── learning/                these notes
├── scripts/                 one-off helper scripts
├── .github/                 GitHub settings: CI workflow, Dependabot, PR template
├── pyproject.toml           project settings (the most important file)
├── Makefile                 command shortcuts
├── README.md                the front page on GitHub
├── CLAUDE.md                rules for Claude (and humans) changing the repo
├── BACKLOG.md               to-do list
├── LICENSE, NOTICE          Apache-2.0 license and copyright line
└── .gitignore, .gitattributes, .editorconfig, .pre-commit-config.yaml   (hidden settings)
```

## Packages and modules

- A **module** is one `.py` file (`cli.py`).
- A **package** is a folder of modules with an `__init__.py` file.
- Importing uses dots: `from consolidated_agent_release_deployment.cli import main`
  means "from the `cli` module inside the package, get `main`".

Package names use underscores (Python can't import names with hyphens); the installed
project name and the command use hyphens. Same name, two spellings — that's normal.

## Why a `src/` folder

Without `src/`, Python could import the package straight from the folder you're in,
even if it was never installed correctly — tests would pass on your machine and break
for users. Putting code under `src/` forces tests to use the *installed* package, the
way users will. This is called the **src layout**.

## `pyproject.toml`, section by section

```toml
[build-system]           # which tool turns the project into an installable package (hatchling)

[project]
name = "consolidated-agent-release-deployment"
version = "0.0.1"        # MAJOR.MINOR.PATCH; 0.x = early, anything may change
requires-python = ">=3.11"
dependencies = []        # runtime dependencies — deliberately empty

[project.optional-dependencies]
dev = ["pytest>=8", ...] # tools needed only to develop and test

[project.scripts]
consolidated-agent-release-deployment = "consolidated_agent_release_deployment.cli:main"
                         # creates a terminal command that calls the main() function

[tool.pytest.ini_options]  # settings for pytest
[tool.ruff]                # settings for ruff
[tool.mypy]                # settings for mypy
```

`>=8` means "version 8 or newer". The `[tool.*]` sections let one file configure every
tool instead of a separate settings file for each.

## Virtual environments

A **virtual environment** is a private folder of installed packages for one project, so
different projects can use different versions without clashing. Ours is `.venv/`
(ignored by Git — it's rebuilt, never committed).

```bash
python -m venv .venv                 # create it
source .venv/bin/activate            # Mac/Linux: use it in this terminal
source .venv/Scripts/activate        # Windows Git Bash
pip install -e ".[dev]"              # install the project + dev tools into it
deactivate                           # stop using it
```

`-e` (editable) means Python reads your source files directly, so edits take effect
without reinstalling. `".[dev]"` means "this folder, plus the `dev` extras".

## How the command works

`cli.py` (simplified):

```python
def main(argv=None) -> int:
    parser = build_parser()  # describes the accepted options
    parser.parse_args(argv)  # reads what the user typed; handles --version and --help
    parser.print_help()
    return 0  # 0 = success (exit code)
```

When you install the project, pip reads `[project.scripts]` and creates a small
launcher called `consolidated-agent-release-deployment` that calls `main()`.

**Exit codes** matter in pipelines: `0` means success, anything else means failure. A CI
system decides pass/fail purely from this number. Our future `check` command will exit
non-zero when an agent breaks a rule, which is how it will block a deployment.

## The hidden settings files

| File | Purpose |
|------|---------|
| `.gitignore` | Files Git should never track: `.venv/`, caches, `.env` files with secrets. |
| `.gitattributes` | Stores all text files with Unix (LF) line endings, so Windows edits don't make every line look changed. |
| `.editorconfig` | Tells editors: UTF-8, spaces not tabs, 4-space indent for Python, 2 for YAML/Markdown. |
| `.pre-commit-config.yaml` | Checks Git runs before each commit (see [topic 05](05-code-quality-tools.md)). |

## Windows note

The `Makefile` assumes Mac/Linux paths (`.venv/bin/...`) and the `make` program, which
Windows doesn't have. On Windows, run the underlying commands directly (they're listed
in the Makefile) with the venv activated, or let Claude/CI run them. Making this
smoother on Windows is in the backlog.

## Try it yourself

1. Open `pyproject.toml` on GitHub and find the line that defines the terminal command.
2. Open `src/consolidated_agent_release_deployment/__init__.py` — where is the version stored?
3. Open `.gitignore` and find the line that keeps secret `.env` files out of Git.
