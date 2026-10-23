# Backlog

One line per item. Move items between sections; don't delete them. Link the PR when done.
Format: `- [ID] Title — one-line outcome (stage)`

## In progress

- [S0-7] Learning notes folder and journal-per-push rule — `learning/` exists; rule in `CLAUDE.md` (PR from `docs/learning-notes`)

## Next up (Stage 0 — finish setup)

- [S0-1] Push the initial commit to github.com/jahanvi15/consolidated_agent_release_deployment — `main` has this scaffold (the only direct push to `main` ever; protection goes on right after)
- [S0-2] Run `scripts/protect-main.sh` — `main` rejects direct pushes and needs green CI
- [S0-3] Confirm the first CI run is green on a pull request — required check `ci-pass` shows up
- [S0-4] Create the free test accounts in `docs/test-accounts.md` — accounts exist, nothing committed
- [S0-5] Add a CODEOWNERS file with your GitHub handle — reviews route to you
- [S0-6] Enable secret scanning and push protection in repo settings — leaked keys are blocked

## Stage 1 — first check end to end (proposed, not yet planned)

- [S1-1] Agent manifest schema (`agent.toml`) with validation and clear errors
- [S1-2] Check: agent only uses tools it declares
- [S1-3] Check: agent output contains no secret-looking strings
- [S1-4] Check: agent stays within its declared step budget
- [S1-5] CLI `consolidated-agent-release-deployment check <path>` with exit codes for pass / fail / error
- [S1-6] Reusable GitHub Action that runs the CLI and annotates the PR

## Inbox (unsorted ideas)

- Pin exact dev tool versions (ruff, mypy) so new releases can't change results unexpectedly (needs an ADR)
- Windows-friendly dev commands (Makefile assumes `make` and `.venv/bin/`; Windows has neither)
- Azure DevOps pipeline task (second platform)
- SARIF output so findings show in GitHub code scanning
- Release automation and PyPI publishing (needs an ADR)
