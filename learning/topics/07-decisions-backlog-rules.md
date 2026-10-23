# 07 — Decision records, backlog and working rules

**You'll learn:** how this project remembers *why* things are the way they are, how
work is planned, and the rules both humans and Claude follow.

## Decision records (ADRs)

Code shows *what* was built; it rarely shows *why*. Six months later nobody remembers
why Python and not Go, or why approvals are set to zero. An **Architecture Decision
Record** is a one-page note answering that, written when the decision is made.

Each lives in `docs/decisions/NNNN-title.md` and has:

1. **Status** — Proposed → Accepted (or Rejected / Superseded by NNNN)
2. **Context** — what problem forced a decision now
3. **Options considered** — with pros and cons
4. **Decision** — stated plainly
5. **Consequences** — what gets easier, harder, and what would make us revisit it

ADRs are **never edited to change the decision**. To change one, write a new ADR that
supersedes it. The old one stays as history.

Current decisions: 0001 Python · 0002 GitHub Actions first · 0003 Apache-2.0 ·
0004 protected `main` · 0005 fake sample agents.

**When is something ADR-worthy?** When a reasonable person could disagree with it:
choosing a library, a file format, a public interface, a security trade-off.

## The backlog

`BACKLOG.md` is the single to-do list, in sections:

- **In progress** — being worked on now
- **Next up** — the current stage, in order
- **Stage N** — planned later work
- **Inbox** — ideas not yet sorted

Each item has an ID (`S1-2` = Stage 1, item 2) used in branch names and PR titles, so
you can trace any code change back to why it was planned. Items move between sections
instead of being deleted, so the file is also a record of what was done.

## The working rules (`CLAUDE.md`)

Claude reads `CLAUDE.md` automatically when working in the repo; humans should follow
it too. Summary:

1. Never commit or push to `main` — branch and open a PR.
2. Run `make check` before calling anything done; never weaken a check to make it pass.
3. No real secrets or personal data anywhere; fake ones start with `FAKE-`.
4. Tests never touch the network or a real AI model.
5. No new runtime dependency without an ADR.
6. Don't change LICENSE, CI workflows, the protection script or accepted ADRs unless asked.
7. **Every push adds a learning journal entry** (this folder).

Plus: one backlog item per PR, PRs under ~400 lines, tests come with every change.

## The pull request template

`.github/pull_request_template.md` pre-fills every new PR with a checklist: checks pass,
tests added, backlog updated, ADR if needed, no secrets, learning entry added. It turns
the rules above into something you tick off at the moment it matters.

## Try it yourself

1. Read `docs/decisions/0004-protected-main-and-ci.md`. Why are required approvals 0?
   What event would change that?
2. Pick a Stage 1 item in `BACKLOG.md`. What branch name would its PR use?
