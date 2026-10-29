# 10 — Audit logs: hash chains, all-or-nothing saves and safe exports

**You'll learn:** what an audit log is for, how a hash chain makes tampering visible,
why records and events are saved in one go, how a script can fail *after* finishing
its work, and two output traps (spreadsheet formulas and Markdown tables). Example
throughout: journal 0004, ADR 0009. Read [topic 09](09-version-records.md) first.

## 1. Record vs event

| | Version record | Audit event |
|---|---|---|
| Answers | *What is* version 3 of this agent? | *What happened*, when, and who did it? |
| Example | model, prompts, file fingerprints | "created v3", "refused: possible secret" |
| Folder | `records/<agent>/000003.json` | `audit/2026/10/000000042-20261030T091500Z.json` |

An auditor asks both questions. Refusals matter as much as successes: "someone tried to
release an agent with a key in its config, and the tool stopped it" is exactly what
compliance staff want to see.

## 2. The hash chain

Each event gets three extra fields:

```
event 1   sequence: 1   previous: none          event_id: sha256:aaa…
event 2   sequence: 2   previous: sha256:aaa…   event_id: sha256:bbb…
event 3   sequence: 3   previous: sha256:bbb…   event_id: sha256:ccc…
```

`event_id` is the fingerprint of the whole event **including `previous`**. So:

- **Edit** event 2: its fingerprint changes, it no longer matches its own `event_id`.
- **Fix up** event 2's `event_id` too: event 3 still points to the *old* id, so the
  link breaks.
- **Delete** event 2: the sequence jumps from 1 to 3.

To hide a change you'd have to rewrite *every* event after it, and anyone holding an
older copy would notice. Blockchains and Git itself use this same idea. Run
`audit verify` to check the whole chain.

What it doesn't prove: *who* ran the tool. That needs digital signatures (Feature 9).

## 3. All or nothing

A run checks four agents and may create two records and four events. If the tool saved
them one by one and crashed halfway, you could end up with a record and no event, which
is a hole in the audit trail.

So everything from one run is written in **one Git commit**: the private-index method
from topic 09, just with several files. Git moves the branch to that commit in a single
step, so either all of it is saved or none of it. Databases call this a **transaction**
or an **atomic** write.

The store also refuses to save a record unless its `version.created` event is in the
same save.

## 4. Failing *after* the work is done

When an agent is refused, `record create` exits with code 1 so GitHub marks the run red.
But a shell script normally stops at the first failing command, and then the refusal
event would never be pushed. The Action does this instead:

```bash
result=0
consolidated-agent-release-deployment record create ... || result=$?   # remember, don't stop
git push ...                                                           # save the evidence
exit "$result"                                                         # now fail
```

`||` means "if the left side failed, run the right side". `$?` is the exit code of the
last command.

## 5. Exporting safely

**CSV injection.** A spreadsheet treats a cell starting with `=`, `+`, `-` or `@` as a
formula. A crafted text like `=HYPERLINK("http://bad.example")` in a log could turn into
a live link in Excel. The export puts an apostrophe in front (`'=HYPERLINK…`), which
spreadsheets show as plain text.

**Markdown tables** use `|` between columns, so a `|` inside a value would break the
table. It is written as `\|`.

## 6. The run summary

GitHub gives every step a file path in the environment variable `GITHUB_STEP_SUMMARY`.
Markdown written there appears on the run's page, so you can see a table of what was
created or refused without reading logs. Outside GitHub the variable doesn't exist and
the tool skips it.

## 7. Records from before the log

The four records made by PR #4's merge have no events, because the log didn't exist
yet. `audit verify` knows this: a record older than the first event is a **note**, not a
problem. A *newer* record without an event would be a problem.

## Try it yourself

1. Run `record create --store-dir /tmp/try sample_agents` twice, then `audit list`.
   How many events, and of which type?
2. Delete one event file in `/tmp/try/audit/` and run `audit verify`. What does it say?
3. Open one event in a text editor, change the actor, and run `audit verify` again. Which
   two problems appear, and why two?
4. Run `audit export -o /tmp/try.csv` and open the file in a spreadsheet.

## Further reading

- Hash chains, simply explained: <https://en.wikipedia.org/wiki/Hash_chain>
- CSV injection: <https://owasp.org/www-community/attacks/CSV_Injection>
- Job summaries in GitHub Actions: <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#adding-a-job-summary>
