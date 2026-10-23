# 05 — Code quality tools: ruff, mypy, pre-commit

**You'll learn:** what linting, formatting and type checking each catch, how to read
their messages, and how pre-commit runs them before every commit.

## Three tools, three jobs

| Tool | Command | Catches |
|------|---------|---------|
| ruff (linter) | `ruff check .` | Likely bugs, unsafe code, unused imports, messy patterns |
| ruff (formatter) | `ruff format .` | Inconsistent layout — fixes it automatically |
| mypy | `mypy` | Wrong kinds of values: passing text where a number is expected, forgetting a value can be `None` |

None of them run the code; they read it. That makes them fast, and they catch whole
categories of mistakes before a single test runs.

## ruff: the linter

Each problem has a **rule code**. The letters say which family it's from. We enabled
(in `pyproject.toml` → `[tool.ruff.lint] select`):

| Code | Family | Example of what it catches |
|------|--------|----------------------------|
| `E`, `W` | pycodestyle | Basic style errors |
| `F` | pyflakes | Unused imports, undefined names — often real bugs |
| `I` | isort | Imports out of order |
| `B` | bugbear | Classic Python traps, e.g. a list as a default argument |
| `UP` | pyupgrade | Old syntax with a modern replacement |
| `S` | bandit | **Security**: hard-coded passwords, unsafe `eval`, shell injection |
| `SIM` | simplify | Code that can be written more simply |
| `RUF` | ruff | ruff's own checks |
| `PT` | pytest style | Test-writing mistakes |

Reading a message:

```
I001 [*] Import block is un-sorted or un-formatted
  --> tests/test_harness.py:1:1
```

Rule `I001`, in that file at line 1, column 1. `[*]` means ruff can fix it
automatically: `ruff check --fix .`

**A real example from journal 0001:** ruff flagged our imports as unsorted because it
thought `sample_agents` was an outside library. The fix wasn't to silence the rule but
to tell ruff the truth (`known-first-party = [... "sample_agents"]`). Prefer fixing the
cause over hiding the warning.

**Silencing a rule** (`# noqa: S101`) is allowed only for one line, with a reason, when
the rule is genuinely wrong there. Our only blanket exception: `S101` (use of `assert`)
in tests, because `assert` is how pytest works.

## ruff: the formatter

Formatting arguments waste time. The formatter decides once: line length 100, double
quotes, consistent spacing. Run `ruff format .` and the whole project matches. CI runs
`ruff format --check .`, which only *reports*, so unformatted code fails CI.

## mypy: the type checker

Python lets you write `def steps(self) -> int:` — a **type hint** saying this returns
an integer. Python itself ignores hints; mypy checks them across the whole project.

What it catches:

```python
def load(path: str) -> Manifest: ...


load(42)  # mypy: Argument 1 has incompatible type "int"; expected "str"

reason: str | None = data.get("expected_reason")
reason.upper()  # mypy: Item "None" of "str | None" has no attribute "upper"
```

The second one is a classic crash ("`NoneType` has no attribute…") caught before running.

We use `strict = true`: every function must have type hints, and loopholes like
untyped `Any` values are flagged. It's more work while writing but makes the code
self-documenting and much safer to change.

**A real example from journal 0001:** a manifest field like `max_steps = true` is a
boolean, but in Python `True` is also technically an integer (`True == 1`). The loader
checks `isinstance(value, bool)` first so `max_steps = true` is rejected with a clear
error. A test (`max_steps = true` → "must be an integer") locks that in.

## pre-commit: checks before each commit

`.pre-commit-config.yaml` lists hooks Git runs automatically when you type
`git commit`:

1. `ruff check --fix` — lint and auto-fix
2. `ruff format` — format
3. **block commits on main** — refuses if you're on `main`, reminding you to branch

If a hook changes files or fails, the commit is stopped. Look at the message, `git add`
the fixed files, and commit again. Installed by `pre-commit install` (part of
`make install`).

`git commit --no-verify` skips hooks. It was used exactly once — to make the very first
commit on `main`, before any branch existed. Don't use it otherwise.

## Order matters: cheapest first

`make check` and CI both run: lint → format → types → tests. Cheap checks first means
you hear about a typo in one second rather than after the full test suite.

## Try it yourself

1. Find `select = [` in `pyproject.toml`. Which rule family is about security?
2. In `sample_agents/harness.py`, find `_int(...)`. Why does it check for `bool` before `int`?
