# consolidated-agent-release-deployment

Release management for AI agents, run inside your CI/CD pipeline: a record of every
agent version, what changed, automatic rule checks — and, stage by stage, safe promotion,
sign-off, audit evidence, gradual release and undo.

**What we're building and where we are: [`docs/project-context.md`](docs/project-context.md).**

> **Status: Stage 0 nearly done; Stage 1 (version record → what changed → rule checks) starting.** See
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
| `docs/project-context.md` | What we're building, roadmap, status, open questions — read first |
| `docs/decisions/` | Decision log (ADRs) |
| `docs/test-accounts.md` | Free accounts needed for integration work |
| `learning/` | Beginner-friendly notes: a journal entry for every push, topic guides, glossary. **Start here if you're new.** |
| `BACKLOG.md` | Planned and in-progress work |
| `CLAUDE.md` | Rules Claude follows when changing this repo |
| `CONTRIBUTING.md` | Step-by-step setup for a new contributor (and the maintainer's checklist) |
| `scripts/protect-main.sh` | One-time setup of branch protection on GitHub |

## Contributing

New here? **Start with [`CONTRIBUTING.md`](CONTRIBUTING.md)** — account, Claude and
workflow setup, step by step for beginners. `main` is protected: branch, open a pull
request, and wait for the `ci-pass` check. Rules for humans and Claude: [`CLAUDE.md`](CLAUDE.md).

## License

[Apache License 2.0](LICENSE).
