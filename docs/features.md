# Features in detail

The 13 features of the plan, in build order. Overview and roadmap:
[`project-context.md`](project-context.md). Order and stage decisions: ADR 0009.

**How to read this.** The plan defines each feature's *name, purpose, stage and
dependencies* — those are decided. Everything else here (examples, scope, inputs and
outputs) is **proposed scope**: a reasonable first interpretation to build from, which the
owner confirms or changes before or during that feature's work. Anything genuinely
undecided is listed under *Open questions* — ask, don't guess, and record answers as ADRs.

Each feature has: **Problem** · **What it does** · **Example** · **Needs / used by** ·
**First version** (what to build first) · **Open questions**.

---

## Stage 1 — the foundation (first version)

### 1. Version record

**Problem.** An AI agent changes in many small ways — its instructions, tools, limits,
code, model settings. Without a record, nobody can say which exact agent is running, what
was approved, or what to go back to. Every other feature needs a fixed thing to point at.

**What it does.** Captures one exact state of an agent as an **immutable** (never edited)
record with a stable ID. Proposed contents:
- the validated manifest (`agent.toml`: name, declared tools, limits, entrypoint);
- a **fingerprint** of the agent's files — a hash: same content → same ID, any change → new ID;
- where it came from (repository, commit, branch, pull request);
- who recorded it and when.

Records are append-only: a new change makes a new version; old ones are never changed.

**Example.**
```text
support_bot  version 3f9a2c1e   recorded 2026-11-02 by @jahanvi15
  from commit 8d41b0f (PR #12)   tools: search, read_file   max_steps: 10
```

**Needs / used by.** Needs nothing. Used by **every** other feature.

**First version.** F1-1 manifest format (PR #2) → F1-2 decide contents and storage →
F1-3 fingerprint → F1-4 `record` command → F1-5 list/show history.

**Open questions.** What exactly a version contains (manifest only, or also code,
prompts, model name and settings)? Where records are stored (files in the agent's repo,
a separate store, a database)? → **F1-2, blocks Stage 1.**

### 2. "What changed" summary

**Problem.** Reviewers can't judge a new agent version from a raw code diff — they need to
know what matters: "it can now send email", "its step limit tripled".

**What it does.** Compares two version records and produces:
- a **structured** list of differences (for rules and later features): tools added or
  removed, limits changed, entrypoint changed, files changed;
- a **readable** summary (plain language / Markdown), suitable as a pull-request comment,
  with the most risk-relevant changes first.

**Example.**
```text
support_bot: 3f9a2c1e → 77b0d4aa
  ⚠ Tool added: send_email
  • max_steps: 10 → 30
  • 2 files changed (agent.py, prompts/system.txt)
```

**Needs / used by.** Needs 1. Used by 3 (change-aware rules), 8 (judging risk for
sign-off), 9 (audit evidence).

**First version.** F2-1 structured comparison → F2-2 readable summary.

**Open questions.** Should changes to instructions/prompts be shown as text diffs, or only
flagged? Which changes count as "high risk"? (Shared with 8.)

### 3. Automatic rule checks

**Problem.** Companies have rules for what agents may do. Checking them by hand on every
change is slow and gets skipped.

**What it does.** Evaluates a version — and, for some rules, its "what changed" summary —
against a set of rules. Each rule returns **pass**, **fail** (with a reason) or **error**
(couldn't run). In a pipeline, any fail stops the release (non-zero exit code), and the
results appear on the pull request. Runs in GitHub Actions first.

**Example rules (proposed; real list = F3-2).**
- No secret-looking strings (API keys, passwords) in agent files.
- `max_steps` within the organization's limit.
- Only tools from an approved list.
- *Change-aware:* adding a new tool is flagged for attention.

**Example output.**
```text
✔ no-secrets-in-files        pass
✘ tools-approved             fail  send_email is not on the approved list
✔ step-limit-within-policy   pass
Result: FAIL (1 of 3 rules failed) — release blocked
```

**Needs / used by.** Needs 1 (and 2 for change-aware rules). Used by 5 (checks before
promotion), 8, 9.

**First version.** F3-1 rule engine and result format → F3-2 decide first rule scope →
F3-3 first rules → F3-4 first change-aware rule → F3-5 GitHub Action.

**Open questions.** Which rules first — security basics, personal-data handling, a
regulation (e.g. EU AI Act), company policies? How are rules configured by users (a file
in their repo)? → **F3-2.**

### Basic audit record (start of feature 9)

**What it does.** From Stage 1, every command appends an entry to an **append-only log**:
who, what (record / compare / check), which agent and version, when, result. Never edited
or deleted. Feature 9 later turns this into full audit evidence. (Decided in ADR 0009.)

**First version.** A-1.

---

## Stage 2 — low-cost additions

### 12. Dependency map

**Problem.** When a business system changes or goes down, nobody knows which agents are affected.

**What it does.** Builds a map from version records: which agents use which tools, and
which tools reach which business systems. Answers "who uses X?" and "what does agent Y
depend on?".

**Example.** `crm.update_contact` ← used by `support_bot` (live), `sales_helper` (testing).

**Needs / used by.** Needs only 1 — cheap. Used by 10 (who is affected by an outside change).

**Open questions.** How tools are linked to business systems (declared in the manifest?
a separate mapping?).

### 4. Quality test before release

**Problem.** An agent can pass every rule on paper and still misbehave when it runs.

**What it does.** Runs the agent against **test scenarios** before release, with fake
tools, and checks its behaviour: uses only declared tools, leaks no secrets in its
answers, stays within its step budget, and gives acceptable results. The repository's
sample agents (`tool_overreach`, `secret_leaker`, `runaway_loop`) already demonstrate
these failures. A basic version works with simple fake tools; it becomes realistic once
fake business systems (13) exist.

**Example.** `runaway_loop: FAIL — 20 steps taken, budget 5`.

**Needs / used by.** Needs 1 (better with 13). Used by 10 (re-test when something
changes) and 6 (test before widening a release).

**Open questions.** How scenarios are written and what counts as an acceptable result;
whether tests may ever call a real AI model (cost, randomness) — default tests don't (ADR 0005).

---

## Stage 3 — test infrastructure

### 13. Ready-made fake business systems

**Problem.** Testing against real business systems is risky (real data, real effects)
and often impossible.

**What it does.** Provides stand-ins that behave like real systems — same kinds of
requests and responses, predictable test data — and can simulate failures and changes
(slow responses, errors, a changed field). Used by quality tests (4), connection checks
(5), undo testing (7), and our own tests.

**Open questions.** Which systems first (depends on first users' agents — open question 3
in the context doc).

---

## Stage 4 — moving between environments

### 5. Moving safely from testing to live use

**Problem.** "It worked in testing" means little if live uses different connections, or
if what reaches live isn't exactly what was tested.

**What it does.**
- Promotes the **same version** (same ID) from one environment to the next — never a rebuild.
- **Per-environment connection setup:** each environment has its own settings (which
  system addresses, which credentials to use). Settings refer to secrets stored safely;
  secrets themselves never go into version records.
- **Connection checks before release:** before promoting, verifies the agent can reach the
  systems it needs in the target environment, with the right permissions.

**Example.** `promote support_bot 77b0d4aa testing → live`: connection checks ✔, rules ✔ → promoted.

**Needs / used by.** Needs 1; connection checks need 13 to be tested properly. Used by
8 (when to ask for approval), 6, 7.

---

## Stage 5 — people and evidence

### 8. Sign-off from the right people

**Problem.** Not every change needs the same approval — a typo fix isn't a new ability to
send email to customers.

**What it does.** Uses the "what changed" summary to judge **risk** and the environment
move to know **when** to ask; requests approval from the right people; records who
approved what; blocks promotion until approved.

**Example.** Tool `send_email` added and target is `live` → security owner must approve.

**Needs.** 2 and 5.

**Open questions.** Who the approvers are and how risk levels map to them.

### 9. Proof for audits

**Problem.** Auditors and regulators ask: what was running, when, who changed it, how was
it checked, who approved it. Answering by hand is slow and unreliable.

**What it does.** Gathers everything the other features produce — version records,
change summaries, rule results, quality tests, approvals, promotions — into evidence that
can be searched and exported. Builds on the audit log started in Stage 1.

**Needs.** Everything before it, so it's most complete here.

**Open questions.** Export format; how long records are kept; which regulations' evidence
needs to be met.

---

## Stage 6 — watching for change

### 10. Watching for outside changes

**Problem.** An agent can break without anyone changing it — when a business system, a
tool or a model provider changes.

**What it does.** Watches for outside changes, including **impact alerts** for business
system changes: uses the dependency map (12) to find affected agents, re-runs their
quality tests (4), and alerts their owners with what changed and what's affected.

**Needs.** 4 and 12.

---

## Stage 7 — live-use safety

### 6. Releasing to a few users first

**Problem.** Some problems only appear with real users.

**What it does.** Releases a new version to a small share of users first, watches how it
behaves, then widens the release step by step — or stops it.

**Needs.** 5 and 4.

### 7. Undoing a bad release, including its mistakes

**Problem.** Switching back to the old version isn't enough if the bad version already
*did* things — sent emails, changed records.

**What it does.** Returns to the previous good version **and** undoes or compensates the
bad version's actions in business systems where possible, using the record of what it
did. The hardest feature, so it's last.

**Needs.** 6, 5, and 13 for safe testing.

---

## Ongoing

### 11. One view across all platforms

**What it does.** A single view of agents, versions, checks and releases across every
supported platform. Not one step: each platform is added over time, starting with
whichever one the first users run.

**Open question — what "platform" means.** It's ambiguous: it could mean **pipeline
platforms** (GitHub Actions, Azure DevOps — where releases run) or **agent platforms**
(where agents are built or hosted), or both. Confirm with the owner before building (F11-1).
