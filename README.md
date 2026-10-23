# consolidated-agent-release-deployment

Pre-deployment compliance checks for AI agents, run inside your CI/CD pipeline.

> **Status: Stage 0 — development environment only.** No checks ship yet. See
> [`BACKLOG.md`](BACKLOG.md) for what's next.

## Quick start (contributors)

```bash
make install    # creates .venv with dev tools
make check      # lint, format check, type check, tests — same as CI
```

Requires Python 3.11+ and `make`.

## Repository map

| Path | What it is |
|------|------------|
| `src/consolidated_agent_release_deployment/` | The product (currently just the CLI shell) |
| `sample_agents/` | Small scripted agents used as test fixtures |
| `tests/` | Automated tests, run on every push and PR |
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
