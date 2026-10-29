# 0004 — The basic audit log

| | |
|---|---|
| **Date** | 2026-10-30 |
| **Push / PR** | Branch `feat/s1-audit-log` → pull request into `main` |
| **Backlog item** | Stage 1, basic audit log |
| **Read first** | [Topic 09 — version records](../topics/09-version-records.md), [Topic 10 — audit logs](../topics/10-audit-logs.md), [ADR 0009](../../docs/decisions/0009-audit-log.md) |

## In one paragraph

Every time the tool runs after a merge, it now writes down what happened to each agent:
a new version was created, nothing changed, or it refused (possible secret,
uncommitted changes, invalid agent). These **audit events** are linked in a hash chain,
so editing or deleting one is detectable with `audit verify`. Events and new records are
saved together in one commit, so a record can never exist without its event. You can
list the events, export them to a spreadsheet, and see a table on each GitHub run's
page. The README now shows which stages and features are done, in progress and pending.

## What changed

| File / folder | Change | Why |
|---------------|--------|-----|
| `src/.../audit.py` | added | Event shape, hash chain, `verify`, CSV and Markdown output |
| `src/.../store.py` | changed | `save(records, events)` writes everything in one go; `append` removed so no record is saved without its event |
| `src/.../cli.py` | changed | `record create` logs every outcome; new `audit list / verify / export` |
| `src/.../source.py` | changed | Writes the GitHub run summary |
| `src/.../version_record.py` | changed | Shared base class renamed `StrictModel` so `audit.py` can use it |
| `.github/actions/record-version/action.yml` | changed | Pushes refusal events *before* failing the step |
| `tests/` | added/changed | 226 tests (was 188); new code at 100 % coverage |
| `README.md` | changed | Project status tables; what the tool does today |
| `docs/decisions/0009-audit-log.md` | added (Proposed) | Your 13 answers, plus the default taken for question 14 |
| `learning/` | added/changed | This entry, topic 10, glossary terms |

## New concepts

Explained properly in [topic 10](../topics/10-audit-logs.md).

- **Audit event** vs **version record**: what happened vs what a version is.
- **Hash chain**: each event stores the fingerprint of the one before. Changing,
  deleting or reordering any event breaks the chain.
- **Atomic (all-or-nothing) write**: one commit per run, so a crash can't leave a record
  without its event.
- **Failing after the work is done**: `|| result=$?` lets the Action push the evidence
  first and fail afterwards.
- **CSV injection**: spreadsheet cells starting with `=` can run as formulas, so exports
  add a `'` in front.
- **Job summary**: Markdown written to `$GITHUB_STEP_SUMMARY` shows on the run's page.

## Commands used

Windows (Git Bash), inside the project folder, after `git switch feat/s1-audit-log`
and reinstalling (`.venv/Scripts/python -m pip install -e ".[dev]"`):

```bash
C=.venv/Scripts/consolidated-agent-release-deployment   # Mac/Linux: .venv/bin/...

$C record create --store-dir /tmp/try sample_agents
# helpful_summarizer: created version 1 (045024061986)
# ...
# audit: logged events 1-4

$C audit list --store-dir /tmp/try
#     1  2026-10-30 09:00Z  helpful_summarizer  v1  created  Your Name

$C audit verify --store-dir /tmp/try
# audit log intact: 4 events, 4 records checked

$C audit export --store-dir /tmp/try -o /tmp/try.csv
# wrote /tmp/try.csv
```

Filters: `--agent runaway_loop`, `--since 2026-10-01`, `--until 2026-10-31`.

## What went wrong / what to watch for

1. **PR #4 was merged before this work started**, so the planned stacked branch
   (question 13B) wasn't needed. The branch starts from `main` instead, which gives the
   same result.
2. **Four records already existed without events.** PR #4's merge recorded the sample
   agents before the log existed. Rather than inventing events afterwards, `verify`
   reports such older records as notes, not problems.
3. **A refused run would have lost its own evidence.** The Action stops at the first
   failing command, so the push after a refusal would have been skipped. Found by
   reading the script before testing; fixed with `|| result=$?`, then rehearsed against
   a copy of the real records branch.
4. **Question 14 had no answer.** The suggested option was taken (records unchanged);
   say if you want otherwise.
5. **A test was wrong, not the code**: the first "mismatched fingerprint" test swapped
   two records, but each record still matched its own event. Rewritten to put a
   genuinely different record in place.

## How to verify it yourself

1. Run the commands above. Then delete `/tmp/try/audit/2026/10/000000002-*.json` and run
   `audit verify`: it must say `NOT intact` and name event 3.
2. After this PR is merged, open the "Record agent versions" run in the **Actions** tab:
   the summary shows a table with four `unchanged` rows (the agents didn't change).
3. On your computer: `git fetch origin agent-releases:agent-releases`, then
   `$C audit verify`. Expect four notes about older records and `audit log intact`.

## Further reading

- [Topic 10](../topics/10-audit-logs.md) and its links.
- [ADR 0009](../../docs/decisions/0009-audit-log.md).
