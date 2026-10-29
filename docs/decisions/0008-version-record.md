# 0008. Version record: one JSON record per agent version, append-only, on a Git branch

- **Status:** Proposed
- **Date:** 2026-10-30
- **Decider:** Jahanvi Joshi (answers given 2026-10-30; to accept)

## Context

Feature 1 ("a clear record of every version") comes first because Features 2 ("what
changed"), 3 (rule checks), 8 (sign-off), 9 (audit proof) and 7 (undo) all read it. Two
open questions blocked Stage 1: what a version contains, and where it is stored.
Fourteen questions were asked; the chosen option for each is listed below.

## Decision

| # | Question | Chosen |
|---|----------|--------|
| 1 | What one version covers | One agent's whole bundle: code, prompts, model, tools, settings |
| 2 | What the record holds | Full: identity, commit, time, author **plus** model + settings, prompts, tools, config, dependencies |
| 3 | Copy or point | Mixed: small values copied in; files (code, prompts) stored as SHA-256 fingerprints; the real file is in Git at the recorded commit |
| 4 | Version ID | A counter per agent (1, 2, 3…) **plus** a content fingerprint |
| 5 | When a version is created | On merge to `main`; pull requests only preview |
| 6 | Where records live | JSON files on a separate branch, `agent-releases`, layout `records/<agent>/<NNNNNN>.json` |
| 7 | Can a record change | Never: append-only; a fix is a new version |
| 8 | Record vs. audit log | Separate: the audit log (later in Stage 1) records *events* and points to records |
| 9 | Record format | JSON |
| 10 | Format checking | pydantic models with a `schema_version` field |
| 11 | How it is used | A CLI, plus a reusable GitHub Action that only calls the CLI |
| 12 | Platform details | Neutral `content`; GitHub details only in a separate `source` section |
| 13 | Secrets | Environment variables recorded by *name* only, plus a scan that blocks a record that looks like it contains a key |
| 14 | Agents per repo | Many: every folder with an `agent.toml` |

Details that follow from those answers:

- **Fingerprint** = SHA-256 of the agent name and `content`, written as canonical JSON
  (sorted keys, no spaces). Time, counter and `source` are excluded, so the same content
  always gives the same fingerprint. If the newest record has the same fingerprint,
  `create` saves nothing ("unchanged").
- Text files are fingerprinted with Windows line endings (`\r\n`) turned into `\n`,
  so the same file gives the same fingerprint on Windows and Linux.
- Loading a record recomputes the fingerprint; a mismatch is an error (tamper check).
- The Git branch is written with Git plumbing commands and a private index, so the
  user's checkout is never touched. The branch moves only if nobody moved it meanwhile
  (`git update-ref` with the old value).
- `create` refuses a folder with uncommitted changes (the commit would not match the
  record) unless `--allow-uncommitted` is passed.
- Storage sits behind `RecordStore`; a folder store exists for local use and tests. A
  database store can be added later without changing the record.
- **New runtime dependency: pydantic (>=2.7,<3).** It is the first one (ADR 0001 kept
  zero). Reason: the record is nested, long-lived and read back by other features;
  pydantic gives strict typed validation, JSON in and out, and a JSON Schema for free.
  The manifest stays hand-written (ADR 0007).
- Workflow `.github/workflows/record-versions.yml` (added at the owner's request)
  previews on pull requests into `main` with read-only access, and saves after each
  merge to `main`. Only that job gets `contents: write`, and saves run one at a time.
  The `protect-main` ruleset covers only `main`, so pushing `agent-releases` is allowed.

## Consequences

- Features 2 and 3 can compare two records without reading the repository again.
- Records never touch `main`, so recording creates no extra pull requests or merges.
- The records branch must not be protected against the tool's pushes, and it grows by
  one commit per new version.
- Changing the record shape means bumping `schema_version` and reading both versions.
- Revisit storage when records need searching across many repos (Feature 11), or when
  the branch becomes slow.
