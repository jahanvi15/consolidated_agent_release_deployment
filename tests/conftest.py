"""Shared test helpers ("fixtures"). pytest finds this file automatically."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from consolidated_agent_release_deployment.gitutil import git
from sample_agents.harness import AGENTS_DIR

# A fixed identity for test commits, so tests never depend on the machine's Git setup.
IDENTITY = ["-c", "user.name=Test User", "-c", "user.email=test@example.invalid"]


def commit_all(repo: Path, message: str = "change") -> str:
    git(["add", "-A"], repo)
    git([*IDENTITY, "commit", "--quiet", "-m", message], repo)
    return git(["rev-parse", "HEAD"], repo)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A fresh Git repository (no network) containing a copy of the sample agents."""
    root = tmp_path / "repo"
    shutil.copytree(AGENTS_DIR, root / "agents", ignore=shutil.ignore_patterns("__pycache__"))
    git(["init", "--quiet", "--initial-branch=main"], tmp_path / "repo")
    git(["config", "user.name", "Test User"], root)
    commit_all(root, "add agents")
    return root
