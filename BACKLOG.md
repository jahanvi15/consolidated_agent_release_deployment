# Backlog

One line per item. Move items between sections; don't delete them. Link the PR when done.
Format: `- [ID] Title — one-line outcome — @owner, branch/PR (when claimed)`

IDs: `S0-n` for Stage 0 setup; `F<feature>-<n>` for product work, using the feature
numbers in [`docs/project-context.md`](docs/project-context.md) (e.g. `F1-3` = feature 1,
item 3). `A-n` = audit record. Stages follow ADR 0009. Branch names use the ID:
`feat/f1-3-version-fingerprint`.

## In progress

- [S0-8] Second-contributor onboarding + project context doc — `CONTRIBUTING.md`, CODEOWNERS, team rules, `docs/project-context.md`, ADRs 0008–0009 — @jahanvi15, PR #3
- [F1-1] Agent manifest schema (was S1-1) — `agent.toml` validated with every error reported at once — @jahanvi15, PR #2

## Next up — Stage 0 (finish setup)

- [S0-4] Create the free test accounts in `docs/test-accounts.md` — accounts exist, nothing committed
- [S0-6] Enable secret scanning and push protection in repo settings — leaked keys are blocked

## Stage 1 — first version (features 1, 2, 3 + basic audit record)

Feature 1 — version record (must come first):
- [F1-2] **Decide** what a version contains and where records are stored — ADR; owner decision (context doc open questions 5–6)
- [F1-3] Version fingerprint — a stable ID computed from a version's contents; same content → same ID
- [F1-4] Record a version — CLI command writes a version record
- [F1-5] Version history — list and show recorded versions of an agent

Basic audit record (start of feature 9):
- [A-1] Append-only audit log — every command records who, what, when, result

Feature 2 — "what changed" summary:
- [F2-1] Compare two versions — structured differences (tools added/removed, limits changed, files changed)
- [F2-2] Readable summary — plain-language/Markdown report, usable as a PR comment

Feature 3 — automatic rule checks:
- [F3-1] Rule engine and results — pass / fail / error per rule; exit codes for pipelines
- [F3-2] **Decide** first compliance scope — which rules first; owner decision (open question 4)
- [F3-3] First rules on a version — e.g. no secret-looking strings in agent files; limits within policy
- [F3-4] First change-aware rule — e.g. flag newly added tools (uses F2)
- [F3-5] GitHub Action — runs record → compare → check on a pull request and posts the summary

## Stage 2 — low-cost additions

- [F12-1] Dependency map — which agents use which tools/business systems (from version records)
- [F4-1] Basic quality test — run an agent on scripted tasks with fake tools; catches the sample agents' undeclared tool use, leaked secrets, step overruns

## Stage 3 — test infrastructure

- [F13-1] Ready-made fake business systems — first set chosen after open question 3

## Stage 4 — moving between environments

- [F5-1] Environments and per-environment connection setup
- [F5-2] Connection checks before release

## Stage 5 — people and evidence

- [F8-1] Sign-off from the right people, judged by change risk
- [F9-1] Proof for audits — complete evidence built on the A-1 log

## Stage 6 — watching for change

- [F10-1] Outside-change watching with impact alerts for business system changes

## Stage 7 — live-use safety

- [F6-1] Release to a few users first
- [F7-1] Undo a bad release, including its effects

## Ongoing

- [F11-1] **Decide** the first agent platform to support (open question 2), then add platforms over time

## Done

- [S0-1] Initial commit pushed to `main` (`f1c54de`)
- [S0-2] `main` locked by ruleset `protect-main` (created in GitHub settings)
- [S0-3] CI green on a pull request: PR #1 shows the required `ci-pass` check
- [S0-7] Learning notes folder and journal-per-push rule — PR #1
- [S0-5] CODEOWNERS file (`.github/CODEOWNERS`) — PR #3

## Superseded (ADR 0009)

Written before the roadmap was in the repo; replaced by the items above.

- [S1-2] Check: agent only uses tools it declares → runtime check, now part of F4-1
- [S1-3] Check: agent output contains no secret-looking strings → F3-3 (files) and F4-1 (runtime output)
- [S1-4] Check: agent stays within its declared step budget → F4-1
- [S1-5] CLI `check` command with exit codes → F3-1
- [S1-6] Reusable GitHub Action → F3-5

## Inbox (unsorted ideas)

- Tick "Require branches to be up to date before merging" in the `protect-main` ruleset (didn't save the first time)
- CI runs twice per PR (on `push` and `pull_request`); limit `push` to `main` to halve the minutes
- Pin exact dev tool versions (ruff, mypy) so new releases can't change results unexpectedly (needs an ADR)
- Windows-friendly dev commands (Makefile assumes `make` and `.venv/bin/`; Windows has neither)
- Azure DevOps pipeline task (second pipeline platform)
- SARIF output so findings show in GitHub code scanning
- Release automation and PyPI publishing (needs an ADR)
