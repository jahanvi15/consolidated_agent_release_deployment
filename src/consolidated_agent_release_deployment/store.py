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

Layout in both: ``records/<agent>/<version, 6 digits>.json``.
"""

from __future__ import annotations

import re
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from consolidated_agent_release_deployment.gitutil import GitError, git, try_git
from consolidated_agent_release_deployment.version_record import VersionRecord

DEFAULT_BRANCH = "agent-releases"
RECORDS_DIR = "records"
_FILE = re.compile(r"(\d{6})\.json")
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
    def _create(self, path: str, text: str, message: str) -> None:
        """Write a new file. Must fail if the file already exists."""

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

    def append(self, record: VersionRecord) -> None:
        expected = self.next_version(record.agent)
        if record.version != expected:
            raise StoreError(
                f"{record.agent}: can only add version {expected}, not {record.version} "
                "(records are never overwritten)"
            )
        message = f"record {record.agent} v{record.version} ({record.fingerprint[7:19]})"
        self._create(record_path(record.agent, record.version), record.to_json(), message)


class DirectoryStore(RecordStore):
    def __init__(self, root: Path) -> None:
        self.root = root

    def _list(self, folder: str) -> list[str]:
        path = self.root / folder
        return [p.name for p in path.iterdir()] if path.is_dir() else []

    def _read(self, path: str) -> str:
        return (self.root / path).read_text(encoding="utf-8")

    def _create(self, path: str, text: str, message: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Mode "x" = create only; it fails if the file is already there.
            with target.open("x", encoding="utf-8", newline="\n") as f:
                f.write(text)
        except FileExistsError:
            raise StoreError(f"{path} already exists (records are never overwritten)") from None


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

    def _create(self, path: str, text: str, message: str) -> None:
        parent = self._head()
        if parent is not None and self._exists(parent, path):
            raise StoreError(f"{path} already exists (records are never overwritten)")
        with tempfile.TemporaryDirectory() as tmp:
            # A private "index" (Git's staging area), so the user's own one is untouched.
            env = {**_BOT, "GIT_INDEX_FILE": str(Path(tmp) / "index")}
            if parent is None:
                git(["read-tree", "--empty"], self.repo, env=env)
            else:
                git(["read-tree", parent], self.repo, env=env)
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
