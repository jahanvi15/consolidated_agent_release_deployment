"""Command-line entry point.

``record`` commands (Feature 1, the version record):

* ``record preview PATH...`` — show the record that *would* be made. Saves nothing.
  Use it on pull requests.
* ``record create PATH...`` — save a new version for each agent whose content changed.
  Use it after a merge to ``main``.
* ``record list AGENT`` / ``record show AGENT VERSION`` — read saved records.

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
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from consolidated_agent_release_deployment import __version__
from consolidated_agent_release_deployment.gitutil import GitError, git
from consolidated_agent_release_deployment.manifest import ManifestError
from consolidated_agent_release_deployment.secret_scan import Finding, scan_settings, scan_text
from consolidated_agent_release_deployment.source import detect_source
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
    _block_secrets(agent_dir, record)
    return record, latest


def _block_secrets(agent_dir: Path, record: VersionRecord) -> None:
    findings: list[Finding] = scan_text(record.to_json(), f"{record.agent} record")
    findings += scan_settings(record.content.config, "config")
    if record.content.model:
        findings += scan_settings(record.content.model.settings, "model.settings")
    if findings:
        lines = "\n".join(f"  - {f}" for f in findings)
        raise CliError(f"{agent_dir}: blocked, the record would contain a secret:\n{lines}")


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
    for agent_dir in discover_agents(args.paths):
        record, latest = build_record(agent_dir, store, env)
        short = record.fingerprint[7:19]
        if latest and latest.fingerprint == record.fingerprint:
            print(f"{record.agent}: unchanged, still version {latest.version} ({short})")
            continue
        if record.source.uncommitted_changes and not args.allow_uncommitted:
            raise CliError(
                f"{agent_dir}: has uncommitted changes, so commit {record.source.commit} "
                "would not match the record. Commit first (or pass --allow-uncommitted)."
            )
        store.append(record)
        print(f"{record.agent}: created version {record.version} ({short})")
    return 0


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
