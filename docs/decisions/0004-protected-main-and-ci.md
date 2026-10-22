# 0004. Protect `main`; all changes via pull request with one required check

- **Status:** Accepted
- **Date:** 2026-10-23
- **Decider:** Jahanvi Joshi

## Context

Claude and humans both change this repo. A compliance tool must itself have a clean,
reviewable history. Every change should pass the same automated checks before landing.

## Decision

- `main` is protected with a GitHub **repository ruleset** (`scripts/protect-main.sh`):
  no direct pushes, no force-pushes, no deletion, pull request required, conversations
  must be resolved, and the status check **`ci-pass`** must succeed on an up-to-date branch.
- Required approvals are **0** for now, because a solo maintainer cannot approve their
  own PR. Raise to 1 when a second reviewer exists.
- CI runs on every push and pull request: ruff lint, ruff format check, mypy strict, and
  pytest with coverage, on Python 3.11 through 3.14. A final `ci-pass` job depends on
  all of them, so branch protection only has to name one check even as the matrix grows.
- Workflow permissions default to `contents: read`.

## Consequences

- GitHub Free only enforces rulesets on **public** repositories. If the repo is private,
  protection needs GitHub Pro (or Team) — otherwise the script's rules are saved but not enforced.
- Changing the CI job names requires updating `ci-pass` dependencies, not branch protection.
