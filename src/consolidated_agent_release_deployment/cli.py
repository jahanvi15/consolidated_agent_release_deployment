"""Command-line entry point.

``record`` commands (Feature 1, the version record):

* ``record preview PATH...`` — show the record that *would* be made. Saves nothing.
  Use it on pull requests.
* ``record create PATH...`` — save a new version for each agent whose content changed.
  Use it after a merge to ``main``.
* ``record list AGENT`` / ``record show AGENT VERSION`` — read saved records.

``audit`` commands (the audit log, ADR 0009):

* ``audit list`` — events, optionally for one agent or a date range.
* ``audit verify`` — check the hash chain, and that events and records match.
* ``audit export`` — events as CSV for a spreadsheet.

``record create`` logs one event per agent: created, unchanged or refused. It saves all
new records and events together, and exits 1 if any agent was refused.

``PATH`` is an agent folder (one with ``agent.toml``) or any folder above it; every
agent found below it is handled (several agents per repository are fine).

Exit codes: 0 = OK, 1 = a problem was found (invalid manifest, secret-looking value,
store error), 2 = the command was typed wrongly.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import ValidationError

from consolidated_agent_release_deployment import __version__
from consolidated_agent_release_deployment.audit import (
    AuditEvent,
    EventDraft,
    created_event,
    to_csv,
    to_markdown,
    verify,
)
from consolidated_agent_release_deployment.gitutil import GitError, git
from consolidated_agent_release_deployment.manifest import ManifestError
from consolidated_agent_release_deployment.secret_scan import Finding, scan_settings, scan_text
from consolidated_agent_release_deployment.source import detect_source, write_github_summary
from consolidated_agent_release_deployment.store import (
    DEFAULT_BRANCH,
    DirectoryStore,
    GitBranchStore,
    RecordStore,
    StoreError,
)
from consolidated_agent_release_deployment.version_record import (
    ContentError,
    VersionRecord,
    load_agent,
    new_record,
)

SKIP_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__"})


class CliError(Exception):
    """A problem to show the user as one clear message (exit code 1)."""


# ---------- finding agents ----------


def discover_agents(paths: Sequence[Path]) -> list[Path]:
    """Agent folders at or below each path, without duplicates, in a stable order."""
    found: set[Path] = set()
    for path in paths:
        if not path.is_dir():
            raise CliError(f"{path}: not a folder")
        if (path / "agent.toml").is_file():
            found.add(path.resolve())
            continue
        for manifest in path.rglob("agent.toml"):
            if not SKIP_DIRS & set(manifest.relative_to(path).parts):
                found.add(manifest.parent.resolve())
    if not found:
        raise CliError("no agent.toml found in: " + ", ".join(str(p) for p in paths))
    return sorted(found)


# ---------- building and checking ----------


def build_record(
    agent_dir: Path,
    store: RecordStore | None,
    env: Mapping[str, str],
    now: datetime | None = None,
) -> tuple[VersionRecord, VersionRecord | None]:
    """The record for this folder, and the latest saved one (None if there isn't one)."""
    manifest, content = load_agent(agent_dir)
    latest = store.latest(manifest.name) if store else None
    version = latest.version + 1 if latest else 1
    source, who = detect_source(agent_dir, env)
    record = new_record(
        manifest.name, content, version=version, created_by=who, source=source, now=now
    )
    findings = secret_findings(record)
    if findings:
        raise CliError(_blocked_message(agent_dir, findings))
    return record, latest


def secret_findings(record: VersionRecord) -> list[Finding]:
    findings = scan_text(record.to_json(), f"{record.agent} record")
    findings += scan_settings(record.content.config, "config")
    if record.content.model:
        findings += scan_settings(record.content.model.settings, "model.settings")
    return findings


def _blocked_message(agent_dir: Path, findings: Sequence[Finding]) -> str:
    lines = "\n".join(f"  - {f}" for f in findings)
    return f"{agent_dir}: blocked, the record would contain a secret:\n{lines}"


@dataclass(frozen=True)
class Outcome:
    """What ``create`` decided for one agent: the event, and a record if one is new."""

    draft: EventDraft
    record: VersionRecord | None
    message: str


def evaluate(
    agent_dir: Path,
    store: RecordStore,
    env: Mapping[str, str],
    now: datetime,
    allow_uncommitted: bool,
) -> Outcome:
    """Decide created / unchanged / refused for one agent. Never raises for those cases."""
    source, who = detect_source(agent_dir, env)
    base = {"occurred_at": now, "actor": who, "via": source.platform, "source": source}

    try:
        manifest, content = load_agent(agent_dir)
    except ManifestError as exc:
        details = [str(i) for i in exc.issues]
        draft = EventDraft(type="version.refused", reason="invalid_agent", details=details, **base)
        return Outcome(draft, None, f"{agent_dir}: refused, invalid agent\n{exc}")
    except ContentError as exc:
        draft = EventDraft(
            type="version.refused", reason="invalid_agent", details=[str(exc)], **base
        )
        return Outcome(draft, None, f"{agent_dir}: refused, {exc}")

    latest = store.latest(manifest.name)
    version = latest.version + 1 if latest else 1
    record = new_record(
        manifest.name, content, version=version, created_by=who, source=source, now=now
    )
    agent = {"agent": record.agent, "fingerprint": record.fingerprint}
    short = record.fingerprint[7:19]

    findings = secret_findings(record)
    if findings:
        draft = EventDraft(
            type="version.refused",
            reason="possible_secret",
            details=[str(f) for f in findings],
            **agent,
            **base,
        )
        return Outcome(draft, None, _blocked_message(agent_dir, findings))

    if latest and latest.fingerprint == record.fingerprint:
        draft = EventDraft(type="version.unchanged", version=latest.version, **agent, **base)
        return Outcome(
            draft, None, f"{record.agent}: unchanged, still version {latest.version} ({short})"
        )

    if source.uncommitted_changes and not allow_uncommitted:
        draft = EventDraft(
            type="version.refused",
            reason="uncommitted_changes",
            details=[f"folder differs from commit {source.commit}"],
            **agent,
            **base,
        )
        return Outcome(
            draft,
            None,
            f"{agent_dir}: has uncommitted changes, so commit {source.commit} "
            "would not match the record. Commit first (or pass --allow-uncommitted).",
        )

    return Outcome(
        created_event(record),
        record,
        f"{record.agent}: created version {record.version} ({short})",
    )


# ---------- commands ----------


def cmd_preview(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    store = open_store_if_any(args)
    for agent_dir in discover_agents(args.paths):
        record, latest = build_record(agent_dir, store, env)
        if latest and latest.fingerprint == record.fingerprint:
            print(f"# {record.agent}: unchanged since version {latest.version}")
        print(record.to_json(), end="")
    return 0


def cmd_create(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    store = open_store(args)
    now = datetime.now(UTC).replace(microsecond=0)
    outcomes = [
        evaluate(agent_dir, store, env, now, args.allow_uncommitted)
        for agent_dir in discover_agents(args.paths)
    ]
    # Everything is saved together; if this fails, nothing is saved (ADR 0009).
    events = store.save(
        [o.record for o in outcomes if o.record is not None], [o.draft for o in outcomes]
    )
    refused = 0
    for outcome in outcomes:
        if outcome.draft.type == "version.refused":
            refused += 1
            print(f"error: {outcome.message}", file=sys.stderr)
        else:
            print(outcome.message)
    print(f"audit: logged events {events[0].sequence}-{events[-1].sequence}")
    write_github_summary(env, to_markdown(events))
    return 1 if refused else 0


def cmd_list(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    store = open_store(args)
    versions = store.versions(args.agent)
    if not versions:
        raise CliError(f"no versions recorded for {args.agent!r}")
    for version in versions:
        r = store.read(args.agent, version)
        print(
            f"{r.version:>4}  {r.created_at:%Y-%m-%d %H:%M}Z  {r.fingerprint[7:19]}  {r.created_by}"
        )
    return 0


def cmd_show(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    store = open_store(args)
    print(store.read(args.agent, args.version).to_json(), end="")
    return 0


def _filtered(args: argparse.Namespace, store: RecordStore) -> list[AuditEvent]:
    events = store.events()
    if args.agent:
        events = [e for e in events if e.agent == args.agent]
    if args.since:
        events = [e for e in events if e.occurred_at.date() >= args.since]
    if args.until:
        events = [e for e in events if e.occurred_at.date() <= args.until]
    return events


def cmd_audit_list(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    events = _filtered(args, open_store(args))
    if not events:
        raise CliError("no audit events match")
    for e in events:
        what = e.type.removeprefix("version.")
        if e.reason:
            what += f" ({e.reason})"
        agent = e.agent or e.source.agent_path
        version = f"v{e.version}" if e.version else "-"
        when = f"{e.occurred_at:%Y-%m-%d %H:%M}Z"
        print(f"{e.sequence:>5}  {when}  {agent}  {version}  {what}  {e.actor}")
    return 0


def cmd_audit_verify(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    events, records = open_store(args).load_all()
    result = verify(events, records)
    for note in result.notes:
        print(f"note: {note}")
    for problem in result.problems:
        print(f"problem: {problem}", file=sys.stderr)
    if not result.ok:
        print(f"audit log NOT intact: {len(result.problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"audit log intact: {result.events} events, {len(records)} records checked")
    return 0


def cmd_audit_export(args: argparse.Namespace, env: Mapping[str, str]) -> int:
    text = to_csv(_filtered(args, open_store(args)))
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8", newline="")
        print(f"wrote {args.output}")
    return 0


def open_store(args: argparse.Namespace) -> RecordStore:
    store = open_store_if_any(args)
    if store is None:
        raise CliError("not inside a Git repository; use --store-dir FOLDER")
    return store


def open_store_if_any(args: argparse.Namespace) -> RecordStore | None:
    """The store chosen on the command line, or None outside Git (preview still works)."""
    if args.store_dir is not None:
        return DirectoryStore(args.store_dir)
    try:
        top = Path(git(["rev-parse", "--show-toplevel"], Path.cwd()))
    except GitError:
        return None
    return GitBranchStore(top, args.branch)


# ---------- argument parsing ----------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="consolidated-agent-release-deployment",
        description="Release management for AI agents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command")

    record = commands.add_parser("record", help="version records (create, preview, read)")
    actions = record.add_subparsers(dest="action", required=True)

    where = argparse.ArgumentParser(add_help=False)
    where.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Git branch for records (default {DEFAULT_BRANCH})",
    )
    where.add_argument("--store-dir", type=Path, help="keep records in this folder instead of Git")

    for name, func, text in (
        ("preview", cmd_preview, "show the record that would be created; save nothing"),
        ("create", cmd_create, "save a new version for each changed agent"),
    ):
        sub = actions.add_parser(name, parents=[where], help=text)
        sub.add_argument("paths", nargs="+", type=Path, help="agent folder(s) or a folder above")
        sub.set_defaults(func=func)
        if name == "create":
            sub.add_argument(
                "--allow-uncommitted",
                action="store_true",
                help="save even if the agent folder has uncommitted changes",
            )

    sub = actions.add_parser("list", parents=[where], help="list saved versions of an agent")
    sub.add_argument("agent")
    sub.set_defaults(func=cmd_list)

    sub = actions.add_parser("show", parents=[where], help="print one saved record")
    sub.add_argument("agent")
    sub.add_argument("version", type=int)
    sub.set_defaults(func=cmd_show)

    audit = commands.add_parser("audit", help="the audit log (list, verify, export)")
    audit_actions = audit.add_subparsers(dest="action", required=True)
    filters = argparse.ArgumentParser(add_help=False)
    filters.add_argument("--agent", help="only events for this agent")
    filters.add_argument("--since", type=date.fromisoformat, help="from this day, YYYY-MM-DD")
    filters.add_argument("--until", type=date.fromisoformat, help="up to this day, YYYY-MM-DD")

    sub = audit_actions.add_parser("list", parents=[where, filters], help="show events")
    sub.set_defaults(func=cmd_audit_list)
    sub = audit_actions.add_parser(
        "verify", parents=[where], help="check the chain and that events match records"
    )
    sub.set_defaults(func=cmd_audit_verify)
    sub = audit_actions.add_parser("export", parents=[where, filters], help="events as CSV")
    sub.add_argument("--format", choices=["csv"], default="csv", help="file format (csv)")
    sub.add_argument("--output", "-o", type=Path, help="write to this file instead of the screen")
    sub.set_defaults(func=cmd_audit_export)
    return parser


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        result: int = args.func(args, os.environ if env is None else env)
    except (CliError, ManifestError, ContentError, StoreError, GitError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
