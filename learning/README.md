# Learning notes

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

1. [Glossary](glossary.md) — skim it once; don't memorize.
2. [Topic 01 — Git and GitHub](topics/01-git-and-github.md)
3. [Journal 0001 — the first push](journal/0001-initial-scaffold.md)
4. [Topic 02 — How a Python project is laid out](topics/02-python-project-layout.md)
5. [Topic 03 — Automated checks (CI)](topics/03-automated-checks-ci.md)
6. [Topic 04 — Testing with pytest](topics/04-testing-with-pytest.md)
7. [Topic 05 — Code quality tools: ruff and mypy](topics/05-code-quality-tools.md)
8. [Topic 06 — Security basics for a code project](topics/06-security-basics.md)
9. [Topic 07 — Decision records, backlog and working rules](topics/07-decisions-backlog-rules.md)
10. [Topic 08 — Designing and validating an input format](topics/08-validating-input.md)
11. [Topic 09 — Version records: fingerprints, append-only storage, Git's inner parts](topics/09-version-records.md)
12. Every later journal entry, in number order.

## Journal index

| # | Date | Push / PR | One-line summary |
|---|------|-----------|------------------|
| [0001](journal/0001-initial-scaffold.md) | 2026-10-23 | First push to `main` (commit `f1c54de`) | The empty-but-complete project skeleton: rules, checks, sample agents, docs |
| [0002](journal/0002-learning-notes.md) | 2026-10-23 | PR from branch `docs/learning-notes` | This learning folder, and the rule that every push adds a journal entry |
| [0003](journal/0003-version-record.md) | 2026-10-30 | PR from branch `feat/s1-1-version-record` | Feature 1: a permanent, fingerprinted record of every agent version, saved on its own branch |

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
