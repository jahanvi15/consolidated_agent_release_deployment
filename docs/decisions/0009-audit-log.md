# 0009. Audit log: one hash-chained event per outcome, saved with the records

- **Status:** Proposed
- **Date:** 2026-10-30
- **Decider:** Jahanvi Joshi (answers given 2026-10-30; to accept)

## Context

Stage 1 includes a basic audit log. ADR 0008 (decision 8B) keeps it separate from the
version records: a record says *what a version is*, an event says *what happened*. The
log is also the base for sign-off (Feature 8) and audit proof (Feature 9). Fourteen
questions were asked; the chosen option for each is below.

## Decision

| # | Question | Chosen |
|---|----------|--------|
| 1 | Which events | Every outcome of `record create`: `version.created`, `version.unchanged`, and `version.refused` with a reason (`possible_secret`, `uncommitted_changes`, `invalid_agent`) |
| 2 | Log PR previews | No: previews are read-only |
| 3 | Event contents | Type, UTC time, who, agent, version, record fingerprint, where (`source`: commit, run link), reason and details for refusals |
| 4 | Who | `actor` (GitHub login, or Git user name locally) **and** `via` (`github-actions` or `local`); no emails |
| 5 | Where | The same `agent-releases` branch, folder `audit/` |
| 6 | Layout | One JSON file per event: `audit/<YYYY>/<MM>/<sequence, 9 digits>-<YYYYMMDDTHHMMSSZ>.json` |
| 7 | If saving the event fails | Everything fails: records and events of one run are saved together |
| 8 | Retention | Forever |
| 9 | Tamper evidence | Hash chain: each event holds the `event_id` of the one before |
| 10 | Event ID | Both: a `sequence` counter across the whole log, and `event_id` = SHA-256 of the event |
| 11 | Commands | `audit list` (filters `--agent`, `--since`, `--until`), `audit verify`, `audit export` (CSV) |
| 12 | GitHub view | A table on the run's summary page |
| 13 | Branch | Planned as a PR stacked on PR #4; PR #4 was merged first, so the branch starts from `main` |
| 14 | Record format | Unanswered; the suggestion was taken: records unchanged (`schema_version` 1), events point to records |

Details that follow from those answers:

- `RecordStore.save(records, events)` replaces `append`. In the Git store it makes **one
  commit** per run, and it refuses a record that has no `version.created` event, so a
  record can't exist without its event. The branch moves with compare-and-swap, so two
  runs can't both add event number N.
- `record create` now handles every agent before saving, logs the refusals, then exits 1
  if any agent was refused. The Action pushes first and fails after, so refusal events
  always reach GitHub.
- `audit verify` checks: sequence has no gaps, each `previous` matches, each `event_id`
  matches its event, file names match, every created event has its record with the same
  fingerprint, and every record has a created event. Records older than the first event
  (made before the log existed) are reported as notes, not problems.
- Refusal details say *where* a possible secret is, never the value.
- CSV cells starting with `=`, `+`, `-`, `@` get a leading `'` so spreadsheets don't run
  them as formulas.

## Consequences

- Every merge adds one commit with one event per agent, even when nothing changed. The
  branch grows steadily; revisit (e.g. monthly bundles) if it becomes slow.
- `verify` reads every event, which is fine for a prototype; it would need an index at
  much larger sizes.
- Feature 3 will add event types for rule checks; adding a type is backward compatible.
- The chain proves the log wasn't changed *after* saving; it doesn't prove who ran the
  tool. Signatures are left for Feature 9.
