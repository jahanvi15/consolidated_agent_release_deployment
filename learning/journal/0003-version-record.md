# 0003 — Feature 1: a clear record of every version

| | |
|---|---|
| **Date** | 2026-10-30 |
| **Push / PR** | Branch `feat/s1-1-version-record` → pull request into `main` |
| **Backlog item** | Stage 1, Feature 1 (version record), including the manifest from the closed PR #2 |
| **Read first** | [Topic 08 — validating input](../topics/08-validating-input.md), [Topic 09 — version records](../topics/09-version-records.md), [ADR 0008](../../docs/decisions/0008-version-record.md) |

## In one paragraph

The tool can now write down, permanently, exactly what each version of an agent is:
which model and settings it uses, its prompts, tools, config and dependencies, plus a
fingerprint of every file. A record is saved only when something really changed. Records
live on a separate Git branch (`agent-releases`), so they never add commits to `main`,
and they can never be edited. "What changed" (Feature 2) and the rule checks
(Feature 3) will be built on top of these records. Every design choice comes from the
14 answers recorded in ADR 0008.

## What changed

| File / folder | Change | Why |
|---------------|--------|-----|
| `src/.../manifest.py` | added | Reads and strictly checks `agent.toml` (from closed PR #2), now with `prompts`, `env`, `dependencies`, `[model]`, `[config]` |
| `src/.../version_record.py` | added | The record's shape (pydantic), fingerprints, building a record from a folder |
| `src/.../store.py` | added | Append-only storage: Git branch store and folder store |
| `src/.../source.py` | added | Works out local vs GitHub Actions; the only platform-specific code |
| `src/.../secret_scan.py` | added | Blocks records that look like they contain a key |
| `src/.../gitutil.py` | added | Runs `git` safely |
| `src/.../cli.py` | changed | New commands: `record preview / create / list / show` |
| `.github/actions/record-version/action.yml` | added | Reusable Action: preview on PRs, create + push otherwise |
| `pyproject.toml` | changed | First runtime dependency, pydantic; mypy's pydantic plugin |
| `sample_agents/*` | changed | New manifest format; test expectations moved to `expected.toml`; `helpful_summarizer` shows every field and has a prompt file |
| `tests/` | added/changed | 188 tests (was 35). Coverage 99.9 % |
| `docs/decisions/0007…`, `0008…` | added (Proposed) | Manifest format; version record. For you to accept |
| `learning/` | added/changed | This entry, topic 09, field table in topic 08, 26 glossary terms |

## New concepts

Each is explained properly in [topic 09](../topics/09-version-records.md).

- **Fingerprint (SHA-256 hash)** — a 64-character code computed from data. Same data,
  same code; any change, different code. Used to spot changes and to catch edited
  records.
- **Counter plus fingerprint** — people read "version 3"; the tool compares
  fingerprints to decide whether a new version is needed at all.
- **Canonical JSON** and **line endings** — two traps that would make identical content
  look different (key order; Windows `\r\n` vs `\n`).
- **Append-only** — records are only added, never changed. A mistake is fixed by a new
  version. This is what makes the history trustworthy for an audit later.
- **Git plumbing** — writing a commit to another branch by hand (blob → tree → commit →
  move the branch), using a private index so your files and staged changes are never
  touched. **Compare-and-swap** stops two runs from overwriting each other.
- **pydantic** — describe data as a class; every value is checked on the way in, and
  converted to and from JSON.
- **A storage layer** (abstract base class) so the storage place can change later
  without changing anything else.
- **Neutral content, separate `source`** — GitHub details live only in `source`, so the
  same agent gets the same fingerprint on any platform.
- **Secrets by name only**, plus a scan that blocks a record and says *where* the
  problem is without ever printing the secret.
- **Safe commands** — `subprocess` with a list (no shell), and `env:` in the Action to
  prevent **script injection**.

## Commands used

Set up once (Windows, Git Bash, inside the project folder):

```bash
git fetch origin
git switch feat/s1-1-version-record
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Mac/Linux: .venv/bin/python
```

On Windows the tools live in `.venv/Scripts/`, not `.venv/bin/`, and `make` isn't
installed, so run the checks directly:

```bash
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .
.venv/Scripts/mypy
.venv/Scripts/pytest            # expect: 188 passed ... Total coverage: 99.87%
```

Try the feature (`C` is just a short name for the long command):

```bash
C=.venv/Scripts/consolidated-agent-release-deployment

$C record preview sample_agents/helpful_summarizer
# prints the record as JSON; saves nothing

$C record create --store-dir /tmp/try-records sample_agents
# helpful_summarizer: created version 1 (045024061986)
# runaway_loop: created version 1 (...)
# ... one line per agent

$C record create --store-dir /tmp/try-records sample_agents
# helpful_summarizer: unchanged, still version 1 (045024061986)

$C record list --store-dir /tmp/try-records helpful_summarizer
# 1  2026-10-30 09:00Z  045024061986  Your Name
```

`--store-dir` keeps your experiments in a throwaway folder. Without it the records go on
the `agent-releases` branch of the repo you're in. Push that branch with
`git push origin agent-releases`. Don't do that on this repo until we decide to (see
below).

## What went wrong / what to watch for

1. **PR #2 (the manifest) was closed without being merged**, so `main` had no
   `agent.toml` reader. Feature 1 can't work without it, so that code is included here
   instead of being a separate PR.
2. **The secret scan blocked a harmless setting.** `max_output_tokens = 400` matched
   the word "token". Fixed: only *text* values are checked, and "tokens" (plural)
   doesn't count. A test now covers it. Lesson: test a safety check against innocent
   inputs too, not only bad ones.
3. **A test assumed the wrong value** (`max_steps` of a sample agent is 5, not 2). The
   test failed, which is exactly its job; the test was fixed, not the code.
4. **The GitHub workflow is not included.** Saving records after each merge needs a
   workflow file with permission to push (`contents: write`). Project rules say workflow
   files change only when you ask, so it's a separate decision.
5. **PR size:** about three times the ~400-line guideline, because the manifest code
   came along and Feature 1 has several parts. Most of the extra lines are tests.

## How to verify it yourself

1. Run the checks above; all must pass.
2. Run `record create --store-dir …` twice; the second run must say "unchanged".
3. Edit `sample_agents/helpful_summarizer/prompts/system.md`, commit it on a scratch
   branch, run `create` again: only that agent gets version 2.
4. Open a saved `000001.json`, change `"max_steps"`, run `record show`: it must fail
   with "fingerprint does not match content".

## Further reading

- [Topic 09](../topics/09-version-records.md) and its links.
- [ADR 0008](../../docs/decisions/0008-version-record.md) — the 14 decisions.
