"""Where version records are kept, behind one small interface.

Records are **append-only**: once version 3 is saved it can never be overwritten or
deleted through this code. A fix is always a new version (ADR 0008, decision 7).

Two stores share the same rules:

* ``GitBranchStore`` — the real one. Saves records as JSON files on a separate Git
  branch (default ``agent-releases``), so they never touch ``main`` and every save is a
  commit with full history. It writes with Git's low-level "plumbing" commands, so your
  current checkout and files are never touched.
* ``DirectoryStore`` — a plain folder. Handy for trying things locally and for tests.

A database store can be added later by writing a third class with the same methods.

Layout in both: ``records/<agent>/<version, 6 digits>.json`` and the audit log under
``audit/`` (see ``audit.py``). ``save`` writes new records **and** their audit events
together: in the Git store that is one commit, so a record can never exist without its
event (ADR 0009).
"""

from __future__ import annotations

import re
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import ValidationError

from consolidated_agent_release_deployment.audit import (
    AUDIT_DIR,
    AuditEvent,
    EventDraft,
    event_path,
    link,
)
from consolidated_agent_release_deployment.gitutil import GitError, git, try_git
from consolidated_agent_release_deployment.version_record import VersionRecord

DEFAULT_BRANCH = "agent-releases"
RECORDS_DIR = "records"
_FILE = re.compile(r"(\d{6})\.json")
_EVENT_FILE = re.compile(r"(\d{9})-\d{8}T\d{6}Z\.json")
# The tool, not a person, makes commits on the records branch.
_BOT = {
    "GIT_AUTHOR_NAME": "agent-release-records",
    "GIT_AUTHOR_EMAIL": "agent-release-records@localhost",
    "GIT_COMMITTER_NAME": "agent-release-records",
    "GIT_COMMITTER_EMAIL": "agent-release-records@localhost",
}


class StoreError(RuntimeError):
    """A record can't be saved or read (e.g. version already exists)."""


def record_path(agent: str, version: int) -> str:
    return f"{RECORDS_DIR}/{agent}/{version:06d}.json"


class RecordStore(ABC):
    """Shared rules. Subclasses only say how to list, read and create files."""

    @abstractmethod
    def _list(self, folder: str) -> list[str]:
        """File names directly inside ``folder`` (empty if it doesn't exist)."""

    @abstractmethod
    def _read(self, path: str) -> str: ...

    @abstractmethod
    def _list_all(self, folder: str) -> list[str]:
        """Every file path below ``folder``, at any depth (empty if it doesn't exist)."""

    @abstractmethod
    def _create_all(self, files: Mapping[str, str], message: str) -> None:
        """Write new files all together. Must fail if any of them already exists."""

    def versions(self, agent: str) -> list[int]:
        names = self._list(f"{RECORDS_DIR}/{agent}")
        return sorted(int(m[1]) for n in names if (m := _FILE.fullmatch(n)))

    def read(self, agent: str, version: int) -> VersionRecord:
        try:
            text = self._read(record_path(agent, version))
        except (FileNotFoundError, GitError):
            raise StoreError(f"{agent} has no version {version}") from None
        record = VersionRecord.from_json(text)  # also re-checks the fingerprint
        if record.agent != agent or record.version != version:
            raise StoreError(f"{record_path(agent, version)} holds a different record")
        return record

    def latest(self, agent: str) -> VersionRecord | None:
        found = self.versions(agent)
        return self.read(agent, found[-1]) if found else None

    def next_version(self, agent: str) -> int:
        found = self.versions(agent)
        return found[-1] + 1 if found else 1

    # ---------- audit events ----------

    def event_paths(self) -> list[str]:
        """Event file paths in sequence order."""
        found = [
            (int(m[1]), p)
            for p in self._list_all(AUDIT_DIR)
            if (m := _EVENT_FILE.fullmatch(p.rsplit("/", 1)[-1]))
        ]
        return [p for _, p in sorted(found)]

    def read_event(self, path: str) -> AuditEvent:
        return AuditEvent.from_json(self._read(path))  # also re-checks event_id

    def events(self) -> list[AuditEvent]:
        return [self.read_event(p) for p in self.event_paths()]

    def last_event(self) -> AuditEvent | None:
        paths = self.event_paths()
        return self.read_event(paths[-1]) if paths else None

    def record_paths(self) -> list[str]:
        return sorted(p for p in self._list_all(RECORDS_DIR) if p.endswith(".json"))

    def load_all(
        self,
    ) -> tuple[list[tuple[str, AuditEvent | str]], list[tuple[str, VersionRecord | str]]]:
        """Every event and record, or the reason a file couldn't be read (for verify)."""
        events: list[tuple[str, AuditEvent | str]] = []
        for path in self.event_paths():
            try:
                events.append((path, self.read_event(path)))
            except ValidationError as exc:
                events.append((path, _first_error(exc)))
        records: list[tuple[str, VersionRecord | str]] = []
        for path in self.record_paths():
            try:
                records.append((path, VersionRecord.from_json(self._read(path))))
            except ValidationError as exc:
                records.append((path, _first_error(exc)))
        return events, records

    # ---------- saving ----------

    def save(
        self, records: Sequence[VersionRecord], drafts: Sequence[EventDraft]
    ) -> list[AuditEvent]:
        """Save new records and audit events together, and return the linked events.

        Every record must come with its ``version.created`` event, and versions must be
        exactly one more than the latest saved (records are never overwritten).
        """
        created = {(d.agent, d.version) for d in drafts if d.type == "version.created"}
        files: dict[str, str] = {}
        for record in records:
            expected = self.next_version(record.agent) + sum(
                1 for r in records if r.agent == record.agent and r.version < record.version
            )
            if record.version != expected:
                raise StoreError(
                    f"{record.agent}: can only add version {expected}, not {record.version} "
                    "(records are never overwritten)"
                )
            if (record.agent, record.version) not in created:
                raise StoreError(f"{record.agent} v{record.version}: no audit event to go with it")
            files[record_path(record.agent, record.version)] = record.to_json()
        events = link(drafts, self.last_event())
        for event in events:
            files[event_path(event)] = event.to_json()
        if files:
            self._create_all(files, _commit_message(records, events))
        return events


class DirectoryStore(RecordStore):
    def __init__(self, root: Path) -> None:
        self.root = root

    def _list(self, folder: str) -> list[str]:
        path = self.root / folder
        return [p.name for p in path.iterdir()] if path.is_dir() else []

    def _read(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")

    def _list_all(self, folder: str) -> list[str]:
        base = self.root / folder
        if not base.is_dir():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file())

    def _create_all(self, files: Mapping[str, str], message: str) -> None:
        # A plain folder can't save several files at once, so check them all first.
        for path in files:
            if (self.root / path).exists():
                raise StoreError(f"{path} already exists (records are never overwritten)")
        for path, text in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            # Mode "x" = create only; it fails if the file is already there.
            with target.open("x", encoding="utf-8", newline="\n") as f:
                f.write(text)


class GitBranchStore(RecordStore):
    """Records as commits on a separate branch of the repository at ``repo``."""

    def __init__(self, repo: Path, branch: str = DEFAULT_BRANCH) -> None:
        self.repo = repo
        self.branch = branch
        git(["check-ref-format", "--branch", branch], repo)  # rejects unsafe names
        self.ref = f"refs/heads/{branch}"

    def _head(self) -> str | None:
        return try_git(["rev-parse", "--verify", "--quiet", f"{self.ref}^{{commit}}"], self.repo)

    def _list(self, folder: str) -> list[str]:
        head = self._head()
        if head is None or not self._exists(head, folder):
            return []
        out = git(["ls-tree", "--name-only", f"{head}:{folder}"], self.repo)
        return [line for line in out.splitlines() if line]

    def _exists(self, head: str, path: str) -> bool:
        return try_git(["cat-file", "-e", f"{head}:{path}"], self.repo) is not None

    def _read(self, path: str) -> str:
        head = self._head()
        if head is None:
            raise FileNotFoundError(path)
        return git(["show", f"{head}:{path}"], self.repo) + "\n"

    def _list_all(self, folder: str) -> list[str]:
        head = self._head()
        if head is None:
            return []
        out = git(["ls-tree", "-r", "--name-only", head, "--", f"{folder}/"], self.repo)
        return [line for line in out.splitlines() if line]

    def _create_all(self, files: Mapping[str, str], message: str) -> None:
        parent = self._head()
        for path in files:
            if parent is not None and self._exists(parent, path):
                raise StoreError(f"{path} already exists (records are never overwritten)")
        with tempfile.TemporaryDirectory() as tmp:
            # A private "index" (Git's staging area), so the user's own one is untouched.
            env = {**_BOT, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
            if parent is None:
                git(["read-tree", "--empty"], self.repo, env=env)
            else:
                git(["read-tree", parent], self.repo, env=env)
            for path, text in files.items():
                blob = git(["hash-object", "-w", "--stdin"], self.repo, input_text=text, env=env)
                git(
                    ["update-index", "--add", "--cacheinfo", f"100644,{blob},{path}"],
                    self.repo,
                    env=env,
                )
            tree = git(["write-tree"], self.repo, env=env)
            parents = ["-p", parent] if parent else []
            commit = git(["commit-tree", tree, *parents, "-m", message], self.repo, env=env)
        # Move the branch only if nobody else moved it meanwhile ("compare and swap").
        old = parent or ""  # empty = "the branch must not exist yet"
        try:
            git(["update-ref", self.ref, commit, old], self.repo)
        except GitError:
            raise StoreError(f"{self.branch} changed while saving; run the command again") from None


def _commit_message(records: Sequence[VersionRecord], events: Sequence[AuditEvent]) -> str:
    span = f"events {events[0].sequence}-{events[-1].sequence}" if events else "no events"
    if not records:
        return f"audit: {span}"
    created = ", ".join(f"{r.agent} v{r.version}" for r in records)
    return f"record: {created} ({span})"


def _first_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    where = ".".join(str(p) for p in error["loc"])
    return f"{where + ': ' if where else ''}{error['msg']}"
