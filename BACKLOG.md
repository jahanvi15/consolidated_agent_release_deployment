# Backlog

One line per item. Move items between sections; don't delete them. Link the PR when done.
Format: `- [ID] Title — one-line outcome (stage)`

## In progress

- [S0-8] Second-contributor onboarding — `CONTRIBUTING.md`, CODEOWNERS, team rules in `CLAUDE.md`, ADR 0008 — @jahanvi15, branch `docs/s0-8-contributor-onboarding`
- [S1-1] Agent manifest schema — `agent.toml` validated with every error reported at once — @jahanvi15, PR #2

## Next up (Stage 0 — finish setup)

- [S0-4] Create the free test accounts in `docs/test-accounts.md` — accounts exist, nothing committed
- [S0-6] Enable secret scanning and push protection in repo settings — leaked keys are blocked

## Stage 1 — first check end to end (proposed, not yet planned)

- [S1-2] Check: agent only uses tools it declares
- [S1-3] Check: agent output contains no secret-looking strings
- [S1-4] Check: agent stays within its declared step budget
- [S1-5] CLI `consolidated-agent-release-deployment check <path>` with exit codes for pass / fail / error
- [S1-6] Reusable GitHub Action that runs the CLI and annotates the PR

## Done

- [S0-1] Initial commit pushed to `main` (`f1c54de`)
- [S0-2] `main` locked by ruleset `protect-main` (created in GitHub settings)
- [S0-3] CI green on a pull request: PR #1 shows the required `ci-pass` check
- [S0-7] Learning notes folder and journal-per-push rule — PR #1
- [S0-5] CODEOWNERS file (`.github/CODEOWNERS`) — in the S0-8 PR

## Inbox (unsorted ideas)

- Tick "Require branches to be up to date before merging" in the `protect-main` ruleset (didn't save the first time)
- CI runs twice per PR (on `push` and `pull_request`); limit `push` to `main` to halve the minutes
- Pin exact dev tool versions (ruff, mypy) so new releases can't change results unexpectedly (needs an ADR)
- Windows-friendly dev commands (Makefile assumes `make` and `.venv/bin/`; Windows has neither)
- Azure DevOps pipeline task (second platform)
- SARIF output so findings show in GitHub code scanning
- Release automation and PyPI publishing (needs an ADR)
