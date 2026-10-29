"""Work out *where* a version is being built: on a laptop or in a CI run.

This is the only module that knows about a specific pipeline platform. The rest of the
code sees a neutral ``Source``. Adding Azure DevOps later means adding one function
here, not changing the record (ADR 0008, decision 12).
"""

from __future__ import annotations

import getpass
from collections.abc import Mapping
from pathlib import Path

from consolidated_agent_release_deployment.gitutil import try_git
from consolidated_agent_release_deployment.version_record import Source


def detect_source(agent_dir: Path, env: Mapping[str, str]) -> tuple[Source, str]:
    """Return the ``Source`` section and who is creating the record.

    ``env`` is the environment (normally ``os.environ``), passed in so tests can fake it.
    """
    top = try_git(["rev-parse", "--show-toplevel"], agent_dir)
    agent_path = agent_dir.resolve().as_posix()
    if top is not None:
        agent_path = agent_dir.resolve().relative_to(Path(top).resolve()).as_posix() or "."
    commit = try_git(["rev-parse", "HEAD"], agent_dir)
    status = try_git(["status", "--porcelain", "--", "."], agent_dir)
    uncommitted = None if status is None else bool(status)

    if env.get("GITHUB_ACTIONS") == "true":
        return _github_source(env, agent_path, commit, uncommitted), env.get("GITHUB_ACTOR", "")

    who = try_git(["config", "user.name"], agent_dir) or getpass.getuser()
    source = Source(
        platform="local", agent_path=agent_path, commit=commit, uncommitted_changes=uncommitted
    )
    return source, who


def _github_source(
    env: Mapping[str, str], agent_path: str, commit: str | None, uncommitted: bool | None
) -> Source:
    # Names of the variables GitHub Actions sets in every run.
    server = env.get("GITHUB_SERVER_URL", "https://github.com")
    repo = env.get("GITHUB_REPOSITORY")
    run_id = env.get("GITHUB_RUN_ID")
    run_url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else None
    return Source(
        platform="github-actions",
        agent_path=agent_path,
        commit=env.get("GITHUB_SHA") or commit,
        uncommitted_changes=uncommitted,
        repository=repo,
        ref=env.get("GITHUB_REF"),
        run_id=run_id,
        run_url=run_url,
    )


def write_github_summary(env: Mapping[str, str], markdown: str) -> None:
    """Add ``markdown`` to the run's summary page. Does nothing outside GitHub Actions."""
    path = env.get("GITHUB_STEP_SUMMARY")
    if path:
        with Path(path).open("a", encoding="utf-8") as f:
            f.write(markdown)
