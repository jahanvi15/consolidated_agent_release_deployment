# consolidated-agent-release-deployment

Release management for AI agents, run inside your CI/CD pipeline: a permanent record
of every agent version, what changed, rule checks, sign-off and audit proof.

> **Prototype.** Stage 1 in progress; not ready for real use yet.

## Project status

Updated in every feature pull request. It describes `main` once that PR is merged.

| Stage | Contents | Status |
|-------|----------|--------|
| 0 | Development environment: CI, tests, rules, learning notes | Done |
| **1** | **The foundation: features 1, 2, 3 and a basic audit log** | **In progress** |
| 2 | 12 Dependency map, 4 Quality test | Pending |
| 3 | 13 Fake business systems | Pending |
| 4 | 5 Environment moves | Pending |
| 5 | 8 Sign-off, 9 Audit proof | Pending |
| 6 | 10 Watching outside changes | Pending |
| 7 | 6 Gradual release, 7 Undo a bad release | Pending |
| ongoing | 11 One view across platforms (GitHub Actions now, Azure DevOps next) | Started |

Stage 1 in detail:

| Feature | Status | Where |
|---------|--------|-------|
| 1 A clear record of every version | Done | PR #4, ADR 0008 |
| Basic audit log | Done | PR #5, ADR 0009 |
| 2 A "what changed" summary | Pending, next | |
| 3 Automatic rule checks | Pending | |

## What it does today

```bash
consolidated-agent-release-deployment record preview sample_agents   # show records, save nothing
consolidated-agent-release-deployment record create sample_agents    # save new versions + audit events
consolidated-agent-release-deployment audit list                     # what happened
consolidated-agent-release-deployment audit verify                   # is the log intact?
consolidated-agent-release-deployment audit export -o log.csv        # for a spreadsheet
```

After every merge to `main`, GitHub Actions runs `record create` and saves the results
on the `agent-releases` branch, with a summary table on the run's page.

## Quick start (contributors)

```bash
make install    # creates .venv with dev tools
make check      # lint, format check, type check, tests — same as CI
```

Requires Python 3.11+ and `make`. On Windows (Git Bash), see the commands in the
latest journal entry in `learning/journal/`.

## Repository map

| Path | What it is |
|------|------------|
| `src/consolidated_agent_release_deployment/` | The product: manifest, version records, audit log, CLI |
| `sample_agents/` | Small scripted agents used as test fixtures |
| `tests/` | Automated tests, run on every push and PR |
| `.github/actions/record-version/` | Reusable GitHub Action that runs the CLI |
| `docs/decisions/` | Decision log (ADRs) |
| `docs/test-accounts.md` | Free accounts needed for integration work |
| `learning/` | Beginner-friendly notes: a journal entry for every push, topic guides, glossary. **Start here if you're new.** |
| `BACKLOG.md` | Planned and in-progress work |
| `CLAUDE.md` | Rules Claude follows when changing this repo |
| `scripts/protect-main.sh` | One-time setup of branch protection on GitHub |

## Contributing

`main` is protected: branch, open a pull request, and wait for the `ci-pass` check.
See [`CLAUDE.md`](CLAUDE.md) — the same rules apply to humans.

## License

[Apache License 2.0](LICENSE).
