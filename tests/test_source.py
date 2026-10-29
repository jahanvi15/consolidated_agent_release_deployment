"""Tests for detecting where a version is built (local machine or GitHub Actions)."""

from __future__ import annotations

from pathlib import Path

import pytest

from consolidated_agent_release_deployment.gitutil import GitError, git, try_git
from consolidated_agent_release_deployment.source import detect_source

GITHUB_ENV = {
    "GITHUB_ACTIONS": "true",
    "GITHUB_ACTOR": "octo-user",
    "GITHUB_REPOSITORY": "owner/project",
    "GITHUB_RUN_ID": "42",
    "GITHUB_SERVER_URL": "https://github.com",
    "GITHUB_SHA": "a" * 40,
    "GITHUB_REF": "refs/heads/main",
}


def test_local_source_uses_git(repo: Path) -> None:
    source, who = detect_source(repo / "agents" / "helpful_summarizer", env={})
    assert source.platform == "local"
    assert source.agent_path == "agents/helpful_summarizer"
    assert source.commit == git(["rev-parse", "HEAD"], repo)
    assert source.uncommitted_changes is False
    assert source.run_id is None
    assert who == "Test User"


def test_uncommitted_changes_are_noticed(repo: Path) -> None:
    agent = repo / "agents" / "helpful_summarizer"
    (agent / "agent.py").write_text("# edited\n")
    source, _ = detect_source(agent, env={})
    assert source.uncommitted_changes is True


def test_changes_in_another_agent_do_not_count(repo: Path) -> None:
    (repo / "agents" / "secret_leaker" / "agent.py").write_text("# edited\n")
    source, _ = detect_source(repo / "agents" / "helpful_summarizer", env={})
    assert source.uncommitted_changes is False


def test_github_actions_source(repo: Path) -> None:
    source, who = detect_source(repo / "agents" / "helpful_summarizer", env=GITHUB_ENV)
    assert who == "octo-user"
    assert source.platform == "github-actions"
    assert source.commit == "a" * 40
    assert source.repository == "owner/project"
    assert source.ref == "refs/heads/main"
    assert source.run_url == "https://github.com/owner/project/actions/runs/42"


def test_folder_outside_git(tmp_path: Path) -> None:
    source, who = detect_source(tmp_path, env={})
    assert source.commit is None
    assert source.uncommitted_changes is None
    assert source.agent_path == tmp_path.resolve().as_posix()
    assert who  # falls back to the computer's user name


def test_git_errors_include_gits_message(tmp_path: Path) -> None:
    with pytest.raises(GitError, match="not a git repository"):
        git(["rev-parse", "HEAD"], tmp_path)
    assert try_git(["rev-parse", "HEAD"], tmp_path) is None


def test_missing_git_program(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(GitError, match="git is not installed"):
        git(["status"], tmp_path)
