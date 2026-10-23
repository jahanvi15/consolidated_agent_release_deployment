# 04 — Testing with pytest

**You'll learn:** what an automated test is, how pytest finds and runs tests, the
pytest features our tests use, coverage, and why our sample agents are fake.

## What a test is

A test is a small function that runs some code and checks the result. If the check
fails, the test fails. Example from `tests/test_cli.py`:

```python
def test_no_arguments_prints_help_and_succeeds(capsys):
    # 1. the program returns 0, which means success
    assert main([]) == 0
    # 2. it printed the help text
    assert "usage: consolidated-agent-release-deployment" in capsys.readouterr().out
```

Tests protect you from breaking things later: change the code, run the tests, and
anything you broke turns red immediately.

## How pytest finds tests

- Looks in `tests/` (set by `testpaths` in `pyproject.toml`).
- Files named `test_*.py`, functions named `test_*`.
- Runs each one and prints `.` for pass, `F` for fail, then a summary.

```
tests/test_cli.py ...                     [  8%]
tests/test_harness.py ...............     [ 51%]
tests/test_sample_agents.py ............. [100%]
35 passed in 0.20s
```

## Features our tests use

**`assert`** — the check. `assert x == 5`. On failure pytest shows both values.

**`pytest.raises`** — checks that code fails *the right way*:

```python
with pytest.raises(ManifestError, match="must be an integer"):
    load_manifest(bad_file)
```

Testing failures is as important as testing success: bad input should give a clear
error, not a crash or a silent wrong answer.

**Fixtures** — ready-made helpers pytest passes in by argument name:
- `tmp_path` — a fresh empty temporary folder, deleted afterwards. Used to write
  broken `agent.toml` files without touching the real ones.
- `capsys` — captures what the code printed so the test can check it.

**`@pytest.mark.parametrize`** — run one test with many inputs:

```python
@pytest.mark.parametrize("agent_dir", AGENT_DIRS, ids=lambda d: d.name)
def test_agents_are_deterministic(agent_dir): ...
```

This becomes four tests, one per sample agent, each named after the agent.

## Coverage

`pytest-cov` records which lines ran during the tests. Our settings fail the run if
coverage drops below 90 %:

```
Name                       Stmts   Miss  Cover   Missing
sample_agents/harness.py     115      1    99%   172
TOTAL                        154      1    99%
```

`Missing` lists line numbers never executed. Coverage tells you what is *untested*; it
can't tell you the tests check the *right* things.

## Strict settings

In `pyproject.toml`:
- `--strict-markers` — a typo in a marker name is an error, not silently ignored.
- `filterwarnings = ["error"]` — any warning fails the tests, so deprecations are dealt
  with immediately instead of piling up.

## Why the sample agents are fake

A real AI agent calls an AI model over the internet. In tests that would be:
- **slow** (seconds per call), **costly** (paid per use), **needs secrets in CI**,
- and **random** — the same question can get a different answer, so tests would fail
  for no reason ("flaky tests").

So each sample agent is a tiny script that always does the same thing, and calls tools
through a `ToolBox` that records every call:

```python
@dataclass
class ToolBox:
    tools: Mapping[str, Tool]
    calls: list[ToolCall] = field(default_factory=list)

    def call(self, name: str, **args: str) -> str:
        self.calls.append(ToolCall(name=name, args=dict(args)))  # record first
        ...
```

Recording *before* running means even a call to a tool that doesn't exist is captured —
exactly what a compliance check needs to see.

`tests/test_sample_agents.py` then proves each fake agent breaks precisely its one rule
and no others. That's "testing the test material": if `secret_leaker` stopped leaking,
the future secret check could appear to work while actually checking nothing.

## Running tests yourself

```bash
pytest                      # everything
pytest tests/test_cli.py    # one file
pytest -k secret            # only tests with "secret" in their name
pytest -x                   # stop at the first failure
pytest -vv                  # verbose: one line per test
```

## Try it yourself

1. Read `tests/test_sample_agents.py`. Which test proves `runaway_loop` can't run forever?
2. In `tests/test_harness.py`, count how many broken manifests the parametrized test
   tries. What does each one get wrong?
