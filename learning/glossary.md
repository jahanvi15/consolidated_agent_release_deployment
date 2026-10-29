# Glossary

Plain-language definitions of every technical term used in this project, A–Z.
When a later push introduces a new term, it is added here in the same change.

---

**Abstract base class (ABC)** — A class that holds shared rules but leaves some methods
for subclasses to fill in. `RecordStore` is one; `GitBranchStore` and `DirectoryStore`
fill it in. See [topic 09](topics/09-version-records.md).

**ADR (Architecture Decision Record)** — A short document recording one decision: the
problem, the options considered, what was chosen and the consequences. Ours live in
`docs/decisions/`. See [topic 07](topics/07-decisions-backlog-rules.md).

**Agent (AI agent)** — A program that uses an AI model to decide what to do next and
takes actions through **tools** (searching, reading files, sending email). This project
checks agents for rule-breaking before they are deployed.

**Annotation** — A note GitHub Actions attaches to a run or to a line of code: an error,
a warning, or (like the Ubuntu 26 notice) plain information.

**Apache License 2.0** — The open-source license this project uses. Anyone may use,
change and sell the code, but must keep the copyright and license notices. It also
grants patent rights. See `docs/decisions/0003-license-apache-2.md`.

**Append-only** — Storage that only ever adds; nothing is overwritten or deleted.
Version records are append-only, so a fix is always a new version.

**assert** — A Python statement that says "this must be true". In tests, a failed
`assert` makes the test fail. Example: `assert 1 + 1 == 2`.

**Backlog** — The ordered to-do list for the project. Ours is `BACKLOG.md`.

**Blob / tree / Git object** — How Git stores everything inside `.git`: a **blob** is
one file's contents, a **tree** is a folder listing, a **commit** points to a tree. Each
is named by its hash. See topic 09.

**Branch** — An independent line of work in Git. `main` is the official version; new
work happens on other branches and is merged in through a **pull request**.

**Branch protection / Ruleset** — GitHub settings that put rules on a branch, such as
"no direct pushes" and "checks must pass before merging". A **ruleset** is GitHub's
newer, more flexible way to define these rules.

**Canonical JSON** — Writing the same data as exactly the same text every time (keys
sorted, no spaces), so its hash is stable.

**CI (Continuous Integration)** — Automatically building and testing the code every
time someone pushes a change, so problems are caught immediately.

**CI/CD pipeline** — The automated sequence that takes code from a commit to running in
production: test it (CI), then release/deploy it (CD, Continuous Delivery/Deployment).
Our product will plug into other people's pipelines.

**CLI (Command-Line Interface)** — A program you run by typing a command in a terminal
rather than clicking buttons. Our product is a CLI:
`consolidated-agent-release-deployment --version`.

**Clone** — Downloading a complete copy of a repository, including all of its history.

**Commit** — A saved snapshot of changes in Git, with a message, an author and a unique
ID (a **hash**, like `f1c54de`). The project's history is a chain of commits.

**Compare-and-swap** — Update something only if it still has the value you last saw;
otherwise fail. `git update-ref <branch> <new> <old>` does this, so two runs can't
overwrite each other's records.

**Composite action** — A reusable GitHub Action written as a list of steps in an
`action.yml` file. Ours is `.github/actions/record-version/`.

**Concurrency group (GitHub Actions)** — A name that makes runs wait for each other
instead of running at the same time. The record workflow uses one so two saves never
overlap.

**Coverage (test coverage)** — The percentage of code lines that were actually run by
the tests. We require at least 90 %. High coverage doesn't prove code is correct, but
low coverage proves parts of it are untested.

**Credential Manager (Git Credential Manager)** — A helper installed with Git for
Windows that signs you in to GitHub through the browser and remembers it securely, so
you never type a password into the terminal.

**CRLF / LF (line endings)** — The invisible characters that end a line of text: Windows
uses two (`\r\n`, CRLF), Linux and Mac one (`\n`, LF). The tool treats them the same
when fingerprinting.

**Dataclass (frozen)** — A Python class defined mostly by its named fields
(`@dataclass`). *Frozen* means its values can't be changed after creation.
`AgentManifest` is one.

**Dependency** — Someone else's code that our code needs. **Runtime** dependencies are
needed to run the product (we have none); **dev** dependencies are only needed to build
and test it (pytest, ruff, mypy…).

**Dependabot** — A GitHub service that opens pull requests to update our dependencies
and GitHub Actions to newer versions. Configured in `.github/dependabot.yml`.

**Deterministic** — Gives exactly the same result every time it runs with the same
input. Our sample agents are deterministic so tests never randomly fail.

**Editable install** — `pip install -e .` installs a project so that Python uses the
files in your folder directly; edits take effect without reinstalling.

**Entrypoint** — The function a program starts from. In `agent.toml`, `entrypoint =
"agent.py:run"` means "call the `run` function in `agent.py`".

**Environment variable** — A named value set outside a program that the program can
read, e.g. `SEARCH_API_KEY`. Secrets are passed this way so they're never written in
files. `agent.toml` lists only the names.

**Fingerprint (SHA-256)** — A 64-character code computed from data with the SHA-256 hash
function. Same data always gives the same code; any change gives a different one.
Written `sha256:…`. See topic 09.

**Fixture (test fixture)** — Anything a test needs that's prepared in advance. Our
sample agents are fixtures. In pytest, a "fixture" is also a specific feature that
hands ready-made objects to tests (like `tmp_path`, a fresh temporary folder).

**Force push** (`git push --force`) — Replaces the history on GitHub with your local
history, discarding commits that only exist on GitHub. Dangerous; blocked on `main`
once protection is on. We used it exactly once, for the first push.

**Executable bit (file mode)** — A flag that marks a file as a runnable program on
Mac/Linux. Git records it. Windows doesn't have it, so unzipping on Windows can drop it
and Git may see that as a change (journal 0001, problem 9).

**Force-with-lease** (`git push --force-with-lease`) — A safer force push: it only
overwrites GitHub's branch if that branch is still exactly what you expect, so you can't
accidentally destroy someone else's new commits.

**Formatter** — A tool that rewrites code layout (spacing, line breaks, quotes) into
one consistent style automatically. We use `ruff format`.

**Git** — The program that records the history of a project and syncs it between
computers. It runs on your machine.

**Git index (staging area)** — Where `git add` puts changes before a commit. The record
store uses its own private index, so yours is never touched.

**GitHub** — A website that hosts Git repositories and adds collaboration features:
pull requests, Actions, issues, security scanning.

**GitHub App (installed vs authorized)** — An integration such as Claude. *Authorized*
means it may act as you; *installed* decides which repositories it can access. It needs
both to work on a repo.

**GitHub Actions** — GitHub's built-in automation service. It reads YAML files in
`.github/workflows/` and runs their jobs on cloud machines when events happen (a push,
a pull request…).

**GITHUB_TOKEN** — A temporary key GitHub gives each workflow run, valid only for that
run and that repository. The `permissions:` setting decides what it may do.

**Hash (commit hash / SHA)** — The unique ID of a commit, a long string of letters and
digits. The first 7 characters (e.g. `f1c54de`) are usually enough to identify it.

**Job / Step / Runner** — In GitHub Actions a **workflow** contains **jobs**; each job
has **steps** (individual commands); each job runs on a **runner** (a fresh cloud
machine that is deleted afterwards).

**Least privilege** — Give each part of a system only the access it needs. In the record
workflow only the job that saves records may write.

**Linter** — A tool that reads code without running it and flags likely bugs, unsafe
patterns and style problems. We use `ruff check`.

**main** — The name of the official branch. Everything on `main` should always work.

**Makefile / make** — A file of named shortcuts (`make check`, `make install`) run by the
`make` program. Note: `make` is not installed on Windows by default.

**Manifest** — A file describing something. Each sample agent's `agent.toml` is its
manifest: name, allowed tools, step limit, expected result.

**Manifest schema version** — The `schema_version` number in a manifest or record. It
changes only when the format changes incompatibly, so old files are recognized, not
misread.

**Matrix (build matrix)** — Running the same CI job several times with different
settings. We run the checks on Python 3.11, 3.12, 3.13 and 3.14.

**Merge** — Combining the changes from one branch into another, e.g. a feature branch
into `main`.

**Merge commit** — A special commit with two parents that joins a branch's history into
another branch. Our chosen way to merge pull requests (ADR 0006).

**Parse, don't validate** — Design rule: convert untrusted input into a trusted, typed
object once, at the edge of the program, so the rest of the code never re-checks it.

**Path traversal** — An attack where input like `../../secret` makes a program reach
files outside the folder it should stay in. The manifest rejects `..` and absolute
paths.

**Plumbing / porcelain (Git)** — Git's friendly commands (`add`, `commit`) are
*porcelain*; the low-level ones underneath (`hash-object`, `write-tree`, `commit-tree`)
are *plumbing*.

**pydantic** — A Python library where you describe data as a class and it checks every
value coming in, and converts to and from JSON. Used for version records (ADR 0008).

**Rebase** — Re-creating commits on top of a different starting point, giving them new
IDs. Useful but rewrites history; never rebase commits others already have.

**mypy** — A **type checker** for Python. It reads type hints and reports places where
the wrong kind of value could be used. We run it in `strict` mode.

**noreply email** — A private email address GitHub gives you
(`<id>+<username>@users.noreply.github.com`) to put on commits so your real email isn't
published in the history.

**Origin / Remote** — A **remote** is a saved address of another copy of the repository;
`origin` is the conventional name for the main copy on GitHub.

**PAT (Personal Access Token)** — A password-like string that lets a program act on
GitHub as you, limited to specific repositories and permissions. Treat it like a
password; never commit it.

**pip** — Python's package installer. `pip install pytest` downloads and installs pytest.

**pre-commit hook** — A script Git runs automatically just before making a commit. Ours
formats the code and refuses commits made directly on `main`.

**pull request (PR)** — A request on GitHub to merge one branch into another. It shows
the exact changes, runs CI, and lets people comment before merging.

**Push / Pull** — **Push** sends your commits to GitHub; **pull** fetches commits from
GitHub and merges them into your copy.

**pyproject.toml** — The central settings file of a modern Python project: its name,
version, dependencies, and the settings for tools like pytest, ruff and mypy.

**pytest** — The testing tool we use. It finds files named `test_*.py`, runs every
function named `test_*`, and reports which passed or failed.

**Regular expression (regex)** — A compact pattern for matching text, e.g.
`[a-z][a-z0-9_-]{0,63}`. Python's `re` module runs them. See topic 08.

**Repository (repo)** — A project folder plus its complete Git history.

**ruff** — A fast Python tool that is both our **linter** (`ruff check`) and our
**formatter** (`ruff format`).

**Runtime dependency** — A library needed to *run* the product, listed in `dependencies`
in `pyproject.toml`. Each one needs an ADR. The first is pydantic.

**Schema** — The rules for what valid data looks like: fields, types, allowed values.
Topic 08 lists the manifest's; `version_record.py` defines the record's.

**Script injection** — When text from outside (a branch name, an input) is pasted into a
script and runs as commands. In GitHub Actions, avoid it by passing values through
`env:`.

**Secret** — Anything that grants access: passwords, API keys, tokens, private keys.
Secrets must never be written into code or committed.

**src layout** — Putting a project's importable code under a `src/` folder. It stops
tests from accidentally using the un-installed copy of the code.

**Status check** — A pass/fail result GitHub shows on a commit or PR, reported by CI.
Our required one is called `ci-pass`.

**Subprocess** — A separate program started by your program, like Python running `git`.
Pass its arguments as a list, never through a shell, so input can't become a command.

**Tamper check** — Recomputing a fingerprint when loading data and failing if it doesn't
match, which proves the data wasn't edited.

**Terminal / Shell / Git Bash** — A text window where you type commands. On Windows,
**Git Bash** is a terminal installed with Git that understands the same commands as
Mac and Linux.

**TOML** — A simple settings-file format (`key = "value"`), used by `pyproject.toml`
and our `agent.toml` manifests.

**Type hint** — A note in Python code saying what kind of value something is, e.g.
`def steps(self) -> int:` says this returns an integer. Python doesn't enforce them;
mypy checks them.

**UTC** — Coordinated Universal Time, the one clock every computer agrees on. Records
store times in UTC (ending in `Z`); India is UTC+05:30.

**Validation** — Checking input against a schema before using it. Ours is strict:
unknown fields are errors and every problem is reported at once.

**Version (semantic versioning)** — A number like `0.0.1` meaning MAJOR.MINOR.PATCH.
`0.x` means "early development, anything may change".

**Version record** — A permanent JSON file describing exactly one version of one agent:
content, fingerprints, who, when and where it was built. Feature 1. See topic 09.

**Virtual environment (venv)** — A private folder of Python packages for one project
(ours is `.venv/`), so projects don't interfere with each other or with system Python.

**Workflow** — A YAML file in `.github/workflows/` telling GitHub Actions what to run
and when. Ours is `ci.yml`.

**Working tree** — The actual files in your project folder, as opposed to the history
stored in the hidden `.git` folder. "Working tree clean" means no unsaved changes.

**YAML** — A settings-file format based on indentation (`key: value`), used for GitHub
Actions workflows. Indentation matters: two spaces, never tabs.
