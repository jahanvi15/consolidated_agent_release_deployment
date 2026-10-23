# Learning notes

> **New contributor?** Do the setup in [`CONTRIBUTING.md`](../CONTRIBUTING.md) first, then come back here.

This folder explains, in plain language, everything technical that happens in this
project. It is written for a beginner: no prior knowledge of Git, Python tooling or
CI/CD is assumed. Every time code is pushed, a new **journal entry** is added here
describing what changed and what you can learn from it.

## How the folder is organized

| Folder / file | What's in it | When to read it |
|---------------|--------------|-----------------|
| [`journal/`](journal/) | One entry per push or pull request, numbered in order. What changed, why, the commands used, new concepts, and mistakes to avoid. | Read each new entry when it lands. Reading them in order retells the whole project. |
| [`topics/`](topics/) | Longer guides on one subject each (Git, CI, testing…). Updated whenever a push teaches something new about that subject. | When a journal entry links to one, or when you want to understand a subject properly. |
| [`glossary.md`](glossary.md) | A–Z of every technical term used in the project, in one or two sentences each. | Whenever you meet a word you don't know. |
| [`journal/_template.md`](journal/_template.md) | The shape every journal entry follows. | If you write your own entry. |

## Suggested reading order for a complete beginner

1. [Project context](../docs/project-context.md) — what we're building and why; then [the features in detail](../docs/features.md).
2. [Glossary](glossary.md) — skim it once; don't memorize.
3. [Topic 01 — Git and GitHub](topics/01-git-and-github.md)
4. [Journal 0001 — the first push](journal/0001-initial-scaffold.md)
5. [Topic 02 — How a Python project is laid out](topics/02-python-project-layout.md)
6. [Topic 03 — Automated checks (CI)](topics/03-automated-checks-ci.md)
7. [Topic 04 — Testing with pytest](topics/04-testing-with-pytest.md)
8. [Topic 05 — Code quality tools: ruff and mypy](topics/05-code-quality-tools.md)
9. [Topic 06 — Security basics for a code project](topics/06-security-basics.md)
10. [Topic 07 — Decision records, backlog and working rules](topics/07-decisions-backlog-rules.md)
11. [Topic 08 — Designing and validating an input format](topics/08-validating-input.md)
12. [Topic 09 — Working with other people on one repository](topics/09-collaborating.md)
13. Every later journal entry, in number order.

## Journal index

| # | Date | Push / PR | One-line summary |
|---|------|-----------|------------------|
| [0001](journal/0001-initial-scaffold.md) | 2026-10-23 | First push to `main` (commit `f1c54de`) | The empty-but-complete project skeleton: rules, checks, sample agents, docs |
| [0002](journal/0002-learning-notes.md) | 2026-10-23 | PR from branch `docs/learning-notes` | This learning folder, and the rule that every push adds a journal entry |
| [0003](journal/0003-manifest-schema.md) | 2026-10-23 | PR from branch `feat/s1-1-manifest-schema` | First product feature: the `agent.toml` format, validated strictly with every error listed at once |
| [0004](journal/0004-contributor-onboarding.md) | 2026-10-24 | PR from branch `docs/s0-8-contributor-onboarding` | Getting the repo ready for a second contributor: `CONTRIBUTING.md`, CODEOWNERS, team rules |
| [0005](journal/0005-project-context-and-roadmap.md) | 2026-10-24 | Added to PR #3 | The product plan written down: 13 features, 7 stages, status, open questions; backlog realigned |
| [0006](journal/0006-feature-descriptions.md) | 2026-10-24 | Added to PR #3 | Detailed description of every feature; decided vs proposed scope |

## Rules for this folder

- **Every push or pull request adds one journal entry** and a row in the index above.
  This is a project rule (see `CLAUDE.md`), not optional.
- New technical terms go into the glossary in the same change that introduces them.
- Explanations assume nothing. If a sentence needs a word the reader might not know,
  link it to the glossary or explain it right there.
- Commands are shown exactly as typed, with the expected output where it helps, and
  noted for **Windows (Git Bash)** where it differs from Mac/Linux.
- Never paste real passwords, tokens or keys here, even as an example.

These notes live in a **public** repository, so anyone can read them. That is fine:
they explain the project, they never contain secrets.
