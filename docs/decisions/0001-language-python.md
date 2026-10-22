# 0001. Use Python 3.11+ as the implementation language

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

The tool inspects and runs AI agents. Most agents people will bring to it are built with
Python frameworks and SDKs. The sample agents we test against should be in the same
language as the tool so one test run covers both.

## Options considered

1. **Python** — matches the agent ecosystem; easy to import and run agents in-process;
   strong typing via mypy. Slower startup, packaging is less tidy than a static binary.
2. **TypeScript** — native fit for GitHub Actions; weaker fit for Python-built agents.
3. **Go** — single binary drops into any pipeline; few agent libraries, so checking a
   Python agent means shelling out.

## Decision

Python, minimum version 3.11 (stdlib `tomllib`, modern typing). CI tests 3.11 through 3.14.

## Consequences

- Tooling: ruff (lint + format), mypy strict, pytest with a 90 % coverage floor.
- Runtime dependencies are kept at zero until an ADR adds one, to keep installs fast
  and the supply-chain surface small.
- Shipping into GitHub Actions means a composite action that installs the package,
  not a JavaScript action. Revisit if action startup time becomes a problem.
