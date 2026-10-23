# 0003 — The agent manifest schema (first product feature)

| | |
|---|---|
| **Date** | 2026-10-23 |
| **Push / PR** | Branch `feat/s1-1-manifest-schema` → pull request into `main` |
| **Backlog item** | S1-1 |
| **Read first** | [Topic 08 — Designing and validating an input format](../topics/08-validating-input.md), [docs/agent-manifest.md](../../docs/agent-manifest.md) |

## In one paragraph

Every agent describes itself in an `agent.toml` file: its name, which tools it may use,
and how many steps it may take. The Stage 1 checks will compare what an agent *does*
with what that file *declares*, so the file itself must be trustworthy. This change
turns the draft format into a real, versioned format with strict validation: any
mistake — a typo, a wrong type, a missing field, a suspicious path — produces a clear
message, and **all** problems are listed at once.

## What changed

| File / folder | Change | Why |
|---------------|--------|-----|
| `src/.../manifest.py` | added | The product's manifest loader and validator — the first real feature code |
| `docs/agent-manifest.md` | added | Reference page for users writing `agent.toml` |
| `docs/decisions/0007-agent-manifest-format.md` | added (Proposed) | Why TOML, flat, strict, all-errors, no library — for you to accept |
| `sample_agents/*/agent.toml` | changed | Rewritten in the new format (`schema_version`, `description`) |
| `sample_agents/*/expected.toml` | added | Test-only expectations moved out of the real manifest |
| `sample_agents/harness.py` | changed | Uses the product's loader; reads `expected.toml`; honours `entrypoint` |
| `tests/test_manifest.py` | added | 54 tests for every rule |
| `tests/test_harness.py`, `tests/test_sample_agents.py` | changed | Adapted; every sample manifest must now pass the real validator |
| `BACKLOG.md` | changed | S1-1 in progress; finished Stage 0 items moved to Done; two new inbox items |

Tests: 35 → **92**. Coverage of `manifest.py`: **100 %**.

## New concepts

**Schema** — the rules for what a valid file looks like: which fields, which types,
which values. `docs/agent-manifest.md` is our schema written for humans;
`manifest.py` is the same schema written as code.

**Validation, and "fail loudly"** — checking input against the schema *before* using
it. The important design choice: an unknown field is an **error**, not ignored. Imagine
someone writes `max_step = 5` (missing "s"). A forgiving loader would ignore that line
— and the agent would have **no step limit at all**, while its owner believes it has
one. For a compliance tool, a silent mistake is worse than a loud one.

**Collect all errors, then report** — instead of stopping at the first problem, every
check appends an `Issue(field, message)` to a list; only at the end, if the list isn't
empty, one `ManifestError` is raised containing all of them. Users fix their file once
instead of playing whack-a-mole.

**"Did you mean…?"** — Python's built-in `difflib.get_close_matches` finds the known
field name most similar to a typo. Small touch, big help.

**Versioning a format** — `schema_version = 1` is required. If the format ever changes
incompatibly, version 2 can be introduced and old files are recognized instead of being
misread.

**Path traversal** — the `entrypoint` names a Python file the tool will later run. If it
could be `../../somewhere/else.py`, a manifest could make the tool run code outside the
agent's folder. So `..` and absolute paths are rejected. Never trust a path that came
from a file someone else wrote.

**Separating product data from test data** — the sample agents' expected results
(`verdict`, `reason`) used to sit inside `agent.toml`. Real users would never write
those, and the new strict validator would reject them as unknown fields. They now live
in `expected.toml`, which only the test harness reads.

**Frozen dataclass** — `AgentManifest` is a `@dataclass(frozen=True)`: a class that is
mostly a bundle of named fields, and *frozen* means it can't be changed after creation.
Once validated, nothing can accidentally alter it.

**Regular expressions** — compact patterns for text. `[a-z][a-z0-9_-]{0,63}` means:
one lowercase letter, then 0–63 characters that are lowercase letters, digits, `_` or
`-`. `fullmatch` requires the *whole* name to fit, not just a part.

See [topic 08](../topics/08-validating-input.md) for these ideas in more depth.

## Commands used

Claude did this work in its own workspace; these are the same steps on your PC.

```bash
# start from the PR #1 branch, because this work needs the learning folder from it
git switch docs/learning-notes
git pull
git switch -c feat/s1-1-manifest-schema    # the new feature branch (ADR 0006 naming)

# ...write code and tests...
ruff check --fix . && ruff format .        # tidy up
make check                                 # everything CI runs; must be green
git add -A
git commit -m "feat: agent manifest schema with full validation (S1-1)"
git push -u origin feat/s1-1-manifest-schema
```

Why start from `docs/learning-notes` instead of `main`? PR #1 isn't merged yet, and this
branch needs its files. Because we merge with **merge commits** (ADR 0006), once PR #1
merges, this branch's history already contains it — nothing to redo. On GitHub, this PR
targets `main` and will show PR #1's commits too until #1 is merged; after that only
S1-1's own changes remain.

Try the validator yourself (inside the project's virtual environment):

```bash
python -c "from pathlib import Path; from consolidated_agent_release_deployment.manifest import load_manifest; print(load_manifest(Path('sample_agents/helpful_summarizer/agent.toml')))"
```

## What went wrong / what to watch for

- **`assert` in product code.** The first version used `assert x is not None` to
  convince the type checker that values were set. But Python **removes all asserts**
  when run with optimization (`python -O`), so asserts must never guard real logic.
  Rewritten with ordinary `if` checks. Asserts belong in tests.
- **`True` is an integer in Python.** `isinstance(True, int)` is `True`, so a naive check
  would accept `max_steps = true` as `1`. Booleans are rejected explicitly — and a test
  locks that in.
- **Order of error messages.** Unknown and missing fields are listed first, then
  per-field problems in a fixed order, so the same file always gives the same message.
  Tests rely on that; users benefit from it.
- **Ruleset check (from Step 5):** "Require branches to be up to date before merging"
  didn't save. Harmless for now; added to the backlog inbox.

## How to verify it yourself

1. On the PR, `ci-pass` is green.
2. Open **Files changed** → `docs/agent-manifest.md` → click **Display the rich diff**
   (page icon) to read it formatted.
3. Break a sample manifest on purpose in your copy (e.g. rename `max_steps` to
   `max_step` in `sample_agents/helpful_summarizer/agent.toml`), run `pytest`, and read
   the error. Then undo with `git restore sample_agents/helpful_summarizer/agent.toml`.
4. Read ADR 0007. If you agree, change its status to **Accepted** (in a later PR) — or
   tell Claude what to change.

## Further reading

- TOML specification — <https://toml.io/en/v1.0.0>
- Python `tomllib` — <https://docs.python.org/3/library/tomllib.html>
- Python `dataclasses` — <https://docs.python.org/3/library/dataclasses.html>
- Python regular expressions HOWTO — <https://docs.python.org/3/howto/regex.html>
- OWASP: Path traversal — <https://owasp.org/www-community/attacks/Path_Traversal>
