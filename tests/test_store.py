"""Tests for record storage: append-only rules, the folder store and the Git branch store."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from consolidated_agent_release_deployment.audit import created_event
from consolidated_agent_release_deployment.gitutil import GitError, git
from consolidated_agent_release_deployment.store import (
    DirectoryStore,
    GitBranchStore,
    RecordStore,
    StoreError,
    record_path,
)
from consolidated_agent_release_deployment.version_record import (
    Source,
    VersionRecord,
    load_agent,
    new_record,
)

NOW = datetime(2026, 10, 30, 9, 0, tzinfo=UTC)


def append(store: RecordStore, record: VersionRecord) -> None:
    """Save one record with its audit event, the only way records can be saved."""
    store.save([record], [created_event(record)])


def record_for(repo: Path, version: int, agent: str = "helpful_summarizer") -> VersionRecord:
    manifest, content = load_agent(repo / "agents" / agent)
    source = Source(platform="local", agent_path=f"agents/{agent}")
    return new_record(
        manifest.name, content, version=version, created_by="tester", source=source, now=NOW
    )


@pytest.fixture(params=["directory", "git-branch"])
def store(request: pytest.FixtureRequest, repo: Path, tmp_path: Path) -> RecordStore:
    if request.param == "directory":
        return DirectoryStore(tmp_path / "records-folder")
    return GitBranchStore(repo)


# ---------- rules every store follows ----------


def test_empty_store(store: RecordStore) -> None:
    assert store.versions("helpful_summarizer") == []
    assert store.latest("helpful_summarizer") is None
    assert store.next_version("helpful_summarizer") == 1


def test_append_then_read_back(store: RecordStore, repo: Path) -> None:
    first, second = record_for(repo, 1), record_for(repo, 2)
    append(store, first)
    append(store, second)
    assert store.versions("helpful_summarizer") == [1, 2]
    assert store.read("helpful_summarizer", 1) == first
    assert store.latest("helpful_summarizer") == second


def test_agents_are_kept_apart(store: RecordStore, repo: Path) -> None:
    append(store, record_for(repo, 1))
    append(store, record_for(repo, 1, agent="secret_leaker"))
    assert store.versions("helpful_summarizer") == [1]
    assert store.versions("secret_leaker") == [1]


def test_cannot_overwrite_an_existing_version(store: RecordStore, repo: Path) -> None:
    append(store, record_for(repo, 1))
    with pytest.raises(StoreError, match="can only add version 2, not 1"):
        append(store, record_for(repo, 1))


def test_cannot_skip_a_version(store: RecordStore, repo: Path) -> None:
    with pytest.raises(StoreError, match="can only add version 1, not 3"):
        append(store, record_for(repo, 3))


def test_reading_a_missing_version(store: RecordStore) -> None:
    with pytest.raises(StoreError, match="has no version 4"):
        store.read("helpful_summarizer", 4)


def test_record_path_layout() -> None:
    assert record_path("my-agent", 12) == "records/my-agent/000012.json"


# ---------- folder store ----------


def test_directory_store_refuses_existing_file(tmp_path: Path, repo: Path) -> None:
    store = DirectoryStore(tmp_path)
    record = record_for(repo, 1)
    (tmp_path / "records" / "helpful_summarizer").mkdir(parents=True)
    (tmp_path / "records" / "helpful_summarizer" / "notes.txt").write_text("ignored")
    append(store, record)
    with pytest.raises(StoreError, match="already exists"):
        store._create_all({record_path(record.agent, 1): record.to_json()}, "again")


def test_misplaced_record_is_detected(tmp_path: Path, repo: Path) -> None:
    store = DirectoryStore(tmp_path)
    append(store, record_for(repo, 1))
    folder = tmp_path / "records" / "helpful_summarizer"
    (folder / "000001.json").rename(folder / "000002.json")
    with pytest.raises(StoreError, match="holds a different record"):
        store.read("helpful_summarizer", 2)


# ---------- Git branch store ----------


def test_git_store_never_touches_the_current_branch_or_files(repo: Path) -> None:
    head_before = git(["rev-parse", "HEAD"], repo)
    (repo / "agents" / "notes.txt").write_text("work in progress\n")
    append(GitBranchStore(repo), record_for(repo, 1))
    assert git(["rev-parse", "HEAD"], repo) == head_before
    assert git(["branch", "--show-current"], repo) == "main"
    assert git(["status", "--porcelain"], repo) == "?? agents/notes.txt"
    assert not (repo / "records").exists()


def test_git_store_makes_one_commit_per_record(repo: Path) -> None:
    store = GitBranchStore(repo)
    append(store, record_for(repo, 1))
    append(store, record_for(repo, 2))
    log = git(["log", "--format=%an|%s", "agent-releases"], repo).splitlines()
    assert log == [
        "agent-release-records|record: helpful_summarizer v2 (events 2-2)",
        "agent-release-records|record: helpful_summarizer v1 (events 1-1)",
    ]
    files = git(["ls-tree", "-r", "--name-only", "agent-releases"], repo).splitlines()
    assert files == [
        "audit/2026/10/000000001-20261030T090000Z.json",
        "audit/2026/10/000000002-20261030T090000Z.json",
        "records/helpful_summarizer/000001.json",
        "records/helpful_summarizer/000002.json",
    ]


def test_git_store_custom_branch_name(repo: Path) -> None:
    append(GitBranchStore(repo, "release-records"), record_for(repo, 1))
    assert git(["branch", "--list", "release-records"], repo).strip() == "release-records"


def test_git_store_rejects_unsafe_branch_names(repo: Path) -> None:
    with pytest.raises(GitError):
        GitBranchStore(repo, "bad..name")


def test_git_store_detects_a_change_made_meanwhile(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = GitBranchStore(repo)
    append(store, record_for(repo, 1))
    stale = store._head()
    other = GitBranchStore(repo)
    append(other, record_for(repo, 2))
    # Pretend this store still sees the old branch tip, as if another run saved in between.
    monkeypatch.setattr(store, "_head", lambda: stale)
    with pytest.raises(StoreError, match="changed while saving"):
        store._create_all({record_path("helpful_summarizer", 3): "{}"}, "late")


def test_git_store_refuses_existing_path(repo: Path) -> None:
    store = GitBranchStore(repo)
    append(store, record_for(repo, 1))
    with pytest.raises(StoreError, match="already exists"):
        store._create_all({record_path("helpful_summarizer", 1): "{}"}, "again")
